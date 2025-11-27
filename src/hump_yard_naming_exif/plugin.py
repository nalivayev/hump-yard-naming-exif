"""Photo naming EXIF plugin for hump-yard."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Optional

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

        # Skip files in 'processed' subfolder to avoid re-processing
        if 'processed' in path.parts:
            return False

        # Skip symlinks
        if path.is_symlink():
            return False

        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Try to parse and validate filename
        parsed = self._parse_and_validate(path.name)
        return parsed is not None

    def process(self, file_path: str, config: dict[str, Any]) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata, and move to processed folder.

        Args:
            file_path: Path to the file to process.
            config: Plugin-specific configuration parameters.

        Returns:
            True if processing successful, False otherwise.
        """
        path = Path(file_path)
        self.logger.info(f"Processing file: {path}")

        # Parse and validate filename
        parsed = self._parse_and_validate(path.name)
        if not parsed:
            self.logger.error(f"Failed to parse or validate filename: {path.name}")
            return False

        # Write EXIF/XMP metadata
        if not self._write_metadata(path, parsed):
            return False

        # Move to processed folder
        if not self._move_to_processed(path):
            return False

        self.logger.info(f"Successfully processed: {path.name}")
        return True

    def _parse_and_validate(self, filename: str) -> Optional[ParsedFilename]:
        """Parse and validate a filename.

        Args:
            filename: The filename to parse and validate.

        Returns:
            Parsed filename data if valid, None otherwise.
        """
        parsed = self.parser.parse(filename)
        if not parsed:
            return None

        validation_errors = self.validator.validate(parsed)
        if validation_errors:
            return None

        return parsed

    def _build_metadata_dict(self, parsed: ParsedFilename) -> dict[str, str]:
        """Build metadata dictionary from parsed filename.

        Args:
            parsed: Parsed filename data.

        Returns:
            Dictionary of metadata tags and values.
        """
        metadata = {"XMP:Identifier": str(uuid.uuid4())}

        # Add EXIF:DateTimeOriginal for exact dates only
        if parsed.modifier == "E":
            metadata["EXIF:DateTimeOriginal"] = (
                f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} "
                f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
            )

        # Add XMP date fields
        iptc_date = self._format_iptc_date(parsed)
        if iptc_date:
            metadata["XMP:Iptc4xmpCore:DateCreated"] = iptc_date

        photoshop_datetime = self._format_photoshop_datetime(parsed)
        if photoshop_datetime:
            metadata["XMP:photoshop:DateCreated"] = photoshop_datetime

        return metadata

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
                # Build metadata dictionary
                metadata = self._build_metadata_dict(parsed)

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

        This field requires a complete date (modifier 'E'), unlike IPTC DateCreated
        which accepts partial dates.

        Args:
            parsed: Parsed filename data.

        Returns:
            Formatted datetime string or None if date is not complete (modifier != 'E').
        """
        # Only for exact dates (modifier 'E')
        if parsed.modifier != "E":
            return None

        # Build full date
        date_part = f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"

        # Add time if not all zeros
        if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
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
