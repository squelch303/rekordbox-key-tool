#!/usr/bin/env python3
"""
rekordbox-key-tool
Converts track keys in rekordbox.xml from standard/MIK notation to Camelot Wheel.

Usage:
    python rekordbox_key_tool.py --input rekordbox.xml --dry-run
    python rekordbox_key_tool.py --input rekordbox.xml --output rekordbox_fixed.xml
    python rekordbox_key_tool.py --input rekordbox.xml --inplace
"""

from __future__ import annotations

import argparse
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Key mapping: standard / MIK notation -> Camelot Wheel
# ---------------------------------------------------------------------------

# All known input variants -> Camelot value
KEY_MAP = {
    # --- Minor keys (A) ---
    "abm":  "1A",  "g#m":  "1A",  "ab minor": "1A",  "g# minor": "1A",
    "ebm":  "2A",  "d#m":  "2A",  "eb minor": "2A",  "d# minor": "2A",
    "bbm":  "3A",  "a#m":  "3A",  "bb minor": "3A",  "a# minor": "3A",
    "fm":   "4A",                  "f minor":  "4A",
    "cm":   "5A",                  "c minor":  "5A",
    "gm":   "6A",                  "g minor":  "6A",
    "dm":   "7A",                  "d minor":  "7A",
    "am":   "8A",                  "a minor":  "8A",
    "em":   "9A",                  "e minor":  "9A",
    "bm":   "10A",                 "b minor":  "10A",
    "f#m":  "11A", "gbm":  "11A", "f# minor": "11A", "gb minor": "11A",
    "c#m":  "12A", "dbm":  "12A", "c# minor": "12A", "db minor": "12A",

    # --- Major keys (B) ---
    "b":    "1B",                  "b major":  "1B",
    "f#":   "2B",  "gb":   "2B",  "f# major": "2B",  "gb major": "2B",
    "db":   "3B",  "c#":   "3B",  "db major": "3B",  "c# major": "3B",
    "ab":   "4B",  "g#":   "4B",  "ab major": "4B",  "g# major": "4B",
    "eb":   "5B",  "d#":   "5B",  "eb major": "5B",  "d# major": "5B",
    "bb":   "6B",  "a#":   "6B",  "bb major": "6B",  "a# major": "6B",
    "f":    "7B",                  "f major":  "7B",
    "c":    "8B",                  "c major":  "8B",
    "g":    "9B",                  "g major":  "9B",
    "d":    "10B",                 "d major":  "10B",
    "a":    "11B",                 "a major":  "11B",
    "e":    "12B",                 "e major":  "12B",
}

# Camelot values we recognise as already correct — skip these
CAMELOT_VALUES = {f"{n}{s}" for n in range(1, 13) for s in ("A", "B")}


def normalise_key(raw: str) -> str | None:
    """Normalise a raw key string to a KEY_MAP lookup key."""
    return raw.strip().lower().replace("♭", "b").replace("♯", "#")


def convert_key(raw: str) -> tuple[str | None, str]:
    """
    Convert a raw key string to Camelot notation.

    Returns (camelot_value, status) where status is one of:
        'converted'  – successfully mapped
        'already'    – already in Camelot format
        'unknown'    – not recognised, left unchanged
        'empty'      – no key set
    """
    if not raw:
        return None, "empty"

    if raw in CAMELOT_VALUES:
        return raw, "already"

    normalised = normalise_key(raw)
    camelot = KEY_MAP.get(normalised)
    if camelot:
        return camelot, "converted"

    return None, "unknown"


# ---------------------------------------------------------------------------
# XML processing
# ---------------------------------------------------------------------------

def process_xml(input_path: Path, output_path: Path, dry_run: bool, verbose: bool) -> dict:
    """Parse rekordbox.xml, convert keys, write output. Returns stats."""
    tree = ET.parse(input_path)
    root = tree.getroot()

    stats = {"converted": 0, "already": 0, "unknown": 0, "empty": 0, "total": 0}
    unknown_keys = set()

    collection = root.find("COLLECTION")
    if collection is None:
        print("Error: no <COLLECTION> element found in XML.", file=sys.stderr)
        sys.exit(1)

    for track in collection:
        name  = track.get("Name", "<unknown>")
        artist = track.get("Artist", "")
        raw_key = track.get("Tonality", "")

        camelot, status = convert_key(raw_key)
        stats[status] += 1
        stats["total"] += 1

        if status == "converted":
            if verbose:
                print(f"  ✓  {artist} – {name}: {raw_key!r} → {camelot}")
            if not dry_run:
                track.set("Tonality", camelot)

        elif status == "unknown" and raw_key:
            unknown_keys.add(raw_key)
            if verbose:
                print(f"  ?  {artist} – {name}: {raw_key!r} (unrecognised)")

    if not dry_run:
        # Preserve the XML declaration and encoding
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    if unknown_keys:
        print(f"\n⚠  Unrecognised key values (not converted): {sorted(unknown_keys)}")
        print("   Please report these at https://github.com/squelch303/rekordbox-key-tool/issues")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    # Output contains ✓ → ⚠ — force UTF-8 so Windows doesn't crash when stdout is piped/redirected
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Convert rekordbox.xml track keys from MIK/standard notation to Camelot Wheel."
    )
    parser.add_argument("--input",   "-i", required=True,  help="Path to rekordbox.xml")
    parser.add_argument("--output",  "-o", default=None,   help="Output file (default: print stats only)")
    parser.add_argument("--inplace", "-I", action="store_true",
                        help="Modify input file in place (creates .bak backup first)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would change without writing anything")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print every conversion")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Resolve output path
    if args.inplace:
        backup = input_path.with_suffix(".bak")
        shutil.copy2(input_path, backup)
        print(f"Backup created: {backup}")
        output_path = input_path
    elif args.output:
        output_path = Path(args.output)
    else:
        output_path = None  # dry-run or stats only

    dry_run = args.dry_run or output_path is None

    if dry_run and not args.inplace:
        print("Dry run — no files will be written.\n")

    stats = process_xml(input_path, output_path, dry_run=dry_run, verbose=args.verbose)

    # Summary
    print(f"\nDone. Processed {stats['total']} tracks:")
    print(f"  {stats['converted']:4d}  converted to Camelot")
    print(f"  {stats['already']:4d}  already in Camelot format")
    print(f"  {stats['unknown']:4d}  unrecognised (left unchanged)")
    print(f"  {stats['empty']:4d}  no key set")

    if not dry_run and output_path:
        print(f"\nWritten to: {output_path}")


if __name__ == "__main__":
    main()
