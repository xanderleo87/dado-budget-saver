"""Loans tracking widget with payment history."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QProgressBar, QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.database import DatabaseManager
from utils.constants import COLORS
from utils.helpers import format_currency


class LoansWidget(QWidget):
    """Loan management view with progress bars and payment history."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(12)

        # Header - Coraline neon style
        header = QLabel("\u2726 Loan Tracker")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"background: transparent; color: {COLORS['magic_glow']}; letter-spacing: 2px;")
        self.main_layout.addWidget(header)

        subtitle = QLabel("Track your loans via chat: \"I loaned 1000 in Billease\"")
        subtitle.setStyleSheet(f"color: {COLORS['pink_hover']}; font-size: 13px; background: transparent; letter-spacing: 1px;")
        self.main_layout.addWidget(subtitle)

        # Summary - Coraline neon box
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 14px;
                border: 2px solid rgba(255, 210, 63, 0.4);
            }}
        """)
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(20, 14, 20, 14)

        self.total_label = QLabel("Total Outstanding: \u20b10")
        self.total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.total_label.setStyleSheet(f"color: {COLORS['yellow']}; background: transparent;")
        summary_layout.addWidget(self.total_label)

        summary_layout.addStretch()

        self.count_label = QLabel("0 active loans")
        self.count_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        summary_layout.addWidget(self.count_label)

        self.main_layout.addWidget(self.summary_frame)

        # Active loans container
        self.active_label = QLabel("\u2726 Active Loans")
        self.active_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.active_label.setStyleSheet(f"background: transparent; color: {COLORS['yellow']}; letter-spacing: 1px;")
        self.main_layout.addWidget(self.active_label)

        self.loans_container = QVBoxLayout()
        self.loans_container.setSpacing(10)
        self.main_layout.addLayout(self.loans_container)

        # Paid off section
        self.paid_label = QLabel("\u2726 Paid Off")
        self.paid_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.paid_label.setStyleSheet(f"background: transparent; color: {COLORS['green']}; letter-spacing: 1px;")
        self.main_layout.addWidget(self.paid_label)

        self.paid_container = QVBoxLayout()
        self.paid_container.setSpacing(8)
        self.main_layout.addLayout(self.paid_container)

        self.main_layout.addStretch()

        scroll.setWidget(self.container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        """Reload all loan data."""
        self._clear_layout(self.loans_container)
        self._clear_layout(self.paid_container)

        active = self.db.get_loans(status="active")
        paid = self.db.get_loans(status="paid")

        total_remaining = sum(l["remaining"] for l in active)
        self.total_label.setText(f"Total Outstanding: {format_currency(total_remaining)}")
        self.count_label.setText(f"{len(active)} active loan{'s' if len(active) != 1 else ''}")

        if not active:
            lbl = QLabel("No active loans. Nice!")
            lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 14px; background: transparent; padding: 12px;")
            self.loans_container.addWidget(lbl)
        else:
            for loan in active:
                card = self._create_loan_card(loan, is_active=True)
                self.loans_container.addWidget(card)

        if not paid:
            self.paid_label.hide()
        else:
            self.paid_label.show()
            for loan in paid:
                card = self._create_loan_card(loan, is_active=False)
                self.paid_container.addWidget(card)

    def _create_loan_card(self, loan: dict, is_active: bool) -> QFrame:
        border_color = COLORS['yellow'] if is_active else COLORS['green']
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 14px;
                border: 2px solid {border_color}55;
                border-left: 4px solid {border_color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header row
        header = QHBoxLayout()
        platform = QLabel(loan["platform"])
        platform.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        platform.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        header.addWidget(platform)

        header.addStretch()

        status = QLabel(loan["status"].upper())
        status_color = COLORS["yellow"] if is_active else COLORS["green"]
        status.setStyleSheet(f"""
            color: {status_color}; background: {status_color}22;
            padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: bold;
        """)
        header.addWidget(status)

        layout.addLayout(header)

        # Amounts row
        amounts = QHBoxLayout()
        for label_text, value in [
            ("Borrowed", format_currency(loan["amount_borrowed"])),
            ("Paid", format_currency(loan["amount_paid"])),
            ("Remaining", format_currency(loan["remaining"])),
        ]:
            col = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; background: transparent;")
            col.addWidget(lbl)
            val = QLabel(value)
            val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
            col.addWidget(val)
            amounts.addLayout(col)

        if loan.get("due_date"):
            col = QVBoxLayout()
            lbl = QLabel("Due Date")
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; background: transparent;")
            col.addWidget(lbl)
            val = QLabel(loan["due_date"])
            val.setFont(QFont("Segoe UI", 13))
            val.setStyleSheet(f"color: {COLORS['peach']}; background: transparent;")
            col.addWidget(val)
            amounts.addLayout(col)

        layout.addLayout(amounts)

        # Progress bar
        if loan["amount_borrowed"] > 0:
            pct = int(loan["amount_paid"] / loan["amount_borrowed"] * 100)
        else:
            pct = 0
        progress = QProgressBar()
        progress.setValue(min(pct, 100))
        progress.setFixedHeight(10)
        progress.setStyleSheet(f"""
            QProgressBar {{ background: {COLORS['background']}; border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background: {COLORS['green']}; border-radius: 4px; }}
        """)
        layout.addWidget(progress)

        pct_label = QLabel(f"{pct}% paid")
        pct_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; background: transparent;")
        layout.addWidget(pct_label)

        # Payment history
        payments = self.db.get_loan_payments(loan["id"])
        if payments:
            pay_header = QLabel("Payment History")
            pay_header.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; font-weight: bold; background: transparent; margin-top: 4px;")
            layout.addWidget(pay_header)
            for p in payments[:5]:
                row = QHBoxLayout()
                dot = QLabel("\u2022")
                dot.setFixedWidth(12)
                dot.setStyleSheet(f"color: {COLORS['green']}; background: transparent;")
                row.addWidget(dot)
                date_lbl = QLabel(p["date"])
                date_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; background: transparent;")
                row.addWidget(date_lbl)
                amt = QLabel(format_currency(p["amount"]))
                amt.setAlignment(Qt.AlignmentFlag.AlignRight)
                amt.setStyleSheet(f"color: {COLORS['green']}; font-size: 12px; background: transparent;")
                row.addWidget(amt)
                wrapper = QWidget()
                wrapper.setLayout(row)
                wrapper.setStyleSheet("background: transparent;")
                layout.addWidget(wrapper)

        return card

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
