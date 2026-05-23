"""Canvas 图表组件 — 折线图 / 雷达图 / 柱状图 / 迷你图。

零外部依赖，使用 Tkinter Canvas 自绘。
"""

import math
import tkinter as tk
from typing import Callable

# ---- 默认配色 ----

SERIES_COLORS = ["#4a90d9", "#e74c3c", "#27ae60", "#f39c12", "#8e44ad", "#1abc9c"]
GRID_COLOR = "#e0e0e0"
AXIS_COLOR = "#999999"
TEXT_COLOR = "#666666"
BG_COLOR = "#ffffff"

DARK_SERIES_COLORS = ["#5dade2", "#f1948a", "#58d68d", "#f7dc6f", "#bb8fce", "#76d7c4"]
DARK_GRID_COLOR = "#3e3e3e"
DARK_AXIS_COLOR = "#888888"
DARK_TEXT_COLOR = "#aaaaaa"
DARK_BG_COLOR = "#1e1e1e"

MARGIN_LEFT = 50
MARGIN_RIGHT = 20
MARGIN_TOP = 30
MARGIN_BOTTOM = 40


def _lighten(hex_color: str, factor: float = 0.3) -> str:
    """将颜色变浅（用于填充区域）。"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


# ============================================================
#  ChartBase — 图表基类
# ============================================================

class ChartBase(tk.Canvas):
    """图表基类，提供坐标轴、网格线、标题绘制。"""

    def __init__(self, parent: tk.Widget, width: int = 500, height: int = 300,
                 title: str = "", dark: bool = False):
        super().__init__(parent, width=width, height=height,
                         bg=DARK_BG_COLOR if dark else BG_COLOR,
                         highlightthickness=0)
        self.chart_width = width
        self.chart_height = height
        self.chart_title = title
        self.dark = dark

        # 绘图区域（去除边距）
        self.plot_x = MARGIN_LEFT
        self.plot_y = MARGIN_TOP
        self.plot_w = width - MARGIN_LEFT - MARGIN_RIGHT
        self.plot_h = height - MARGIN_TOP - MARGIN_BOTTOM

        # 绑定 resize
        self.bind("<Configure>", self._on_resize)

    @property
    def _series_colors(self):
        return DARK_SERIES_COLORS if self.dark else SERIES_COLORS

    @property
    def _grid_color(self):
        return DARK_GRID_COLOR if self.dark else GRID_COLOR

    @property
    def _axis_color(self):
        return DARK_AXIS_COLOR if self.dark else AXIS_COLOR

    @property
    def _text_color(self):
        return DARK_TEXT_COLOR if self.dark else TEXT_COLOR

    def _draw_title(self) -> None:
        if self.chart_title:
            self.create_text(
                self.chart_width // 2, 14,
                text=self.chart_title,
                fill=self._text_color,
                font=("Microsoft YaHei", 11, "bold"),
                tags="title"
            )

    def _draw_axes(self, x_label: str = "", y_label: str = "") -> None:
        # X 轴
        self.create_line(
            self.plot_x, self.plot_y + self.plot_h,
            self.plot_x + self.plot_w, self.plot_y + self.plot_h,
            fill=self._axis_color, width=1, tags="axes"
        )
        # Y 轴
        self.create_line(
            self.plot_x, self.plot_y,
            self.plot_x, self.plot_y + self.plot_h,
            fill=self._axis_color, width=1, tags="axes"
        )
        # X 轴标签
        if x_label:
            self.create_text(
                self.plot_x + self.plot_w // 2,
                self.chart_height - 8,
                text=x_label, fill=self._text_color,
                font=("Microsoft YaHei", 8), tags="axes"
            )
        # Y 轴标签
        if y_label:
            self.create_text(
                12, self.plot_y + self.plot_h // 2,
                text=y_label, fill=self._text_color,
                font=("Microsoft YaHei", 8), angle=90, tags="axes"
            )

    def _draw_grid(self, y_ticks: int = 5) -> None:
        """绘制水平网格线。"""
        for i in range(y_ticks + 1):
            y = self.plot_y + self.plot_h * i // y_ticks
            self.create_line(
                self.plot_x, y,
                self.plot_x + self.plot_w, y,
                fill=self._grid_color, width=1, dash=(2, 4), tags="grid"
            )

    def _on_resize(self, event) -> None:
        if event.width > 10 and event.height > 10:
            self.chart_width = event.width
            self.chart_height = event.height
            self.plot_x = MARGIN_LEFT
            self.plot_y = MARGIN_TOP
            self.plot_w = event.width - MARGIN_LEFT - MARGIN_RIGHT
            self.plot_h = event.height - MARGIN_TOP - MARGIN_BOTTOM

    def _clear(self, *tags: str) -> None:
        for tag in tags:
            self.delete(tag)


# ============================================================
#  LineChart — 多系列折线图
# ============================================================

class LineChart(ChartBase):
    """多系列折线图，用于状态趋势展示。"""

    def __init__(self, parent: tk.Widget, width: int = 500, height: int = 300,
                 title: str = "", dark: bool = False):
        super().__init__(parent, width, height, title, dark)
        self._labels: list[str] = []
        self._series: dict[str, list[float]] = {}
        self._on_period_change: Callable[[str], None] | None = None

    def set_period_callback(self, callback: Callable[[str], None]) -> None:
        """设置周期切换回调。"""
        self._on_period_change = callback

    def set_data(self, labels: list[str], series: dict[str, list[float]]) -> None:
        """设置图表数据并重绘。"""
        self._labels = labels
        self._series = series
        self._redraw()

    def _redraw(self) -> None:
        self._clear("data", "grid", "axes", "title", "legend")
        self._draw_title()
        self._draw_axes()
        self._draw_grid()

        if not self._labels or not self._series:
            self.create_text(
                self.plot_x + self.plot_w // 2,
                self.plot_y + self.plot_h // 2,
                text="暂无数据", fill=self._text_color,
                font=("Microsoft YaHei", 10), tags="data"
            )
            return

        all_values = [v for vals in self._series.values() for v in vals]
        if not all_values:
            return

        y_min = min(all_values)
        y_max = max(all_values)
        y_range = y_max - y_min or 1
        # 上下留 10% 空间
        y_min -= y_range * 0.1
        y_max += y_range * 0.1
        y_range = y_max - y_min

        # Y 轴刻度
        for i in range(6):
            val = y_min + y_range * i / 5
            y = self.plot_y + self.plot_h - self.plot_h * i / 5
            self.create_text(
                self.plot_x - 6, y,
                text=f"{val:.1f}", fill=self._text_color,
                font=("Microsoft YaHei", 7), anchor=tk.E, tags="data"
            )

        n = len(self._labels)
        if n < 2:
            n = 2

        # 绘制各系列
        for si, (name, values) in enumerate(self._series.items()):
            color = self._series_colors[si % len(self._series_colors)]
            points = []
            for i, v in enumerate(values):
                x = self.plot_x + self.plot_w * i / (n - 1) if n > 1 else self.plot_x + self.plot_w / 2
                ratio = (v - y_min) / y_range
                y = self.plot_y + self.plot_h * (1 - ratio)
                points.append((x, y))

            # 折线
            if len(points) >= 2:
                for j in range(len(points) - 1):
                    self.create_line(
                        points[j][0], points[j][1],
                        points[j + 1][0], points[j + 1][1],
                        fill=color, width=2, smooth=True, tags="data"
                    )

            # 填充区域
            if len(points) >= 2:
                fill_pts = [points[0][0], self.plot_y + self.plot_h]
                for px, py in points:
                    fill_pts.extend([px, py])
                fill_pts.extend([points[-1][0], self.plot_y + self.plot_h])
                flat = [x for x in fill_pts]
                self.create_polygon(
                    flat, fill=_lighten(color, 0.5),
                    outline="", tags="data"
                )

            # 数据点
            for px, py in points:
                self.create_oval(
                    px - 3, py - 3, px + 3, py + 3,
                    fill=color, outline="#ffffff", width=1, tags="data"
                )

            # 重绘折线（覆盖在填充和点上）
            if len(points) >= 2:
                for j in range(len(points) - 1):
                    self.create_line(
                        points[j][0], points[j][1],
                        points[j + 1][0], points[j + 1][1],
                        fill=color, width=2, tags="data"
                    )

        # X 轴标签（最多显示 10 个）
        step = max(1, n // 8)
        for i in range(0, n, step):
            x = self.plot_x + self.plot_w * i / (n - 1) if n > 1 else self.plot_x + self.plot_w / 2
            lbl = self._labels[i]
            if len(lbl) > 6:
                lbl = lbl[-5:]
            self.create_text(
                x, self.plot_y + self.plot_h + 8,
                text=lbl, fill=self._text_color,
                font=("Microsoft YaHei", 7), angle=30, anchor=tk.N, tags="data"
            )

        # 图例
        legend_x = self.plot_x + self.plot_w - 10
        legend_y = self.plot_y + 4
        for si, name in enumerate(reversed(list(self._series.keys()))):
            color = self._series_colors[(len(self._series) - 1 - si) % len(self._series_colors)]
            ly = legend_y + si * 18
            self.create_rectangle(
                legend_x - 60, ly, legend_x - 48, ly + 10,
                fill=color, outline="", tags="legend"
            )
            self.create_text(
                legend_x - 44, ly + 5,
                text=name, fill=self._text_color,
                font=("Microsoft YaHei", 8), anchor=tk.W, tags="legend"
            )


# ============================================================
#  RadarChart — 雷达图
# ============================================================

class RadarChart(ChartBase):
    """技能雷达图，展示多维度能力分布。"""

    def __init__(self, parent: tk.Widget, width: int = 300, height: int = 300,
                 title: str = "", dark: bool = False):
        super().__init__(parent, width, height, title, dark)
        self._categories: list[str] = []
        self._values: list[float] = []
        self._max_val: float = 5.0

    def set_data(self, categories: list[str], values: list[float],
                 max_val: float = 5.0) -> None:
        """设置雷达图数据。"""
        self._categories = categories
        self._values = values
        self._max_val = max_val
        self._redraw()

    def _redraw(self) -> None:
        self._clear("data", "grid", "axes", "title", "legend")
        self._draw_title()

        if not self._categories or not self._values:
            cx = self.chart_width // 2
            cy = self.chart_height // 2
            self.create_text(
                cx, cy, text="暂无数据",
                fill=self._text_color, font=("Microsoft YaHei", 10), tags="data"
            )
            return

        n = len(self._categories)
        cx = self.chart_width // 2
        cy = self.chart_height // 2 + 10
        radius = min(cx, cy) - 50

        color = self._series_colors[0]
        fill_color = _lighten(color, 0.5)

        # 绘制网格（同心多边形）
        for level in range(1, 6):
            r = radius * level / 5
            pts = []
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                pts.extend([x, y])
            if level == 5:
                self.create_polygon(pts, outline=self._grid_color,
                                   fill="", width=1, tags="grid")
            else:
                self.create_polygon(pts, outline=self._grid_color,
                                   fill="", width=1, dash=(2, 2), tags="grid")

        # 绘制轴线 + 标签
        for i, cat in enumerate(self._categories):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            ex = cx + (radius + 16) * math.cos(angle)
            ey = cy + (radius + 16) * math.sin(angle)
            # 轴线
            self.create_line(
                cx, cy,
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle),
                fill=self._grid_color, width=1, tags="axes"
            )
            # 标签
            anchor = tk.CENTER
            if angle < -math.pi * 0.25 and angle > -math.pi * 0.75:
                anchor = tk.S
            elif angle > math.pi * 0.25 and angle < math.pi * 0.75:
                anchor = tk.N
            self.create_text(
                ex, ey, text=cat, fill=self._text_color,
                font=("Microsoft YaHei", 8), anchor=anchor, tags="data"
            )

        # 绘制数据多边形
        data_pts = []
        for i, val in enumerate(self._values):
            r = radius * val / self._max_val
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            data_pts.extend([x, y])

        if len(data_pts) >= 6:
            self.create_polygon(data_pts, fill=fill_color,
                               outline=color, width=2, tags="data")

        # 数据点
        for i, val in enumerate(self._values):
            r = radius * val / self._max_val
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            self.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=color, outline="#ffffff", width=1, tags="data"
            )


# ============================================================
#  BarChart — 柱状图
# ============================================================

class BarChart(ChartBase):
    """类别分布柱状图。"""

    def __init__(self, parent: tk.Widget, width: int = 400, height: int = 250,
                 title: str = "", dark: bool = False):
        super().__init__(parent, width, height, title, dark)
        self._labels: list[str] = []
        self._values: list[int] = []

    def set_data(self, labels: list[str], values: list[int]) -> None:
        """设置柱状图数据。"""
        self._labels = labels
        self._values = values
        self._redraw()

    def _redraw(self) -> None:
        self._clear("data", "grid", "axes", "title", "legend")

        if not self._labels or not self._values:
            cx = self.plot_x + self.plot_w // 2
            cy = self.plot_y + self.plot_h // 2
            self.create_text(
                cx, cy, text="暂无数据",
                fill=self._text_color, font=("Microsoft YaHei", 10), tags="data"
            )
            return

        max_val = max(self._values) or 1
        max_val *= 1.15  # 留顶部空间

        # Y 轴网格和刻度
        self._draw_grid()
        for i in range(6):
            val = max_val * i / 5
            y = self.plot_y + self.plot_h - self.plot_h * i / 5
            self.create_text(
                self.plot_x - 6, y,
                text=f"{val:.0f}", fill=self._text_color,
                font=("Microsoft YaHei", 7), anchor=tk.E, tags="data"
            )

        # X 轴
        self.create_line(
            self.plot_x, self.plot_y + self.plot_h,
            self.plot_x + self.plot_w, self.plot_y + self.plot_h,
            fill=self._axis_color, width=1, tags="axes"
        )

        n = len(self._labels)
        bar_gap = 8
        bar_w = max(12, min(50, (self.plot_w - bar_gap * (n + 1)) / n))

        for i, (label, value) in enumerate(zip(self._labels, self._values)):
            x0 = self.plot_x + bar_gap + i * (bar_w + bar_gap)
            x1 = x0 + bar_w
            bar_h = self.plot_h * value / max_val if max_val > 0 else 0
            y0 = self.plot_y + self.plot_h - bar_h
            y1 = self.plot_y + self.plot_h

            color = self._series_colors[i % len(self._series_colors)]

            # 柱子
            self.create_rectangle(
                x0, y0, x1, y1, fill=color, outline="", tags="data"
            )

            # 数值标签
            if value > 0:
                self.create_text(
                    (x0 + x1) / 2, y0 - 8,
                    text=str(value), fill=self._text_color,
                    font=("Microsoft YaHei", 8), tags="data"
                )

            # X 轴标签
            self.create_text(
                (x0 + x1) / 2, self.plot_y + self.plot_h + 10,
                text=label if len(label) <= 4 else label[:3] + "..",
                fill=self._text_color,
                font=("Microsoft YaHei", 7), anchor=tk.N, tags="data"
            )


# ============================================================
#  MiniChart — 迷你趋势图
# ============================================================

class MiniChart(tk.Canvas):
    """迷你缩略折线图，用于仪表盘卡片内嵌。"""

    def __init__(self, parent: tk.Widget, width: int = 140, height: int = 44,
                 dark: bool = False):
        super().__init__(parent, width=width, height=height,
                         bg=DARK_BG_COLOR if dark else BG_COLOR,
                         highlightthickness=0)
        self.chart_width = width
        self.chart_height = height
        self.dark = dark
        self.color = DARK_SERIES_COLORS[0] if dark else SERIES_COLORS[0]
        self.fill_color = _lighten(self.color, 0.5)

    def set_data(self, values: list[float]) -> None:
        """设置数据并绘制迷你折线。"""
        self.delete("all")

        if not values or len(values) < 2:
            self.create_text(
                self.chart_width // 2, self.chart_height // 2,
                text="--", fill=DARK_TEXT_COLOR if self.dark else TEXT_COLOR,
                font=("Microsoft YaHei", 8)
            )
            return

        pad = 4
        pw = self.chart_width - pad * 2
        ph = self.chart_height - pad * 2

        vmin = min(values)
        vmax = max(values)
        vr = vmax - vmin or 1
        vmin -= vr * 0.05
        vmax += vr * 0.05
        vr = vmax - vmin

        n = len(values)
        points = []
        for i, v in enumerate(values):
            x = pad + pw * i / (n - 1)
            ratio = (v - vmin) / vr
            y = pad + ph * (1 - ratio)
            points.append((x, y))

        # 填充区域
        fill_pts = [points[0][0], pad + ph]
        for px, py in points:
            fill_pts.extend([px, py])
        fill_pts.extend([points[-1][0], pad + ph])
        self.create_polygon(fill_pts, fill=self.fill_color, outline="")

        # 折线
        for j in range(len(points) - 1):
            self.create_line(
                points[j][0], points[j][1],
                points[j + 1][0], points[j + 1][1],
                fill=self.color, width=1.5
            )

        # 首尾数据点
        self.create_oval(
            points[0][0] - 2, points[0][1] - 2,
            points[0][0] + 2, points[0][1] + 2,
            fill=self.color, outline=""
        )
        self.create_oval(
            points[-1][0] - 2, points[-1][1] - 2,
            points[-1][0] + 2, points[-1][1] + 2,
            fill=self.color, outline=""
        )


# ============================================================
#  CalendarHeatmap — GitHub 贡献图风格年度热力图
# ============================================================

class CalendarHeatmap(tk.Canvas):
    """GitHub 贡献图风格的年度打卡热力图。"""

    CELL_SIZE = 12
    CELL_GAP = 2
    WEEK_COUNT = 53
    DAY_COUNT = 7

    DEFAULT_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    def __init__(self, parent: tk.Widget, width: int = 720, height: int = 130,
                 color_scheme: list[str] | None = None, dark: bool = False):
        bg = DARK_BG_COLOR if dark else BG_COLOR
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0)
        self.chart_width = width
        self.chart_height = height
        self.dark = dark
        self.colors = color_scheme or self.DEFAULT_COLORS
        self._data: dict[str, float] = {}
        self._tooltip = None

        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)

    def set_data(self, date_values: dict[str, float], year: int | None = None) -> None:
        """设置热力图数据。date_values: {"YYYY-MM-DD": count, ...}"""
        self._data = date_values
        self._redraw(year)

    def set_color_scheme(self, base_color: str) -> None:
        """根据基础色动态生成 5 级色阶。"""
        hex_color = base_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

        self.colors = ["#ebedf0"]
        for i in range(1, 5):
            factor = i / 4.0
            rr = int(r * factor)
            gg = int(g * factor)
            bb = int(b * factor)
            self.colors.append(f"#{rr:02x}{gg:02x}{bb:02x}")

        if self._data:
            self._redraw()

    def _redraw(self, year: int | None = None) -> None:
        self.delete("all")

        from datetime import datetime, date, timedelta

        if year is None:
            year = datetime.now().year

        # 计算数据范围
        values = list(self._data.values())
        max_val = max(values) if values else 1

        # 从该年第一天开始，找到第一个周日
        year_start = date(year, 1, 1)
        start_weekday = year_start.weekday()  # Mon=0, Sun=6
        # 使用周日作为周起始 (GitHub style)
        first_sunday = year_start - timedelta(days=start_weekday + 1 if start_weekday < 6 else 0)

        pad_left = 30
        pad_top = 20
        pad_bottom = 10

        cell_total = self.CELL_SIZE + self.CELL_GAP

        # 绘制月份标签
        month_names = ["1月", "2月", "3月", "4月", "5月", "6月",
                       "7月", "8月", "9月", "10月", "11月", "12月"]
        for m in range(1, 13):
            month_first = date(year, m, 1)
            week_offset = (month_first - first_sunday).days // 7
            x = pad_left + week_offset * cell_total
            if 0 <= week_offset < self.WEEK_COUNT:
                self.create_text(
                    x + self.CELL_SIZE // 2, 8,
                    text=month_names[m - 1],
                    fill=DARK_TEXT_COLOR if self.dark else TEXT_COLOR,
                    font=("Microsoft YaHei", 7), anchor=tk.N
                )

        # 绘制日期格子
        for week in range(self.WEEK_COUNT):
            for day in range(self.DAY_COUNT):
                cell_date = first_sunday + timedelta(days=week * 7 + day)
                date_str = cell_date.isoformat()

                x = pad_left + week * cell_total
                y = pad_top + day * cell_total

                # 只绘制该年的日期
                if cell_date.year == year:
                    value = self._data.get(date_str, 0)
                    level = self._value_to_level(value, max_val)
                    color = self.colors[min(level, len(self.colors) - 1)]

                    self.create_rectangle(
                        x, y, x + self.CELL_SIZE, y + self.CELL_SIZE,
                        fill=color, outline="", tags=("cell", f"d_{date_str}")
                    )
                else:
                    # 非本年日期留空
                    self.create_rectangle(
                        x, y, x + self.CELL_SIZE, y + self.CELL_SIZE,
                        fill=self["bg"], outline="", tags="cell"
                    )

        # 图例
        legend_x = pad_left
        legend_y = pad_top + self.DAY_COUNT * cell_total + 4
        for li, (color, label) in enumerate(zip(
            self.colors, ["0", "", "", "", f"{max_val:.0f}" if max_val > 0 else "1"]
        )):
            lx = legend_x + li * (self.CELL_SIZE + self.CELL_GAP)
            self.create_rectangle(
                lx, legend_y, lx + self.CELL_SIZE, legend_y + self.CELL_SIZE,
                fill=color, outline="#cccccc", width=1 if color == "#ebedf0" else 0
            )

    @staticmethod
    def _value_to_level(value: float, max_val: float) -> int:
        """数值映射到 0-4 级别。"""
        if max_val <= 0:
            return 0
        if value <= 0:
            return 0
        ratio = value / max_val
        if ratio <= 0.25:
            return 1
        elif ratio <= 0.5:
            return 2
        elif ratio <= 0.75:
            return 3
        else:
            return 4

    def _on_mouse_move(self, event) -> None:
        """显示日期和数值的 tooltip。"""
        item = self.find_closest(event.x, event.y)
        if not item:
            self._hide_tooltip()
            return
        tags = self.gettags(item[0]) if item else ()
        date_tag = next((t for t in tags if t.startswith("d_")), None)
        if not date_tag:
            self._hide_tooltip()
            return

        date_str = date_tag[2:]
        value = self._data.get(date_str, 0)
        self._show_tooltip(event.x, event.y, date_str, value)

    def _show_tooltip(self, x: int, y: int, date_str: str, value: float) -> None:
        self._hide_tooltip()
        text = f"{date_str}  {value:.0f}次" if value > 0 else f"{date_str}  无打卡"
        self._tooltip = self.create_text(
            x + 12, y - 10, text=text,
            fill="#333333", font=("Microsoft YaHei", 9),
            anchor=tk.SW, tags="tooltip"
        )
        bbox = self.bbox(self._tooltip)
        if bbox:
            self.create_rectangle(
                bbox[0] - 4, bbox[1] - 2, bbox[2] + 4, bbox[3] + 2,
                fill="#ffffff", outline="#cccccc", tags="tooltip_bg"
            )
            self.tag_lower("tooltip_bg", self._tooltip)

    def _hide_tooltip(self) -> None:
        if self._tooltip:
            self.delete("tooltip")
            self.delete("tooltip_bg")
            self._tooltip = None

    def _on_mouse_leave(self, event) -> None:
        self._hide_tooltip()


# ============================================================
#  factory 函数
# ============================================================

def create_status_line_chart(parent: tk.Widget, dark: bool = False) -> LineChart:
    """创建状态趋势折线图。"""
    return LineChart(parent, width=560, height=240,
                     title="状态趋势", dark=dark)


def create_skill_radar_chart(parent: tk.Widget, dark: bool = False) -> RadarChart:
    """创建技能雷达图。"""
    return RadarChart(parent, width=300, height=280,
                      title="技能分布", dark=dark)


def create_category_bar_chart(parent: tk.Widget, dark: bool = False) -> BarChart:
    """创建类别分布柱状图。"""
    return BarChart(parent, width=400, height=220,
                    title="类别分布", dark=dark)
