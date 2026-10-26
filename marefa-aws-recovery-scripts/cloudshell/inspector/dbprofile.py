#!/usr/bin/env python3
"""Scan mounted filesystems and profile databases for the MAREFA recovery inventory.

  scan <work> <mount>...                  locate databases, data files, Git repos, Docker state
  sqlite <dir>                            profile the consistent SQLite copies
  pg-roles <scan.json>                    candidate PostgreSQL login names (names only)
  pg <container> <role> <db> <n> <path>   profile one PostgreSQL database (one JSON line)
  inventory <work> <mount>...             summary for the report

Output never carries passwords, tokens or environment values.
"""
import gzip
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict

SKIP_PARTS = {"proc", "sys", "node_modules", "site-packages", "dist-packages", "__pycache__"}
SKIP_PREFIXES = ("usr/", "lib/", "lib64/", "bin/", "sbin/", "snap/", "boot/")
DATA_EXT = {".csv", ".tsv", ".json", ".jsonl", ".ndjson", ".parquet", ".xlsx", ".xls", ".xlsm", ".feather",
            ".arrow", ".h5", ".hdf5", ".pdf", ".sql", ".dump", ".bak", ".zip", ".gz", ".tgz", ".7z", ".tar",
            ".xml", ".xbrl", ".html", ".htm", ".duckdb", ".db", ".sqlite", ".sqlite3", ".pkl", ".pickle", ".npz"}
KEY_COL = re.compile(r"(company|symbol|ticker|isin|cik|issuer|tadawul|stock_code|^code$)", re.I)
PERIOD_COL = re.compile(r"(year|period|date|as_of|quarter|filed|observed)", re.I)
URL_CRED = re.compile(r"://[^/\s@]+@")


def rel(mount, path):
    return os.path.relpath(path, mount)


def walk(mount):
    dev = os.stat(mount).st_dev
    for root, dirs, files in os.walk(mount):
        r = rel(mount, root)
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS and os.lstat(os.path.join(root, d)).st_dev == dev
                   and not (r == "." and d in {"proc", "sys", "dev", "run"})]
        yield root, r, dirs, files


def git_info(repo, mount):
    def git(*a):
        out = subprocess.run(["git", "-c", "safe.directory=*", "--git-dir", repo, *a],
                             capture_output=True, text=True, timeout=60)
        return out.stdout.strip()
    remotes = [URL_CRED.sub("://<credentials-removed>@", line) for line in git("remote", "-v").splitlines()]
    return {"path": rel(mount, repo), "head": git("rev-parse", "--short", "HEAD"),
            "branch": git("symbolic-ref", "--short", "-q", "HEAD"),
            "branches": len(git("for-each-ref", "--format=%(refname)", "refs/heads").splitlines()),
            "last_commit": git("log", "-1", "--format=%cI %s"),
            "commits": git("rev-list", "--all", "--count"), "remotes": sorted(set(remotes))}


def scan(work, mounts):
    out = defaultdict(list)
    roles = set()
    for mount in mounts:
        for root, r, dirs, files in walk(mount):
            name_set = set(files)
            if "PG_VERSION" in name_set and os.path.exists(os.path.join(root, "global", "pg_control")):
                out["postgres"].append({"mount": mount, "path": root, "relative": r,
                                        "version": open(os.path.join(root, "PG_VERSION")).read().strip(),
                                        "unclean_shutdown_marker": "postmaster.pid" in name_set})
            if "ibdata1" in name_set or ("mysql" in dirs and any(f.endswith(".ibd") for f in files)):
                out["mysql"].append({"mount": mount, "relative": r})
            if "WiredTiger" in name_set:
                out["mongodb"].append({"mount": mount, "relative": r})
            if os.path.basename(root) == ".git" or ({"HEAD", "objects", "refs"} <= set(dirs) | name_set and r.endswith(".git")):
                try:
                    out["git"].append(git_info(root, mount))
                except Exception as error:
                    out["git"].append({"path": r, "error": str(error)})
                dirs[:] = []
                continue
            if r.startswith("var/lib/docker/volumes/") and r.count("/") == 4 and r.endswith("_data"):
                out["docker_volumes"].append({"relative": r})
            for f in files:
                path = os.path.join(root, f)
                rp = rel(mount, path)
                try:
                    st = os.lstat(path)
                except OSError:
                    continue
                if not os.path.isfile(path) or os.path.islink(path):
                    continue
                if re.match(r"(docker-)?compose.*\.ya?ml$", f):
                    out["compose_files"].append(rp)
                if rp.startswith("var/lib/docker/containers/") and f == "config.v2.json":
                    try:
                        c = json.load(open(path))
                        out["docker_containers"].append({"name": c.get("Name"), "image": c.get("Config", {}).get("Image"),
                                                         "mounts": sorted((c.get("MountPoints") or {}).keys())})
                        for env in c.get("Config", {}).get("Env") or []:
                            if env.split("=", 1)[0] in {"POSTGRES_USER", "PGUSER", "DB_USER"}:
                                roles.add(env.split("=", 1)[1])
                    except (ValueError, OSError):
                        pass
                if f.startswith(".env") and st.st_size < 1 << 20:
                    try:
                        for line in open(path, errors="ignore"):
                            key, _, value = line.strip().partition("=")
                            if key in {"POSTGRES_USER", "PGUSER", "DB_USER"} and value:
                                roles.add(value.strip("'\""))
                            if key.endswith("DATABASE_URL"):
                                m = re.match(r"\w+://([^:/@]+)", value.strip("'\""))
                                if m:
                                    roles.add(m.group(1))
                    except OSError:
                        pass
                if st.st_size >= 512 and not rp.startswith(SKIP_PREFIXES):
                    try:
                        with open(path, "rb") as fh:
                            if fh.read(16) == b"SQLite format 3\x00":
                                out["sqlite"].append({"path": path, "relative": rp, "size": st.st_size})
                                continue
                    except OSError:
                        pass
                ext = os.path.splitext(f)[1].lower()
                if ext in DATA_EXT and not rp.startswith(SKIP_PREFIXES) and "/.git/" not in rp:
                    out["data_files"].append({"relative": rp, "ext": ext, "size": st.st_size})
    out["pg_role_candidates"] = sorted(r for r in roles if re.fullmatch(r"[A-Za-z0-9_.-]{1,63}", r))
    json.dump(out, sys.stdout, indent=1)


def profile_columns(query, table, columns):
    """Distinct companies and period ranges for identifier/period-looking columns."""
    result = {}
    for col in columns:
        q = f'"{col}"'
        try:
            if KEY_COL.search(col):
                distinct = query(f'SELECT count(DISTINCT {q}) FROM "{table}"')[0][0]
                values = [row[0] for row in query(f'SELECT DISTINCT {q} FROM "{table}" WHERE {q} IS NOT NULL LIMIT 400')]
                result[col] = {"kind": "identifier", "distinct": distinct, "values": [str(v)[:80] for v in values]}
            elif PERIOD_COL.search(col):
                lo, hi = query(f'SELECT min({q}), max({q}) FROM "{table}"')[0]
                years = query(f'SELECT DISTINCT substr(CAST({q} AS TEXT),1,4) FROM "{table}" WHERE {q} IS NOT NULL LIMIT 200')
                result[col] = {"kind": "period", "min": str(lo)[:40], "max": str(hi)[:40],
                               "years": sorted({str(y[0]) for y in years if str(y[0]).isdigit()})}
        except Exception as error:  # profiling is best effort, counts are not
            result[col] = {"error": str(error)[:200]}
    return result


def sqlite_profiles(directory):
    index = {}
    if os.path.exists(os.path.join(directory, "index.tsv")):
        for line in open(os.path.join(directory, "index.tsv")):
            n, path = line.rstrip("\n").split("\t", 1)
            index[n] = path
    out = []
    for n, source in sorted(index.items(), key=lambda kv: int(kv[0])):
        name = os.path.basename(source)
        copy = os.path.join(directory, n, name + ".consistent.sqlite3")
        if not os.path.exists(copy):
            out.append({"source": source, "error": "no consistent copy (too large for the inspector disk)"})
            continue
        entry = {"source": source, "size": os.path.getsize(copy), "tables": []}
        try:
            con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
            query = lambda sql: con.execute(sql).fetchall()
            entry["integrity"] = query("PRAGMA quick_check")[0][0]
            for (table,) in query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                cols = [c[1] for c in query(f'PRAGMA table_info("{table}")')]
                rows = query(f'SELECT count(*) FROM "{table}"')[0][0]
                entry["tables"].append({"name": table, "rows": rows, "columns": cols,
                                        "profile": profile_columns(query, table, cols)})
            con.close()
        except sqlite3.Error as error:
            entry["error"] = str(error)
        out.append(entry)
    json.dump(out, sys.stdout, indent=1)


def pg_profile(container, role, db, n, path):
    def query(sql):
        out = subprocess.run(["docker", "exec", container, "psql", "-h", "/tmp", "-U", role, "-d", db, "-AtX",
                              "-F", "\x1f", "-c", "SET statement_timeout='300s'", "-c", sql],
                             capture_output=True, text=True, timeout=400)
        if out.returncode:
            raise RuntimeError(out.stderr.strip()[:200])
        return [line.split("\x1f") for line in out.stdout.splitlines() if line and line != "SET"]
    entry = {"cluster": int(n), "path": path, "database": db, "tables": []}
    entry["size_bytes"] = int(query("SELECT pg_database_size(current_database())")[0][0])
    tables = query("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE' "
                   "AND table_schema NOT IN ('pg_catalog','information_schema') ORDER BY 1,2")
    for schema, table in tables:
        full = f'{schema}"."{table}'
        cols = [c[0] for c in query(f"SELECT column_name FROM information_schema.columns WHERE table_schema='{schema}' "
                                    f"AND table_name='{table}' ORDER BY ordinal_position")]
        item = {"name": f"{schema}.{table}", "columns": cols}
        try:
            item["rows"] = int(query(f'SELECT count(*) FROM "{full}"')[0][0])
            item["profile"] = profile_columns(query, full, cols)
        except RuntimeError as error:
            item["error"] = str(error)
        entry["tables"].append(item)
    print(json.dumps(entry))


def pg_roles(scan_path):
    print(" ".join(json.load(open(scan_path)).get("pg_role_candidates", [])))


def inventory(work, mounts):
    scanned = json.load(open(os.path.join(work, "scan.json")))
    summary = {"filesystems": [], "secrets_bundle_files": 0}
    for mount in mounts:
        tag = mount.replace("/mnt/marefa/", "").replace("/", "_")
        kinds, by_ext, top = Counter(), Counter(), Counter()
        total = 0
        with gzip.open(os.path.join(work, f"files-{tag}.tsv.gz"), "rt", errors="replace") as fh:
            for line in fh:
                kind, size, _, path = (line.rstrip("\n").split("\t", 3) + [""] * 4)[:4]
                kinds[kind] += 1
                if kind == "f":
                    total += int(size)
                    top[path.split("/", 1)[0]] += int(size)
        for item in scanned.get("data_files", []):
            by_ext[item["ext"]] += 1
        st = os.statvfs(mount)
        summary["filesystems"].append({
            "mount": mount, "used_bytes": (st.f_blocks - st.f_bfree) * st.f_frsize, "file_bytes": total,
            "files": kinds["f"], "directories": kinds["d"], "symlinks": kinds["l"],
            "largest_top_level": dict(top.most_common(15))})
        secret_list = os.path.join(work, f"secrets-{tag}.list")
        if os.path.exists(secret_list):
            summary["secrets_bundle_files"] += sum(1 for _ in open(secret_list))
    data = scanned.get("data_files", [])
    ext_bytes = Counter()
    dirs = Counter()
    for item in data:
        ext_bytes[item["ext"]] += item["size"]
        dirs[os.path.dirname(item["relative"])] += 1
    summary["data_files"] = {"by_extension": {e: {"files": c, "bytes": ext_bytes[e]} for e, c in Counter(i["ext"] for i in data).most_common()},
                             "busiest_directories": dict(dirs.most_common(40))}
    summary["databases"] = {"sqlite": json.load(open(os.path.join(work, "sqlite-profile.json"))),
                            "postgres": [json.loads(l) for l in open(os.path.join(work, "pg-profile.jsonl")) if l.strip()],
                            "postgres_clusters": scanned.get("postgres", []), "mysql": scanned.get("mysql", []),
                            "mongodb": scanned.get("mongodb", [])}
    for key in ("git", "docker_volumes", "docker_containers", "compose_files"):
        summary[key] = scanned.get(key, [])
    json.dump(summary, sys.stdout, indent=1, default=str)


if __name__ == "__main__":
    command, args = sys.argv[1], sys.argv[2:]
    {"scan": lambda: scan(args[0], args[1:]), "sqlite": lambda: sqlite_profiles(args[0]),
     "pg-roles": lambda: pg_roles(args[0]), "pg": lambda: pg_profile(*args),
     "inventory": lambda: inventory(args[0], args[1:])}[command]()
