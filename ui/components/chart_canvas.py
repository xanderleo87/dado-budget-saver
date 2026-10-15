"""Matplotlib canvas wrapper with Coraline neon theme and gradient bars."""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from utils.constants import COLORS

_SURFACE = "#1A1E35"
_BG = "#0A0E1A"
_TEXT_DIM = "#B8C5D6"
_TEXT = "#F0F4F8"
_BORDER = "#2D1B4E"


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=4, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=100)
        self.fig.patch.set_facecolor(_SURFACE)
        self.axes = self.fig.add_subplot(111)
        self._style_axes()
        super().__init__(self.fig)
        self.setStyleSheet("background: transparent;")

    def _style_axes(self):
        ax = self.axes
        ax.set_facecolor(_SURFACE)
        ax.tick_params(colors=_TEXT_DIM, labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(_BORDER)
        ax.spines["left"].set_color(_BORDER)
        ax.xaxis.label.set_color(_TEXT_DIM)
        ax.yaxis.label.set_color(_TEXT_DIM)
        ax.title.set_color(_TEXT)

    def clear_and_reset(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        self._style_axes()


class PieChartCanvas(ChartCanvas):
    def plot(self, labels, values, colors):
        self.clear_and_reset()
        if not values or all(v == 0 for v in values):
            self.axes.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          color=_TEXT_DIM, fontsize=14, transform=self.axes.transAxes)
            self.draw()
            return
        self.axes.set_position([0.05, 0.05, 0.55, 0.85])
        wedges, texts, autotexts = self.axes.pie(
            values, labels=None, colors=colors, autopct="%1.0f%%",
            startangle=90, pctdistance=0.8,
            wedgeprops={"linewidth": 2, "edgecolor": _SURFACE},
        )
        for t in autotexts:
            t.set_color("white")
            t.set_fontsize(9)
        self.axes.legend(
            wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
            fontsize=9, frameon=False, labelcolor=_TEXT_DIM,
        )
        self.axes.set_title("Spending by Category", fontsize=13, pad=10)
        self.fig.tight_layout()
        self.draw()


class BarChartCanvas(ChartCanvas):
    def plot(self, dates, values):
        self.clear_and_reset()
        if not values:
            self.axes.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          color=_TEXT_DIM, fontsize=14, transform=self.axes.transAxes)
            self.draw()
            return
        short_dates = []
        for d in dates:
            try:
                parts = d.split("-")
                short_dates.append(f"{parts[1]}/{parts[2]}")
            except (IndexError, ValueError):
                short_dates.append(d)
        n = len(values)
        cmap = LinearSegmentedColormap.from_list("neon", ["#16B5B3", "#E91E8C", "#FFD23F"])
        bar_colors = [cmap(i / max(n - 1, 1)) for i in range(n)]
        bars = self.axes.bar(
            range(len(values)), values, color=bar_colors, alpha=0.9, width=0.6,
            linewidth=0.5, edgecolor=[cmap(i / max(n - 1, 1)) for i in range(n)],
        )
        self.axes.set_xticks(range(len(short_dates)))
        self.axes.set_xticklabels(short_dates, rotation=45, ha="right", fontsize=8)
        self.axes.set_title("Daily Spending", fontsize=13, pad=10)
        self.axes.set_ylabel("\u20b1", fontsize=10)
        for bar, val in zip(bars, values):
            if val > 0:
                self.axes.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    f"{val:,.0f}", ha="center", va="bottom", color=_TEXT_DIM, fontsize=7,
                )
        self.fig.tight_layout()
        self.draw()
