import numpy as np
import pytest
from mancha.models.calibration import Calibration
from mancha.models.measurement import compute_measurements


def test_calibration_factor():
    cal = Calibration(units="µm", magnitude=10, pixels=100)
    assert cal.factor == 0.1


def test_calibration_factor_squared_for_area():
    cal = Calibration(units="µm", magnitude=10, pixels=100)
    assert cal.area_factor == pytest.approx(0.01)


def test_measurements_for_simple_rectangle():
    mask = np.zeros((20, 20), dtype=np.uint16)
    mask[5:15, 4:14] = 1

    m = compute_measurements(mask, 1)

    assert m.area_px == 100
    assert m.edge_cell is False


def test_complete_circle_has_circularity_one():
    y, x = np.ogrid[-50:50, -50:50]
    mask = np.zeros((100, 100), dtype=np.uint16)
    mask[x**2 + y**2 <= 40**2] = 1

    m = compute_measurements(mask, 1)

    assert m.circularity == pytest.approx(1.0, abs=0.1)


def test_edge_cell_detected():
    mask = np.zeros((20, 20), dtype=np.uint16)
    mask[0:5, 0:5] = 1

    m = compute_measurements(mask, 1)

    assert m.edge_cell is True


def test_measurements_with_calibration():
    cal = Calibration(units="µm", magnitude=10, pixels=100)
    mask = np.zeros((20, 20), dtype=np.uint16)
    mask[5:15, 4:14] = 1

    m = compute_measurements(mask, 1, calibration=cal)

    assert m.area == pytest.approx(1.0)
    assert m.area_px == 100


def test_measurements_without_calibration_are_none():
    mask = np.zeros((20, 20), dtype=np.uint16)
    mask[5:15, 4:14] = 1

    m = compute_measurements(mask, 1)

    assert m.area is None
    assert m.area_px == 100
