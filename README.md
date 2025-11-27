# Hump Yard Naming EXIF Plugin

A plugin for [Hump Yard](https://github.com/nalivayev/hump-yard) that extracts metadata from structured photo filenames and writes it to EXIF/XMP fields.

## Overview

This plugin processes photo files with systematically structured filenames, extracting date/time information and other metadata, then writing it to appropriate EXIF and XMP fields within the image files.

## Filename Format

The plugin expects filenames in the following format:

```
YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNNNN.ext
```

Where:
- `YYYY` - Year (4 digits)
- `MM` - Month (01-12, or 00 if unknown)
- `DD` - Day (01-31, or 00 if unknown)
- `HH` - Hour (00-23)
- `NN` - Minute (00-59)
- `SS` - Second (00-59)
- `X` - Date modifier:
  - `A` - Absent (date unknown)
  - `B` - Before (before specified date)
  - `C` - Circa (approximately)
  - `E` - Exact (precise date/time)
  - `F` - aFter (after specified date)
- `GGG` - Group code (alphanumeric)
- `SSS` - Subgroup code (alphanumeric)
- `NNNNNN` - Sequence number (digits)
- `ext` - File extension (.tiff, .tif, .jpg, .jpeg)

**Optional suffixes** (ignored by the parser):
- `.A` / `.R` - Side markers (avers/revers)
- `.RAW` / `.MSR` / `.WEB` / `.PRT` - Version markers

### Examples

- `1950.06.15.12.00.00.E.FAM.POR.000001.tiff` - Exact date with full time
- `1950.06.00.00.00.00.C.FAM.POR.000002.jpg` - Circa June 1950
- `1950.00.00.00.00.00.C.TRV.LND.000003.tiff` - Circa 1950
- `0000.00.00.00.00.00.A.UNK.000.000001.jpg` - Unknown date

## Metadata Mapping

The plugin writes the following EXIF/XMP fields:

### For Exact Dates (Modifier `E`)
- `EXIF:DateTimeOriginal` - Full date and time in format `YYYY:MM:DD HH:MM:SS`
- `XMP:Iptc4xmpCore:DateCreated` - Date only in format `YYYY-MM-DD` (or partial: `YYYY-MM`, `YYYY`)
- `XMP:photoshop:DateCreated` - Full datetime in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`
- `XMP-dc:Identifier` - Random UUID4
- `XMP-xmp:Identifier` - Same UUID4 (duplicated)

### For Non-Exact Dates (Modifiers `A`, `B`, `C`, `F`)
- `XMP:Iptc4xmpCore:DateCreated` - Partial or full date (supports year only, year-month, or full date)
- `XMP-dc:Identifier` - Random UUID4
- `XMP-xmp:Identifier` - Same UUID4 (duplicated)

**Note:** `EXIF:DateTimeOriginal` is only written for exact dates (modifier `E`).

## Installation

### Prerequisites

1. **Hump Yard** (version 0.3.0 or higher)

2. **pyexiv2** library will be installed automatically as a dependency
   - On Windows, the required exiv2 DLL is bundled with pyexiv2
   - On Linux/macOS, you may need to install exiv2: `apt install libexiv2-dev` or `brew install exiv2`

### Installing the Plugin

```bash
pip install hump-yard-naming-exif
```

Or from source:

```bash
git clone https://github.com/nalivayev/hump-yard-naming-exif.git
cd hump-yard-naming-exif
pip install -e .
```

## Configuration

Add the plugin to your Hump Yard configuration file (`config.json`):

```json
{
  "watch_folders": [
    {
      "path": "/path/to/incoming/photos",
      "recursive": true,
      "plugins": ["naming_exif"]
    }
  ]
}
```

## How It Works

1. **File Detection:** The plugin monitors the watched folder(s) configured in Hump Yard
2. **Filename Parsing:** Extracts date, time, modifier, and other components from the filename
3. **Validation:** Validates date/time values and filename format
4. **EXIF Writing:** Writes metadata to appropriate EXIF/XMP fields using ExifTool
5. **File Movement:** Moves successfully processed files to a `processed/` subfolder

### Processing Rules

- Only files with extensions `.tiff`, `.tif`, `.jpg`, `.jpeg` are processed (case-insensitive)
- Symbolic links are ignored
- Files with invalid filenames or dates are skipped and logged
- If metadata cannot be written completely, the file remains in the watched folder
- Successfully processed files are moved to `processed/` subfolder (preserving directory structure if recursive)

## Validation Rules

The plugin enforces the following validation rules:

1. **Date Components:**
   - Month must be 00-12
   - Day must be 00-31 (and valid for the specific month)
   - If month=00, then day must also be 00
   - If day=00, then time must be 00:00:00

2. **Time Components:**
   - Hour must be 00-23
   - Minute must be 00-59
   - Second must be 00-59
   - If hour=00, then minute and second must be 00
   - If minute=00, then second must be 00

3. **Date Modifier:**
   - Must be one of: A, B, C, E, F (case-insensitive)

## Logging

The plugin provides detailed logging:

```
INFO: Processing file: /path/to/1950.06.15.12.00.00.E.FAM.POR.000001.tiff
INFO:   Metadata written to 1950.06.15.12.00.00.E.FAM.POR.000001.tiff:
INFO:     - XMP:Identifier: 550e8400-e29b-41d4-a716-446655440000
INFO:     - EXIF:DateTimeOriginal: 1950:06:15 12:00:00
INFO:     - XMP:Iptc4xmpCore:DateCreated: 1950-06-15
INFO:     - XMP:photoshop:DateCreated: 1950-06-15T12:00:00
INFO:   Moved to: /path/to/processed/1950.06.15.12.00.00.E.FAM.POR.000001.tiff
INFO: Successfully processed: 1950.06.15.12.00.00.E.FAM.POR.000001.tiff
```

For invalid files:

```
ERROR: Invalid filename format: 1950.13.15.00.00.00.E.FAM.POR.000001.tiff
  - Invalid month value: 13 (must be 00-12)
```

## Development

### Requirements

- Python 3.10+
- ExifTool 11.00+
- hump-yard 0.3.0+

### Project Structure

```
hump-yard-naming-exif/
├── src/
│   └── hump_yard_naming_exif/
│       ├── __init__.py          # Package initialization
│       ├── plugin.py            # Main plugin class
│       ├── parser.py            # Filename parser
│       └── validator.py         # Validation logic
├── tests/
│   └── fixtures/                # Test files
├── pyproject.toml               # Project configuration
├── README.md                    # This file
└── LICENSE                      # MIT License
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [Hump Yard](https://github.com/nalivayev/hump-yard) - File monitoring daemon with plugin support
- [ExifTool](https://exiftool.org/) - Read and write meta information in files
