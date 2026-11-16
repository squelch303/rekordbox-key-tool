#!/usr/bin/env python3
"""
rekordbox-key-tool
Converts track keys in rekordbox.xml from standard/MIK notation to Camelot Wheel.

Usage:
    python rekordbox_key_tool.py rekordbox.xml            # writes rekordbox_fixed.xml
    python rekordbox_key_tool.py --input rekordbox.xml --dry-run
    python rekordbox_key_tool.py --input rekordbox.xml --output rekordbox_fixed.xml
    python rekordbox_key_tool.py --input rekordbox.xml --inplace
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import ssl
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

__version__ = "1.1.0"

RELEASES_API = "https://api.github.com/repos/squelch303/rekordbox-key-tool/releases/latest"
RELEASES_URL = "https://github.com/squelch303/rekordbox-key-tool/releases/latest"
UPDATE_CHECK_DAYS = 7
NO_UPDATE_CHECK_ENV = "REKORDBOX_KEY_TOOL_NO_UPDATE_CHECK"

# ---------------------------------------------------------------------------
# Key mapping: standard / MIK notation -> Camelot Wheel
# ---------------------------------------------------------------------------

# Standard notation (normalised: lower case, no spaces, "m" = minor) -> Camelot
KEY_MAP = {
    # --- Minor keys (A) ---
    "abm": "1A",  "g#m": "1A",
    "ebm": "2A",  "d#m": "2A",
    "bbm": "3A",  "a#m": "3A",
    "fm":  "4A",
    "cm":  "5A",
    "gm":  "6A",
    "dm":  "7A",
    "am":  "8A",
    "em":  "9A",
    "bm":  "10A",
    "f#m": "11A", "gbm": "11A",
    "c#m": "12A", "dbm": "12A",

    # --- Major keys (B) ---
    "b":   "1B",
    "f#":  "2B",  "gb":  "2B",
    "db":  "3B",  "c#":  "3B",
    "ab":  "4B",  "g#":  "4B",
    "eb":  "5B",  "d#":  "5B",
    "bb":  "6B",  "a#":  "6B",
    "f":   "7B",
    "c":   "8B",
    "g":   "9B",
    "d":   "10B",
    "a":   "11B",
    "e":   "12B",
}

# Camelot values we recognise as already correct — skip these
CAMELOT_VALUES = {f"{n}{s}" for n in range(1, 13) for s in ("A", "B")}

CAMELOT_RE = re.compile(r"^0?([1-9]|1[0-2])([ab])$")   # 8a, 08A
OPEN_KEY_RE = re.compile(r"^0?([1-9]|1[0-2])([md])$")  # Open Key: 1m = Am = 8A, 1d = C = 8B
SEPARATORS_RE = re.compile(r"\s*[/|,]\s*|\s+-\s+")   # "Am/8A", "8A - Am"


def normalise_key(raw: str) -> str:
    """Normalise a raw key string: 'F# Minor' -> 'f#m', 'A♭ maj' -> 'ab'."""
    key = raw.strip().lower().replace("♭", "b").replace("♯", "#").replace(" ", "")
    for long, short in (("minor", "m"), ("min", "m"), ("major", ""), ("maj", "")):
        key = key.replace(long, short)
    return key


def to_camelot(raw: str) -> str | None:
    """Convert a single key token to Camelot, or None if not recognised."""
    key = normalise_key(raw)
    m = CAMELOT_RE.match(key)
    if m:
        return f"{int(m.group(1))}{m.group(2).upper()}"
    m = OPEN_KEY_RE.match(key)
    if m:
        number = (int(m.group(1)) + 6) % 12 + 1
        return f"{number}{'A' if m.group(2) == 'm' else 'B'}"
    return KEY_MAP.get(key)


def convert_key(raw: str) -> tuple[str | None, str]:
    """
    Convert a raw key string to Camelot notation.

    Returns (camelot_value, status) where status is one of:
        'converted'  – successfully mapped
        'already'    – already in Camelot format
        'unknown'    – not recognised, left unchanged
        'empty'      – no key set
    """
    if not raw or not raw.strip():
        return None, "empty"

    if raw in CAMELOT_VALUES:
        return raw, "already"

    camelot = to_camelot(raw)
    if camelot is None:
        # Combined formats like "Am/8A" or "8A - Am": every recognised part must agree
        results = {to_camelot(part) for part in SEPARATORS_RE.split(raw.strip()) if part}
        results.discard(None)
        if len(results) == 1:
            camelot = results.pop()

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
# Update check
# ---------------------------------------------------------------------------

def parse_version(text: str) -> tuple[int, ...] | None:
    """'v1.2.0' / '1.2' -> (1, 2, 0); None if it isn't a plain release version."""
    m = re.match(r"^v?(\d+)\.(\d+)(?:\.(\d+))?$", text.strip())
    return tuple(int(part or 0) for part in m.groups()) if m else None


def cache_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "rekordbox-key-tool"


def fetch_latest_version(timeout: float = 3) -> str | None:
    """Tag name of the latest GitHub release, e.g. 'v1.2.0'."""
    context = ssl.create_default_context()
    # The frozen macOS binary may not find Python's own CA bundle; the system one always exists
    if sys.platform == "darwin" and Path("/etc/ssl/cert.pem").exists():
        context.load_verify_locations("/etc/ssl/cert.pem")
    request = urllib.request.Request(RELEASES_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"rekordbox-key-tool/{__version__}",
    })
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return json.load(response).get("tag_name")


def check_for_update(state_file: Path | None = None, now: float | None = None,
                     fetch=fetch_latest_version) -> str | None:
    """
    Return the newer version if one has been released, else None. Never raises.

    Asks GitHub at most once every UPDATE_CHECK_DAYS and remembers the answer in
    state_file, so the notice keeps showing between checks without going online.
    """
    state_file = state_file or cache_dir() / "update-check.json"
    now = time.time() if now is None else now
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if not isinstance(state, dict):
        state = {}

    last = state.get("checked")
    if not isinstance(last, (int, float)) or not 0 <= now - last < UPDATE_CHECK_DAYS * 86400:
        try:
            latest = fetch()
        except Exception:  # offline, rate limited, proxy, bad JSON... never get in the way
            latest = None
        if isinstance(latest, str) and parse_version(latest):
            state["latest"] = latest
        state["checked"] = now  # also after a failure, so offline users aren't slowed down every run
        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state), encoding="utf-8")
        except OSError:
            pass

    latest = state.get("latest")
    latest_version = parse_version(latest) if isinstance(latest, str) else None
    if latest_version and latest_version > parse_version(__version__):
        return latest.strip().lstrip("v")
    return None


def update_check_wanted(args: argparse.Namespace) -> bool:
    """Only in interactive runs: not in scripts, pipes, CI, or when switched off."""
    if args.no_update_check or os.environ.get(NO_UPDATE_CHECK_ENV):
        return False
    return sys.stdout.isatty()


def print_update_notice(latest: str) -> None:
    print(f"\nA new version is available: {latest} (you have {__version__})")
    if getattr(sys, "frozen", False):
        print(f"Download it from {RELEASES_URL}")
    else:
        print(f"Upgrade with: pip install -U rekordbox-key-tool   (what's new: {RELEASES_URL})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def backup_path(input_path: Path) -> Path:
    """rekordbox.xml -> rekordbox.xml.bak; never overwrite an existing backup."""
    backup = input_path.with_name(input_path.name + ".bak")
    if backup.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = input_path.with_name(f"{input_path.name}.{stamp}.bak")
    return backup


def main():
    # Output contains ✓ → ⚠ — force UTF-8 so Windows doesn't crash when stdout is piped/redirected
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Convert rekordbox.xml track keys from MIK/standard notation to Camelot Wheel.",
        epilog="Just a file and no options (or dragging rekordbox.xml onto the program) "
               "writes <name>_fixed.xml next to it and leaves the original untouched.",
    )
    parser.add_argument("xml", nargs="?", help="Path to rekordbox.xml (same as --input)")
    parser.add_argument("--input",   "-i", default=None,   help="Path to rekordbox.xml")
    parser.add_argument("--output",  "-o", default=None,   help="Output file (default: print stats only)")
    parser.add_argument("--inplace", "-I", action="store_true",
                        help="Modify input file in place (creates rekordbox.xml.bak first)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would change without writing anything")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print every conversion")
    parser.add_argument("--no-update-check", action="store_true",
                        help=f"Don't check GitHub for a newer version (checked at most every "
                             f"{UPDATE_CHECK_DAYS} days; or set {NO_UPDATE_CHECK_ENV}=1)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # Drop mode: only a file was given (e.g. rekordbox.xml dragged onto the .exe)
    drop_mode = bool(args.xml) and not (args.input or args.output or args.inplace or args.dry_run)
    # A frozen .exe started by double-click or drag-and-drop closes its window at once — keep it open
    pause = getattr(sys, "frozen", False) and (drop_mode or len(sys.argv) == 1)

    try:
        run(parser, args, drop_mode)
        # After the work is done, so a slow or missing network never delays the conversion
        if update_check_wanted(args):
            latest = check_for_update()
            if latest:
                print_update_notice(latest)
    finally:
        if pause:
            try:
                input("\nPress Enter to close...")
            except EOFError:
                pass


def run(parser: argparse.ArgumentParser, args: argparse.Namespace, drop_mode: bool) -> None:
    if args.xml and args.input:
        parser.error("give the input file once: either as an argument or with --input")
    if not (args.xml or args.input):
        if getattr(sys, "frozen", False):
            print("Drag your rekordbox.xml onto this program to convert it.")
            print("rekordbox: File > Export Collection in xml format")
            return
        parser.error("no input file given (rekordbox-key-tool rekordbox.xml, or --input)")

    input_path = Path(args.xml or args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    if args.inplace and args.output:
        parser.error("use either --output or --inplace, not both")

    # Resolve output path
    if args.inplace:
        output_path = input_path
    elif args.output:
        output_path = Path(args.output)
        if output_path.resolve() == input_path.resolve():
            parser.error("--output is the same file as --input; use --inplace to overwrite (a backup is made)")
    elif drop_mode:
        output_path = input_path.with_name(f"{input_path.stem}_fixed{input_path.suffix}")
    else:
        output_path = None  # stats only

    dry_run = args.dry_run or output_path is None

    if dry_run:
        print("Dry run — no files will be written.\n")
    elif args.inplace:
        backup = backup_path(input_path)
        shutil.copy2(input_path, backup)
        print(f"Backup created: {backup}")

    try:
        stats = process_xml(input_path, output_path, dry_run=dry_run, verbose=args.verbose)
    except ET.ParseError as e:
        print(f"Error: {input_path} is not a valid XML file ({e}).", file=sys.stderr)
        sys.exit(1)

    # Summary
    print(f"\nDone. Processed {stats['total']} tracks:")
    print(f"  {stats['converted']:4d}  converted to Camelot")
    print(f"  {stats['already']:4d}  already in Camelot format")
    print(f"  {stats['unknown']:4d}  unrecognised (left unchanged)")
    print(f"  {stats['empty']:4d}  no key set")

    if not dry_run and output_path:
        print(f"\nWritten to: {output_path}")
        if drop_mode:
            print("Import it in rekordbox to update your keys (see README).")


if __name__ == "__main__":
    main()
