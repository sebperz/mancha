import pytest
from pathlib import Path
from mancha.models.image_pair import discover_pairs, ImagePair, ValidationWarning
import numpy as np
from tifffile import imwrite
from PIL import Image


def test_empty_folder_returns_no_pairs(tmp_path: Path):
    pairs, warnings = discover_pairs(tmp_path)
    assert pairs == []
    assert warnings == []


def test_matching_pair_discovered(tmp_path: Path):
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint16)
    Image.fromarray(img).save(tmp_path / "test.jpg")
    imwrite(tmp_path / "test_masks.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert len(pairs) == 1
    assert pairs[0] == ImagePair(
        source_path=tmp_path / "test.jpg",
        mask_path=tmp_path / "test_masks.tif",
        stem="test",
    )
    assert warnings == []


def test_png_source_discovered(tmp_path: Path):
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint16)
    Image.fromarray(img).save(tmp_path / "test.png")
    imwrite(tmp_path / "test_masks.tif", mask)

    pairs, _ = discover_pairs(tmp_path)

    assert len(pairs) == 1
    assert pairs[0].source_path.suffix == ".png"
    assert pairs[0].stem == "test"


def test_missing_source_warns(tmp_path: Path):
    mask = np.zeros((10, 10), dtype=np.uint16)
    imwrite(tmp_path / "orphan_masks.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert pairs == []
    assert len(warnings) == 1
    assert warnings[0].level == "missing_source"
    assert warnings[0].file == tmp_path / "orphan_masks.tif"


def test_uppercase_extension_discovered(tmp_path: Path):
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint16)
    Image.fromarray(img).save(tmp_path / "cells.JPG")
    imwrite(tmp_path / "cells_masks.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert len(pairs) == 1
    assert pairs[0].source_path == tmp_path / "cells.JPG"
    assert pairs[0].stem == "cells"
    assert warnings == []


def test_size_mismatch_warns(tmp_path: Path):
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint16)
    Image.fromarray(img).save(tmp_path / "img.jpg")
    imwrite(tmp_path / "img_masks.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert len(warnings) == 1
    assert warnings[0].level == "size_mismatch"
    assert warnings[0].file == tmp_path / "img.jpg"
    assert pairs == []


def test_tif_source_not_confused_as_mask(tmp_path: Path):
    mask = np.zeros((10, 10), dtype=np.uint16)
    imwrite(tmp_path / "image_masks.tif", mask)
    imwrite(tmp_path / "image.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert len(pairs) == 1
    assert pairs[0].source_path.suffix == ".tif"
    assert pairs[0].mask_path.name == "image_masks.tif"
    assert warnings == []


def test_multiple_pairs_discovered(tmp_path: Path):
    for i in range(3):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        mask = np.zeros((10, 10), dtype=np.uint16)
        Image.fromarray(img).save(tmp_path / f"img_{i}.jpg")
        imwrite(tmp_path / f"img_{i}_masks.tif", mask)

    pairs, warnings = discover_pairs(tmp_path)

    assert len(pairs) == 3
    stems = {p.stem for p in pairs}
    assert stems == {f"img_{i}" for i in range(3)}
    assert warnings == []


def test_sample_data_all_18_pairs():
    sample_dir = Path(__file__).parent.parent / "sampleData"
    pairs, warnings = discover_pairs(sample_dir)

    assert len(pairs) == 18
    assert warnings == []

    stems = {p.stem for p in pairs}
    expected = {
        f"Croc1_II{i}" for i in
        [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 19, 21, 22, 23]
    }
    assert stems == expected
