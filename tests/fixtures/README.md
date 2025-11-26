# Test Fixtures

This directory contains example files for testing the plugin.

## Running Tests

From the project root directory:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=hump_yard_naming_exif --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::TestFilenameParser::test_parse_exact_date_with_time
```

## Test Structure

- `test_parser.py` - Tests for filename parsing (11 tests)
- `test_validator.py` - Tests for filename validation (15 tests)
- `test_plugin.py` - Tests for plugin functionality (20 tests)

**Total: 46 unit tests**

## Valid Filenames

- `1950.06.15.12.00.00.E.FAM.POR.000001.tiff` - Exact date with full time
- `1950.06.15.00.00.00.E.FAM.POR.000002.tiff` - Exact date, no time
- `1950.06.00.00.00.00.C.FAM.VAC.000003.jpg` - Circa June 1950
- `1950.00.00.00.00.00.C.TRV.LND.000004.jpg` - Circa 1950
- `0000.00.00.00.00.00.A.UNK.000.000005.tiff` - Unknown date

## Invalid Filenames (Should be rejected)

- `1950.13.15.00.00.00.E.FAM.POR.000001.tiff` - Invalid month (13)
- `1950.02.30.00.00.00.E.FAM.POR.000002.tiff` - Invalid day (Feb 30)
- `1950.06.15.25.00.00.E.FAM.POR.000003.tiff` - Invalid hour (25)
- `1950.00.15.00.00.00.C.FAM.POR.000004.tiff` - Month=00 but day=15
- `1950.06.00.14.30.00.C.FAM.POR.000005.tiff` - Day=00 but time specified
- `photo.jpg` - Not in expected format

## Creating Test Files

To create actual image files for testing:

```bash
# Create a small test TIFF image
convert -size 100x100 xc:white test.tiff

# Rename to valid format
mv test.tiff 1950.06.15.12.00.00.E.FAM.POR.000001.tiff
```

Or use ImageMagick/similar tools to generate small test images.
