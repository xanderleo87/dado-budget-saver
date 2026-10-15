"""Main application window with tabbed interface and aurora background."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar, QLabel,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from core.database import DatabaseManager
from core.ai_engine import AIEngine
from core.security import SecurityManager
from ui.chat_widget import ChatWidget
from ui.dashboard_widget import DashboardWidget
from ui.loans_widget import LoansWidget
from ui.history_widget import HistoryWidget
from ui.settings_widget import SettingsWidget
from ui.components.animated_bg import AuroraBackground
from utils.constants import APP_NAME, APP_DISPLAY_NAME, COLORS, ANIMATION_DURATION


class MainWindow(QMainWindow):
    """Main application window with Chat, Dashboard, Loans, History, and Settings tabs."""

    def __init__(self, db: DatabaseManager, ai: AIEngine,
                 security: SecurityManager, encrypted_db_path: str,
                 parent=None):
        super().__init__(parent)
        self.db = db
        self.ai = ai
        self.security = security
        self.encrypted_db_path = encrypted_db_path
        self._fade_anim = None

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_ui(self):
        # Central widget with aurora background behind tabs
        central = QWidget()
        self.setCentralWidget(central)

        # Aurora background as direct child, will be resized in resizeEvent
        self.aurora = AuroraBackground(central)
        self.aurora.lower()

        # Tab widget on top of aurora
        self.tabs = QTabWidget(central)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)

        # Make tab panes transparent so aurora shows through
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background: transparent; border: none; }
            QStackedWidget { background: transparent; }
        """)

        # Use a layout for the tabs so they fill the central widget
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

        # Chat tab
        self.chat_widget = ChatWidget(self.db, self.ai)
        self.tabs.addTab(self.chat_widget, "\U0001f4ac  Chat")

        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.db)
        self.tabs.addTab(self.dashboard_widget, "\U0001f4ca  Dashboard")

        # Loans tab
        self.loans_widget = LoansWidget(self.db)
        self.tabs.addTab(self.loans_widget, "\U0001f4b3  Loans")

        # History tab
        self.history_widget = HistoryWidget(self.db)
        self.tabs.addTab(self.history_widget, "\U0001f4cb  History")

        # Settings tab
        self.settings_widget = SettingsWidget(self.db, self.security, self.encrypted_db_path)
        self.tabs.addTab(self.settings_widget, "\u2699\ufe0f  Settings")

        # Connect signals
        self.chat_widget.data_changed.connect(self._on_data_changed)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("\u2726 Diday — Keyword Mode (type 'help' for guide)")
        self.status_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px; letter-spacing: 1px;")
        self.status_bar.addWidget(self.status_label)

    def _on_data_changed(self):
        """Refresh dashboard and loans when data changes via chat, and save."""
        self.save_database()
        current = self.tabs.currentIndex()
        if current == 1:
            self.dashboard_widget.refresh()
        elif current == 2:
            self.loans_widget.refresh()
        elif current == 3:
            self.history_widget.refresh()

    def _on_tab_changed(self, index):
        """Refresh tab content when switching, with fade-in animation."""
        widget = self.tabs.widget(index)

        # Fade-in animation on tab switch
        # Remove any previous effect to prevent rendering corruption
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        self._fade_anim = QPropertyAnimation(effect, b"opacity")
        self._fade_anim.setDuration(ANIMATION_DURATION)
        self._fade_anim.setStartValue(0.3)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Remove the effect once animation finishes to prevent rendering bugs
        self._fade_anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._fade_anim.start()

        if index == 1:
            self.dashboard_widget.refresh()
        elif index == 2:
            self.loans_widget.refresh()
        elif index == 3:
            self.history_widget.refresh()

    def resizeEvent(self, event):
        """Keep aurora background filling the entire central widget."""
        super().resizeEvent(event)
        if hasattr(self, 'aurora') and self.centralWidget():
            self.aurora.setGeometry(self.centralWidget().rect())

    def closeEvent(self, event):
        """Minimize to tray instead of closing, but save data first."""
        self.save_database()
        self.hide()
        event.ignore()

    def save_database(self):
        """Flush WAL and encrypt the working database back to disk."""
        try:
            self.db.checkpoint()
            self.security.encrypt_database(
                self.db.db_path, self.encrypted_db_path
            )
        except Exception:
            pass

    def force_close(self):
        """Actually close the window (called from tray Exit)."""
        self.aurora.stop()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
