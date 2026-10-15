"""System tray icon with notifications and reminders."""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import QTimer, QTime, Qt, QRect

from core.database import DatabaseManager
from utils.constants import COLORS, APP_NAME
from utils.helpers import format_currency, today_str


def _create_tray_pixmap() -> QPixmap:
    """Create a cat tray icon on teal circle."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(COLORS["accent"]))
    painter.setPen(QColor("transparent"))
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor(COLORS["background"]))
    painter.setFont(QFont("Segoe UI Emoji", 16))
    painter.drawText(QRect(0, -1, 32, 32), Qt.AlignmentFlag.AlignCenter, "\U0001f431")
    painter.end()
    return pixmap


class SystemTrayManager:
    """System tray icon with context menu and scheduled notifications."""

    def __init__(self, main_window, db: DatabaseManager):
        self.main_window = main_window
        self.db = db

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(_create_tray_pixmap()))
        self.tray_icon.setToolTip(APP_NAME)

        self._setup_menu()
        self._setup_timers()

        self.tray_icon.activated.connect(self._on_activated)

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{ background: {COLORS['surface']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {COLORS['surface_hover']}; }}
        """)

        open_action = QAction("Open Diday", menu)
        open_action.triggered.connect(self._show_window)
        menu.addAction(open_action)

        summary_action = QAction("Today's Summary", menu)
        summary_action.triggered.connect(self._show_daily_summary)
        menu.addAction(summary_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self._exit_app)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)

    def _setup_timers(self):
        # Hourly reminder
        reminder_enabled = self.db.get_setting("reminder_enabled")
        interval_min = int(self.db.get_setting("reminder_interval") or 60)

        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._show_reminder)
        if reminder_enabled == "1":
            self.reminder_timer.start(interval_min * 60 * 1000)

        # Daily summary timer
        self.daily_timer = QTimer()
        self.daily_timer.timeout.connect(self._check_daily_summary)
        self.daily_timer.start(60 * 1000)  # Check every minute

    def show(self):
        self.tray_icon.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _show_reminder(self):
        self.tray_icon.showMessage(
            "Diday Reminder",
            "What did you spend in the last hour? Click to log.",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def _show_daily_summary(self):
        today = today_str()
        total = self.db.get_total_spent(today, today)
        expenses = self.db.get_expenses(start_date=today, end_date=today, limit=100)
        count = len(expenses)

        if total > 0:
            msg = f"Today you spent {format_currency(total)} across {count} transaction{'s' if count != 1 else ''}."
        else:
            msg = "No expenses logged today. Great saving!"

        self.tray_icon.showMessage(
            "Diday - Daily Summary",
            msg,
            QSystemTrayIcon.MessageIcon.Information,
            8000,
        )

    def _check_daily_summary(self):
        summary_time = self.db.get_setting("daily_summary_time") or "20:00"
        now = QTime.currentTime()
        target = QTime.fromString(summary_time, "HH:mm")
        # Trigger if within 1 minute of target time
        if abs(now.secsTo(target)) < 30:
            self._show_daily_summary()

    def _exit_app(self):
        self.tray_icon.hide()
        self.main_window.force_close()
