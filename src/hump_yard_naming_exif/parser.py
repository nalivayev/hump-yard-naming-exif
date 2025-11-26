"""Filename parser for structured photo filenames."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ParsedFilename:
    """Parsed filename data."""

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    modifier: str
    group: str
    subgroup: str
    sequence: str
    extension: str


class FilenameParser:
    """Parser for structured photo filenames.

    Expected format: YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNNNN.ext
    Optional suffixes (ignored): .A, .R, .RAW, .MSR, .WEB, .PRT, etc.
    """

    # Pattern to match the filename format
    # First 10 components are required, everything after is ignored
    PATTERN = re.compile(
        r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.([a-zA-Z])\.([^.]+)\.([^.]+)\.(\d+)"
        r"(?:\.[^.]+)*"  # Optional suffixes (ignored)
        r"\.([a-zA-Z]+)$",  # Extension
        re.IGNORECASE
    )

    def parse(self, filename: str) -> Optional[ParsedFilename]:
        """Parse a filename into components.

        Args:
            filename: Filename to parse.

        Returns:
            ParsedFilename object if parsing successful, None otherwise.
        """
        match = self.PATTERN.match(filename)
        if not match:
            return None

        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            modifier = match.group(7)
            group = match.group(8)
            subgroup = match.group(9)
            sequence = match.group(10)
            extension = match.group(11)

            return ParsedFilename(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second,
                modifier=modifier.upper(),  # Normalize to uppercase
                group=group,
                subgroup=subgroup,
                sequence=sequence,
                extension=extension.lower()  # Normalize to lowercase
            )

        except (ValueError, IndexError):
            return None
