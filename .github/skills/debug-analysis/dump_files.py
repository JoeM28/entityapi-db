#!/usr/bin/env python3
"""
Dumps all source files from entity-api-service into skills/download-sources/
as a flat collection (no subdirectories) so GitHub Copilot Chat can reference them.
Run this script whenever source files change to keep the skill context up to date.
"""

import os
import shutil
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent                    # .github/skills/debug-analysis/
REPO_ROOT    = SCRIPT_DIR.parent.parent.parent          # repo root
SOURCE_DIR   = REPO_ROOT / "entity-api-service"
DOWNLOAD_DIR = REPO_ROOT / "skills" / "download-sources"

# File extensions to include
EXTENSIONS = {'.java', '.yaml', '.yml', '.xml', '.http'}

def dump_files():
    if not SOURCE_DIR.exists():
        print(f"ERROR: Source directory does not exist: {SOURCE_DIR}")
        return False

    # Clean destination so there are no stale or duplicate files
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)
    DOWNLOAD_DIR.mkdir(parents=True)
    print(f"Destination cleared and ready: {DOWNLOAD_DIR}\n")

    copied   = []
    skipped  = []

    # Also include entity-api.yaml from repo root
    extra_files = [REPO_ROOT / "entity-api.yaml"]

    all_files = list(SOURCE_DIR.rglob('*')) + extra_files

    for file_path in all_files:
        file_path = Path(file_path)
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in EXTENSIONS:
            continue
        # Skip generated model classes — they are derived from entity-api.yaml
        if "generated-sources" in str(file_path) or "target" in str(file_path):
            continue

        dest = DOWNLOAD_DIR / file_path.name
        try:
            shutil.copy2(file_path, dest)
            copied.append(file_path.name)
            print(f"  copied: {file_path.name}")
        except Exception as e:
            skipped.append((file_path.name, str(e)))
            print(f"  SKIP:   {file_path.name} — {e}")

    # Write manifest
    manifest = DOWNLOAD_DIR / "FILES_COPIED.txt"
    with open(manifest, 'w') as f:
        f.write("Entity API — Source Dump\n")
        f.write(f"Source : {SOURCE_DIR}\n")
        f.write(f"Files  : {len(copied)}\n\n")
        for name in sorted(copied):
            f.write(f"{name}\n")

    print(f"\nDone — {len(copied)} files copied to {DOWNLOAD_DIR}")
    if skipped:
        print(f"Skipped {len(skipped)}: {[s[0] for s in skipped]}")
    return True

if __name__ == "__main__":
    success = dump_files()
    exit(0 if success else 1)
