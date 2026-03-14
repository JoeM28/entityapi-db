"""
sync-sibling-repos.py

Scans entity-api-service/pom.xml for cross-repo dependencies (any
com.company artifact that is not this service itself), then clones or
pulls each one into a local sibling-repo/ folder alongside this repo.

Usage:
    python sync-sibling-repos.py

Requirements:
    - Python 3.8+
    - git available on PATH
    - GitHub CLI (gh) authenticated, OR set GITHUB_ORG env var

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
GROUP_ID     = "com.company"                            # only these deps are cross-repo
GITHUB_ORG   = os.environ.get("GITHUB_ORG", "JoeM28")
GITHUB_BASE  = f"https://github.com/{GITHUB_ORG}"

# The service's own artifactId — never clone itself
OWN_ARTIFACT = "entity-api-service"

# ── Helpers ────────────────────────────────────────────────────────────────

def find_cross_repo_deps(pom: Path) -> list[dict]:
    """Return list of {artifactId, version} for com.company deps that are
    not this service itself."""
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    tree = ET.parse(pom)
    root = tree.getroot()

    deps = []
    for dep in root.findall(".//m:dependency", ns):
        gid  = (dep.findtext("m:groupId",    namespaces=ns) or "").strip()
        aid  = (dep.findtext("m:artifactId", namespaces=ns) or "").strip()
        ver  = (dep.findtext("m:version",    namespaces=ns) or "").strip()
        if gid == GROUP_ID and aid and aid != OWN_ARTIFACT:
            deps.append({"artifactId": aid, "version": ver})
    return deps


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def sync_repo(artifact_id: str, version: str) -> None:
    repo_url    = f"{GITHUB_BASE}/{artifact_id}.git"
    target_dir  = SIBLING_DIR / artifact_id

    if target_dir.exists():
        print(f"\n[{artifact_id}] Already cloned — pulling latest changes")
        rc = run(["git", "pull"], cwd=target_dir)
        if rc != 0:
            print(f"  WARNING: git pull failed for {artifact_id}")
    else:
        print(f"\n[{artifact_id}] Cloning from {repo_url}")
        rc = run(["git", "clone", repo_url, str(target_dir)])
        if rc != 0:
            print(f"  ERROR: git clone failed for {artifact_id} — skipping")
            return

    print(f"  version in pom: {version or '(not pinned)'}")

# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    if not POM_PATH.exists():
        print(f"ERROR: pom.xml not found at {POM_PATH}")
        sys.exit(1)

    deps = find_cross_repo_deps(POM_PATH)
    if not deps:
        print("No cross-repo com.company dependencies found in pom.xml.")
        return

    print(f"Found {len(deps)} cross-repo dependency/dependencies:")
    for d in deps:
        print(f"  {GROUP_ID}:{d['artifactId']}:{d['version']}")

    SIBLING_DIR.mkdir(exist_ok=True)
    print(f"\nSyncing into: {SIBLING_DIR}\n{'-' * 60}")

    for dep in deps:
        sync_repo(dep["artifactId"], dep["version"])

    print(f"\n{'-' * 60}")
    print("Done. Sibling repos are in:", SIBLING_DIR)


if __name__ == "__main__":
    main()
