from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QFileDialog, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from mancha.models.image_pair import discover_pairs, ImagePair
from mancha.models.cell_type import CellTypeManager
from mancha.models.calibration import Calibration
from mancha.models.session import Session
from mancha.models.csv_export import export_csv
from mancha.utils.undo import UndoManager
from mancha.widgets.viewport import Viewport
from mancha.widgets.cell_type_panel import CellTypePanel
from mancha.widgets.image_list import ImageList


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mancha")
        self.resize(1400, 900)

        self._session: Session | None = None
        self._pairs: list[ImagePair] = []
        self._current_index: int = -1
        self._undo_manager = UndoManager()

        self._setup_ui()
        self._setup_menus()
        self._setup_shortcuts()

        self._show_welcome()

    # --- UI setup ---

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Horizontal)

        # Sidebar
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)

        self._cell_type_panel = CellTypePanel()
        self._cell_type_panel.cell_type_added.connect(self._on_cell_type_added)
        self._cell_type_panel.cell_type_removed.connect(self._on_cell_type_removed)
        self._cell_type_panel.cell_type_renamed.connect(self._on_cell_type_renamed)
        self._cell_type_panel.cell_type_selected.connect(
            self._on_cell_type_selected
        )

        self._image_list = ImageList()

        nav_layout = QHBoxLayout()
        self._prev_btn = QPushButton("< Prev")
        self._prev_btn.clicked.connect(self._prev_image)
        self._next_btn = QPushButton("Next >")
        self._next_btn.clicked.connect(self._next_image)
        nav_layout.addWidget(self._prev_btn)
        nav_layout.addWidget(self._next_btn)

        sidebar_layout.addWidget(self._cell_type_panel)
        sidebar_layout.addWidget(self._image_list)
        sidebar_layout.addLayout(nav_layout)

        # Viewport
        self._viewport = Viewport()
        self._viewport.mask_left_clicked.connect(self._on_mask_left_click)
        self._viewport.mask_right_clicked.connect(self._on_mask_right_click)

        splitter.addWidget(sidebar)
        splitter.addWidget(self._viewport)
        splitter.setSizes([300, 1100])

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(splitter)

        # Welcome screen
        self._welcome = QWidget()
        welcome_layout = QVBoxLayout(self._welcome)
        welcome_layout.addStretch()
        title = QLabel("Mancha")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        desc = QLabel("Classify and measure cells in microscopy images")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #666;")
        open_btn = QPushButton("Select Image Folder")
        open_btn.setFixedWidth(200)
        open_btn.clicked.connect(self._on_open_folder)
        welcome_layout.addWidget(title)
        welcome_layout.addWidget(desc)
        welcome_layout.addSpacing(20)
        btn_wrap = QHBoxLayout()
        btn_wrap.addStretch()
        btn_wrap.addWidget(open_btn)
        btn_wrap.addStretch()
        welcome_layout.addLayout(btn_wrap)
        welcome_layout.addStretch()

        # Stack welcome on top of splitter
        self._content_stack = QWidget()
        stack_layout = QVBoxLayout(self._content_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.addWidget(self._welcome)
        stack_layout.addWidget(splitter)
        splitter.hide()

        main_layout.addWidget(self._content_stack)

        self.setStatusBar(QStatusBar(self))

    def _setup_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("&Open Folder...", self._on_open_folder, "Ctrl+O")
        file_menu.addAction("Change &Calibration...", self._on_change_calibration)
        file_menu.addAction("Reload Folder", self._on_reload_folder)
        file_menu.addSeparator()
        file_menu.addAction("&Export CSV", self._on_export_csv, "Ctrl+E")
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close, "Ctrl+Q")

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction("&Undo", self._on_undo, "Ctrl+Z")
        edit_menu.addAction("&Redo", self._on_redo, "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("Add Cell Type...", self._cell_type_panel._add_clicked)
        edit_menu.addAction("Delete Cell Type", lambda: self._cell_type_panel._remove_clicked())
        edit_menu.addSeparator()
        edit_menu.addAction("Delete Progress", self._on_delete_progress)

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction("Zoom &In", self._viewport._zoom_in, "Ctrl+=")
        view_menu.addAction("Zoom &Out", self._viewport._zoom_out, "Ctrl+-")
        view_menu.addAction("Fit to Window", self._viewport.fit_to_window, "F")

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About", self._show_about)

    def _setup_shortcuts(self):
        for i in range(1, 10):
            QShortcut(QKeySequence(str(i)), self).activated.connect(
                lambda n=i-1: self._select_type_by_index(n)
            )
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(
            self._prev_image
        )
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(
            self._next_image
        )
        QShortcut(QKeySequence(Qt.Key_Space), self).activated.connect(
            self._next_image
        )

    # --- Welcome / Folder ---

    def _show_welcome(self):
        self._welcome.show()
        self._content_stack.findChildren(QSplitter)[0].hide()

    def _on_open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Image Folder"
        )
        if not folder:
            return
        self._open_folder(Path(folder))

    def _open_folder(self, folder: Path):
        self._welcome.hide()
        self._content_stack.findChildren(QSplitter)[0].show()

        self._session = Session.load(folder)
        self._pairs, warnings = discover_pairs(folder)

        if warnings:
            msg = "\n".join(
                f"[{w.level}] {w.message}" for w in warnings
            )
            QMessageBox.warning(self, "Folder Warnings", msg)

        if not self._pairs:
            QMessageBox.information(self, "No Images", "No valid image-mask pairs found.")
            return

        self._cell_type_panel.load(self._session.cell_types)
        self._image_list.load(self._pairs, self._session)
        self._image_list.list_widget.itemClicked.connect(self._on_image_clicked)

        self._current_index = 0
        self._show_current_image()

        self.setWindowTitle(f"Mancha — {folder.name}")
        self._update_status()

    def _on_reload_folder(self):
        if self._session:
            self._open_folder(self._session.folder)

    # --- Image navigation ---

    def _show_current_image(self):
        if 0 <= self._current_index < len(self._pairs):
            pair = self._pairs[self._current_index]
            self._viewport.load_pair(pair)
            self._update_mask_colors_from_session()
            self._image_list.list_widget.setCurrentRow(self._current_index)
            self._update_status()

    def _prev_image(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._show_current_image()

    def _next_image(self):
        if self._current_index < len(self._pairs) - 1:
            self._current_index += 1
            self._show_current_image()

    def _on_image_clicked(self, item):
        index = item.data(1)
        if index is not None and index != self._current_index:
            self._current_index = index
            self._show_current_image()

    # --- Mask interaction ---

    def _on_mask_left_click(self, mask_id: int):
        if not self._session or self._current_index < 0:
            return
        ct_id = self._cell_type_panel.selected_id
        if ct_id is None:
            return
        stem = self._pairs[self._current_index].stem

        old = self._session.get_classification(stem, mask_id)
        self._session.classify(stem, mask_id, ct_id)
        self._save_session()

        self._undo_manager.push(
            do=lambda: (
                self._session.classify(stem, mask_id, ct_id),
                self._save_session(),
                self._update_mask_colors(),
            ),
            undo=lambda: (
                self._session.unclassify(stem, mask_id) if ct_id == self._session.get_classification(stem, mask_id) else (
                    self._session.classify(stem, mask_id, old) if old else self._session.unclassify(stem, mask_id)
                ),
                self._save_session(),
                self._update_mask_colors(),
            ),
        )

        self._update_mask_colors()
        self._update_image_list()
        self._update_status()

    def _on_mask_right_click(self, mask_id: int):
        if not self._session or self._current_index < 0:
            return
        stem = self._pairs[self._current_index].stem
        old = self._session.get_classification(stem, mask_id)
        if old is None:
            return

        self._session.unclassify(stem, mask_id)
        self._save_session()

        self._undo_manager.push(
            do=lambda: (
                self._session.unclassify(stem, mask_id),
                self._save_session(),
                self._update_mask_colors(),
            ),
            undo=lambda: (
                self._session.classify(stem, mask_id, old),
                self._save_session(),
                self._update_mask_colors(),
            ),
        )

        self._update_mask_colors()
        self._update_image_list()
        self._update_status()

    def _update_mask_colors(self):
        self._update_mask_colors_from_session()

    def _update_mask_colors_from_session(self):
        if not self._session:
            return
        colors = {}
        for ct in self._session.cell_types.types:
            stem = (
                self._pairs[self._current_index].stem
                if 0 <= self._current_index < len(self._pairs)
                else None
            )
            if stem:
                for mid, ct_id in self._session.classifications.get(
                    stem, {}
                ).items():
                    if ct_id == ct.id:
                        colors[mid] = ct.color
        self._viewport.set_cell_type_colors(colors)

    # --- Cell type management ---

    def _on_cell_type_added(self, name: str):
        if self._session:
            self._session.cell_types.add(name)
            self._cell_type_panel.load(self._session.cell_types)
            self._save_session()

    def _on_cell_type_removed(self, ct_id: str):
        if self._session:
            for stem in self._session.classifications:
                to_remove = [
                    mid for mid, cid in self._session.classifications[stem].items()
                    if cid == ct_id
                ]
                for mid in to_remove:
                    self._session.unclassify(stem, mid)
            self._session.cell_types.remove(ct_id)
            self._cell_type_panel.load(self._session.cell_types)
            self._update_mask_colors_from_session()
            self._save_session()

    def _on_cell_type_renamed(self, ct_id: str, new_name: str):
        if self._session:
            self._session.cell_types.rename(ct_id, new_name)
            self._cell_type_panel.load(self._session.cell_types)
            self._save_session()

    def _on_cell_type_selected(self, ct_id: str):
        pass  # selection is tracked internally by the panel

    def _select_type_by_index(self, index: int):
        if self._session and index < self._cell_type_panel.list_widget.count():
            item = self._cell_type_panel.list_widget.item(index)
            self._cell_type_panel.list_widget.setCurrentItem(item)
            self._cell_type_panel.list_widget.itemClicked.emit(item)

    # --- Menu actions ---

    def _on_change_calibration(self):
        if not self._session:
            return
        # TODO: proper calibration dialog
        from PySide6.QtWidgets import QInputDialog
        pixels, ok1 = QInputDialog.getDouble(
            self, "Calibration", "Number of pixels:", 100, 1, 100000
        )
        if not ok1:
            return
        magnitude, ok2 = QInputDialog.getDouble(
            self, "Calibration", f"Equal how many units?", 10, 0.001, 100000
        )
        if not ok2:
            return
        units, ok3 = QInputDialog.getText(self, "Calibration", "Unit name (e.g. µm):", text="µm")
        if not ok3:
            return
        self._session.calibration = Calibration(
            units=units.strip(),
            magnitude=magnitude,
            pixels=pixels,
        )
        self._save_session()
        self._update_status()

    def _on_export_csv(self):
        if not self._session:
            return
        if self._session.calibration is None:
            reply = QMessageBox.question(
                self,
                "No Calibration",
                "No calibration set. Export in raw pixels?",
            )
            if reply != QMessageBox.Yes:
                return
        path = export_csv(self._session, self._pairs)
        self.statusBar().showMessage(f"Exported: {path.name}")

    def _on_undo(self):
        self._undo_manager.undo()
        self._update_mask_colors_from_session()
        self._update_image_list()
        self._update_status()

    def _on_redo(self):
        self._undo_manager.redo()
        self._update_mask_colors_from_session()
        self._update_image_list()
        self._update_status()

    def _on_delete_progress(self):
        if not self._session:
            return
        reply = QMessageBox.warning(
            self,
            "Delete Progress",
            "This will delete all classifications and cell types "
            "for this folder. This action cannot be undone.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        config_path = self._session.folder / ".mancha"
        if config_path.exists():
            config_path.unlink()

        self._session = Session.new(self._session.folder)
        self._session.save()
        self._cell_type_panel.load(self._session.cell_types)
        self._image_list.load(self._pairs, self._session)
        self._update_mask_colors_from_session()
        self._update_status()
        self._undo_manager.clear()

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Mancha",
            "Mancha v0.5\n\n"
            "Desktop tool for classifying and measuring\n"
            "cells in microscopy images.\n\n"
            "https://github.com/sebperz/mancha",
        )

    # --- Helpers ---

    def _save_session(self):
        if self._session:
            self._session.save()

    def _update_image_list(self):
        if self._session:
            self._image_list.load(self._pairs, self._session)

    def _update_status(self):
        if not self._session or self._current_index < 0:
            self.statusBar().showMessage("")
            return

        pair = self._pairs[self._current_index]
        total = len(self._pairs)
        classified = self._session.classified_count(pair.stem)
        ct_name = self._cell_type_panel.selected_id or "-"
        cal = self._session.calibration
        cal_str = (
            f"{cal.factor:.2f} {cal.units}/px" if cal else "not set"
        )

        self.statusBar().showMessage(
            f"{pair.source_path.name} ({self._current_index+1}/{total})"
            f"  |  Classified: {classified}"
            f"  |  Calibration: {cal_str}"
            f"  |  Cell type: {ct_name}"
        )
