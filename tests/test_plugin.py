"""Unit tests for PhotoNamingExifPlugin."""

import pytest
from pathlib import Path
from hump_yard_naming_exif.plugin import PhotoNamingExifPlugin
from hump_yard_naming_exif.parser import FilenameParser


class TestPhotoNamingExifPlugin:
    """Test cases for PhotoNamingExifPlugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return PhotoNamingExifPlugin()

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == 'naming_exif'

    def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == '0.1.0'

    def test_can_handle_valid_tiff(self, plugin):
        """Test can_handle accepts valid TIFF file."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.tiff') is True

    def test_can_handle_valid_jpg(self, plugin):
        """Test can_handle accepts valid JPG file."""
        assert plugin.can_handle('1950.06.00.00.00.00.C.FAM.POR.000002.jpg') is True

    def test_can_handle_invalid_extension(self, plugin):
        """Test can_handle rejects invalid extension."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.png') is False

    def test_can_handle_invalid_filename(self, plugin):
        """Test can_handle rejects invalid filename format."""
        assert plugin.can_handle('invalid.jpg') is False

    def test_can_handle_invalid_date(self, plugin):
        """Test can_handle rejects invalid date."""
        assert plugin.can_handle('1950.13.15.00.00.00.E.FAM.POR.000001.tiff') is False

    def test_can_handle_case_insensitive_extension(self, plugin):
        """Test can_handle works with uppercase extensions."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.TIFF') is True
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.JPG') is True

    def test_parse_and_validate_valid_file(self, plugin):
        """Test _parse_and_validate with valid filename."""
        result = plugin._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self, plugin):
        """Test _parse_and_validate with invalid filename."""
        result = plugin._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self, plugin):
        """Test _parse_and_validate with invalid date."""
        result = plugin._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.tiff')
        assert result is None

    def test_build_metadata_dict_exact_date(self, plugin, parser):
        """Test _build_metadata_dict for exact date."""
        parsed = parser.parse('1950.06.15.12.30.00.E.FAM.POR.000001.tiff')
        metadata = plugin._build_metadata_dict(parsed)
        
        assert 'XMP:Identifier' in metadata
        assert 'EXIF:DateTimeOriginal' in metadata
        assert 'XMP:Iptc4xmpCore:DateCreated' in metadata
        assert 'XMP:photoshop:DateCreated' in metadata
        assert metadata['EXIF:DateTimeOriginal'] == '1950:06:15 12:30:00'
        assert metadata['XMP:Iptc4xmpCore:DateCreated'] == '1950-06-15'
        assert metadata['XMP:photoshop:DateCreated'] == '1950-06-15T12:30:00'

    def test_build_metadata_dict_circa_date(self, plugin, parser):
        """Test _build_metadata_dict for circa date."""
        parsed = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.jpg')
        metadata = plugin._build_metadata_dict(parsed)
        
        assert 'XMP:Identifier' in metadata
        assert 'EXIF:DateTimeOriginal' not in metadata  # No EXIF for non-exact dates
        assert 'XMP:Iptc4xmpCore:DateCreated' in metadata
        assert metadata['XMP:Iptc4xmpCore:DateCreated'] == '1950-06'

    def test_build_metadata_dict_year_only(self, plugin, parser):
        """Test _build_metadata_dict for year only."""
        parsed = parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.tiff')
        metadata = plugin._build_metadata_dict(parsed)
        
        assert 'XMP:Iptc4xmpCore:DateCreated' in metadata
        assert metadata['XMP:Iptc4xmpCore:DateCreated'] == '1950'

    def test_build_metadata_dict_absent_date(self, plugin, parser):
        """Test _build_metadata_dict for absent date."""
        parsed = parser.parse('0000.00.00.00.00.00.A.UNK.000.000001.jpg')
        metadata = plugin._build_metadata_dict(parsed)
        
        assert 'XMP:Identifier' in metadata
        # No date fields when year is 0
        assert 'XMP:Iptc4xmpCore:DateCreated' not in metadata
        assert 'XMP:photoshop:DateCreated' not in metadata

    def test_format_iptc_date_full(self, plugin, parser):
        """Test _format_iptc_date with full date."""
        parsed = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.tiff')
        result = plugin._format_iptc_date(parsed)
        assert result == '1950-06-15'

    def test_format_iptc_date_year_month(self, plugin, parser):
        """Test _format_iptc_date with year and month."""
        parsed = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.jpg')
        result = plugin._format_iptc_date(parsed)
        assert result == '1950-06'

    def test_format_iptc_date_year_only(self, plugin, parser):
        """Test _format_iptc_date with year only."""
        parsed = parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.tiff')
        result = plugin._format_iptc_date(parsed)
        assert result == '1950'

    def test_format_iptc_date_absent(self, plugin, parser):
        """Test _format_iptc_date with absent date."""
        parsed = parser.parse('0000.00.00.00.00.00.A.UNK.000.000001.jpg')
        result = plugin._format_iptc_date(parsed)
        assert result is None

    def test_format_photoshop_datetime_with_time(self, plugin, parser):
        """Test _format_photoshop_datetime with time."""
        parsed = parser.parse('1950.06.15.12.30.45.E.FAM.POR.000001.tiff')
        result = plugin._format_photoshop_datetime(parsed)
        assert result == '1950-06-15T12:30:45'

    def test_format_photoshop_datetime_no_time(self, plugin, parser):
        """Test _format_photoshop_datetime without time."""
        parsed = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.jpg')
        result = plugin._format_photoshop_datetime(parsed)
        assert result == '1950-06'

    def test_supported_extensions(self, plugin):
        """Test all supported extensions."""
        extensions = ['.tiff', '.tif', '.jpg', '.jpeg']
        
        for ext in extensions:
            filename = f'1950.06.15.12.00.00.E.FAM.POR.000001{ext}'
            assert plugin.can_handle(filename) is True, f"Extension {ext} should be supported"
