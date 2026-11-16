# rekordbox-key-tool

[![CI](https://github.com/squelch303/rekordbox-key-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/squelch303/rekordbox-key-tool/actions/workflows/ci.yml)

Converts track keys in a `rekordbox.xml` library file from standard musical notation
(as exported by Mixed In Key / MIK) to Camelot Wheel notation used by rekordbox.

<!-- TODO: demo GIF from the Reel 01 recording → docs/demo.gif -->

## The problem

When Mixed In Key analyzes your tracks and writes key data back to rekordbox,
it sometimes writes keys in standard notation (`Am`, `C`, `F#m`) rather than
the Camelot wheel format that rekordbox uses natively (`8A`, `8B`, `2B`).
This tool fixes that — in bulk, across your whole library.

## Quick start — no coding needed

1. **Download** the latest version for your computer from
   [Releases](https://github.com/squelch303/rekordbox-key-tool/releases/latest):
   - Windows: `rekordbox-key-tool-windows.exe`
   - macOS (Apple Silicon): `rekordbox-key-tool-macos-arm64.zip`
2. **Export your library** from rekordbox: **File → Export Collection in xml format**.
3. **Convert it**
   - Windows: drag `rekordbox.xml` onto `rekordbox-key-tool-windows.exe`.
   - macOS: unzip, then in Terminal run `./rekordbox-key-tool ~/path/to/rekordbox.xml`.

   You get `rekordbox_fixed.xml` next to the original. The original is never touched.
4. **Import `rekordbox_fixed.xml` back into rekordbox** (see [Importing](#importing-into-rekordbox)).

> The downloads aren't code-signed yet. Windows SmartScreen may say *"Windows protected your PC"*:
> click **More info → Run anyway**. On macOS, if it's blocked, right-click → **Open**, or run
> `xattr -d com.apple.quarantine rekordbox-key-tool` once.

## With Python

Requires Python 3.9+. No dependencies outside the standard library.

```bash
# Run straight from PyPI with uv, no install step
uvx rekordbox-key-tool rekordbox.xml

# Or install it
pip install rekordbox-key-tool
```

## Usage

```bash
# Just the file: writes rekordbox_fixed.xml, original untouched
rekordbox-key-tool rekordbox.xml

# Preview changes without modifying anything
rekordbox-key-tool --input rekordbox.xml --dry-run

# Show every track that changes
rekordbox-key-tool --input rekordbox.xml --dry-run --verbose

# Convert and write to a named file
rekordbox-key-tool --input rekordbox.xml --output rekordbox_fixed.xml

# Convert in place (backs up to rekordbox.xml.bak first; an existing backup is never overwritten)
rekordbox-key-tool --input rekordbox.xml --inplace
```

## Update check

When you run it yourself (not from a script or pipe), the tool asks GitHub for the latest
release at most once a week and tells you at the end of the run if a newer version is out.
It only sends a plain request to the GitHub releases API; nothing about your library leaves
your computer. If GitHub can't be reached, it says nothing and carries on.

Switch it off with `--no-update-check`, or set the environment variable
`REKORDBOX_KEY_TOOL_NO_UPDATE_CHECK=1`.

## Recognised key formats

| Format | Examples | Result |
|--------|----------|--------|
| Standard / MIK | `Am`, `F#m`, `Bbm`, `C`, `Eb` | `8A`, `11A`, `3A`, `8B`, `5B` |
| Long form | `F# minor`, `Ab Major`, `A min`, `C maj` | `11A`, `4B`, `8A`, `8B` |
| Unicode accidentals | `A♭m`, `F♯` | `1A`, `2B` |
| Camelot, odd casing / zero-padded | `8a`, `08A` | `8A` |
| Open Key (Traktor, Beatport) | `1m`, `1d`, `6m` | `8A`, `8B`, `1A` |
| Combined | `Am/8A`, `8A - Am` | `8A` |

Keys already in Camelot are left as they are. Anything not recognised is left unchanged
and listed at the end of the run. Please report those as an
[issue](https://github.com/squelch303/rekordbox-key-tool/issues).

## Where is rekordbox.xml?

Export it from rekordbox: **File → Export Collection in xml format**

Default locations:
- Windows: `C:\Users\<user>\Documents\Pioneer\rekordbox\rekordbox.xml`
- macOS: `~/Library/Pioneer/rekordbox/rekordbox.xml`

## Importing into rekordbox

Back up your rekordbox library first (**File → Library → Backup Library**).

1. **Preferences → Advanced → Database → rekordbox xml → Imported Library**: choose `rekordbox_fixed.xml`.
2. Make sure **rekordbox xml** is ticked under **Preferences → View → Layout**, so it shows in the tree view.
3. In the tree view, open **rekordbox xml**, right-click **All Tracks** → **Import to Collection**.

## Key format mapping

| Standard (MIK) | Camelot |
|----------------|---------|
| Ab minor / G# minor | 1A |
| B major | 1B |
| Eb minor / D# minor | 2A |
| F# major / Gb major | 2B |
| Bb minor / A# minor | 3A |
| Db major / C# major | 3B |
| F minor | 4A |
| Ab major / G# major | 4B |
| C minor | 5A |
| Eb major / D# major | 5B |
| G minor | 6A |
| Bb major / A# major | 6B |
| D minor | 7A |
| F major | 7B |
| A minor | 8A |
| C major | 8B |
| E minor | 9A |
| G major | 9B |
| B minor | 10A |
| D major | 10B |
| F# minor / Gb minor | 11A |
| A major | 11B |
| C# minor / Db minor | 12A |
| E major | 12B |

## Development

```bash
python -m unittest discover -s tests -v
```

Releases are built by GitHub Actions when a `v*` tag is pushed: Windows .exe, macOS binary,
PyPI package and the GitHub Release page.

## License

MIT — see [LICENSE](LICENSE).

---

Part of [squelch303](https://github.com/squelch303)
