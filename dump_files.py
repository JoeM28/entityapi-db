#!/usr/bin/env python3
"""
Script to dump all Java files and yaml/html/xml/http files from entity-api-service
to a download folder while preserving directory structure.
"""

import os
import shutil
from pathlib import Path

# Define source and destination directories
SOURCE_DIR = Path("C:/Users/mohan/entityapi-db/entity-api-service")
DOWNLOAD_DIR = Path("C:/Users/mohan/Downloads/entityapi-dump")

# File extensions to copy
EXTENSIONS = {'.java', '.yaml', '.yml', '.html', '.xml', '.http'}

def get_relative_path(file_path, source_dir):
    """Get the relative path of a file from the source directory."""
    return Path(file_path).relative_to(source_dir)

def dump_files():
    """Copy all matching files from source to download directory."""

    if not SOURCE_DIR.exists():
        print(f"❌ Source directory does not exist: {SOURCE_DIR}")
        return False

    # Create download directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Download directory: {DOWNLOAD_DIR}")

    copied_count = 0
    file_list = []

    # Walk through the source directory
    for file_path in SOURCE_DIR.rglob('*'):
        if file_path.is_file():
            # Check if file extension matches
            if file_path.suffix.lower() in EXTENSIONS:
                # Get relative path
                rel_path = get_relative_path(file_path, SOURCE_DIR)

                # Create destination path
                dest_path = DOWNLOAD_DIR / rel_path

                # Create parent directories if they don't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                try:
                    shutil.copy2(file_path, dest_path)
                    copied_count += 1
                    file_list.append(str(rel_path))
                    print(f"✓ Copied: {rel_path}")
                except Exception as e:
                    print(f"❌ Error copying {rel_path}: {e}")

    # Print summary
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   Total files copied: {copied_count}")
    print(f"   Destination: {DOWNLOAD_DIR}")
    print("="*60)

    # Create a summary file listing all copied files
    summary_file = DOWNLOAD_DIR / "FILES_COPIED.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Entity API Files Dump\n")
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

