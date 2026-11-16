# Changelog

## [1.1.0] - 2026-11-16

- Downloadable Windows .exe and macOS binary: drag `rekordbox.xml` onto the .exe to get `rekordbox_fixed.xml`
- Just a file and no options (`rekordbox-key-tool rekordbox.xml`) writes `rekordbox_fixed.xml` and leaves the original untouched
- More key formats: lowercase/zero-padded Camelot (`8a`, `08A`), Open Key (`1m`, `1d`), `A min` / `C maj`, combined values like `Am/8A` and `8A - Am`
- `--inplace` backs up to `rekordbox.xml.bak` and never overwrites an existing backup; `--inplace --dry-run` no longer makes a backup
- Refuse `--output` pointing at the input file, and `--output` together with `--inplace`
- Clean error message for invalid XML instead of a traceback
- `--version`
- Fixed: `--verbose` crashed on Windows when output was piped or redirected
- Fixed: crashed on Python 3.9 (minimum is now 3.9)
- Tests and CI on Windows, macOS and Linux; published to PyPI

## [1.0.0] - 2026-06-01

- Transferred from `isd-labs` to `squelch303`
- Added `pyproject.toml` — installable via `pip install -e .` or `uv run`
- Fixed issue tracker URL in tool output

## [0.1.0] - 2026-05-10

Initial release. Converts MIK-exported keys (standard notation) to Camelot Wheel format in `rekordbox.xml`. Supports dry-run, in-place editing with backup, and verbose output.
