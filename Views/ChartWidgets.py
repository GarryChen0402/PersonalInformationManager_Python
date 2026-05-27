"""图表组件 — PySide6 QPainter 版本。

零外部依赖，使用 QPainter 自绘。
替代原有 Tkinter Canvas 实现。
"""

import math
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF


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


def _lighten(hex_color: str, factor: float = 0.3) -> QColor:
    """将颜色变浅（用于填充区域）。"""
    c = QColor(hex_color)
    r = min(255, int(c.red() + (255 - c.red()) * factor))
    g = min(255, int(c.green() + (255 - c.green()) * factor))
    b = min(255, int(c.blue() + (255 - c.blue()) * factor))
    return QColor(r, g, b)


def _darken(hex_color: str, factor: float = 0.5) -> QColor:
    """将颜色变深。"""
    c = QColor(hex_color)
    return QColor(
        int(c.red() * (1 - factor)),
        int(c.green() * (1 - factor)),
        int(c.blue() * (1 - factor))
    )


# ============================================================
#  ChartBase — 图表基类
# ============================================================

class ChartBase(QWidget):
    """图表基类，提供坐标轴、网格线、标题绘制。"""

    def __init__(self, parent=None, title="", dark=False):
        super().__init__(parent)
        self.chart_title = title
        self.dark = dark
        self.setMinimumSize(300, 200)

        # 边距
        self._margin_left = MARGIN_LEFT
        self._margin_right = MARGIN_RIGHT
        self._margin_top = MARGIN_TOP
        self._margin_bottom = MARGIN_BOTTOM

    @property
    def _series_colors(self) -> list[str]:
        return DARK_SERIES_COLORS if self.dark else SERIES_COLORS

    @property
    def _grid_color(self) -> QColor:
        return QColor(DARK_GRID_COLOR if self.dark else GRID_COLOR)

    @property
    def _axis_color(self) -> QColor:
        return QColor(DARK_AXIS_COLOR if self.dark else AXIS_COLOR)

    @property
    def _text_color(self) -> QColor:
        return QColor(DARK_TEXT_COLOR if self.dark else TEXT_COLOR)

    @property
    def _bg_color(self) -> QColor:
        return QColor(DARK_BG_COLOR if self.dark else BG_COLOR)

    def _plot_rect(self) -> QRectF:
        """返回绘图区域（去除边距）。"""
        w = self.width()
        h = self.height()
        return QRectF(
            self._margin_left, self._margin_top,
            w - self._margin_left - self._margin_right,
            h - self._margin_top - self._margin_bottom
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 背景
        painter.fillRect(self.rect(), self._bg_color)
        self._draw(painter)
        painter.end()

    def _draw(self, painter: QPainter) -> None:
        """子类重写实现具体绘制逻辑。"""
        pass

    def _draw_title(self, painter: QPainter) -> None:
        if self.chart_title:
            painter.setPen(QPen(self._text_color))
            painter.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
            painter.drawText(
                QRectF(0, 2, self.width(), self._margin_top - 4),
                Qt.AlignCenter, self.chart_title
            )

    def _draw_axes(self, painter: QPainter) -> None:
        rect = self._plot_rect()
        pen = QPen(self._axis_color, 1)
        painter.setPen(pen)
        # X 轴
        painter.drawLine(
            QPointF(rect.left(), rect.bottom()),
            QPointF(rect.right(), rect.bottom())
        )
        # Y 轴
        painter.drawLine(
            QPointF(rect.left(), rect.top()),
            QPointF(rect.left(), rect.bottom())
        )

    def _draw_grid(self, painter: QPainter, y_ticks: int = 5) -> None:
        rect = self._plot_rect()
        pen = QPen(self._grid_color, 1, Qt.DashLine)
        painter.setPen(pen)
        for i in range(y_ticks + 1):
            y = rect.top() + rect.height() * i / y_ticks
            painter.drawLine(
                QPointF(rect.left(), y),
                QPointF(rect.right(), y)
            )

    def _draw_no_data(self, painter: QPainter) -> None:
        rect = self._plot_rect()
        painter.setPen(QPen(self._text_color))
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(rect, Qt.AlignCenter, "暂无数据")


# ============================================================
#  LineChart — 多系列折线图
# ============================================================

class LineChart(ChartBase):
    """多系列折线图，用于状态趋势展示。"""

    def __init__(self, parent=None, title="", dark=False):
        super().__init__(parent, title, dark)
        self._labels: list[str] = []
        self._series: dict[str, list[float]] = {}

    def set_data(self, labels: list[str], series: dict[str, list[float]]) -> None:
        self._labels = labels
        self._series = series
        self.update()

    def _draw(self, painter: QPainter) -> None:
        self._draw_title(painter)

        if not self._labels or not self._series:
            self._draw_no_data(painter)
            return

        self._draw_axes(painter)
        self._draw_grid(painter)

        rect = self._plot_rect()
        all_values = [v for vals in self._series.values() for v in vals]
        if not all_values:
            self._draw_no_data(painter)
            return

        y_min = min(all_values)
        y_max = max(all_values)
        y_range = y_max - y_min or 1
        y_min -= y_range * 0.1
        y_max += y_range * 0.1
        y_range = y_max - y_min

        # Y 轴刻度
        painter.setPen(QPen(self._text_color))
        painter.setFont(QFont("Microsoft YaHei", 7))
        for i in range(6):
            val = y_min + y_range * i / 5
            y = rect.bottom() - rect.height() * i / 5
            painter.drawText(
                QRectF(0, y - 8, self._margin_left - 6, 16),
                Qt.AlignRight | Qt.AlignVCenter, f"{val:.1f}"
            )

        n = len(self._labels)
        if n < 2:
            n = 2

        # 绘制各系列
        for si, (name, values) in enumerate(self._series.items()):
            color = QColor(self._series_colors[si % len(self._series_colors)])
            fill_color = _lighten(self._series_colors[si % len(self._series_colors)], 0.6)

            points = []
            for i, v in enumerate(values):
                x = rect.left() + rect.width() * i / (n - 1) if n > 1 else rect.center().x()
                ratio = (v - y_min) / y_range
                y = rect.bottom() - rect.height() * ratio
                points.append(QPointF(x, y))

            # 填充区域
            if len(points) >= 2:
                fill_path = QPainterPath()
                fill_path.moveTo(points[0].x(), rect.bottom())
                for p in points:
                    fill_path.lineTo(p)
                fill_path.lineTo(points[-1].x(), rect.bottom())
                fill_path.closeSubpath()
                painter.fillPath(fill_path, fill_color)

            # 折线
            if len(points) >= 2:
                pen = QPen(color, 2)
                painter.setPen(pen)
                for j in range(len(points) - 1):
                    painter.drawLine(points[j], points[j + 1])

            # 数据点
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(color)
            for p in points:
                painter.drawEllipse(p, 3, 3)

        # X 轴标签
        painter.setPen(QPen(self._text_color))
        painter.setFont(QFont("Microsoft YaHei", 7))
        step = max(1, n // 8)
        for i in range(0, n, step):
            x = rect.left() + rect.width() * i / (n - 1) if n > 1 else rect.center().x()
            lbl = self._labels[i]
            if len(lbl) > 6:
                lbl = lbl[-5:]
            painter.save()
            painter.translate(x, rect.bottom() + 8)
            painter.rotate(30)
            painter.drawText(QPointF(0, 0), lbl)
            painter.restore()

        # 图例
        legend_x = rect.right() - 10
        legend_y = rect.top() + 4
        painter.setFont(QFont("Microsoft YaHei", 8))
        for si, name in enumerate(reversed(list(self._series.keys()))):
            c = QColor(self._series_colors[(len(self._series) - 1 - si) % len(self._series_colors)])
            ly = legend_y + si * 18
            painter.fillRect(QRectF(legend_x - 60, ly, 12, 10), c)
            painter.setPen(QPen(self._text_color))
            painter.drawText(QPointF(legend_x - 44, ly + 9), name)


# ============================================================
#  RadarChart — 雷达图
# ============================================================

class RadarChart(ChartBase):
    """技能雷达图，展示多维度能力分布。"""

    def __init__(self, parent=None, title="", dark=False):
        super().__init__(parent, title, dark)
        self._categories: list[str] = []
        self._values: list[float] = []
        self._max_val: float = 5.0

    def set_data(self, categories: list[str], values: list[float], max_val: float = 5.0) -> None:
        self._categories = categories
        self._values = values
        self._max_val = max_val
        self.update()

    def _draw(self, painter: QPainter) -> None:
        self._draw_title(painter)

        if not self._categories or not self._values:
            self._draw_no_data(painter)
            return

        n = len(self._categories)
        cx = self.width() / 2
        cy = self.height() / 2 + 10
        radius = min(cx, cy) - 50

        color = QColor(self._series_colors[0])
        fill_color = _lighten(self._series_colors[0], 0.6)

        # 同心多边形网格
        painter.setPen(QPen(self._grid_color, 1))
        for level in range(1, 6):
            r = radius * level / 5
            pts = []
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
            if level < 5:
                pen = QPen(self._grid_color, 1, Qt.DashLine)
                painter.setPen(pen)
            else:
                painter.setPen(QPen(self._grid_color, 1))
            painter.drawPolygon(pts)

        # 轴线 + 标签
        painter.setPen(QPen(self._grid_color, 1))
        for i, cat in enumerate(self._categories):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            ex = cx + radius * math.cos(angle)
            ey = cy + radius * math.sin(angle)
            painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))

            # 标签（在轴线末端外侧）
            label_x = cx + (radius + 16) * math.cos(angle)
            label_y = cy + (radius + 16) * math.sin(angle)
            painter.setPen(QPen(self._text_color))
            painter.setFont(QFont("Microsoft YaHei", 8))
            text_rect = QRectF(label_x - 30, label_y - 8, 60, 16)
            painter.drawText(text_rect, Qt.AlignCenter, cat)

        # 数据多边形
        data_pts = []
        for i, val in enumerate(self._values):
            r = radius * val / self._max_val
            angle = -math.pi / 2 + 2 * math.pi * i / n
            data_pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))

        if len(data_pts) >= 3:
            painter.setPen(QPen(color, 2))
            painter.setBrush(fill_color)
            painter.drawPolygon(data_pts)

        # 数据点
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(color)
        for p in data_pts:
            painter.drawEllipse(p, 4, 4)


# ============================================================
#  BarChart — 柱状图
# ============================================================

class BarChart(ChartBase):
    """类别分布柱状图。"""

    def __init__(self, parent=None, title="", dark=False):
        super().__init__(parent, title, dark)
        self._labels: list[str] = []
        self._values: list[int] = []

    def set_data(self, labels: list[str], values: list[int]) -> None:
        self._labels = labels
        self._values = values
        self.update()

    def _draw(self, painter: QPainter) -> None:
        self._draw_title(painter)

        if not self._labels or not self._values:
            self._draw_no_data(painter)
            return

        self._draw_axes(painter)
        self._draw_grid(painter)

        rect = self._plot_rect()
        max_val = max(self._values) or 1
        max_val *= 1.15

        # Y 轴刻度
        painter.setPen(QPen(self._text_color))
        painter.setFont(QFont("Microsoft YaHei", 7))
        for i in range(6):
            val = max_val * i / 5
            y = rect.bottom() - rect.height() * i / 5
            painter.drawText(
                QRectF(0, y - 8, self._margin_left - 6, 16),
                Qt.AlignRight | Qt.AlignVCenter, f"{val:.0f}"
            )

        n = len(self._labels)
        bar_gap = 8
        bar_w = max(12, min(50, (rect.width() - bar_gap * (n + 1)) / n))

        painter.setFont(QFont("Microsoft YaHei", 7))
        for i, (label, value) in enumerate(zip(self._labels, self._values)):
            x0 = rect.left() + bar_gap + i * (bar_w + bar_gap)
            bar_h = rect.height() * value / max_val if max_val > 0 else 0
            y0 = rect.bottom() - bar_h

            color = QColor(self._series_colors[i % len(self._series_colors)])
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(QRectF(x0, y0, bar_w, bar_h))

            # 数值标签
            if value > 0:
                painter.setPen(QPen(self._text_color))
                painter.drawText(
                    QRectF(x0, y0 - 16, bar_w, 14),
                    Qt.AlignCenter, str(value)
                )

            # X 轴标签
            display_label = label if len(label) <= 4 else label[:3] + ".."
            painter.drawText(
                QRectF(x0, rect.bottom() + 4, bar_w, 14),
                Qt.AlignCenter, display_label
            )


# ============================================================
#  MiniChart — 迷你趋势图
# ============================================================

class MiniChart(QWidget):
    """迷你缩略折线图，用于仪表盘卡片内嵌。"""

    def __init__(self, parent=None, dark=False):
        super().__init__(parent)
        self.dark = dark
        self.setMinimumSize(120, 40)
        self.setMaximumHeight(50)
        self._values: list[float] = []
        self._color = QColor(SERIES_COLORS[0])
        self._fill_color = _lighten(SERIES_COLORS[0], 0.6)

    def set_data(self, values: list[float]) -> None:
        self._values = values
        self.update()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        self._color = QColor(DARK_SERIES_COLORS[0] if dark else SERIES_COLORS[0])
        self._fill_color = _lighten(
            DARK_SERIES_COLORS[0] if dark else SERIES_COLORS[0], 0.6
        )
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(DARK_BG_COLOR if self.dark else BG_COLOR))

        if not self._values or len(self._values) < 2:
            painter.setPen(QPen(QColor(DARK_TEXT_COLOR if self.dark else TEXT_COLOR)))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(self.rect(), Qt.AlignCenter, "--")
            painter.end()
            return

        pad = 4
        pw = self.width() - pad * 2
        ph = self.height() - pad * 2

        vmin = min(self._values)
        vmax = max(self._values)
        vr = vmax - vmin or 1
        vmin -= vr * 0.05
        vmax += vr * 0.05
        vr = vmax - vmin

        n = len(self._values)
        points = []
        for i, v in enumerate(self._values):
            x = pad + pw * i / (n - 1)
            ratio = (v - vmin) / vr
            y = pad + ph * (1 - ratio)
            points.append(QPointF(x, y))

        # 填充
        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), pad + ph)
        for p in points:
            fill_path.lineTo(p)
        fill_path.lineTo(points[-1].x(), pad + ph)
        fill_path.closeSubpath()
        painter.fillPath(fill_path, self._fill_color)

        # 折线
        painter.setPen(QPen(self._color, 1.5))
        for j in range(len(points) - 1):
            painter.drawLine(points[j], points[j + 1])

        # 首尾点
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(points[0], 2, 2)
        painter.drawEllipse(points[-1], 2, 2)

        painter.end()


# ============================================================
#  CalendarHeatmap — GitHub 贡献图风格年度热力图
# ============================================================

class CalendarHeatmap(QWidget):
    """GitHub 贡献图风格的年度打卡热力图。"""

    CELL_SIZE = 12
    CELL_GAP = 2
    WEEK_COUNT = 53
    DAY_COUNT = 7

    DEFAULT_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    def __init__(self, parent=None, color_scheme=None, dark=False):
        super().__init__(parent)
        self.dark = dark
        self.colors = color_scheme or self.DEFAULT_COLORS
        self._data: dict[str, float] = {}
        self._year: int = datetime.now().year
        self.setMinimumSize(600, 130)
        self.setMouseTracking(True)

    def set_data(self, date_values: dict[str, float], year: int | None = None) -> None:
        self._data = date_values
        if year is not None:
            self._year = year
        self.update()

    def set_color_scheme(self, base_color: str) -> None:
        c = QColor(base_color)
        self.colors = ["#ebedf0"]
        for i in range(1, 5):
            factor = i / 4.0
            self.colors.append(
                f"#{int(c.red() * factor):02x}{int(c.green() * factor):02x}{int(c.blue() * factor):02x}"
            )
        if self._data:
            self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QColor(DARK_BG_COLOR if self.dark else BG_COLOR)
        painter.fillRect(self.rect(), bg)
        self._draw(painter)
        painter.end()

    def _draw(self, painter: QPainter) -> None:
        year = self._year

        # 数据范围
        values = list(self._data.values())
        max_val = max(values) if values else 1

        # 计算起始日期（找到第一个周日）
        year_start = date(year, 1, 1)
        start_weekday = year_start.weekday()
        first_sunday = year_start - timedelta(days=start_weekday + 1 if start_weekday < 6 else 0)

        pad_left = 30
        pad_top = 20

        cell_total = self.CELL_SIZE + self.CELL_GAP

        # 月份标签
        painter.setPen(QPen(QColor(DARK_TEXT_COLOR if self.dark else TEXT_COLOR)))
        painter.setFont(QFont("Microsoft YaHei", 7))
        month_names = ["1月", "2月", "3月", "4月", "5月", "6月",
                       "7月", "8月", "9月", "10月", "11月", "12月"]
        for m in range(1, 13):
            month_first = date(year, m, 1)
            week_offset = (month_first - first_sunday).days // 7
            x = pad_left + week_offset * cell_total
            if 0 <= week_offset < self.WEEK_COUNT:
                painter.drawText(
                    QRectF(x, 0, self.CELL_SIZE + 4, pad_top - 4),
                    Qt.AlignCenter, month_names[m - 1]
                )

        # 日期格子
        for week in range(self.WEEK_COUNT):
            for day in range(self.DAY_COUNT):
                cell_date = first_sunday + timedelta(days=week * 7 + day)
                date_str = cell_date.isoformat()

                x = pad_left + week * cell_total
                y = pad_top + day * cell_total

                if cell_date.year == year:
                    value = self._data.get(date_str, 0)
                    level = self._value_to_level(value, max_val)
                    color = QColor(self.colors[min(level, len(self.colors) - 1)])
                    painter.fillRect(
                        QRectF(x, y, self.CELL_SIZE, self.CELL_SIZE), color
                    )
                    if value <= 0 and self.dark:
                        # 深色主题下无数据格子添加边框
                        painter.setPen(QPen(QColor("#555555"), 0.5))
                        painter.drawRect(
                            QRectF(x, y, self.CELL_SIZE, self.CELL_SIZE)
                        )
                        painter.setPen(Qt.NoPen)

        # 图例
        legend_x = pad_left
        legend_y = pad_top + self.DAY_COUNT * cell_total + 4
        painter.setFont(QFont("Microsoft YaHei", 7))
        for li, color in enumerate(self.colors):
            lx = legend_x + li * (self.CELL_SIZE + self.CELL_GAP)
            painter.fillRect(
                QRectF(lx, legend_y, self.CELL_SIZE, self.CELL_SIZE),
                QColor(color)
            )
            if color == "#ebedf0":
                painter.setPen(QPen(QColor("#cccccc"), 1))
                painter.drawRect(
                    QRectF(lx, legend_y, self.CELL_SIZE, self.CELL_SIZE)
                )
                painter.setPen(Qt.NoPen)

    @staticmethod
    def _value_to_level(value: float, max_val: float) -> int:
        if max_val <= 0 or value <= 0:
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

    def _get_date_at_position(self, pos_x: int, pos_y: int) -> str | None:
        year = self._year
        year_start = date(year, 1, 1)
        start_weekday = year_start.weekday()
        first_sunday = year_start - timedelta(days=start_weekday + 1 if start_weekday < 6 else 0)

        pad_left = 30
        pad_top = 20
        cell_total = self.CELL_SIZE + self.CELL_GAP

        week = (pos_x - pad_left) // cell_total
        day = (pos_y - pad_top) // cell_total

        if 0 <= week < self.WEEK_COUNT and 0 <= day < self.DAY_COUNT:
            cell_date = first_sunday + timedelta(days=week * 7 + day)
            if cell_date.year == year:
                return cell_date.isoformat()
        return None

    def mouseMoveEvent(self, event) -> None:
        date_str = self._get_date_at_position(
            int(event.position().x()), int(event.position().y())
        )
        if date_str:
            value = self._data.get(date_str, 0)
            text = f"{date_str}  {value:.0f}次" if value > 0 else f"{date_str}  无记录"
            QToolTip.showText(event.globalPos(), text, self)
        else:
            QToolTip.hideText()


# ============================================================
#  factory 函数（兼容旧接口）
# ============================================================

def create_status_line_chart(parent=None, dark=False) -> LineChart:
    return LineChart(parent, title="状态趋势", dark=dark)


def create_skill_radar_chart(parent=None, dark=False) -> RadarChart:
    return RadarChart(parent, title="技能分布", dark=dark)


def create_category_bar_chart(parent=None, dark=False) -> BarChart:
    return BarChart(parent, title="类别分布", dark=dark)
