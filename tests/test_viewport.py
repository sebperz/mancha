import numpy as np
from PIL import Image
from pathlib import Path
from tifffile import imwrite
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt, QPointF

from mancha.models.image_pair import ImagePair
from mancha.widgets.viewport import Viewport


def _make_pair(tmp_path: Path, stem: str, size: tuple[int, int] = (10, 10)) -> ImagePair:
    img = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    mask = np.zeros((size[0], size[1]), dtype=np.uint16)
    mask[2:5, 2:5] = 1
    mask[6:8, 6:8] = 2
    Image.fromarray(img).save(tmp_path / f"{stem}.jpg")
    imwrite(tmp_path / f"{stem}_masks.tif", mask)
    return ImagePair(
        source_path=tmp_path / f"{stem}.jpg",
        mask_path=tmp_path / f"{stem}_masks.tif",
        stem=stem,
    )


def _setup_viewport(qtbot, tmp_path, stem="test"):
    pair = _make_pair(tmp_path, stem)
    viewport = Viewport()
    qtbot.addWidget(viewport)
    viewport.resize(200, 200)
    viewport.load_pair(pair)
    viewport.resetTransform()
    viewport.setSceneRect(0, 0, 10, 10)
    return viewport


def _click(viewport, qtbot, scene_x, scene_y, button=Qt.LeftButton):
    widget_pos = viewport.mapFromScene(QPointF(scene_x, scene_y))
    qtbot.mouseClick(viewport.viewport(), button, pos=widget_pos)


def test_load_pair_populates_scene(qtbot: QtBot, tmp_path: Path):
    pair = _make_pair(tmp_path, "test")

    viewport = Viewport()
    qtbot.addWidget(viewport)

    viewport.load_pair(pair)

    assert len(viewport.scene().items()) > 0


def test_mask_overlay_count_matches_mask_file(qtbot: QtBot, tmp_path: Path):
    pair = _make_pair(tmp_path, "test")

    viewport = Viewport()
    qtbot.addWidget(viewport)

    viewport.load_pair(pair)

    mask_items = viewport.mask_items
    assert len(mask_items) == 2


def test_set_cell_type_colors_updates_brush(qtbot: QtBot, tmp_path: Path):
    pair = _make_pair(tmp_path, "test")

    viewport = Viewport()
    qtbot.addWidget(viewport)

    viewport.load_pair(pair)
    viewport.set_cell_type_colors({1: (255, 0, 0)})

    item = viewport.mask_items[0]
    color = item.brush().color()
    assert color.red() == 255
    assert color.green() == 0
    assert color.blue() == 0


def test_show_hide_masks_toggles_visibility(qtbot: QtBot, tmp_path: Path):
    pair = _make_pair(tmp_path, "test")

    viewport = Viewport()
    qtbot.addWidget(viewport)

    viewport.load_pair(pair)

    viewport.hide_masks()
    assert all(not item.isVisible() for item in viewport.mask_items)

    viewport.show_masks()
    assert all(item.isVisible() for item in viewport.mask_items)


def test_unclassified_masks_are_gray(qtbot: QtBot, tmp_path: Path):
    pair = _make_pair(tmp_path, "test")

    viewport = Viewport()
    qtbot.addWidget(viewport)

    viewport.load_pair(pair)

    for item in viewport.mask_items:
        color = item.brush().color()
        assert color.red() == 128
        assert color.green() == 128
        assert color.blue() == 128
        assert color.alpha() == 76


def test_left_click_on_mask_emits_signal(qtbot: QtBot, tmp_path: Path):
    viewport = _setup_viewport(qtbot, tmp_path)

    clicked_ids = []
    viewport.mask_left_clicked.connect(lambda mid: clicked_ids.append(mid))

    _click(viewport, qtbot, 3, 3)

    assert clicked_ids == [1]


def test_right_click_on_mask_emits_signal(qtbot: QtBot, tmp_path: Path):
    viewport = _setup_viewport(qtbot, tmp_path)

    clicked_ids = []
    viewport.mask_right_clicked.connect(lambda mid: clicked_ids.append(mid))

    _click(viewport, qtbot, 3, 3, Qt.RightButton)

    assert clicked_ids == [1]


def test_click_on_background_emits_nothing(qtbot: QtBot, tmp_path: Path):
    viewport = _setup_viewport(qtbot, tmp_path)

    left_ids = []
    right_ids = []
    viewport.mask_left_clicked.connect(lambda mid: left_ids.append(mid))
    viewport.mask_right_clicked.connect(lambda mid: right_ids.append(mid))

    _click(viewport, qtbot, 0, 0)

    assert left_ids == []
    assert right_ids == []


def test_selected_mask_id_updates_on_click(qtbot: QtBot, tmp_path: Path):
    viewport = _setup_viewport(qtbot, tmp_path)

    assert viewport.selected_mask_id is None

    _click(viewport, qtbot, 3, 3)
    assert viewport.selected_mask_id == 1

    _click(viewport, qtbot, 7, 7)
    assert viewport.selected_mask_id == 2
