"""Dashboard widget with charts, analytics, and income tracking."""

from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QProgressBar, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.database import DatabaseManager
from ui.components.summary_card import SummaryCard
from ui.components.chart_canvas import PieChartCanvas, BarChartCanvas
from utils.constants import COLORS
from utils.helpers import format_currency, current_month_year, month_display


class DashboardWidget(QWidget):
    """Dashboard with summary cards, charts, and budget progress."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_month = current_month_year()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setContentsMargins(20, 16, 20, 16)
        self.layout_main.setSpacing(16)

        # Month navigation - Coraline style
        nav = QHBoxLayout()
        nav_btn_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['surface_solid']}, stop:1 rgba(45, 27, 78, 0.5));
                border-radius: 8px;
                color: {COLORS['magic_glow']};
                font-size: 14px;
                border: 2px solid rgba(22, 181, 179, 0.3);
            }}
            QPushButton:hover {{
                background: {COLORS['surface_hover']};
                border: 2px solid rgba(22, 181, 179, 0.6);
            }}
        """
        self.prev_btn = QPushButton("\u25c0")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setStyleSheet(nav_btn_style)
        self.prev_btn.clicked.connect(self._prev_month)

        self.month_label = QLabel(month_display(self._current_month))
        self.month_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.month_label.setStyleSheet(f"background: transparent; color: {COLORS['magic_glow']}; letter-spacing: 2px;")

        self.next_btn = QPushButton("\u25b6")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setStyleSheet(nav_btn_style)
        self.next_btn.clicked.connect(self._next_month)

        nav.addWidget(self.prev_btn)
        nav.addWidget(self.month_label)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        self.layout_main.addLayout(nav)

        # Summary cards - 2x3 grid
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        self.total_card = SummaryCard("Total Spent", "\u20b10", "", COLORS["red"])
        self.budget_card = SummaryCard("Budget Left", "\u20b10", "", COLORS["green"])
        self.loans_card = SummaryCard("Active Loans", "0", "", COLORS["yellow"])
        self.top_cat_card = SummaryCard("Top Category", "-", "", COLORS["accent"])
        self.income_card = SummaryCard("Monthly Income", "\u20b10", "", COLORS["accent"])
        self.savings_card = SummaryCard("Income vs Expense", "\u20b10", "", COLORS["pink"])

        cards_grid.addWidget(self.total_card, 0, 0)
        cards_grid.addWidget(self.budget_card, 0, 1)
        cards_grid.addWidget(self.loans_card, 0, 2)
        cards_grid.addWidget(self.top_cat_card, 1, 0)
        cards_grid.addWidget(self.income_card, 1, 1)
        cards_grid.addWidget(self.savings_card, 1, 2)

        self.layout_main.addLayout(cards_grid)

        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)

        # Pie chart - Coraline neon card
        pie_frame = QFrame()
        pie_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 16px;
                border: 2px solid rgba(22, 181, 179, 0.4);
            }}
        """)
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(12, 12, 12, 12)
        self.pie_chart = PieChartCanvas(5, 3.5)
        pie_layout.addWidget(self.pie_chart)
        charts_layout.addWidget(pie_frame)

        # Bar chart
        bar_frame = QFrame()
        bar_frame.setStyleSheet(pie_frame.styleSheet())
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(12, 12, 12, 12)
        self.bar_chart = BarChartCanvas(5, 3.5)
        bar_layout.addWidget(self.bar_chart)
        charts_layout.addWidget(bar_frame)

        self.layout_main.addLayout(charts_layout)

        # Budget progress section
        budget_header = QLabel("\u2726 Budget Progress")
        budget_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        budget_header.setStyleSheet(f"background: transparent; color: {COLORS['magic_glow']}; letter-spacing: 1px;")
        self.layout_main.addWidget(budget_header)

        self.budget_frame = QFrame()
        self.budget_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 14px;
                border: 2px solid rgba(22, 181, 179, 0.3);
            }}
        """)
        self.budget_layout = QVBoxLayout(self.budget_frame)
        self.budget_layout.setContentsMargins(16, 12, 16, 12)
        self.budget_layout.setSpacing(10)
        self.layout_main.addWidget(self.budget_frame)

        # Recent expenses
        recent_header = QLabel("\u2726 Recent Expenses")
        recent_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        recent_header.setStyleSheet(f"background: transparent; color: {COLORS['pink_hover']}; letter-spacing: 1px;")
        self.layout_main.addWidget(recent_header)

        self.recent_frame = QFrame()
        self.recent_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 14px;
                border: 2px solid rgba(233, 30, 140, 0.25);
            }}
        """)
        self.recent_layout = QVBoxLayout(self.recent_frame)
        self.recent_layout.setContentsMargins(16, 12, 16, 12)
        self.recent_layout.setSpacing(6)
        self.layout_main.addWidget(self.recent_frame)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        """Refresh all dashboard data."""
        month = self._current_month
        year, mo = month.split("-")
        start = f"{month}-01"
        if int(mo) == 12:
            end = f"{int(year)+1}-01-01"
        else:
            end = f"{year}-{int(mo)+1:02d}-01"
        from datetime import datetime as dt, timedelta
        end_date = (dt.strptime(end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        # Summary data
        summary = self.db.get_expense_summary(start, end_date)
        total = summary["total"]
        categories = summary["categories"]

        # Budget
        budgets = self.db.get_budgets(month)
        total_budget = sum(b["monthly_limit"] for b in budgets) if budgets else 0
        total_budget_spent = sum(b["spent"] for b in budgets) if budgets else 0
        budget_left = total_budget - total_budget_spent

        # Loans
        loan_count = self.db.get_active_loan_count()
        loan_balance = self.db.get_total_loan_balance()

        # Top category
        top_cat = categories[0]["name"] if categories else "-"
        top_pct = f"{categories[0]['total']/total*100:.0f}%" if categories and total > 0 else ""

        # Income data
        monthly_income = self.db.get_total_income(start, end_date)
        savings = monthly_income - total
        spending_ratio = f"{total/monthly_income*100:.0f}%" if monthly_income > 0 else "N/A"

        # Update cards
        self.total_card.update_values(format_currency(total))
        if total_budget > 0:
            self.budget_card.update_values(format_currency(budget_left), f"of {format_currency(total_budget)}")
        else:
            self.budget_card.update_values("No budget set", "Set via chat")
        self.loans_card.update_values(str(loan_count), format_currency(loan_balance) if loan_count else "No loans")
        self.top_cat_card.update_values(top_cat, top_pct)

        # Income cards
        self.income_card.update_values(format_currency(monthly_income), "This month")
        if monthly_income > 0:
            savings_text = format_currency(savings)
            if savings < 0:
                self.savings_card.update_values(savings_text, f"Over budget! ({spending_ratio} spent)")
            else:
                self.savings_card.update_values(savings_text, f"Saved ({spending_ratio} spent)")
        else:
            self.savings_card.update_values("No income", "Add via chat")

        # Pie chart
        if categories:
            self.pie_chart.plot(
                [c["name"] for c in categories],
                [c["total"] for c in categories],
                [c["color"] for c in categories],
            )
        else:
            self.pie_chart.plot([], [], [])

        # Bar chart - daily spending for current month
        daily = self.db.get_daily_totals(start, end_date)
        if daily:
            self.bar_chart.plot(
                [d["date"] for d in daily],
                [d["total"] for d in daily],
            )
        else:
            self.bar_chart.plot([], [])

        # Budget progress bars
        self._refresh_budgets(budgets)

        # Recent expenses
        self._refresh_recent(start, end_date)

        self.month_label.setText(month_display(month))

    def _refresh_budgets(self, budgets):
        """Update budget progress bars."""
        while self.budget_layout.count():
            item = self.budget_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not budgets:
            lbl = QLabel("No budgets set. Tell the AI to set a budget for a category!")
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
            self.budget_layout.addWidget(lbl)
            return

        for b in budgets:
            row = QHBoxLayout()

            name = QLabel(b["category_name"])
            name.setFixedWidth(120)
            name.setStyleSheet(f"color: {COLORS['text']}; background: transparent; font-size: 13px;")
            row.addWidget(name)

            progress = QProgressBar()
            pct = int(b["spent"] / b["monthly_limit"] * 100) if b["monthly_limit"] > 0 else 0
            progress.setValue(min(pct, 100))
            progress.setFixedHeight(12)

            if pct >= 100:
                chunk_color = COLORS["red"]
            elif pct >= 80:
                chunk_color = COLORS["yellow"]
            else:
                chunk_color = COLORS["green"]
            progress.setStyleSheet(f"""
                QProgressBar {{ background: {COLORS['background']}; border-radius: 4px; border: none; }}
                QProgressBar::chunk {{ background: {chunk_color}; border-radius: 4px; }}
            """)
            row.addWidget(progress, 1)

            amount = QLabel(f"{format_currency(b['spent'])} / {format_currency(b['monthly_limit'])}")
            amount.setFixedWidth(160)
            amount.setAlignment(Qt.AlignmentFlag.AlignRight)
            amount.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; font-size: 12px;")
            row.addWidget(amount)

            wrapper = QWidget()
            wrapper.setLayout(row)
            wrapper.setStyleSheet("background: transparent;")
            self.budget_layout.addWidget(wrapper)

    def _refresh_recent(self, start: str, end: str):
        """Show recent expenses."""
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        expenses = self.db.get_expenses(start_date=start, end_date=end, limit=8)
        if not expenses:
            lbl = QLabel("No expenses this month yet.")
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
            self.recent_layout.addWidget(lbl)
            return

        for e in expenses:
            row = QHBoxLayout()

            cat_dot = QLabel("\u25cf")
            cat_dot.setFixedWidth(16)
            cat_dot.setStyleSheet(f"color: {e.get('category_color', COLORS['accent'])}; background: transparent; font-size: 14px;")
            row.addWidget(cat_dot)

            desc = QLabel(e.get("description", "")[:30])
            desc.setStyleSheet(f"color: {COLORS['text']}; background: transparent; font-size: 13px;")
            row.addWidget(desc, 1)

            merchant = QLabel(e.get("merchant", "") or "")
            merchant.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; font-size: 12px;")
            row.addWidget(merchant)

            amount = QLabel(format_currency(e.get("amount", 0)))
            amount.setAlignment(Qt.AlignmentFlag.AlignRight)
            amount.setFixedWidth(100)
            amount.setStyleSheet(f"color: {COLORS['red']}; background: transparent; font-weight: bold; font-size: 13px;")
            row.addWidget(amount)

            date_lbl = QLabel(e.get("date", ""))
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            date_lbl.setFixedWidth(80)
            date_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; font-size: 11px;")
            row.addWidget(date_lbl)

            wrapper = QWidget()
            wrapper.setLayout(row)
            wrapper.setStyleSheet("background: transparent;")
            self.recent_layout.addWidget(wrapper)

    def _prev_month(self):
        year, mo = self._current_month.split("-")
        mo = int(mo) - 1
        if mo < 1:
            mo = 12
            year = str(int(year) - 1)
        self._current_month = f"{year}-{mo:02d}"
        self.refresh()

    def _next_month(self):
        year, mo = self._current_month.split("-")
        mo = int(mo) + 1
        if mo > 12:
            mo = 1
            year = str(int(year) + 1)
        self._current_month = f"{year}-{mo:02d}"
        self.refresh()
