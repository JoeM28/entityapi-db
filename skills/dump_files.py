#!/usr/bin/env python3
"""
Script to dump all Java files and yaml/html/xml/http files from entity-api-service
to a single flat folder (entity-api-db/skills/download-sources) without preserving directory structure.
"""

import os
import shutil
from pathlib import Path

# Define source and destination directories with proper Windows paths
SOURCE_DIR = Path(r"C:\Users\mohan\entityapi-db\entity-api-service")
DOWNLOAD_DIR = Path(r"C:\Users\mohan\entityapi-db\skills\download-sources")

# File extensions to copy
EXTENSIONS = {'.java', '.yaml', '.yml', '.html', '.xml', '.http'}

def dump_files():
    """Copy all matching files from source to download directory (flat structure)."""

    if not SOURCE_DIR.exists():
        print(f"❌ Source directory does not exist: {SOURCE_DIR}")
        return False

    print(f"📂 Source directory: {SOURCE_DIR}")

    # Create download directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Download directory: {DOWNLOAD_DIR}")

    copied_count = 0
    file_list = []
    duplicates = {}

    # Walk through the source directory
    for file_path in SOURCE_DIR.rglob('*'):
        if file_path.is_file():
            # Check if file extension matches
            if file_path.suffix.lower() in EXTENSIONS:
                # Get just the filename (without directory structure)
                filename = file_path.name

                # Create destination path (flat structure)
                dest_path = DOWNLOAD_DIR / filename

                # Handle duplicate filenames
                if dest_path.exists():
                    if filename not in duplicates:
                        duplicates[filename] = 1
                    duplicates[filename] += 1
                    # Add number before extension for duplicates
                    name, ext = os.path.splitext(filename)
                    dest_path = DOWNLOAD_DIR / f"{name}_{duplicates[filename]}{ext}"
                    print(f"⚠ Duplicate detected: {filename} -> {dest_path.name}")

                # Copy file
                try:
                    shutil.copy2(file_path, dest_path)
                    copied_count += 1
                    file_list.append(dest_path.name)
                    print(f"✓ Copied: {file_path.relative_to(SOURCE_DIR)} -> {dest_path.name}")
                except Exception as e:
                    print(f"❌ Error copying {filename}: {e}")

    # Print summary
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   Total files copied: {copied_count}")
    print(f"   Destination: {DOWNLOAD_DIR}")
    print("="*60)

    # Create a summary file listing all copied files
    summary_file = DOWNLOAD_DIR / "FILES_COPIED.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Entity API Files Dump (Flattened)\n")
        f.write(f"Generated from: {SOURCE_DIR}\n")
        f.write(f"Total files copied: {copied_count}\n")
        f.write(f"File extensions: {', '.join(sorted(EXTENSIONS))}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"Files copied:\n{'='*60}\n\n")
        for file in sorted(file_list):
            f.write(f"{file}\n")

    print(f"📝 Summary saved to: {summary_file}")
    return True

if __name__ == "__main__":
    success = dump_files()
    exit(0 if success else 1)

