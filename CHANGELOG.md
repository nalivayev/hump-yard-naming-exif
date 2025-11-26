# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-26

### Added
- Initial release
- Parse structured photo filenames in format `YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNNNN.ext`
- Write metadata to EXIF/XMP fields:
  - `EXIF:DateTimeOriginal` (for exact dates only)
  - `XMP:Iptc4xmpCore:DateCreated` (date only)
  - `XMP:photoshop:DateCreated` (date + time in ISO 8601)
  - `XMP:Identifier` (random UUID4)
- Validate dates and filename format with detailed error messages
- Support for date modifiers: A (Absent), B (Before), C (Circa), E (Exact), F (aFter)
- Support for partial dates (year only, year+month, full date)
- Support for file extensions: .tiff, .tif, .jpg, .jpeg (case-insensitive)
- Automatic creation of `processed/` subfolder
- Move successfully processed files to `processed/` subfolder
- Preserve directory structure when processing files recursively
- Detailed logging of all operations
- Integration with Hump Yard plugin system via entry points
- ExifTool version check (requires >= 11.00)
- Skip symlinks and unsupported file types
- Ignore optional filename suffixes (.A, .R, .RAW, .MSR, .WEB, .PRT)
