from PyQt5.QtWidgets import QLabel, QRubberBand
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPainter, QColor, QPen


class PDFViewWidget(QLabel):
    def __init__(self, parent=None, annotation_callback=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)
        self.rubberBand = None
        self.origin = QPoint()
        self.zoom = 1.5
        self.annotation_callback = annotation_callback
        self.selection_mode = False
        self.displayed_width = 0
        self.displayed_height = 0
        self.text_rects = []
        self.page_rect = None
        self.current_pixmap = None  # Lưu pixmap hiện tại

    def set_selection_mode(self, enabled):
        self.selection_mode = enabled
        if not enabled and self.rubberBand:
            self.rubberBand.hide()
            self.rubberBand.deleteLater()
            self.rubberBand = None
        self.update_cursor()

    def update_cursor(self):
        pos = self.mapFromGlobal(QCursor.pos())
        if not self.underMouse():
            return
        if self.selection_mode:
            self.setCursor(Qt.CrossCursor)
        elif self.is_position_in_text(pos):
            self.setCursor(Qt.IBeamCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.selection_mode:
            self.origin = event.pos()
            if self.rubberBand:
                self.rubberBand.deleteLater()
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.update_cursor()
        if self.selection_mode and self.rubberBand and self.rubberBand.isVisible():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selection_mode and self.rubberBand and self.rubberBand.isVisible():
            rubber_rect = self.rubberBand.geometry().normalized()
            self.rubberBand.hide()
            self.rubberBand.deleteLater()
            self.rubberBand = None
            if rubber_rect.width() > 10 and rubber_rect.height() > 10:
                if not self.pixmap():
                    return
                pixmap_w = self.displayed_width
                pixmap_h = self.displayed_height
                if pixmap_w == 0 or pixmap_h == 0:
                    return
                offset_x = (self.width() - pixmap_w) // 2
                offset_y = (self.height() - pixmap_h) // 2
                if (rubber_rect.left() < offset_x or
                        rubber_rect.right() > offset_x + pixmap_w or
                        rubber_rect.top() < offset_y or
                        rubber_rect.bottom() > offset_y + pixmap_h):
                    local_rect = QRect(
                        max(rubber_rect.left(), offset_x),
                        max(rubber_rect.top(), offset_y),
                        0, 0
                    )
                    local_rect.setRight(min(rubber_rect.right(), offset_x + pixmap_w - 1))
                    local_rect.setBottom(min(rubber_rect.bottom(), offset_y + pixmap_h - 1))
                else:
                    local_rect = rubber_rect
                local_rect = local_rect.translated(-offset_x, -offset_y)
                if local_rect.width() > 10 and local_rect.height() > 10:
                    if self.annotation_callback:
                        self.annotation_callback(local_rect)
        super().mouseReleaseEvent(event)

    def is_position_in_text(self, pos):
        if not self.text_rects or not self.page_rect:
            return False
        sx = self.displayed_width / self.page_rect.width
        sy = self.displayed_height / self.page_rect.height
        for r in self.text_rects:
            wr = QRect(int(r.x0 * sx), int(r.y0 * sy),
                       max(1, int(r.width * sx)), max(1, int(r.height * sy)))
            if wr.contains(pos):
                return True
        return False

    def set_text_regions(self, rects, page_rect):
        self.text_rects = rects
        self.page_rect = page_rect

    def show_page(self, pixmap):
        if not pixmap:
            self.clear()
            self.current_pixmap = None
            return
        img = QImage(pixmap.samples, pixmap.width, pixmap.height, pixmap.stride, QImage.Format_RGB888)
        qpixmap = QPixmap.fromImage(img)

        # LƯU pixmap vào biến
        self.current_pixmap = qpixmap

        self.setPixmap(qpixmap)
        self.displayed_width = qpixmap.width()
        self.displayed_height = qpixmap.height()
        self.setMinimumSize(qpixmap.size())
        self.updateGeometry()
        self.update()

    def highlight_search_rect(self, rect):
        if not self.current_pixmap or rect is None or rect.isEmpty():
            return

        pixmap_copy = self.current_pixmap.copy()

        painter = QPainter(pixmap_copy)
        painter.setRenderHint(QPainter.Antialiasing)

        highlight_color = QColor(0, 255, 0, 100)  # Green with alpha
        painter.fillRect(rect, highlight_color)

        # Draw border
        pen = QPen(QColor(0, 200, 0), 2)
        painter.setPen(pen)
        painter.drawRect(rect)

        painter.end()

        self.setPixmap(pixmap_copy)

    def clear(self):
        super().clear()
        self.current_pixmap = None
        self.text_rects = []
        self.page_rect = None
        self.displayed_width = 0
        self.displayed_height = 0