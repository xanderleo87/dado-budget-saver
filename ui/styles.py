"""Color constants, style helpers, and animation utilities - Coraline neon theme."""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PySide6.QtGui import QColor

from utils.constants import COLORS


def glassmorphism_style(accent_color=None):
    """Semi-transparent card with neon border glow effect (Coraline style)."""
    accent = accent_color or COLORS["accent"]
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
        border-radius: 16px;
        border: none;
    """


def create_fade_in(widget: QWidget, duration: int = 250) -> QPropertyAnimation:
    """Create a fade-in animation on a widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


def create_slide_in(widget: QWidget, duration: int = 300,
                    start_offset: int = 30) -> QPropertyAnimation:
    """Create a slide-in-from-bottom animation."""
    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


def apply_glow_shadow(widget: QWidget, color: str = None, radius: int = 25,
                      offset: int = 0) -> QGraphicsDropShadowEffect:
    """Apply a neon glowing drop shadow effect."""
    glow_color = color or COLORS["glow_teal"]
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(radius)
    effect.setColor(QColor(glow_color))
    effect.setOffset(offset, offset)
    widget.setGraphicsEffect(effect)
    return effect


def gradient_button_style():
    """Teal-to-pink gradient button style (Coraline neon)."""
    return """
        QPushButton {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16B5B3, stop:1 #E91E8C);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 14px;
            letter-spacing: 1px;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7EFFF5, stop:1 #FF6BB5);
            border: none;
        }
    """


def card_style(bg=None):
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(13, 2, 33, 0.7), stop:1 rgba(26, 30, 53, 0.85));
        border-radius: 14px;
        padding: 16px;
        border: none;
    """


def user_bubble_style():
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {COLORS['user_bubble']}, stop:1 #0D7A78);
        color: white;
        border-radius: 18px;
        border-bottom-right-radius: 4px;
        padding: 10px 14px;
        font-size: 14px;
        border: none;
    """


def assistant_bubble_style():
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(26, 30, 53, 0.95), stop:1 rgba(45, 27, 78, 0.7));
        color: {COLORS['text']};
        border-radius: 18px;
        border-bottom-left-radius: 4px;
        padding: 10px 14px;
        font-size: 14px;
        border: none;
    """


def accent_button_style():
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent']}, stop:1 #0D7A78);
            color: {COLORS['background']};
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 14px;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_hover']}, stop:1 {COLORS['accent']});
            border: none;
        }}
    """


def chip_style(color=None):
    color = color or COLORS["accent"]
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {color}22, stop:1 {color}15);
        color: {color};
        border: none;
        border-radius: 16px;
        padding: 5px 14px;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 1px;
    """
