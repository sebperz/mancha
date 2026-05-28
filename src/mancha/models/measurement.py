from dataclasses import dataclass

import numpy as np
from skimage.measure import regionprops

from mancha.models.calibration import Calibration


@dataclass
class Measurements:
    area_px: float
    area: float | None
    major_axis: float | None
    minor_axis: float | None
    feret: float | None
    feret_min: float | None
    perimeter: float | None
    circularity: float
    edge_cell: bool


def compute_measurements(
    mask_array: np.ndarray,
    mask_id: int,
    calibration: Calibration | None = None,
) -> Measurements:
    binary = (mask_array == mask_id).astype(np.uint8)
    props_list = regionprops(binary)

    if not props_list:
        raise ValueError(f"No region found for mask_id {mask_id} in array")

    p = props_list[0]
    h, w = mask_array.shape

    area_px = float(p.area)
    perimeter = float(p.perimeter)
    circularity = (4 * np.pi * area_px) / (perimeter * perimeter) if perimeter > 0 else 1.0

    edge_cell = (
        p.bbox[0] == 0 or p.bbox[1] == 0
        or p.bbox[2] == h or p.bbox[3] == w
    )

    factor = calibration.factor if calibration else None
    area_factor = calibration.area_factor if calibration else None

    return Measurements(
        area_px=area_px,
        area=area_px * area_factor if area_factor else None,
        major_axis=float(p.axis_major_length) * factor if factor else None,
        minor_axis=float(p.axis_minor_length) * factor if factor else None,
        feret=float(p.feret_diameter_max) * factor if factor else None,
        feret_min=_feret_min(binary) * factor if factor else None,
        perimeter=perimeter * factor if factor else None,
        circularity=circularity,
        edge_cell=edge_cell,
    )


def _feret_min(binary: np.ndarray) -> float:
    """Approximate minimum Feret diameter by rotating bounding box region."""
    from skimage.transform import rotate
    rows, cols = np.where(binary)
    if len(rows) == 0:
        return 0.0
    r_min, r_max = rows.min(), rows.max()
    c_min, c_max = cols.min(), cols.max()
    crop = binary[r_min:r_max+1, c_min:c_max+1]
    angles = np.arange(0, 180, 5)
    min_width = float("inf")
    for angle in angles:
        rotated = rotate(crop.astype(float), angle, resize=True, order=0)
        r, c = np.where(rotated > 0.5)
        if len(r) == 0:
            continue
        width = c.max() - c.min() + 1
        min_width = min(min_width, width)
    return min_width
