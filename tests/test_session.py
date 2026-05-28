import json
from pathlib import Path
import pytest
from mancha.models.session import Session
from mancha.models.calibration import Calibration


def test_new_session_has_template_types_and_no_calibration(tmp_path: Path):
    session = Session.new(tmp_path)

    assert session.folder == tmp_path
    assert session.cell_types.count == 2
    assert session.cell_types.types[0].name == "Cell Type 1"
    assert session.cell_types.types[1].name == "Cell Type 2"
    assert session.calibration is None
    assert session.classifications == {}
    assert session.version == "0.5"


def test_classify_assigns_cell_type(tmp_path: Path):
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]

    session.classify("img_01", 3, ct.id)
    session.classify("img_01", 7, ct.id)

    assert session.get_classification("img_01", 3) == ct.id
    assert session.get_classification("img_01", 7) == ct.id


def test_unclassify_removes_assignment(tmp_path: Path):
    session = Session.new(tmp_path)
    ct = session.cell_types.types[0]

    session.classify("img_01", 3, ct.id)
    session.unclassify("img_01", 3)

    assert session.get_classification("img_01", 3) is None


def test_get_classification_returns_none_for_unknown(tmp_path: Path):
    session = Session.new(tmp_path)

    assert session.get_classification("img_01", 3) is None
    assert session.get_classification("nonexistent", 99) is None


def test_save_and_load_roundtrip(tmp_path: Path):
    session = Session.new(tmp_path)
    session.calibration = Calibration(units="µm", magnitude=10, pixels=100)
    ct = session.cell_types.add("Neuron")
    session.classify("img_01", 3, ct.id)
    session.save()

    loaded = Session.load(tmp_path)

    assert loaded.folder == tmp_path
    assert loaded.cell_types.count == 3
    assert loaded.cell_types.types[2].name == "Neuron"
    assert loaded.cell_types.types[2].id == ct.id
    assert loaded.cell_types.types[2].color == ct.color
    assert loaded.calibration == Calibration(units="µm", magnitude=10, pixels=100)
    assert loaded.get_classification("img_01", 3) == ct.id
    assert loaded.version == "0.5"


def test_corrupted_mancha_renamed_and_fresh_start(tmp_path: Path):
    config_path = tmp_path / ".mancha"
    config_path.write_text("not valid json {{{")

    session = Session.load(tmp_path)

    assert session.cell_types.count == 2
    assert session.calibration is None
    assert (tmp_path / ".mancha.corrupt").exists()
    assert not config_path.exists()

    session.save()
    assert config_path.exists()
    assert json.loads(config_path.read_text())
