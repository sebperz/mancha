import csv
from datetime import date
from pathlib import Path

from mancha.models.session import Session
from mancha.models.image_pair import ImagePair
from mancha.models.measurement import compute_measurements
from tifffile import imread

COLUMNS = [
    "image", "mask_id", "cell_type",
    "area", "major_axis", "minor_axis",
    "feret", "feret_min", "perimeter",
    "circularity", "calibration", "edge_cell",
]


def export_csv(
    session: Session,
    pairs: list[ImagePair],
    output_folder: Path | None = None,
) -> Path:
    output_folder = output_folder or session.folder
    filename = f"mancha-{date.today().strftime('%Y%m%d')}.csv"
    output_path = output_folder / filename

    cal_str = ""
    if session.calibration:
        cal_str = f"{session.calibration.factor} {session.calibration.units}/px"

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()

        for pair in pairs:
            masks = imread(pair.mask_path)
            for mask_id, cell_type_id in session.classifications.get(
                pair.stem, {}
            ).items():
                ct = session.cell_types.get(cell_type_id)
                cell_type_name = ct.name if ct else cell_type_id

                m = compute_measurements(masks, mask_id, session.calibration)

                writer.writerow({
                    "image": pair.source_path.name,
                    "mask_id": str(mask_id),
                    "cell_type": cell_type_name,
                    "area": f"{m.area:.2f}" if m.area else "",
                    "major_axis": f"{m.major_axis:.2f}" if m.major_axis else "",
                    "minor_axis": f"{m.minor_axis:.2f}" if m.minor_axis else "",
                    "feret": f"{m.feret:.2f}" if m.feret else "",
                    "feret_min": f"{m.feret_min:.2f}" if m.feret_min else "",
                    "perimeter": f"{m.perimeter:.2f}" if m.perimeter else "",
                    "circularity": f"{m.circularity:.4f}",
                    "calibration": cal_str,
                    "edge_cell": str(m.edge_cell),
                })

    return output_path
