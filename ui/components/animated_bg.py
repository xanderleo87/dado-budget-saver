"""Aurora animated background with floating neon orbs, sparkle particles, and button rain."""

import math
import time
import random

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QRectF
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QPen, QLinearGradient

from utils.constants import AURORA_FPS


class AuroraBackground(QWidget):
    """Animated background with neon orbs, sparkle particles, and falling button rain."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._start_time = time.time()

        # Orbs: (color, speed_x, speed_y, phase, radius_factor)
        self._orbs = [
            (QColor(22, 181, 179, 30), 0.25, 0.18, 0.0, 0.38),    # Teal
            (QColor(233, 30, 140, 25), 0.20, 0.28, 1.5, 0.32),     # Pink
            (QColor(45, 27, 78, 40), 0.30, 0.12, 3.0, 0.42),       # Purple
            (QColor(126, 255, 245, 15), 0.35, 0.22, 4.5, 0.25),    # Magic glow
            (QColor(233, 30, 140, 20), 0.15, 0.25, 2.0, 0.28),     # Pink 2
            (QColor(22, 181, 179, 22), 0.28, 0.15, 5.5, 0.30),     # Teal 2
        ]

        # Sparkle particles
        self._sparkles = []
        for _ in range(30):
            self._sparkles.append({
                'x': random.random(),
                'y': random.random(),
                'size': random.uniform(1.5, 4.5),
                'speed': random.uniform(0.3, 1.2),
                'phase': random.uniform(0, 6.28),
                'color': random.choice([
                    QColor(126, 255, 245, 180),  # Magic glow
                    QColor(255, 210, 63, 160),    # Yellow
                    QColor(233, 30, 140, 140),    # Pink
                    QColor(255, 255, 255, 120),   # White
                    QColor(167, 139, 250, 130),   # Purple
                ]),
            })

        # Button rain particles (falling circles like the Coraline HTML)
        self._rain_drops = []
        rain_colors = [
            QColor(255, 210, 63, 50),   # Yellow
            QColor(233, 30, 140, 40),    # Pink
            QColor(22, 181, 179, 45),    # Teal
            QColor(126, 255, 245, 35),   # Magic glow
            QColor(184, 197, 214, 30),   # Silver
        ]
        for _ in range(35):
            self._rain_drops.append({
                'x': random.random(),
                'y': random.random(),
                'size': random.uniform(6, 18),
                'speed': random.uniform(0.015, 0.045),
                'color': random.choice(rain_colors),
                'wobble_speed': random.uniform(0.3, 1.0),
                'wobble_phase': random.uniform(0, 6.28),
                'wobble_amount': random.uniform(5, 20),
            })

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // AURORA_FPS)

    def _tick(self):
        # Update rain drop positions
        for drop in self._rain_drops:
            drop['y'] += drop['speed']
            if drop['y'] > 1.15:
                drop['y'] = -0.1
                drop['x'] = random.random()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        t = time.time() - self._start_time

        # Draw background gradient (deep purple diagonal like Coraline)
        bg_gradient = QLinearGradient(0, 0, w, h)
        bg_gradient.setColorAt(0.0, QColor(10, 14, 26))
        bg_gradient.setColorAt(0.5, QColor(25, 18, 45))
        bg_gradient.setColorAt(1.0, QColor(10, 14, 26))
        painter.fillRect(0, 0, w, h, bg_gradient)

        # Draw button rain (behind orbs)
        for drop in self._rain_drops:
            dx = drop['x'] * w + math.sin(t * drop['wobble_speed'] + drop['wobble_phase']) * drop['wobble_amount']
            dy = drop['y'] * h
            size = drop['size']

            # Glowing circle
            glow_gradient = QRadialGradient(dx, dy, size * 2)
            glow_color = QColor(drop['color'])
            glow_color.setAlpha(int(glow_color.alpha() * 0.4))
            glow_gradient.setColorAt(0.0, glow_color)
            glow_transparent = QColor(glow_color)
            glow_transparent.setAlpha(0)
            glow_gradient.setColorAt(1.0, glow_transparent)
            painter.setBrush(glow_gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(dx - size * 2, dy - size * 2, size * 4, size * 4))

            # Solid button circle
            painter.setBrush(drop['color'])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(dx - size / 2, dy - size / 2, size, size))

            # Button holes (like Coraline buttons)
            if size > 10:
                hole_color = QColor(0, 0, 0, 80)
                painter.setBrush(hole_color)
                hole_size = size * 0.18
                painter.drawEllipse(QRectF(dx - hole_size * 1.5, dy - hole_size / 2, hole_size, hole_size))
                painter.drawEllipse(QRectF(dx + hole_size * 0.5, dy - hole_size / 2, hole_size, hole_size))

        # Draw orbs
        for color, sx, sy, phase, rf in self._orbs:
            cx = w * (0.5 + 0.4 * math.sin(t * sx + phase))
            cy = h * (0.5 + 0.4 * math.cos(t * sy + phase * 0.7))
            radius = min(w, h) * rf

            gradient = QRadialGradient(cx, cy, radius)
            gradient.setColorAt(0.0, color)
            transparent = QColor(color)
            transparent.setAlpha(0)
            gradient.setColorAt(1.0, transparent)

            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Draw sparkle particles
        for s in self._sparkles:
            sx = s['x'] * w
            sy_base = s['y'] * h
            # Gentle floating motion
            sy = sy_base + math.sin(t * s['speed'] + s['phase']) * 15
            # Twinkle effect
            alpha_mod = (math.sin(t * s['speed'] * 2 + s['phase']) + 1) / 2
            c = QColor(s['color'])
            c.setAlpha(int(c.alpha() * alpha_mod))

            size = s['size'] * (0.7 + 0.3 * alpha_mod)

            # Draw cross sparkle for larger particles
            if size > 2.5:
                painter.setPen(QPen(c, 1))
                painter.drawLine(
                    int(sx - size * 1.5), int(sy),
                    int(sx + size * 1.5), int(sy)
                )
                painter.drawLine(
                    int(sx), int(sy - size * 1.5),
                    int(sx), int(sy + size * 1.5)
                )

            # Draw dot
            painter.setBrush(c)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(sx - size, sy - size, size * 2, size * 2))

        painter.end()

    def stop(self):
        self._timer.stop()

    def start(self):
        if not self._timer.isActive():
            self._timer.start(1000 // AURORA_FPS)
