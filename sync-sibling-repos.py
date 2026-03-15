"""
sync-sibling-repos.py

Clones or pulls cross-repo source code into a local sibling-repo/ folder.

Two sources of repos to sync:

  1. AUTO — scans entity-api-service/pom.xml for com.company Maven dependencies
             (library repos such as entity-dob-validation)

  2. EXTRA_REPOS — a list you maintain manually below for repos that are HTTP
                   service dependencies and therefore never appear in pom.xml
                   (e.g. entity-name-api)

Usage:
    python sync-sibling-repos.py

Requirements:
    - Python 3.8+
    - git available on PATH

The GitHub org/user defaults to JoeM28. Override with:
    GITHUB_ORG=MyOrg python sync-sibling-repos.py
"""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()          # entityapi-db/
SIBLING_DIR  = SCRIPT_DIR / "sibling-repo"              # entityapi-db/sibling-repo/
POM_PATH     = SCRIPT_DIR / "entity-api-service" / "pom.xml"
GROUP_ID     = "com.company"                            # only these Maven deps are cross-repo
GITHUB_ORG   = os.environ.get("GITHUB_ORG", "JoeM28")
GITHUB_BASE  = f"https://github.com/{GITHUB_ORG}"

# The service's own artifactId — never clone itself
OWN_ARTIFACT = "entity-api-service"

# ── Extra repos (HTTP service dependencies not in pom.xml) ─────────────────
# Add any repo name here that should always be cloned into sibling-repo/
# regardless of whether it appears as a Maven dependency.
#
# Format: just the repo name as it appears on GitHub, e.g. "entity-name-api"
#
EXTRA_REPOS = [
    "entity-name-api",
    "entity-kafka-service",
    "entityapi-vertx",
]

# ── Helpers ────────────────────────────────────────────────────────────────

def find_pom_deps(pom: Path) -> list[dict]:
    """Return list of {name, label} for com.company Maven deps (auto-discovered)."""
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    tree = ET.parse(pom)
    root = tree.getroot()

    deps = []
    for dep in root.findall(".//m:dependency", ns):
        gid  = (dep.findtext("m:groupId",    namespaces=ns) or "").strip()
        aid  = (dep.findtext("m:artifactId", namespaces=ns) or "").strip()
        ver  = (dep.findtext("m:version",    namespaces=ns) or "").strip()
        if gid == GROUP_ID and aid and aid != OWN_ARTIFACT:
            deps.append({"name": aid, "label": f"{GROUP_ID}:{aid}:{ver} (pom.xml)"})
    return deps


def build_repo_list(pom: Path) -> list[dict]:
    """Merge pom-discovered deps with EXTRA_REPOS, deduplicated by name."""
    repos = {r["name"]: r for r in find_pom_deps(pom)}

    for repo_name in EXTRA_REPOS:
        if repo_name not in repos:
            repos[repo_name] = {"name": repo_name, "label": f"{repo_name} (EXTRA_REPOS)"}

    return list(repos.values())


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def sync_repo(name: str) -> None:
    repo_url   = f"{GITHUB_BASE}/{name}.git"
    target_dir = SIBLING_DIR / name

    if target_dir.exists():
        print(f"\n[{name}] Already cloned — pulling latest changes")
        rc = run(["git", "pull"], cwd=target_dir)
        if rc != 0:
            print(f"  WARNING: git pull failed for {name}")
    else:
        print(f"\n[{name}] Cloning from {repo_url}")
        rc = run(["git", "clone", repo_url, str(target_dir)])
        if rc != 0:
            print(f"  ERROR: git clone failed for {name} — skipping")

# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    if not POM_PATH.exists():
        print(f"ERROR: pom.xml not found at {POM_PATH}")
        sys.exit(1)

    repos = build_repo_list(POM_PATH)
    if not repos:
        print("No repos to sync (pom.xml has no cross-repo deps and EXTRA_REPOS is empty).")
        return

    print(f"Repos to sync ({len(repos)} total):")
    for r in repos:
        print(f"  {r['label']}")

    SIBLING_DIR.mkdir(exist_ok=True)
    print(f"\nSyncing into: {SIBLING_DIR}\n{'-' * 60}")

    for r in repos:
        sync_repo(r["name"])

    print(f"\n{'-' * 60}")
    print("Done. Sibling repos are in:", SIBLING_DIR)


if __name__ == "__main__":
    main()
