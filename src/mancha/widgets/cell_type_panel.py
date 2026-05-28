from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QBrush

from mancha.models.cell_type import CellTypeManager


class CellTypePanel(QWidget):
    cell_type_selected = Signal(str)
    cell_type_added = Signal(str)
    cell_type_removed = Signal(str)
    cell_type_renamed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self._selected_id: str | None = None

        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._add_clicked)
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._remove_clicked)
        self._rename_btn = QPushButton("Rename")
        self._rename_btn.clicked.connect(self._rename_clicked)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addWidget(self._rename_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)

    def load(self, manager: CellTypeManager) -> None:
        self.list_widget.clear()
        self._selected_id = None
        for ct in manager.types:
            item = QListWidgetItem(ct.name)
            item.setData(1, ct.id)
            item.setBackground(QBrush(QColor(*ct.color)))
            self.list_widget.addItem(item)

    @property
    def selected_id(self) -> str | None:
        return self._selected_id

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        ct_id = item.data(1)
        if ct_id:
            self._selected_id = ct_id
            self.cell_type_selected.emit(ct_id)

    def _add_clicked(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Add Cell Type", "Name:"
        )
        if ok and name.strip():
            self.cell_type_added.emit(name.strip())

    def _remove_clicked(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        ct_id = item.data(1)
        if ct_id:
            reply = QMessageBox.question(
                self,
                "Remove Cell Type",
                f"Remove '{item.text()}'? Masks will become unclassified.",
            )
            if reply == QMessageBox.Yes:
                self.cell_type_removed.emit(ct_id)

    def _rename_clicked(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        ct_id = item.data(1)
        if ct_id:
            name, ok = QInputDialog.getText(
                self, "Rename Cell Type", "New name:", text=item.text()
            )
            if ok and name.strip():
                self.cell_type_renamed.emit(ct_id, name.strip())
