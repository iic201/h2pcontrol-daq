from __future__ import annotations

from typing import Any

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

from .grpc.gui_grpc import ServiceStatus


STYLESHEET = """
QMainWindow {
    background: #f8fafc;
}
QToolBar {
    spacing: 4px;
    padding: 3px 6px;
    border: 0px;
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
}
QToolBar QToolButton {
    padding: 4px 7px;
    border-radius: 4px;
}
QToolBar QToolButton:hover {
    background: #eef2ff;
}
QToolBar QToolButton,
QToolBar QToolButton:disabled {
    color: #000000;
}
QComboBox, QLineEdit, QTableView, QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #d6dbe3;
    border-radius: 4px;
}
QComboBox, QLineEdit {
    padding: 3px 6px;
}
QTableView::item {
    color: #000000;
    padding: 2px 4px;
}
QTableView::item:selected {
    color: #000000;
    background: #dfeafe;
}
QHeaderView::section {
    color: #000000;
    background: #f9fafb;
    border: 0px;
    border-bottom: 1px solid #d6dbe3;
    padding: 4px;
}
QLabel {
    color: #111827;
}
QStatusBar {
    color: #374151;
    background: #ffffff;
    border-top: 1px solid #e5e7eb;
}
"""


class ServiceTableModel(QtCore.QAbstractTableModel):
    headers = ["Service", "Manager", "GUI", "Address"]

    def __init__(self) -> None:
        super().__init__()
        self._services: list[ServiceStatus] = []

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._services)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.headers)

    def data(
        self,
        index: QtCore.QModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._services)):
            return None
        service = self._services[index.row()]
        values = [
            service.name,
            "ok" if service.healthy else "down",
            "yes" if service.gui_connectable else "no",
            service.address,
        ]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole and index.column() in (1, 2):
            return QtCore.Qt.AlignmentFlag.AlignCenter
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and index.column() in (1, 2):
            healthy = service.healthy if index.column() == 1 else service.gui_connectable
            return QtGui.QBrush(QtGui.QColor("#047857" if healthy else "#b91c1c"))
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            lines = [
                f"name: {service.name}",
                f"address: {service.address}",
                f"manager: {'ok' if service.healthy else 'down'}",
                f"gui: {'yes' if service.gui_connectable else 'no'}",
            ]
            if service.last_seen:
                lines.append(f"last seen: {service.last_seen}")
            if service.detail:
                lines.append(service.detail)
            return "\n".join(lines)
        return None

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal and 0 <= section < len(self.headers):
            return self.headers[section]
        return section + 1

    def set_services(self, services: list[ServiceStatus]) -> None:
        self.beginResetModel()
        self._services = list(services)
        self.endResetModel()

    def service_at(self, row: int) -> ServiceStatus | None:
        if 0 <= row < len(self._services):
            return self._services[row]
        return None


def build_main_window_ui(window) -> None:
    toolbar = window.addToolBar("Actions")
    toolbar.setMovable(False)
    toolbar.setIconSize(QtCore.QSize(18, 18))
    toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    style = window.style()
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload),
        "Refresh",
        window._refresh_services,
    )
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton),
        "Connect",
        window._connect_selected_service,
    )
    window.target_edit = QtWidgets.QLineEdit(window.target)
    window.target_edit.setPlaceholderText("127.0.0.1:5055")
    window.target_edit.setMinimumWidth(150)
    window.target_edit.setMaximumWidth(210)
    window.target_edit.returnPressed.connect(window._connect_selected_service)
    toolbar.addWidget(QtWidgets.QLabel("Target"))
    toolbar.addWidget(window.target_edit)
    toolbar.addSeparator()
    window.start_stream_action = toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay),
        "Start stream",
        window._start_local_stream,
    )
    window.start_stream_action.setToolTip("Start receiving preview frames in this GUI")
    window.stop_stream_action = toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop),
        "Stop stream",
        window._stop_local_stream,
    )
    window.stop_stream_action.setToolTip("Stop receiving preview frames in this GUI")
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton),
        "Save selection",
        window._save_history_interval,
    )
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton),
        "Save local",
        window._save_selection_locally,
    )
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton),
        "Integral",
        window._calculate_selection_integral,
    )
    toolbar.addSeparator()
    toolbar.addWidget(QtWidgets.QLabel("Selection window"))
    window.window_spin = QtWidgets.QDoubleSpinBox()
    window.window_spin.setRange(1.0, 3600.0)
    window.window_spin.setDecimals(1)
    window.window_spin.setSingleStep(5.0)
    window.window_spin.setValue(window.history_seconds)
    window.window_spin.setSuffix(" s")
    window.window_spin.setMinimumWidth(100)
    window.window_spin.valueChanged.connect(window._selection_window_changed)
    toolbar.addWidget(window.window_spin)
    toolbar.addAction(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload),
        "Clear data",
        window._clear_display_data,
    )
    toolbar.addSeparator()
    window.source_combo = QtWidgets.QComboBox()
    window.source_combo.setMinimumWidth(150)
    window.source_combo.setMaximumWidth(240)
    window.source_combo.setEnabled(False)
    window.source_combo.currentIndexChanged.connect(window._source_selected)
    toolbar.addWidget(QtWidgets.QLabel("Source"))
    toolbar.addWidget(window.source_combo)

    central = QtWidgets.QWidget(window)
    window.setCentralWidget(central)
    root_layout = QtWidgets.QVBoxLayout(central)
    root_layout.setContentsMargins(10, 8, 10, 10)
    root_layout.setSpacing(8)

    header = QtWidgets.QHBoxLayout()
    header.setSpacing(10)

    window.title_label = QtWidgets.QLabel("h2pgui")
    title_font = QtGui.QFont()
    title_font.setPointSize(13)
    title_font.setBold(True)
    window.title_label.setFont(title_font)

    window.context_label = QtWidgets.QLabel("Select a server from the list and connect.")
    window.context_label.setStyleSheet("color: #6b7280;")
    window.context_label.setTextInteractionFlags(
        QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
    )

    header.addWidget(window.title_label)
    header.addWidget(window.context_label, 1)
    header.addStretch(1)
    root_layout.addLayout(header)

    splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
    splitter.setChildrenCollapsible(False)

    plot_container = QtWidgets.QWidget()
    plot_layout = QtWidgets.QVBoxLayout(plot_container)
    plot_layout.setContentsMargins(0, 0, 0, 0)
    plot_layout.setSpacing(0)
    axis = DateAxisItem(orientation="bottom")
    window.plot_widget = pg.PlotWidget(axisItems={"bottom": axis})
    window.plot_widget.setBackground("w")
    window.plot_widget.showGrid(x=True, y=True, alpha=0.2)
    window.plot_widget.setLabel("bottom", "time")
    window.plot_widget.setLabel("left", "value")
    window.plot_widget.setMenuEnabled(False)
    window.plot_widget.setClipToView(True)
    window.plot_widget.addLegend(offset=(12, 12))
    window.selection_region = pg.LinearRegionItem(
        values=(0.0, window.history_seconds),
        orientation="vertical",
        brush=pg.mkBrush(37, 99, 235, 45),
        pen=pg.mkPen("#2563eb", width=1.5),
    )
    window.selection_region.setZValue(10)
    window.selection_region.sigRegionChanged.connect(window._selection_region_changed)
    window.selection_region.sigRegionChangeFinished.connect(window._selection_region_changed)
    window.plot_widget.addItem(window.selection_region)
    window.selection_label = pg.TextItem(color="#1d4ed8", anchor=(0, 1))
    window.selection_label.setZValue(11)
    window.plot_widget.addItem(window.selection_label, ignoreBounds=True)
    plot_layout.addWidget(window.plot_widget)

    side = QtWidgets.QWidget()
    side.setMinimumWidth(340)
    side_layout = QtWidgets.QVBoxLayout(side)
    side_layout.setContentsMargins(0, 0, 0, 0)
    side_layout.setSpacing(8)

    section_font = QtGui.QFont()
    section_font.setPointSize(10)
    section_font.setBold(True)

    services_header = QtWidgets.QHBoxLayout()
    services_title = QtWidgets.QLabel("Services")
    services_title.setFont(section_font)
    window.services_count_label = QtWidgets.QLabel("0")
    window.services_count_label.setStyleSheet("color: #6b7280;")
    services_header.addWidget(services_title)
    services_header.addStretch(1)
    services_header.addWidget(window.services_count_label)

    window.service_model = ServiceTableModel()
    window.service_view = QtWidgets.QTableView()
    window.service_view.setModel(window.service_model)
    window.service_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    window.service_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
    window.service_view.setAlternatingRowColors(True)
    window.service_view.setShowGrid(False)
    window.service_view.horizontalHeader().setStretchLastSection(False)
    window.service_view.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    window.service_view.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
    window.service_view.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
    window.service_view.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
    window.service_view.setColumnWidth(1, 72)
    window.service_view.setColumnWidth(2, 54)
    window.service_view.verticalHeader().setVisible(False)
    window.service_view.verticalHeader().setDefaultSectionSize(24)
    window.service_view.doubleClicked.connect(lambda _index: window._connect_selected_service())
    selection_model = window.service_view.selectionModel()
    if selection_model is not None:
        selection_model.selectionChanged.connect(lambda *_args: window._on_service_select())

    window.latest_title = QtWidgets.QLabel("Latest")
    window.latest_title.setFont(section_font)
    window.latest_text = QtWidgets.QPlainTextEdit()
    window.latest_text.setReadOnly(True)
    window.latest_text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
    window.latest_text.setMaximumBlockCount(400)
    mono = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
    mono.setPointSize(10)
    window.latest_text.setFont(mono)

    side_layout.addLayout(services_header)
    side_layout.addWidget(window.service_view, 2)
    side_layout.addWidget(window.latest_title)
    side_layout.addWidget(window.latest_text, 1)

    splitter.addWidget(plot_container)
    splitter.addWidget(side)
    splitter.setStretchFactor(0, 4)
    splitter.setStretchFactor(1, 2)
    splitter.setSizes([720, 340])
    root_layout.addWidget(splitter, 1)

    window.statusBar().showMessage("Starting stream")
    window.setStyleSheet(STYLESHEET)
