"""Test homeassistant volume utility functions."""

import unittest
import homeassistant.util.volume as volume_util
from homeassistant.const import (PRESSURE_PA, PRESSURE_HPA, PRESSURE_MBAR,
                                 PRESSURE_INHG)
import pytest

INVALID_SYMBOL = 'bob'
VALID_SYMBOL = PRESSURE_PA


class TestVolumeUtil(unittest.TestCase):
    """Test the volume utility functions."""

    def test_convert_same_unit(self):
        """Test conversion from any unit to same unit."""
        assert volume_util.convert(2, PRESSURE_PA, PRESSURE_PA) == 2
        assert volume_util.convert(3, PRESSURE_HPA, PRESSURE_HPA) == 3
        assert volume_util.convert(4, PRESSURE_MBAR, PRESSURE_MBAR) == 4
        assert volume_util.convert(5, PRESSURE_INHG, PRESSURE_INHG) == 5

    def test_convert_invalid_unit(self):
        """Test exception is thrown for invalid units."""
        with pytest.raises(ValueError):
            volume_util.convert(5, INVALID_SYMBOL, VALID_SYMBOL)

        with pytest.raises(ValueError):
            volume_util.convert(5, VALID_SYMBOL, INVALID_SYMBOL)

    def test_convert_nonnumeric_value(self):
        """Test exception is thrown for nonnumeric type."""
        with pytest.raises(TypeError):
            volume_util.convert('a', PRESSURE_HPA, PRESSURE_INHG)

    def test_convert_from_hpascals(self):
        """Test conversion from liters to other units."""
        hpascals = 1000
        self.assertAlmostEqual(
            volume_util.convert(hpascals, PRESSURE_HPA, PRESSURE_INHG),
            29.529983071445)
        self.assertAlmostEqual(
            volume_util.convert(hpascals, PRESSURE_HPA, PRESSURE_PA),
            10)
        self.assertAlmostEqual(
            volume_util.convert(hpascals, PRESSURE_HPA, PRESSURE_MBAR),
            1000)

    def test_convert_from_inhg(self):
        """Test conversion from gallons to other units."""
        inhg = 30
        self.assertAlmostEqual(
            volume_util.convert(inhg, PRESSURE_INHG, PRESSURE_HPA),
            1015.9166)
        self.assertAlmostEqual(
            volume_util.convert(inhg, PRESSURE_INHG, PRESSURE_PA),
            101591)
        self.assertAlmostEqual(
            volume_util.convert(inhg, PRESSURE_INHG, PRESSURE_MBAR),
            1015.9166)
