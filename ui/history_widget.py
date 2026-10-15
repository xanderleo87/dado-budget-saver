"""Searchable expense and income history table with view toggle."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QPushButton, QAbstractItemView, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from core.database import DatabaseManager
from utils.constants import COLORS
from utils.helpers import format_currency, current_month_year


class HistoryWidget(QWidget):
    """Searchable expense/income history with filters and view toggle."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._view_mode = "expenses"  # "expenses" or "income"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header row with view toggle
        header_row = QHBoxLayout()

        self.header_label = QLabel("\u2726 Expense History")
        self.header_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.header_label.setStyleSheet(f"background: transparent; color: {COLORS['magic_glow']}; letter-spacing: 2px;")
        header_row.addWidget(self.header_label)

        header_row.addStretch()

        # View toggle
        view_label = QLabel("View:")
        view_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 13px; background: transparent;")
        header_row.addWidget(view_label)

        self.view_selector = QComboBox()
        self.view_selector.setMinimumHeight(32)
        self.view_selector.setMinimumWidth(130)
        self.view_selector.addItems(["Expenses", "Income"])
        self.view_selector.currentIndexChanged.connect(self._on_view_changed)
        header_row.addWidget(self.view_selector)

        layout.addLayout(header_row)

        # Filters row
        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search expenses...")
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self._on_search)
        filters.addWidget(self.search_input, 1)

        self.category_filter = QComboBox()
        self.category_filter.setMinimumHeight(36)
        self.category_filter.setMinimumWidth(150)
        self.category_filter.addItem("All Categories", None)
        categories = self.db.get_categories()
        for cat in categories:
            self.category_filter.addItem(cat["name"], cat["id"])
        self.category_filter.currentIndexChanged.connect(self._on_filter)
        filters.addWidget(self.category_filter)

        self.period_filter = QComboBox()
        self.period_filter.setMinimumHeight(36)
        self.period_filter.setMinimumWidth(130)
        self.period_filter.addItems(["This Month", "Last Month", "Last 3 Months", "All Time"])
        self.period_filter.currentIndexChanged.connect(self._on_filter)
        filters.addWidget(self.period_filter)

        layout.addLayout(filters)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Description", "Merchant", "Category", "Amount", "ID"])
        self.table.setColumnHidden(5, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header_view = self.table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table, 1)

        # Summary row
        self.summary_label = QLabel("0 expenses | Total: \u20b10.00")
        self.summary_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; background: transparent;")
        layout.addWidget(self.summary_label)

    def _on_view_changed(self, index):
        """Switch between Expenses and Income views."""
        if index == 0:
            self._view_mode = "expenses"
            self.header_label.setText("\u2726 Expense History")
            self.search_input.setPlaceholderText("Search expenses...")
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["Date", "Description", "Merchant", "Category", "Amount", "ID"])
            self.table.setColumnHidden(5, True)
            self.category_filter.setVisible(True)
        else:
            self._view_mode = "income"
            self.header_label.setText("\u2726 Income History")
            self.search_input.setPlaceholderText("Search income...")
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["Date", "Source", "Description", "Recurring", "Amount", "ID"])
            self.table.setColumnHidden(5, True)
            self.category_filter.setVisible(False)

        # Re-setup header sizing
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._on_filter()

    def refresh(self):
        """Reload data based on filters."""
        self._on_filter()

    def _get_date_range(self) -> tuple:
        from datetime import datetime, timedelta
        from utils.helpers import now_ph
        now = now_ph()
        period = self.period_filter.currentText()

        if period == "This Month":
            start = now.strftime("%Y-%m-01")
            end = now.strftime("%Y-%m-%d")
        elif period == "Last Month":
            first = now.replace(day=1) - timedelta(days=1)
            start = first.strftime("%Y-%m-01")
            end = first.strftime("%Y-%m-%d")
        elif period == "Last 3 Months":
            start = (now - timedelta(days=90)).strftime("%Y-%m-%d")
            end = now.strftime("%Y-%m-%d")
        else:
            start = "2000-01-01"
            end = now.strftime("%Y-%m-%d")
        return start, end

    def _on_search(self, text):
        self._on_filter()

    def _on_filter(self):
        if self._view_mode == "expenses":
            self._load_expenses()
        else:
            self._load_income()

    def _load_expenses(self):
        start, end = self._get_date_range()
        cat_id = self.category_filter.currentData()
        search = self.search_input.text().strip()

        if search:
            expenses = self.db.search_expenses(description_like=search, limit=200)
            expenses = [e for e in expenses if start <= e["date"] <= end]
            if cat_id:
                expenses = [e for e in expenses if e["category_id"] == cat_id]
        else:
            expenses = self.db.get_expenses(start_date=start, end_date=end,
                                            category_id=cat_id, limit=200)

        self.table.setRowCount(len(expenses))
        total = 0
        for i, e in enumerate(expenses):
            self.table.setItem(i, 0, QTableWidgetItem(e.get("date", "")))
            self.table.setItem(i, 1, QTableWidgetItem(e.get("description", "")))
            self.table.setItem(i, 2, QTableWidgetItem(e.get("merchant", "") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(e.get("category_name", "")))

            amount = e.get("amount", 0)
            total += amount
            amt_item = QTableWidgetItem(format_currency(amount))
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, amt_item)

            self.table.setItem(i, 5, QTableWidgetItem(str(e.get("id", ""))))

        self.summary_label.setText(
            f"{len(expenses)} expense{'s' if len(expenses) != 1 else ''} | Total: {format_currency(total)}"
        )

    def _load_income(self):
        start, end = self._get_date_range()
        search = self.search_input.text().strip()

        if search:
            income_list = self.db.search_income(source_like=search, limit=200)
            income_list = [i for i in income_list if start <= i["date"] <= end]
        else:
            income_list = self.db.get_income(start_date=start, end_date=end, limit=200)

        self.table.setRowCount(len(income_list))
        total = 0
        for i, inc in enumerate(income_list):
            self.table.setItem(i, 0, QTableWidgetItem(inc.get("date", "")))
            self.table.setItem(i, 1, QTableWidgetItem(inc.get("source", "")))
            self.table.setItem(i, 2, QTableWidgetItem(inc.get("description", "") or ""))
            recurring = "Yes" if inc.get("is_recurring") else "No"
            self.table.setItem(i, 3, QTableWidgetItem(recurring))

            amount = inc.get("amount", 0)
            total += amount
            amt_item = QTableWidgetItem(format_currency(amount))
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            amt_item.setForeground(QColor(COLORS["green"]))
            self.table.setItem(i, 4, amt_item)

            self.table.setItem(i, 5, QTableWidgetItem(str(inc.get("id", ""))))

        self.summary_label.setText(
            f"{len(income_list)} income entr{'ies' if len(income_list) != 1 else 'y'} | Total: {format_currency(total)}"
        )
