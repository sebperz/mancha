from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt

from mancha.models.cell_type import CellTypeManager
from mancha.widgets.cell_type_panel import CellTypePanel


def test_panel_shows_types(qtbot: QtBot):
    manager = CellTypeManager.create_template()
    panel = CellTypePanel()
    qtbot.addWidget(panel)

    panel.load(manager)

    assert panel.list_widget.count() == 2
    assert "Cell Type 1" in panel.list_widget.item(0).text()
    assert "Cell Type 2" in panel.list_widget.item(1).text()


def test_select_type_emits_signal(qtbot: QtBot):
    manager = CellTypeManager.create_template()
    panel = CellTypePanel()
    qtbot.addWidget(panel)
    panel.load(manager)

    emitted = []
    panel.cell_type_selected.connect(lambda ct_id: emitted.append(ct_id))

    item = panel.list_widget.item(0)
    panel.list_widget.itemClicked.emit(item)

    assert emitted == ["cell_type_1"]


def test_select_type_updates_button_state(qtbot: QtBot):
    manager = CellTypeManager.create_template()
    panel = CellTypePanel()
    qtbot.addWidget(panel)
    panel.load(manager)

    panel.list_widget.setCurrentRow(0)
    panel.list_widget.itemClicked.emit(panel.list_widget.item(0))

    assert panel._selected_id is not None
