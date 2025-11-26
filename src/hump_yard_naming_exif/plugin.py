"""Photo naming EXIF plugin for hump-yard."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import exiftool

from hump_yard.base_plugin import FileProcessorPlugin

from .parser import FilenameParser, ParsedFilename
from .validator import FilenameValidator


class PhotoNamingExifPlugin(FileProcessorPlugin):
    """Plugin that extracts metadata from structured photo filenames and writes to EXIF/XMP."""

    SUPPORTED_EXTENSIONS = {".tiff", ".tif", ".jpg", ".jpeg"}

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.parser = FilenameParser()
        self.validator = FilenameValidator()
        self._exiftool_version_checked = False

    @property
    def name(self) -> str:
        """Get the unique name of the plugin.

        Returns:
            The plugin name.
        """
        return "naming_exif"

    @property
    def version(self) -> str:
        """Get the version of the plugin.

        Returns:
            The plugin version string.
        """
        return "0.1.0"

    def can_handle(self, file_path: str) -> bool:
        """Check if the plugin can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the plugin can process the file, False otherwise.
        """
        path = Path(file_path)

        # Skip symlinks
        if path.is_symlink():
            return False

        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Try to parse filename
        parsed = self.parser.parse(path.name)
        if not parsed:
            return False

        # Validate parsed data
        validation_errors = self.validator.validate(parsed)
        return len(validation_errors) == 0

    def _check_exiftool(self) -> bool:
        """Check if ExifTool is installed and meets minimum version requirement.

        Returns:
            True if ExifTool is available and version >= 11.00, False otherwise.
        """
        if self._exiftool_version_checked:
            return True

        try:
            with exiftool.ExifToolHelper() as et:
                version_output = et.version
                # Version is returned as float (e.g., 12.42)
                if version_output >= 11.0:
                    self.logger.info(f"ExifTool version {version_output} detected")
                    self._exiftool_version_checked = True
                    return True
                else:
                    self.logger.error(
                        f"ExifTool version {version_output} is too old. "
                        f"Minimum required version is 11.00"
                    )
                    return False
        except Exception as e:
            self.logger.error(f"ExifTool not found or not accessible: {e}")
            self.logger.error(
                "Please install ExifTool from https://exiftool.org/ and ensure it's in your PATH"
            )
            return False

    def initialize(self, config: dict) -> bool:
        """Initialize the plugin with configuration.

        Args:
            config: Plugin configuration dictionary.

        Returns:
            True if initialization successful, False otherwise.
        """
        if not self._check_exiftool():
            return False

        self.logger.info("PhotoNamingExifPlugin initialized successfully")
        return True

    def process(self, file_path: str, config: Dict[str, Any]) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata, and move to processed folder.

        Args:
            file_path: Path to the file to process.
            config: Plugin-specific configuration parameters.

        Returns:
            True if processing successful, False otherwise.
        """
        path = Path(file_path)
        self.logger.info(f"Processing file: {path}")

        # Parse filename (can_handle already validated, but we parse again to get data)
        parsed = self.parser.parse(path.name)
        if not parsed:
            self.logger.error(f"Failed to parse filename: {path.name}")
            return False

        # Validate parsed data (should not fail if can_handle passed, but double-check)
        validation_errors = self.validator.validate(parsed)
        if validation_errors:
            self.logger.error(
                f"Invalid filename format: {path.name}\n"
                + "\n".join(f"  - {error}" for error in validation_errors)
            )
            return False

        # Write EXIF/XMP metadata
        if not self._write_metadata(path, parsed):
            return False

        # Move to processed folder
        if not self._move_to_processed(path):
            return False

        self.logger.info(f"Successfully processed: {path.name}")
        return True

    def _write_metadata(self, file_path: Path, parsed: ParsedFilename) -> bool:
        """Write metadata to EXIF/XMP fields.

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data.

        Returns:
            True if all metadata written successfully, False otherwise.
        """
        try:
            with exiftool.ExifToolHelper() as et:
                # Generate UUID for identifier
                file_uuid = str(uuid.uuid4())

                # Prepare metadata dictionary
                metadata = {
                    "XMP:Identifier": file_uuid,
                }

                # Add dates based on modifier
                if parsed.modifier.upper() == "E":
                    # Exact date: write to EXIF:DateTimeOriginal
                    exif_datetime = f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                    metadata["EXIF:DateTimeOriginal"] = exif_datetime

                # Write to XMP:Iptc4xmpCore:DateCreated (date only)
                iptc_date = self._format_iptc_date(parsed)
                if iptc_date:
                    metadata["XMP:Iptc4xmpCore:DateCreated"] = iptc_date

                # Write to XMP:photoshop:DateCreated (date + time in ISO 8601)
                photoshop_datetime = self._format_photoshop_datetime(parsed)
                if photoshop_datetime:
                    metadata["XMP:photoshop:DateCreated"] = photoshop_datetime

                # Set metadata
                et.set_tags(
                    str(file_path),
                    tags=metadata,
                    params=["-P", "-overwrite_original"]
                )

                # Log detailed information
                self.logger.info(f"  Metadata written to {file_path.name}:")
                for key, value in metadata.items():
                    self.logger.info(f"    - {key}: {value}")

                return True

        except Exception as e:
            self.logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False

    def _format_iptc_date(self, parsed: ParsedFilename) -> Optional[str]:
        """Format date for XMP:Iptc4xmpCore:DateCreated (date only, no time).

        Args:
            parsed: Parsed filename data.

        Returns:
            Formatted date string or None if date is completely unknown.
        """
        if parsed.year == 0:
            return None

        if parsed.month == 0:
            return f"{parsed.year:04d}"

        if parsed.day == 0:
            return f"{parsed.year:04d}-{parsed.month:02d}"

        return f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"

    def _format_photoshop_datetime(self, parsed: ParsedFilename) -> Optional[str]:
        """Format datetime for XMP:photoshop:DateCreated (ISO 8601 with time).

        Args:
            parsed: Parsed filename data.

        Returns:
            Formatted datetime string or None if date is completely unknown.
        """
        if parsed.year == 0:
            return None

        # Build date part
        if parsed.month == 0:
            date_part = f"{parsed.year:04d}"
        elif parsed.day == 0:
            date_part = f"{parsed.year:04d}-{parsed.month:02d}"
        else:
            date_part = f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"

        # Add time if day is known and time is not all zeros
        if parsed.day != 0 and (parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0):
            time_part = f"T{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
            return date_part + time_part

        return date_part

    def _move_to_processed(self, file_path: Path) -> bool:
        """Move file to processed subfolder, preserving directory structure.

        Args:
            file_path: Path to the file.

        Returns:
            True if move successful, False otherwise.
        """
        try:
            # Determine the watched folder root
            # We need to find the base watched folder to create processed/ structure
            # For now, create processed/ in the same directory as the file
            file_dir = file_path.parent
            processed_dir = file_dir / "processed"

            # Create processed directory if it doesn't exist
            processed_dir.mkdir(parents=True, exist_ok=True)

            # Destination path
            dest_path = processed_dir / file_path.name

            # Check if destination already exists
            if dest_path.exists():
                self.logger.error(
                    f"Destination file already exists: {dest_path}. "
                    f"Leaving source file in place."
                )
                return False

            # Move file
            shutil.move(str(file_path), str(dest_path))
            self.logger.info(f"  Moved to: {dest_path}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to move file {file_path} to processed/: {e}")
            return False
