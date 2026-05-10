# rekordbox-key-tool

Converts track keys in a `rekordbox.xml` library file from standard musical notation
(as exported by Mixed In Key / MIK) to Camelot Wheel notation used by rekordbox.

## The problem

When Mixed In Key analyzes your tracks and writes key data back to rekordbox,
it sometimes writes keys in standard notation (`Am`, `C`, `F#m`) rather than
the Camelot wheel format that rekordbox uses natively (`8A`, `8B`, `2B`).
This tool fixes that — in bulk, across your whole library.

## Usage

```bash
# Preview changes without modifying anything
python rekordbox_key_tool.py --input rekordbox.xml --dry-run

# Convert and write to a new file (recommended first run)
python rekordbox_key_tool.py --input rekordbox.xml --output rekordbox_fixed.xml

# Convert in-place (creates a .bak backup automatically)
python rekordbox_key_tool.py --input rekordbox.xml --inplace

# Verbose output — show every track that was changed
python rekordbox_key_tool.py --input rekordbox.xml --output rekordbox_fixed.xml --verbose
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

## Requirements

Python 3.8+. No external dependencies — uses the standard library only.

## License

MIT
