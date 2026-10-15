"""Chat message bubble with avatar bubble heads, slide-in + fade animations, neon glow."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer,
    QParallelAnimationGroup, QPoint,
)
from PySide6.QtGui import QFont, QColor

from utils.constants import COLORS


class MessageBubble(QWidget):
    """A chat message bubble with avatar and smooth slide-in + fade animation."""

    def __init__(self, text: str, role: str = "user", timestamp: str = "", parent=None):
        super().__init__(parent)
        self.role = role
        self._setup_ui(text, timestamp)
        # Defer animation to after widget is placed in layout
        QTimer.singleShot(10, self._animate_in)

    def _setup_ui(self, text: str, timestamp: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 6)
        outer.setSpacing(10)

        # Avatar bubble head
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.role == "user":
            avatar.setText("\U0001f9d1")
            avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['accent']};
                    border-radius: 20px;
                    font-size: 20px;
                    border: none;
                }}
            """)
        else:
            avatar.setText("\U0001f431")
            avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['pink']};
                    border-radius: 20px;
                    font-size: 20px;
                    border: none;
                }}
            """)

        if self.role == "user":
            outer.addStretch()

        if self.role == "assistant":
            outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        # Message bubble
        bubble = QWidget()
        bubble.setMaximumWidth(480)

        if self.role == "user":
            bubble.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {COLORS['accent']}, stop:1 #0D7A78);
                    border-radius: 18px;
                    border-bottom-right-radius: 4px;
                    border: none;
                }}
            """)
        else:
            bubble.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(26, 30, 53, 0.95), stop:1 rgba(45, 27, 78, 0.7));
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    border: none;
                }}
            """)

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(16, 12, 16, 10)
        inner.setSpacing(4)

        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_label.setStyleSheet(f"""
            QLabel {{
                color: {'white' if self.role == 'user' else COLORS['text']};
                font-size: 14px;
                background: transparent;
                padding: 0;
                line-height: 1.4;
            }}
        """)
        inner.addWidget(msg_label)

        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            time_label.setStyleSheet(f"""
                QLabel {{
                    color: {'rgba(255,255,255,0.5)' if self.role == 'user' else COLORS['text_dim']};
                    font-size: 10px;
                    background: transparent;
                    padding: 0;
                }}
            """)
            inner.addWidget(time_label)

        outer.addWidget(bubble)

        if self.role == "user":
            outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        if self.role == "assistant":
            outer.addStretch()

    def _animate_in(self):
        """Smooth slide-up + fade-in animation."""
        # Fade effect
        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)

        fade = QPropertyAnimation(opacity_effect, b"opacity")
        fade.setDuration(400)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide effect - move from below
        slide = QPropertyAnimation(self, b"pos")
        slide.setDuration(400)
        current_pos = self.pos()
        slide.setStartValue(QPoint(current_pos.x(), current_pos.y() + 20))
        slide.setEndValue(current_pos)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Run both together
        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(fade)
        self._anim_group.addAnimation(slide)
        self._anim_group.start()


class TypingIndicator(QWidget):
    """Animated typing indicator with cat avatar and neon bouncing dots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dot_index = 0
        self._setup_ui()
        self._start_animation()

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 6)
        outer.setSpacing(10)

        # Cat avatar
        avatar = QLabel("\U0001f431")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['pink']};
                border-radius: 20px;
                font-size: 20px;
                border: none;
            }}
        """)
        outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        bubble = QWidget()
        bubble.setMaximumWidth(90)
        bubble.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(26, 30, 53, 0.95), stop:1 rgba(45, 27, 78, 0.7));
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                border: none;
            }}
        """)

        inner = QHBoxLayout(bubble)
        inner.setContentsMargins(18, 14, 18, 14)
        inner.setSpacing(8)

        self._dots = []
        for _ in range(3):
            dot = QLabel("\u2022")
            dot.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_dim']};
                    font-size: 24px;
                    background: transparent;
                }}
            """)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inner.addWidget(dot)
            self._dots.append(dot)

        outer.addWidget(bubble)
        outer.addStretch()

    def _start_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._cycle_dot)
        self._timer.start(350)

    def _cycle_dot(self):
        colors = [COLORS["magic_glow"], COLORS["pink_hover"], COLORS["yellow"]]
        for i, dot in enumerate(self._dots):
            if i == self._dot_index:
                dot.setStyleSheet(f"""
                    QLabel {{
                        color: {colors[i]};
                        font-size: 28px;
                        background: transparent;
                    }}
                """)
            else:
                dot.setStyleSheet(f"""
                    QLabel {{
                        color: {COLORS['text_dim']};
                        font-size: 24px;
                        background: transparent;
                    }}
                """)
        self._dot_index = (self._dot_index + 1) % 3
