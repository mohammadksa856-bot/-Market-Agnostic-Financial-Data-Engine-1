#!/bin/bash
# MAREFA recovery extraction, run on the isolated inspector through SSM.
# usage: extract.sh <bucket> <prefix> <region> <passphrase-param> <restored-volume-id>...
# The restored volumes are set read-only at the block layer and mounted without journal replay.
# PostgreSQL clusters run on an overlay (writes go to the inspector disk, never to the restored copy).
set -euo pipefail
trap 'echo "[$(date -u +%H:%M:%S)] STOPPED at line $LINENO: $BASH_COMMAND (exit $?)"' ERR
BUCKET=$1; PREFIX=$2; REGION=$3; PASS_PARAM=$4; shift 4; VOLUMES=("$@")
WORK=/opt/marefa/work; MNT=/mnt/marefa; TOOLS=/opt/marefa
# A previous attempt may have left processes, containers and mounts behind. Read-only mounts are reused;
# the file listings and the scan are kept, so a re-run resumes after them.
pkill -f "$TOOLS/dbprofile.py" 2>/dev/null || true
for c in $(docker ps -aq --filter name=marefa-pg 2>/dev/null); do docker rm -f "$c" >/dev/null; done
for d in /opt/marefa/pg/*/data; do if mountpoint -q "$d"; then umount "$d"; fi; done
rm -rf /opt/marefa/pg "$WORK/sqlite" "$WORK/hashes.tsv" "$WORK/pg-profile.jsonl" "$WORK"/secrets-extra.list
mkdir -p "$WORK" "$MNT"; cd "$WORK"
log() { echo "[$(date -u +%H:%M:%S)] $*"; }
s3put() { aws s3 cp --only-show-errors --region "$REGION" "$1" "s3://$BUCKET/$PREFIX/$2"; }

# Stream stdin to S3 while recording size and SHA256 in $WORK/hashes.tsv.
stream_up() {  # stream_up <relative-key> <expected-size>
  local key=$1 expected=$2
  python3 -c '
import hashlib, sys
h = hashlib.sha256(); n = 0
src, dst = sys.stdin.buffer, sys.stdout.buffer
while True:
    block = src.read(8 << 20)
    if not block: break
    h.update(block); n += len(block); dst.write(block)
dst.flush()
open(sys.argv[1], "a").write(f"{sys.argv[2]}\t{n}\t{h.hexdigest()}\n")' "$WORK/hashes.tsv" "$key" \
  | aws s3 cp --only-show-errors --region "$REGION" --expected-size "$expected" - "s3://$BUCKET/$PREFIX/$key"
}
put_file() {  # upload a small local file and record its hash
  local file=$1 key=$2
  printf '%s\t%s\t%s\n' "$key" "$(stat -c %s "$file")" "$(sha256sum "$file" | cut -d' ' -f1)" >> "$WORK/hashes.tsv"
  s3put "$file" "$key"
}

log "installing tools"
dnf install -y -q pigz git sqlite docker lvm2 xfsprogs e2fsprogs >/dev/null
command -v gpg >/dev/null || { log "gpg missing"; exit 4; }
if ! swapon --show=NAME --noheadings | grep -qx /marefa-swap; then
  fallocate -l 4G /marefa-swap && chmod 600 /marefa-swap && mkswap /marefa-swap >/dev/null && swapon /marefa-swap
fi
log "memory: $(free -m | awk '/Mem:/{print $2" MiB RAM"}'), swap $(swapon --show=SIZE --noheadings | head -1)"
systemctl start docker
: > "$WORK/hashes.tsv"

# ---------------------------------------------------------------- mount read-only
declare -a MOUNTS=()
for vol in "${VOLUMES[@]}"; do
  link=/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${vol/-/}
  for _ in $(seq 60); do [ -e "$link" ] && break; sleep 2; done
  disk=$(readlink -f "$link")
  log "volume $vol is $disk"
  blockdev --setro "$disk"
  for part in $(lsblk -lnpo NAME "$disk"); do blockdev --setro "$part"; done
  lsblk -Jbo NAME,FSTYPE,SIZE,LABEL,UUID,PARTLABEL,MOUNTPOINT "$disk" > "$WORK/lsblk-$vol.json"
  while read -r part fstype; do
    target="$MNT/$vol/$(basename "$part")"
    case "$fstype" in
      ext2|ext3|ext4) opts=ro,noload,noexec,nodev,nosuid ;;
      xfs) opts=ro,norecovery,nouuid,noexec,nodev,nosuid ;;
      btrfs) opts=ro,nologreplay,noexec,nodev,nosuid ;;
      vfat|ntfs) opts=ro,noexec,nodev,nosuid ;;
      LVM2_member) log "LVM on $part: activate read-only by hand (vgchange -ay --readonly); not mounted"; continue ;;
      *) log "skip $part ($fstype)"; continue ;;
    esac
    mkdir -p "$target"
    if findmnt -rno SOURCE "$target" | grep -qx "$part"; then MOUNTS+=("$target"); log "reusing mount of $part at $target"
    elif mount -t "$fstype" -o "$opts" "$part" "$target"; then MOUNTS+=("$target"); log "mounted $part ($fstype) ro at $target"
    else log "could not mount $part ($fstype)"; fi
  done < <(lsblk -lnpo NAME,FSTYPE "$disk" | awk 'NF==2')
done
[ ${#MOUNTS[@]} -gt 0 ] || { log "no filesystem mounted"; exit 2; }
for m in "${MOUNTS[@]}"; do
  findmnt -no OPTIONS "$m" | grep -qw ro || { log "SAFETY: $m is not read-only"; exit 3; }
done

# ---------------------------------------------------------------- inventory and secret candidates
SECRET_RE='(/\.env(\.[^/]*)?$|\.pem$|\.key$|\.p12$|\.pfx$|/id_(rsa|dsa|ecdsa|ed25519)$|/\.aws/credentials$|/\.netrc$|/\.pgpass$|/\.git-credentials$|/\.docker/config\.json$|/\.(bash|zsh|psql|mysql|python|sqlite)_history$|/etc/shadow-?$|/etc/gshadow-?$|/var/lib/docker/containers/[^/]+/config\.v2\.json$|/[^/]*(secret|credential)[^/]*\.(json|ya?ml|txt|ini|conf|cfg|env|toml|csv)$|/\.ssh/id_[^/]*$|/\.ssh/[^/]*_key$)'
for m in "${MOUNTS[@]}"; do
  tag=$(echo "${m#$MNT/}" | tr '/' '_')
  if [ -s "$WORK/files-$tag.tsv.gz" ] && [ -f "$WORK/secrets-$tag.list" ] && gzip -t "$WORK/files-$tag.tsv.gz" 2>/dev/null; then
    log "listing of $m kept from the previous attempt"; continue
  fi
  log "listing $m"
  find "$m" -xdev \( -path "$m/proc" -o -path "$m/sys" \) -prune -o -printf '%y\t%s\t%TY-%Tm-%Td\t%P\n' \
    | gzip > "$WORK/files-$tag.tsv.gz"
  zcat "$WORK/files-$tag.tsv.gz" | awk -F'\t' '$1=="f"{print $4}' \
    | grep -E "$SECRET_RE" | grep -vE '^(usr|lib|lib64|snap|opt/aws)/|/site-packages/|/node_modules/|/dist-packages/' \
    > "$WORK/secrets-$tag.list" || true
  # Git configs whose remote URL embeds a token or password
  zcat "$WORK/files-$tag.tsv.gz" | awk -F'\t' '$1=="f" && $4 ~ /(^|\/)\.git\/config$/ {print $4}' | while read -r cfg; do
    if grep -qE '://[^/@[:space:]]+@' "$m/$cfg"; then echo "$cfg"; fi
  done >> "$WORK/secrets-$tag.list"
  log "$(wc -l < "$WORK/secrets-$tag.list") secret candidates in $m (paths only are reported)"
done

if python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$WORK/scan.json" 2>/dev/null; then
  log "scan kept from the previous attempt"
else
  python3 "$TOOLS/dbprofile.py" scan "$WORK" "${MOUNTS[@]}" > "$WORK/scan.json.part"
  mv "$WORK/scan.json.part" "$WORK/scan.json"
fi
log "scan: $(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print({k:len(v) for k,v in d.items() if isinstance(v,list)})' "$WORK/scan.json")"

# ---------------------------------------------------------------- SQLite: consistent copies + profiles
mkdir -p "$WORK/sqlite"
python3 - "$WORK/scan.json" <<'EOF' > "$WORK/sqlite.list"
import json, sys
for item in json.load(open(sys.argv[1]))["sqlite"]: print(item["path"])
EOF
i=0
while read -r db; do
  [ -n "$db" ] || continue
  i=$((i+1)); copy="$WORK/sqlite/$i"; mkdir -p "$copy"
  name=$(basename "$db")
  need=$(stat -c %s "$db"); if [ -f "$db-wal" ]; then need=$((need + $(stat -c %s "$db-wal"))); fi
  free=$(df -B1 --output=avail "$WORK" | tail -1)
  echo -e "$i\t$db" >> "$WORK/sqlite/index.tsv"
  if [ "$need" -gt $((free - 4294967296)) ]; then
    log "  skip consistent copy of $db ($((need / 1048576)) MiB, too large for the inspector disk); it stays in the filesystem archive"
    echo "$db: skipped, $need bytes" >> "$WORK/sqlite-errors.log"; continue
  fi
  # one copy only: fold the WAL into the copy itself, so the copy is the consistent database
  cp -p "$db" "$copy/$name.consistent.sqlite3"
  for ext in -wal -journal; do if [ -f "$db$ext" ]; then cp -p "$db$ext" "$copy/$name.consistent.sqlite3$ext"; fi; done
  sqlite3 "$copy/$name.consistent.sqlite3" "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null 2>>"$WORK/sqlite-errors.log" || true
  rm -f "$copy/$name.consistent.sqlite3-wal" "$copy/$name.consistent.sqlite3-shm"
done < "$WORK/sqlite.list"
log "sqlite: $i databases, inspector disk $(df -h --output=avail "$WORK" | tail -1) free"
python3 "$TOOLS/dbprofile.py" sqlite "$WORK/sqlite" > "$WORK/sqlite-profile.json"
if [ "$i" -gt 0 ]; then
  tar -C "$WORK/sqlite" -cf - . | pigz | stream_up "databases/sqlite-consistent.tar.gz" 1000000000000 \
    || log "sqlite archive finished with warnings"
fi
find "$WORK/sqlite" -name '*.consistent.sqlite3*' -delete  # uploaded; free the space for PostgreSQL

# ---------------------------------------------------------------- PostgreSQL: start a copy-on-write view and dump
python3 - "$WORK/scan.json" <<'EOF' > "$WORK/pg.list"
import json, sys
for item in json.load(open(sys.argv[1]))["postgres"]: print(item["path"] + "\t" + item["version"])
EOF
: > "$WORK/pg-profile.jsonl"
n=0
while IFS=$'\t' read -r pgdata version; do
  [ -n "$pgdata" ] || continue
  n=$((n+1)); base=/opt/marefa/pg/$n; mkdir -p "$base/upper" "$base/work" "$base/data"
  mount -t overlay overlay -o "lowerdir=$pgdata,upperdir=$base/upper,workdir=$base/work" "$base/data"
  owner=$(stat -c %u:%g "$pgdata")
  rm -f "$base/data/postmaster.pid"
  [ -f "$base/data/postgresql.conf" ] || : > "$base/data/postgresql.conf"
  printf 'local all all trust\n' > "$base/data/marefa_hba.conf"
  image="postgres:$version"
  if grep -qs timescaledb "$base/data/postgresql.conf" "$base/data/postgresql.auto.conf"; then image="timescale/timescaledb:latest-pg$version"; fi
  log "postgres #$n: $pgdata (v$version, owner $owner) with $image"
  docker rm -f "marefa-pg$n" >/dev/null 2>&1 || true
  if ! docker run -d --name "marefa-pg$n" --network none --user "$owner" -v "$base/data:/var/lib/postgresql/data" \
      "$image" postgres -D /var/lib/postgresql/data -c listen_addresses= -c hba_file=/var/lib/postgresql/data/marefa_hba.conf \
      -c unix_socket_directories=/tmp >/dev/null; then
    echo "{\"cluster\": $n, \"path\": \"$pgdata\", \"error\": \"container did not start\"}" >> "$WORK/pg-profile.jsonl"; continue
  fi
  ready=""
  for _ in $(seq 90); do docker exec "marefa-pg$n" pg_isready -h /tmp -q 2>/dev/null && ready=1 && break; sleep 2; done
  if [ -z "$ready" ]; then
    docker logs "marefa-pg$n" > "$WORK/pg$n.log" 2>&1 || true
    echo "{\"cluster\": $n, \"path\": \"$pgdata\", \"error\": \"not ready; see logs/pg$n.log\"}" >> "$WORK/pg-profile.jsonl"; continue
  fi
  role=""
  for candidate in postgres $(python3 "$TOOLS/dbprofile.py" pg-roles "$WORK/scan.json"); do
    if docker exec "marefa-pg$n" psql -h /tmp -U "$candidate" -d postgres -Atc 'select 1' >/dev/null 2>&1 \
       || docker exec "marefa-pg$n" psql -h /tmp -U "$candidate" -d template1 -Atc 'select 1' >/dev/null 2>&1; then role=$candidate; break; fi
  done
  if [ -z "$role" ]; then
    echo "{\"cluster\": $n, \"path\": \"$pgdata\", \"error\": \"no login role found\"}" >> "$WORK/pg-profile.jsonl"; continue
  fi
  docker exec "marefa-pg$n" pg_dumpall -h /tmp -U "$role" --globals-only > "$WORK/pg$n-globals.sql" || log "  globals dump failed"
  echo "$WORK/pg$n-globals.sql" >> "$WORK/secrets-extra.list"
  for db in $(docker exec "marefa-pg$n" psql -h /tmp -U "$role" -d template1 -Atc \
      "select datname from pg_database where datallowconn and not datistemplate"); do
    log "  dump $db"
    docker exec "marefa-pg$n" pg_dump -h /tmp -U "$role" -Fc "$db" | stream_up "databases/postgres-$n/$db.dump" 1000000000000 \
      || { log "  dump of $db failed"; echo "{\"cluster\": $n, \"database\": \"$db\", \"error\": \"pg_dump failed\"}" >> "$WORK/pg-profile.jsonl"; continue; }
    docker exec "marefa-pg$n" pg_dump -h /tmp -U "$role" --schema-only "$db" > "$WORK/pg$n-$db-schema.sql"
    put_file "$WORK/pg$n-$db-schema.sql" "databases/postgres-$n/$db-schema.sql"
    python3 "$TOOLS/dbprofile.py" pg "marefa-pg$n" "$role" "$db" "$n" "$pgdata" >> "$WORK/pg-profile.jsonl"
  done
  docker stop "marefa-pg$n" >/dev/null
done < "$WORK/pg.list"

# ---------------------------------------------------------------- secrets: separate encrypted bundle
passphrase=$(openssl rand -base64 36)
aws ssm put-parameter --region "$REGION" --name "$PASS_PARAM" --type SecureString --overwrite --value "$passphrase" >/dev/null
for m in "${MOUNTS[@]}"; do
  tag=$(echo "${m#$MNT/}" | tr '/' '_')
  sed "s|^|$m/|" "$WORK/secrets-$tag.list"
done > "$WORK/secrets-all.list"
cat "$WORK/secrets-extra.list" >> "$WORK/secrets-all.list" 2>/dev/null || true
tar -cf - --files-from "$WORK/secrets-all.list" 2>/dev/null | gzip \
  | gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-fd 3 3<<<"$passphrase" \
  | stream_up "secrets/secrets.tar.gz.gpg" 100000000000 || log "secrets bundle finished with warnings"
rm -f "$WORK"/pg*-globals.sql
unset passphrase
log "secrets bundle: $(wc -l < "$WORK/secrets-all.list") files, AES256, passphrase in SSM $PASS_PARAM"

# ---------------------------------------------------------------- full filesystem archives (secrets excluded)
for m in "${MOUNTS[@]}"; do
  tag=$(echo "${m#$MNT/}" | tr '/' '_')
  { sed 's|^|./|' "$WORK/secrets-$tag.list"; printf './proc/*\n./sys/*\n./dev/*\n./run/*\n./swapfile\n./swap.img\n'; } > "$WORK/exclude-$tag.list"
  used=$(df -B1 --output=used "$m" | tail -1)
  log "archiving $m ($((used / 1048576)) MiB used)"
  tar --numeric-owner --xattrs --acls -cpf - -C "$m" --exclude-from="$WORK/exclude-$tag.list" . 2>>"$WORK/tar-$tag.log" \
    | pigz | stream_up "filesystems/$tag.tar.gz" "$((used + 1073741824))" || log "tar finished with warnings (see logs/tar-$tag.log)"
done

# ---------------------------------------------------------------- inventory + manifest
for f in "$WORK"/files-*.tsv.gz "$WORK"/lsblk-*.json "$WORK/scan.json" "$WORK/sqlite-profile.json" "$WORK/pg-profile.jsonl"; do
  if [ -f "$f" ]; then put_file "$f" "inventory/$(basename "$f")"; fi
done
for f in "$WORK"/*.log; do if [ -f "$f" ]; then s3put "$f" "logs/$(basename "$f")"; fi; done
python3 "$TOOLS/dbprofile.py" inventory "$WORK" "${MOUNTS[@]}" > "$WORK/inventory.json"
put_file "$WORK/inventory.json" "inventory.json"
python3 - "$WORK/hashes.tsv" <<'EOF' > "$WORK/manifest.json"
import json, sys
rows = [line.rstrip("\n").split("\t") for line in open(sys.argv[1]) if line.strip()]
latest = {}
for path, size, digest in rows: latest[path] = {"path": path, "size": int(size), "sha256": digest}
print(json.dumps({"objects": sorted(latest.values(), key=lambda o: o["path"])}, indent=1))
EOF
s3put "$WORK/manifest.json" "manifest.json"
s3put "$WORK/inventory.json" "inventory.json"
for m in "${MOUNTS[@]}"; do umount "$m"; done
log "done: $(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(len(d["objects"]),"objects",round(sum(o["size"] for o in d["objects"])/2**30,2),"GiB")' "$WORK/manifest.json")"
