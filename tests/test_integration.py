"""Integration smoke test: full pipeline from folder open to CSV export."""
import csv
from pathlib import Path

from mancha.models.image_pair import discover_pairs
from mancha.models.calibration import Calibration
from mancha.models.session import Session
from mancha.models.csv_export import export_csv


def test_full_pipeline_on_sample_data(tmp_path: Path):
    sample_dir = Path(__file__).parent.parent / "sampleData"
    pairs, warnings = discover_pairs(sample_dir)
    assert len(pairs) == 18
    assert warnings == []

    session = Session.new(tmp_path)
    session.calibration = Calibration(units="µm", magnitude=10, pixels=100)
    ct = session.cell_types.add("Neuron")

    for pair in pairs[:3]:
        masks = __import__("tifffile").imread(pair.mask_path)
        for mask_id in [int(i) for i in __import__("numpy").unique(masks[masks > 0])[:2]]:
            session.classify(pair.stem, mask_id, ct.id)

    path = export_csv(session, pairs, output_folder=tmp_path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0
    for row in rows:
        assert row["cell_type"] == "Neuron"
        assert row["calibration"] == "0.1 µm/px"
