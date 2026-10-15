"""Dashboard summary card with neon glow border and hover effects - Coraline style."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from utils.constants import COLORS


class SummaryCard(QFrame):
    """A stat card with prominent neon border glow and hover animation (Coraline style)."""

    def __init__(self, title: str, value: str, subtitle: str = "",
                 accent_color: str = None, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color or COLORS["accent"]
        self._glow_effect = None
        self._setup_ui(title, value, subtitle)

    def _setup_ui(self, title: str, value: str, subtitle: str):
        self.setStyleSheet(self._base_style())
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {COLORS['text_dim']}; font-size: 11px;
            font-weight: 600; background: transparent;
            letter-spacing: 2px; text-transform: uppercase;
        """)
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        layout.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"""
            color: {COLORS['text_dim']}; font-size: 11px; background: transparent;
        """)
        layout.addWidget(self.subtitle_label)

        # Permanent subtle glow
        self._apply_base_glow()

    def _base_style(self):
        return f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
                border-radius: 16px;
                border: 2px solid {self.accent_color}66;
                border-left: 4px solid {self.accent_color};
            }}
        """

    def _hover_style(self):
        return f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 2, 33, 0.85), stop:1 rgba(45, 27, 78, 0.7));
                border-radius: 16px;
                border: 2px solid {self.accent_color}AA;
                border-left: 4px solid {self.accent_color};
            }}
        """

    def _apply_base_glow(self):
        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setBlurRadius(20)
        self._glow_effect.setColor(QColor(self.accent_color))
        self._glow_effect.setOffset(0, 2)
        self.setGraphicsEffect(self._glow_effect)

    def update_values(self, value: str, subtitle: str = ""):
        self.value_label.setText(value)
        if subtitle:
            self.subtitle_label.setText(subtitle)

    def enterEvent(self, event):
        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setBlurRadius(40)
        self._glow_effect.setColor(QColor(self.accent_color))
        self._glow_effect.setOffset(0, 4)
        self.setGraphicsEffect(self._glow_effect)
        self.setStyleSheet(self._hover_style())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_base_glow()
        self.setStyleSheet(self._base_style())
        super().leaveEvent(event)
