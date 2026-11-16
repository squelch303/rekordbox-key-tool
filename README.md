# rekordbox-key-tool

Converts track keys in a `rekordbox.xml` library file from standard musical notation
(as exported by Mixed In Key / MIK) to Camelot Wheel notation used by rekordbox.

## The problem

When Mixed In Key analyzes your tracks and writes key data back to rekordbox,
it sometimes writes keys in standard notation (`Am`, `C`, `F#m`) rather than
the Camelot wheel format that rekordbox uses natively (`8A`, `8B`, `2B`).
This tool fixes that — in bulk, across your whole library.

## Install

No external dependencies — uses the Python standard library only. Requires Python 3.8+.

### With uv (recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and run — no install step needed
git clone https://github.com/squelch303/rekordbox-key-tool
cd rekordbox-key-tool
uv run rekordbox-key-tool --help
```

### With pip

```bash
pip install -e .
rekordbox-key-tool --help
```

### Without install

```bash
python rekordbox_key_tool.py --help
```

## Usage

```bash
# Preview changes without modifying anything
rekordbox-key-tool --input rekordbox.xml --dry-run

# Convert and write to a new file (recommended first run)
rekordbox-key-tool --input rekordbox.xml --output rekordbox_fixed.xml

# Convert in-place (creates a .bak backup automatically)
rekordbox-key-tool --input rekordbox.xml --inplace

# Verbose output — show every track that was changed
rekordbox-key-tool --input rekordbox.xml --output rekordbox_fixed.xml --verbose
```

## Where is rekordbox.xml?

Export it from rekordbox: **File → Export Collection in xml format**

Default locations:
- Windows: `C:\Users\<user>\Documents\Pioneer\rekordbox\rekordbox.xml`
- macOS: `~/Library/Pioneer/rekordbox/rekordbox.xml`

After conversion, import it back: **File → Import Collection → From rekordbox**

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

## License

MIT

---

Part of [squelch303](https://github.com/squelch303)
