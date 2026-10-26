#!/usr/bin/env python3
"""MAREFA AWS recovery, run from AWS CloudShell (eu-north-1) on the console session's own credentials.

Steps (each paid step needs --confirm):
  inspect            read-only: account, instance, volumes, KMS, permissions (dry run), prices
  snapshot --confirm snapshot the original volume (instance must be stopped; it is never started)
  launch   --confirm restored volume + isolated inspector (no inbound rules, SSM only) + private bucket
  extract            run the read-only extraction on the inspector; archives go to the bucket
  presign            download list for Windows (HTTPS presigned links + SHA256)
  status             show recorded state
  cleanup  --confirm terminate the inspector and delete the restored copy only

Never touched: the original instance, its volumes, and any snapshot (no delete call exists here).
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REGION = "eu-north-1"
LOCATION = "EU (Stockholm)"
INSTANCE_NAME = "financial-data-engine"
TAG_KEY, TAG_VALUE = "marefa-recovery", "true"
INSPECTOR_TYPE = "t3.medium"
INSPECTOR_ROOT_GIB = 160  # room for consistent SQLite copies and PostgreSQL overlays
ROLE_NAME = "marefa-recovery-inspector"
SG_NAME = "marefa-recovery-inspector-no-inbound"
PASSPHRASE_PARAM = "/marefa-recovery/secrets-passphrase"
HOME = Path.home() / "marefa-recovery"
STATE_FILE = HOME / "state.json"
HERE = Path(__file__).resolve().parent
# Used only when the Pricing API cannot be read; reported as such.
FALLBACK_USD = {"snapshot_gb_month": 0.05, "gp3_gb_month": 0.0836, "t3_medium_hour": 0.0432,
                "transfer_out_gb": 0.09, "s3_standard_gb_month": 0.023}

session = boto3.session.Session(region_name=REGION)
ec2 = session.client("ec2")


def tags(name: str) -> list[dict]:
    return [{"Key": TAG_KEY, "Value": TAG_VALUE}, {"Key": "Name", "Value": name}]


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(**values) -> dict:
    HOME.mkdir(parents=True, exist_ok=True)
    state = {**load_state(), **values}
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    return state


def write_report(name: str, data: dict) -> Path:
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    return path


def need_confirm(args, what: str) -> None:
    if not args.confirm:
        sys.exit(f"STOP: {what} creates paid resources. Re-run with --confirm after approving the cost shown by 'inspect'.")


# ---------------------------------------------------------------- discovery

def find_instance(instance_id: str | None) -> dict:
    if instance_id:
        found = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"]
    else:
        found = ec2.describe_instances(Filters=[{"Name": "tag:Name", "Values": [INSTANCE_NAME]}])["Reservations"]
    instances = [i for r in found for i in r["Instances"] if i["State"]["Name"] != "terminated"]
    if len(instances) != 1:
        listing = [(i["InstanceId"], i["State"]["Name"]) for i in instances]
        sys.exit(f"STOP: expected one instance named {INSTANCE_NAME}, found {listing}. Pass --instance-id.")
    return instances[0]


def require_stopped(instance: dict) -> None:
    state = instance["State"]["Name"]
    if state != "stopped":
        sys.exit(f"STOP: instance {instance['InstanceId']} is '{state}', not 'stopped'. Nothing was changed.")


def dry_run(call, **kwargs) -> str:
    try:
        call(DryRun=True, **kwargs)
    except ClientError as error:
        code = error.response["Error"]["Code"]
        return "allowed" if code == "DryRunOperation" else f"denied ({code})"
    return "allowed"


def latest_al2023_ami() -> str:
    ssm = session.client("ssm")
    return ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64")["Parameter"]["Value"]


def kms_report(key_id: str, caller_arn: str) -> dict:
    kms = session.client("kms")
    out = {"key": key_id}
    try:
        meta = kms.describe_key(KeyId=key_id)["KeyMetadata"]
        out.update(arn=meta["Arn"], state=meta["KeyState"], manager=meta["KeyManager"], enabled=meta["Enabled"])
    except ClientError as error:
        out["describe_key"] = f"denied ({error.response['Error']['Code']})"
    principal = caller_arn
    if ":assumed-role/" in caller_arn:  # simulate against the role behind the console session
        account = caller_arn.split(":")[4]
        principal = f"arn:aws:iam::{account}:role/{caller_arn.split('/')[1]}"
    actions = ["kms:CreateGrant", "kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKeyWithoutPlaintext",
               "kms:ReEncryptFrom", "kms:ReEncryptTo"]
    try:
        results = session.client("iam").simulate_principal_policy(
            PolicySourceArn=principal, ActionNames=actions,
            ResourceArns=[out.get("arn", f"arn:aws:kms:{REGION}:*:key/*")])["EvaluationResults"]
        out["iam_simulation"] = {r["EvalActionName"]: r["EvalDecision"] for r in results}
    except ClientError as error:
        out["iam_simulation"] = f"not available ({error.response['Error']['Code']}); a missing KMS right shows at 'launch' and changes nothing"
    if out.get("manager") == "AWS":
        out["note"] = "AWS-managed key (aws/ebs): usable by any principal allowed to use EBS in this account"
    return out


# ---------------------------------------------------------------- prices

def _price(service: str, filters: dict) -> list[dict]:
    pricing = boto3.client("pricing", region_name="us-east-1")
    rows = pricing.get_products(ServiceCode=service, MaxResults=100,
                                Filters=[{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items()])
    dims = []
    for raw in rows["PriceList"]:
        item = json.loads(raw)
        for term in item.get("terms", {}).get("OnDemand", {}).values():
            for dim in term["priceDimensions"].values():
                usd = float(dim["pricePerUnit"].get("USD", "0"))
                dims.append({"usd": usd, "unit": dim["unit"], "begin": dim.get("beginRange"),
                             "description": dim["description"], "usagetype": item["product"]["attributes"].get("usagetype")})
    return dims


def prices() -> dict:
    found, source = {}, {}
    queries = {
        "snapshot_gb_month": ("AmazonEC2", {"location": LOCATION, "productFamily": "Storage Snapshot"},
                              lambda d: "SnapshotUsage" in (d["usagetype"] or "") and "Archive" not in d["description"]),
        "gp3_gb_month": ("AmazonEC2", {"location": LOCATION, "productFamily": "Storage", "volumeApiName": "gp3"},
                         lambda d: d["unit"].startswith("GB")),
        "t3_medium_hour": ("AmazonEC2", {"location": LOCATION, "instanceType": INSPECTOR_TYPE, "operatingSystem": "Linux",
                                         "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"},
                           lambda d: d["unit"] == "Hrs"),
        "transfer_out_gb": ("AWSDataTransfer", {"fromLocation": LOCATION, "toLocation": "External",
                                                "transferType": "AWS Outbound"},
                            lambda d: d["usd"] > 0),
        "s3_standard_gb_month": ("AmazonS3", {"location": LOCATION, "storageClass": "General Purpose",
                                              "volumeType": "Standard"}, lambda d: d["unit"].startswith("GB")),
    }
    for key, (service, filters, keep) in queries.items():
        try:
            dims = [d for d in _price(service, filters) if keep(d) and d["usd"] > 0]
            if dims:  # first paid tier
                found[key] = max(dims, key=lambda d: d["usd"])["usd"] if key == "transfer_out_gb" else dims[0]["usd"]
                source[key] = "AWS Pricing API"
                continue
        except ClientError as error:
            source[key] = f"fallback ({error.response['Error']['Code']})"
        found.setdefault(key, FALLBACK_USD[key])
        source.setdefault(key, "fallback list price, Pricing API returned nothing")
    return {"usd": found, "source": source}


def cost_table(price: dict, used_gib: float, volume_gib: int, hours: float = 24, days_kept: float = 3) -> dict:
    p = price["usd"]
    archive_gib = used_gib  # compressed archives are usually smaller; upper bound
    one_time = {
        "restored_gp3_volume": volume_gib * p["gp3_gb_month"] * days_kept / 30,
        "inspector_instance": hours * p["t3_medium_hour"],
        "inspector_root_volume": INSPECTOR_ROOT_GIB * p["gp3_gb_month"] * days_kept / 30,
        "s3_staging_storage": archive_gib * p["s3_standard_gb_month"] * days_kept / 30,
        "transfer_to_windows_no_free_tier": archive_gib * p["transfer_out_gb"],
    }
    return {"assumed_used_gib": round(used_gib, 2),
            "snapshot_per_month": round(used_gib * p["snapshot_gb_month"], 2),
            "one_time": {k: round(v, 2) for k, v in one_time.items()},
            "one_time_total": round(sum(one_time.values()), 2),
            "note": "Transfer: the first 100 GB/month out to the internet are free per account if not used elsewhere. "
                    "S3 bucket and archives stay until you delete them after local verification."}


# ---------------------------------------------------------------- commands

def cmd_inspect(args) -> None:
    identity = session.client("sts").get_caller_identity()
    instance = find_instance(args.instance_id)
    volumes = ec2.describe_volumes(VolumeIds=[m["Ebs"]["VolumeId"] for m in instance["BlockDeviceMappings"]])["Volumes"]
    mapping = {m["Ebs"]["VolumeId"]: m for m in instance["BlockDeviceMappings"]}
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "account": identity["Account"], "caller": identity["Arn"], "region": REGION,
        "instance": {
            "id": instance["InstanceId"], "state": instance["State"]["Name"],
            "state_reason": instance.get("StateReason", {}).get("Message"),
            "transition": instance.get("StateTransitionReason"), "type": instance["InstanceType"],
            "az": instance["Placement"]["AvailabilityZone"], "platform": instance.get("PlatformDetails"),
            "image": instance["ImageId"], "launch_time": instance["LaunchTime"],
            "vpc": instance.get("VpcId"), "subnet": instance.get("SubnetId"),
            "root_device": instance.get("RootDeviceName"),
            "tags": {t["Key"]: t["Value"] for t in instance.get("Tags", [])},
        },
        "volumes": [],
    }
    try:
        attr = ec2.describe_instance_attribute(InstanceId=instance["InstanceId"], Attribute="disableApiTermination")
        report["instance"]["termination_protection"] = attr["DisableApiTermination"]["Value"]
    except ClientError:
        pass
    for volume in volumes:
        vid = volume["VolumeId"]
        entry = {"id": vid, "device": mapping[vid]["DeviceName"], "size_gib": volume["Size"], "type": volume["VolumeType"],
                 "state": volume["State"], "encrypted": volume["Encrypted"], "kms_key": volume.get("KmsKeyId"),
                 "delete_on_termination": mapping[vid]["Ebs"].get("DeleteOnTermination"),
                 "created": volume["CreateTime"], "from_snapshot": volume.get("SnapshotId") or None,
                 "existing_snapshots": [
                     {"id": s["SnapshotId"], "start": s["StartTime"], "state": s["State"],
                      "full_size_bytes": s.get("FullSnapshotSizeInBytes")}
                     for s in ec2.describe_snapshots(OwnerIds=["self"],
                                                     Filters=[{"Name": "volume-id", "Values": [vid]}])["Snapshots"]],
                 "dry_run_create_snapshot": dry_run(ec2.create_snapshot, VolumeId=vid)}
        if volume["Encrypted"]:
            entry["kms"] = kms_report(volume["KmsKeyId"], identity["Arn"])
        report["volumes"].append(entry)
    try:
        ami = latest_al2023_ami()
        report["dry_run_launch_inspector"] = dry_run(
            ec2.run_instances, ImageId=ami, InstanceType=INSPECTOR_TYPE, MinCount=1, MaxCount=1,
            Placement={"AvailabilityZone": report["instance"]["az"]})
    except ClientError as error:
        report["dry_run_launch_inspector"] = f"denied ({error.response['Error']['Code']})"
    report["dry_run_create_volume"] = dry_run(ec2.create_volume, AvailabilityZone=report["instance"]["az"],
                                              Size=1, VolumeType="gp3")
    price = prices()
    size = sum(v["size_gib"] for v in report["volumes"])
    report["prices"] = price
    report["cost_scenarios_by_used_space"] = {f"{g}GiB": cost_table(price, g, size)
                                              for g in sorted({10, 30, 60, size})}
    report["warnings"] = []
    if report["instance"]["state"] != "stopped":
        report["warnings"].append("instance is not stopped: snapshot step will refuse")
    if any(v["delete_on_termination"] for v in report["volumes"]):
        report["warnings"].append("a volume is DeleteOnTermination=true: terminating the instance would delete it; "
                                  "the snapshot protects against that")
    path = write_report("01-inspect.json", report)
    save_state(account=report["account"], instance_id=instance["InstanceId"], az=report["instance"]["az"],
               volumes=[v["id"] for v in report["volumes"]], volume_gib=size)
    print(json.dumps({k: report[k] for k in ("account", "instance", "volumes", "dry_run_launch_inspector",
                                             "dry_run_create_volume", "warnings")}, indent=2, default=str))
    print("\nCost (USD) by used space; the exact used space is measured right after the snapshot:")
    for key, table in report["cost_scenarios_by_used_space"].items():
        print(f"  used {key:>7}: snapshot {table['snapshot_per_month']}/month, one-time ~{table['one_time_total']}")
    print(f"  price source: {json.dumps(price['source'])}")
    print(f"\nFull report: {path}  (contains no credentials)")


def snapshot_size_bytes(snapshot_id: str) -> int | None:
    snap = ec2.describe_snapshots(SnapshotIds=[snapshot_id])["Snapshots"][0]
    if snap.get("FullSnapshotSizeInBytes"):
        return snap["FullSnapshotSizeInBytes"]
    try:  # EBS direct API: written blocks only
        ebs = session.client("ebs")
        count, size, token = 0, 0, None
        while True:
            kwargs = {"SnapshotId": snapshot_id, "MaxResults": 10000, **({"NextToken": token} if token else {})}
            page = ebs.list_snapshot_blocks(**kwargs)
            count += len(page["Blocks"]); size = page["BlockSize"]; token = page.get("NextToken")
            if not token:
                return count * size
    except ClientError:
        return None


def cmd_snapshot(args) -> None:
    need_confirm(args, "snapshot")
    state = load_state()
    instance = find_instance(args.instance_id or state.get("instance_id"))
    require_stopped(instance)
    done = dict(state.get("snapshots", {}))
    for mapping in instance["BlockDeviceMappings"]:
        vid = mapping["Ebs"]["VolumeId"]
        if vid in done:
            print(f"{vid}: already snapshotted as {done[vid]}"); continue
        snap = ec2.create_snapshot(
            VolumeId=vid, Description=f"MAREFA recovery of {INSTANCE_NAME} {vid} (original untouched)",
            TagSpecifications=[{"ResourceType": "snapshot", "Tags": tags(f"marefa-recovery-{vid}")}])
        done[vid] = snap["SnapshotId"]
        save_state(snapshots=done)
        print(f"{vid}: snapshot {snap['SnapshotId']} started")
    for vid, sid in done.items():
        while True:
            snap = ec2.describe_snapshots(SnapshotIds=[sid])["Snapshots"][0]
            print(f"  {sid}: {snap['State']} {snap.get('Progress', '')}", flush=True)
            if snap["State"] == "completed":
                break
            if snap["State"] == "error":
                sys.exit(f"STOP: snapshot {sid} failed: {snap.get('StateMessage')}")
            time.sleep(30)
    sizes = {sid: snapshot_size_bytes(sid) for sid in done.values()}
    used = sum(b for b in sizes.values() if b) / 2**30
    save_state(snapshot_bytes=sizes, used_gib=used)
    price = prices()
    table = cost_table(price, used, load_state().get("volume_gib", 100))
    write_report("02-snapshot.json", {"snapshots": done, "bytes": sizes, "cost": table})
    print(json.dumps({"snapshots": done, "used_gib": round(used, 2), "cost_usd": table}, indent=2))
    print("\nOriginal instance and volume untouched. Next (after approving the one-time cost): launch --confirm")


def ensure_role(iam, bucket: str) -> str:
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"},
                                                     "Action": "sts:AssumeRole"}]}
    try:
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust),
                        Description="MAREFA recovery inspector (temporary)", Tags=tags(ROLE_NAME))
    except iam.exceptions.EntityAlreadyExistsException:
        pass
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")
    account = load_state()["account"]
    inline = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject", "s3:AbortMultipartUpload"],
         "Resource": f"arn:aws:s3:::{bucket}/*"},
        {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": f"arn:aws:s3:::{bucket}"},
        {"Effect": "Allow", "Action": ["ssm:PutParameter"],
         "Resource": f"arn:aws:ssm:{REGION}:{account}:parameter{PASSPHRASE_PARAM}"}]}
    iam.put_role_policy(RoleName=ROLE_NAME, PolicyName="marefa-recovery-bucket", PolicyDocument=json.dumps(inline))
    try:
        iam.create_instance_profile(InstanceProfileName=ROLE_NAME, Tags=tags(ROLE_NAME))
        iam.add_role_to_instance_profile(InstanceProfileName=ROLE_NAME, RoleName=ROLE_NAME)
        time.sleep(15)  # profile propagation
    except iam.exceptions.EntityAlreadyExistsException:
        pass
    return ROLE_NAME


def ensure_bucket(state: dict) -> str:
    s3 = session.client("s3")
    bucket = state.get("bucket") or f"marefa-recovery-{state['account']}-{secrets.token_hex(3)}"
    try:
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": REGION})
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass
    s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    s3.put_bucket_encryption(Bucket=bucket, ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]})
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps({"Version": "2012-10-17", "Statement": [{
        "Sid": "TlsOnly", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}))
    s3.put_bucket_tagging(Bucket=bucket, Tagging={"TagSet": tags(bucket)})
    save_state(bucket=bucket)
    return bucket


def inspector_subnet(instance: dict) -> tuple[str, str]:
    """A subnet in the original's AZ with an internet route (SSM agent and package downloads)."""
    az = instance["Placement"]["AvailabilityZone"]
    candidates = ec2.describe_subnets(Filters=[{"Name": "availability-zone", "Values": [az]}])["Subnets"]
    candidates.sort(key=lambda s: (not s.get("DefaultForAz"), s["SubnetId"] != instance.get("SubnetId")))
    for subnet in candidates:
        tables = ec2.describe_route_tables(Filters=[{"Name": "association.subnet-id", "Values": [subnet["SubnetId"]]}])["RouteTables"] \
            or ec2.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [subnet["VpcId"]]},
                                                  {"Name": "association.main", "Values": ["true"]}])["RouteTables"]
        if any(r.get("GatewayId", "").startswith("igw-") and r.get("DestinationCidrBlock") == "0.0.0.0/0"
               for t in tables for r in t["Routes"]):
            return subnet["SubnetId"], subnet["VpcId"]
    sys.exit(f"STOP: no subnet in {az} has an internet gateway route; the inspector needs one for SSM.")


def cmd_launch(args) -> None:
    need_confirm(args, "launch")
    state = load_state()
    if not state.get("snapshots"):
        sys.exit("STOP: run 'snapshot --confirm' first.")
    instance = find_instance(state["instance_id"])
    require_stopped(instance)
    subnet, vpc = inspector_subnet(instance)  # free checks before anything is created
    bucket = ensure_bucket(state)
    profile = ensure_role(session.client("iam"), bucket)
    if not state.get("security_group"):
        sg = ec2.create_security_group(GroupName=SG_NAME, VpcId=vpc, Description="MAREFA recovery: no inbound rules",
                                       TagSpecifications=[{"ResourceType": "security-group", "Tags": tags(SG_NAME)}])
        save_state(security_group=sg["GroupId"])
    state = load_state()
    if not state.get("inspector_id"):
        for attempt in range(6):
            try:
                run = ec2.run_instances(
                    ImageId=latest_al2023_ami(), InstanceType=INSPECTOR_TYPE, MinCount=1, MaxCount=1,
                    IamInstanceProfile={"Name": profile},
                    NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": subnet, "Groups": [state["security_group"]],
                                        "AssociatePublicIpAddress": True}],
                    MetadataOptions={"HttpTokens": "required"},
                    BlockDeviceMappings=[{"DeviceName": "/dev/xvda", "Ebs": {
                        "VolumeSize": INSPECTOR_ROOT_GIB, "VolumeType": "gp3", "DeleteOnTermination": True, "Encrypted": True}}],
                    TagSpecifications=[{"ResourceType": "instance", "Tags": tags("marefa-recovery-inspector")},
                                       {"ResourceType": "volume", "Tags": tags("marefa-recovery-inspector-root")}])
                save_state(inspector_id=run["Instances"][0]["InstanceId"]); break
            except ClientError as error:
                if "instance profile" not in str(error).lower() or attempt == 5:
                    raise
                time.sleep(10)
    state = load_state()
    ec2.get_waiter("instance_running").wait(InstanceIds=[state["inspector_id"]])
    restored = dict(state.get("restored_volumes", {}))
    letters = iter("fghijklmnop")
    for vid, sid in state["snapshots"].items():
        if vid not in restored:
            vol = ec2.create_volume(SnapshotId=sid, AvailabilityZone=instance["Placement"]["AvailabilityZone"],
                                    VolumeType="gp3",
                                    TagSpecifications=[{"ResourceType": "volume", "Tags": tags(f"marefa-restored-{vid}")}])
            restored[vid] = vol["VolumeId"]
            save_state(restored_volumes=restored)
    ec2.get_waiter("volume_available").wait(VolumeIds=list(restored.values()))
    for vid, rid in restored.items():
        current = ec2.describe_volumes(VolumeIds=[rid])["Volumes"][0]
        if not current["Attachments"]:
            ec2.attach_volume(VolumeId=rid, InstanceId=state["inspector_id"], Device=f"/dev/sd{next(letters)}")
    ec2.get_waiter("volume_in_use").wait(VolumeIds=list(restored.values()))
    print("waiting for the SSM agent on the inspector ...", flush=True)
    ssm = session.client("ssm")
    for _ in range(60):
        info = ssm.describe_instance_information(Filters=[{"Key": "InstanceIds", "Values": [state["inspector_id"]]}])
        if info["InstanceInformationList"] and info["InstanceInformationList"][0]["PingStatus"] == "Online":
            break
        time.sleep(10)
    else:
        sys.exit("STOP: SSM agent not online after 10 minutes; nothing was extracted. Re-run 'launch --confirm' to resume.")
    print(json.dumps({"bucket": bucket, "inspector": state["inspector_id"], "restored_volumes": restored,
                      "inbound_rules": 0}, indent=2))
    print("Next: python3 marefa_recovery.py extract")


def ssm_run(commands: list[str], timeout_s: int = 300) -> str:
    """Run a short command on the inspector and return its output."""
    ssm = session.client("ssm")
    iid = load_state()["inspector_id"]
    cid = ssm.send_command(InstanceIds=[iid], DocumentName="AWS-RunShellScript",
                           Parameters={"commands": commands, "executionTimeout": [str(timeout_s)]})["Command"]["CommandId"]
    for _ in range(timeout_s // 3 + 20):
        time.sleep(3)
        try:
            inv = ssm.get_command_invocation(CommandId=cid, InstanceId=iid)
        except ClientError:
            continue
        if inv["Status"] not in {"Pending", "InProgress", "Delayed"}:
            if inv["Status"] != "Success":
                raise RuntimeError(f"{inv['Status']}: {inv.get('StandardErrorContent', '')[-1000:]}")
            return inv.get("StandardOutputContent", "")
    raise RuntimeError("short SSM command timed out")


STATUS = ["if systemctl is-active --quiet marefa-extract; then echo STATE=running; "
          "else echo STATE=$(cat /opt/marefa/extract.status 2>/dev/null || echo none); fi",
          "tail -n 2 /opt/marefa/extract.log 2>/dev/null || true"]


def extraction_state() -> tuple[str, str]:
    out = ssm_run(STATUS, 60).strip().splitlines()
    state = out[0].split("=", 1)[1] if out and out[0].startswith("STATE=") else "unknown"
    return state, " | ".join(line.strip() for line in out[1:])[-200:]


def start_extraction(bucket: str, prefix: str) -> None:
    """Run extract.sh as its own systemd unit, so it does not depend on the SSM document worker."""
    state = load_state()
    volumes = " ".join(state["restored_volumes"].values())
    job = (f"bash /opt/marefa/extract.sh {bucket} {prefix} {REGION} {PASSPHRASE_PARAM} {volumes} "
           "> /opt/marefa/extract.log 2>&1; echo $? > /opt/marefa/extract.status; "
           f"aws s3 cp --only-show-errors --region {REGION} /opt/marefa/extract.log s3://{bucket}/{prefix}/logs/extract.log")
    ssm_run([
        "set -e", "mkdir -p /opt/marefa",
        "pkill -f /opt/marefa/extract.sh || true", "sleep 2",
        "systemctl stop marefa-extract 2>/dev/null || true", "systemctl reset-failed marefa-extract 2>/dev/null || true",
        "rm -f /opt/marefa/extract.status /opt/marefa/extract.log",
        f"aws s3 cp --only-show-errors --region {REGION} s3://{bucket}/tools/extract.sh /opt/marefa/extract.sh",
        f"aws s3 cp --only-show-errors --region {REGION} s3://{bucket}/tools/dbprofile.py /opt/marefa/dbprofile.py",
        "systemd-run --unit marefa-extract --collect --setenv=HOME=/root bash -c '" + job + "'",
    ], 300)


def cmd_extract(args) -> None:
    state = load_state()
    if not state.get("inspector_id"):
        sys.exit("STOP: run 'launch --confirm' first.")
    s3 = session.client("s3")
    bucket = state["bucket"]
    current, _ = extraction_state()
    if current == "running" and state.get("prefix"):
        print("resuming: the extraction is already running on the inspector")
        prefix = state["prefix"]
    elif current == "0" and state.get("prefix"):
        prefix = state["prefix"]
    else:
        for name in ("extract.sh", "dbprofile.py"):
            s3.upload_file(str(HERE / "inspector" / name), bucket, f"tools/{name}")
        prefix = f"recovery/{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        save_state(prefix=prefix, last_command=None)
        start_extraction(bucket, prefix)
        print(f"extraction started as a service on the inspector (log: s3://{bucket}/{prefix}/logs/extract.log)")
    while True:
        try:
            current, tail = extraction_state()
        except RuntimeError as error:
            current, tail = "unknown", f"status check failed ({str(error)[:80]}); retrying"
        print(f"  [{datetime.now(timezone.utc):%H:%M:%S}] {current}: {tail}", flush=True)
        if current not in {"running", "unknown"}:
            break
        time.sleep(60)
    if current != "0":
        print(ssm_run(["tail -n 40 /opt/marefa/extract.log"], 60))
        sys.exit(f"STOP: extraction ended with exit code {current}. Source copy untouched. "
                 "Send the lines above; re-running 'extract' starts it again.")
    save_state(extracted_prefix=prefix)
    s3.download_file(bucket, f"{prefix}/inventory.json", str(HOME / "inventory.json"))
    print(f"\nInventory: {HOME / 'inventory.json'} (no credentials; attach it in the chat for the comparison).")
    print("Next: python3 ~/marefa/marefa_recovery.py presign")


def cmd_presign(args) -> None:
    state = load_state()
    s3 = session.client("s3")
    bucket, prefix = state["bucket"], state.get("extracted_prefix") or state["prefix"]
    manifest = json.loads(s3.get_object(Bucket=bucket, Key=f"{prefix}/manifest.json")["Body"].read())
    expires = args.hours * 3600
    lines = ["relative_path\tsize\tsha256\turl"]
    for item in manifest["objects"]:
        url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": f"{prefix}/{item['path']}"},
                                        ExpiresIn=expires)
        lines.append(f"{item['path']}\t{item['size']}\t{item['sha256']}\t{url}")
    out = HOME / "download-list.tsv"
    out.write_text("\n".join(lines) + "\n")
    total = sum(i["size"] for i in manifest["objects"])
    print(f"{len(manifest['objects'])} files, {total / 2**30:.2f} GiB -> {out}")
    print("The links work only while this CloudShell session's credentials are valid (often about an hour); "
          "re-run 'presign' and the Windows script resumes where it stopped. Do not share this file.")


def cmd_all(args) -> None:
    """Extraction (or resume) -> download list -> one PowerShell line for Windows."""
    cmd_extract(args)
    cmd_presign(args)
    state = load_state()
    s3 = session.client("s3")
    bucket, prefix = state["bucket"], state["extracted_prefix"]
    s3.upload_file(str(HERE / "Receive-MarefaRecovery.ps1"), bucket, f"{prefix}/windows/Receive-MarefaRecovery.ps1")
    s3.upload_file(str(HOME / "download-list.tsv"), bucket, f"{prefix}/windows/download-list.tsv")
    link = lambda key: s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key},
                                                 ExpiresIn=args.hours * 3600)
    script, listing = link(f"{prefix}/windows/Receive-MarefaRecovery.ps1"), link(f"{prefix}/windows/download-list.tsv")
    line = (f"cd $HOME\\Downloads; curl.exe -sSfo Receive-MarefaRecovery.ps1 \"{script}\"; "
            f"curl.exe -sSfo download-list.tsv \"{listing}\"; "
            "powershell -ExecutionPolicy Bypass -File .\\Receive-MarefaRecovery.ps1 -ListFile .\\download-list.tsv")
    (HOME / "windows-command.txt").write_text(line + "\n")
    print("\n=== Copy the ONE line below into Windows PowerShell on your laptop (do not share it) ===\n")
    print(line)
    print("\n(also saved in ~/marefa-recovery/windows-command.txt; links last while this CloudShell session is valid —"
          " if they expire, run this command again and the download resumes)")


def cmd_status(args) -> None:
    print(json.dumps(load_state(), indent=2))


def cmd_cleanup(args) -> None:
    need_confirm(args, "cleanup (deletes only the inspector and the restored copy)")
    state = load_state()
    if state.get("inspector_id"):
        inst = ec2.describe_instances(InstanceIds=[state["inspector_id"]])["Reservations"][0]["Instances"][0]
        if {t["Key"]: t["Value"] for t in inst.get("Tags", [])}.get(TAG_KEY) != TAG_VALUE:
            sys.exit("STOP: inspector id is not tagged as a recovery resource.")
        ec2.terminate_instances(InstanceIds=[state["inspector_id"]])
        ec2.get_waiter("instance_terminated").wait(InstanceIds=[state["inspector_id"]])
    restored = list(state.get("restored_volumes", {}).values())
    if restored:
        ec2.get_waiter("volume_available").wait(VolumeIds=restored)  # detaches after the inspector terminates
    for rid in restored:
        vol = ec2.describe_volumes(VolumeIds=[rid])["Volumes"][0]
        if {t["Key"]: t["Value"] for t in vol.get("Tags", [])}.get(TAG_KEY) == TAG_VALUE and rid not in state.get("volumes", []):
            ec2.delete_volume(VolumeId=rid)
    if state.get("security_group"):
        ec2.delete_security_group(GroupId=state["security_group"])
    print("Removed: inspector, restored copy, security group. Kept: original instance and volume, snapshot(s), "
          f"bucket {state.get('bucket')} (delete it yourself only after the Windows copy is verified).")
    save_state(inspector_id=None, restored_volumes={}, security_group=None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["inspect", "snapshot", "launch", "extract", "presign", "all", "status", "cleanup"])
    parser.add_argument("--instance-id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--hours", type=int, default=12, help="presigned link lifetime (capped by the session)")
    args = parser.parse_args()
    globals()[f"cmd_{args.command}"](args)


if __name__ == "__main__":
    main()
