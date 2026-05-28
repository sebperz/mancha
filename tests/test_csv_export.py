import csv
from pathlib import Path
import numpy as np
from PIL import Image
from tifffile import imwrite

from mancha.models.session import Session
from mancha.models.image_pair import ImagePair, discover_pairs
from mancha.models.calibration import Calibration
from mancha.models.csv_export import export_csv


def _make_pair(tmp_path: Path, stem: str, size=(10, 10)) -> ImagePair:
    img = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    mask = np.zeros((size[0], size[1]), dtype=np.uint16)
    mask[2:5, 2:5] = 1
    Image.fromarray(img).save(tmp_path / f"{stem}.jpg")
    imwrite(tmp_path / f"{stem}_masks.tif", mask)
    return discover_pairs(tmp_path)[0][0]


def test_empty_session_produces_header_only(tmp_path: Path):
    session = Session.new(tmp_path)
    pairs: list[ImagePair] = []

    path = export_csv(session, pairs, output_folder=tmp_path)

    with open(path) as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0] == [
        "image", "mask_id", "cell_type",
        "area", "major_axis", "minor_axis",
        "feret", "feret_min", "perimeter",
        "circularity", "calibration", "edge_cell",
    ]


def test_one_classified_mask_produces_one_row(tmp_path: Path):
    pair = _make_pair(tmp_path, "img01")
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]
    session.classify("img01", 1, ct.id)

    path = export_csv(session, [pair], output_folder=tmp_path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["image"] == "img01.jpg"
    assert rows[0]["mask_id"] == "1"
    assert rows[0]["cell_type"] == "Cell Type 1"


def test_only_classified_masks_exported(tmp_path: Path):
    pair = _make_pair(tmp_path, "img01")
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]
    session.classify("img01", 1, ct.id)

    path = export_csv(session, [pair], output_folder=tmp_path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1


def test_export_with_calibration(tmp_path: Path):
    pair = _make_pair(tmp_path, "img01")
    session = Session.new(tmp_path)
    session.calibration = Calibration(units="µm", magnitude=10, pixels=100)
    ct = session.cell_types.types[0]
    session.classify("img01", 1, ct.id)

    path = export_csv(session, [pair], output_folder=tmp_path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]["area"] != ""
    assert rows[0]["calibration"] == "0.1 µm/px"


def test_filename_has_date(tmp_path: Path):
    session = Session.new(tmp_path)
    pairs: list[ImagePair] = []

    path = export_csv(session, pairs, output_folder=tmp_path)

    assert path.name.startswith("mancha-")
    assert path.name.endswith(".csv")
