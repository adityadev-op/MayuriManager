from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QPushButton, QWidget


class PremiumButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class RevenueChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = []
        self.setMinimumSize(250, 190)
        self.setAccessibleName("Daily revenue chart")
        self.setAccessibleDescription(
            "Bar chart of daily completed-payment revenue. Exact values appear in the adjacent table."
        )

    def set_points(self, points):
        self._points = points[-14:]
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect().adjusted(12, 14, -12, -14)
        text_color = self.palette().color(self.foregroundRole())
        painter.setPen(text_color)

        if not self._points:
            painter.drawText(bounds, Qt.AlignmentFlag.AlignCenter, "No revenue to chart")
            return

        values = [max(float(value), 0.0) for _, value in self._points]
        peak = max(values) or 1.0
        label_height = 24
        chart_area = bounds.adjusted(0, 4, 0, -label_height)
        baseline = chart_area.bottom()
        painter.setPen(QColor("#d9c8b8"))
        painter.drawLine(chart_area.left(), baseline, chart_area.right(), baseline)

        count = len(values)
        slot_width = chart_area.width() / count
        bar_width = min(30.0, slot_width * 0.58)
        for index, (label, value) in enumerate(self._points):
            height = max(
                3.0,
                chart_area.height() * max(float(value), 0.0) / peak,
            )
            x = chart_area.left() + slot_width * (index + 0.5) - bar_width / 2
            bar = QPainterPath()
            bar.addRoundedRect(x, baseline - height, bar_width, height, 5, 5)
            painter.fillPath(bar, QColor("#e97832"))

            if count <= 7 or index in (0, count - 1):
                date_label = str(label)[-5:]
                painter.setPen(text_color)
                painter.drawText(
                    int(chart_area.left() + slot_width * index),
                    baseline + 4,
                    int(slot_width),
                    label_height,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    date_label,
                )
