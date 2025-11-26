"""Unit tests for filename parser."""

import pytest
from hump_yard_naming_exif.parser import FilenameParser, ParsedFilename


class TestFilenameParser:
    """Test cases for FilenameParser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_parse_exact_date_with_time(self, parser):
        """Test parsing filename with exact date and time."""
        result = parser.parse('1950.06.15.12.30.45.E.FAM.POR.000001.tiff')
        
        assert result is not None
        assert result.year == 1950
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.modifier == 'E'
        assert result.group == 'FAM'
        assert result.subgroup == 'POR'
        assert result.sequence == '000001'
        assert result.extension == 'tiff'

    def test_parse_circa_month(self, parser):
        """Test parsing filename with circa month."""
        result = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.jpg')
        
        assert result is not None
        assert result.year == 1950
        assert result.month == 6
        assert result.day == 0
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.modifier == 'C'

    def test_parse_circa_year(self, parser):
        """Test parsing filename with circa year only."""
        result = parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.tiff')
        
        assert result is not None
        assert result.year == 1950
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'C'

    def test_parse_absent_date(self, parser):
        """Test parsing filename with absent date."""
        result = parser.parse('0000.00.00.00.00.00.A.UNK.000.000001.jpg')
        
        assert result is not None
        assert result.year == 0
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'A'

    def test_parse_with_suffix_a(self, parser):
        """Test parsing filename with .A suffix."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.tiff')
        
        assert result is not None
        assert result.year == 1950
        assert result.extension == 'tiff'

    def test_parse_with_suffix_raw(self, parser):
        """Test parsing filename with .RAW suffix."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.RAW.jpg')
        
        assert result is not None
        assert result.extension == 'jpg'

    def test_parse_with_multiple_suffixes(self, parser):
        """Test parsing filename with multiple suffixes."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.RAW.WEB.tiff')
        
        assert result is not None
        assert result.extension == 'tiff'

    def test_parse_invalid_format(self, parser):
        """Test parsing invalid filename format."""
        result = parser.parse('invalid.jpg')
        assert result is None

    def test_parse_incomplete_date(self, parser):
        """Test parsing filename with incomplete date components."""
        result = parser.parse('1950.06.15.tiff')
        assert result is None

    def test_parse_modifier_case_insensitive(self, parser):
        """Test that modifier is converted to uppercase."""
        result = parser.parse('1950.06.15.12.00.00.e.FAM.POR.000001.tiff')
        
        assert result is not None
        assert result.modifier == 'E'

    def test_parse_extension_case_insensitive(self, parser):
        """Test that extension is converted to lowercase."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.TIFF')
        
        assert result is not None
        assert result.extension == 'tiff'
