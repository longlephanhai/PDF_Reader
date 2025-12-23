from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont
from PyQt5.QtWidgets import (
    QMainWindow, QToolBar, QAction, QFileDialog, QLabel, QVBoxLayout,
    QWidget, QScrollArea, QMessageBox, QInputDialog, QLineEdit,
    QHBoxLayout, QListWidget, QListWidgetItem, QSplitter
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from .pdf_view_widget import PDFViewWidget
from .dialogs.export_dialog import ExportDialog
from .dialogs.translate_dialog import TranslateDialog
from .dialogs.summarize_dialog import SummarizeDialog
from core.pdf_model import PDFModel
import pymupdf as fitz
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.page_input = None
        self.status_label = None
        self.find_next_action = None
        self.find_prev_action = None
        self.search_input = None
        self.search_result_label = None
        self.dialog_prev_btn = None
        self.dialog_next_btn = None
        self.setWindowTitle("PDF Editor Pro")
        self.showMaximized()
        self.annotation_mode = None
        self.pdf_model = PDFModel()

        self._setup_ui()
        self.setup_toolbar()
        self.setup_statusbar()

    def _setup_ui(self):
        # PDF view
        self.pdf_view = PDFViewWidget(annotation_callback=self.annotation_rect)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.pdf_view)

        # Thumbnail panel
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(350)
        self.list_widget.itemClicked.connect(self.on_thumbnail_clicked)

        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.setStretchFactor(1, 1)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.splitter)
        self.setCentralWidget(container)

    def setup_toolbar(self):
        tb = QToolBar("Toolbar")
        tb.setIconSize(QSize(32, 32))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(tb)

        font = QFont()
        font.setPointSize(10)

        def add_action(name, icon_path, callback, shortcut=None):
            action = QAction(QIcon(icon_path), name, self)
            action.triggered.connect(callback)
            action.setFont(font)
            if shortcut:
                action.setShortcut(shortcut)
            tb.addAction(action)
            return action

        # File operations
        add_action("Open", "icons/open.png", self.open_pdf, "Ctrl+O")
        add_action("Save", "icons/save.png", self.save_pdf, "Ctrl+S")
        add_action("Save As", "icons/save_as.png", self.save_as_pdf, "Ctrl+Shift+S")
        add_action("Print", "icons/print.png", self.print_pdf, "Ctrl+P")
        add_action("Export", "icons/export.png", self.show_export_dialog, "Ctrl+E")
        tb.addSeparator()

        # Navigation
        add_action("Prev", "icons/prev.png", self.prev_page, "Left")
        add_action("Next", "icons/next.png", self.next_page, "Right")
        tb.addSeparator()

        # Zoom
        add_action("Zoom In", "icons/zoom_in.png", self.zoom_in, "Ctrl++")
        add_action("Zoom Out", "icons/zoom_out.png", self.zoom_out, "Ctrl+-")
        add_action("Reset", "icons/reset.png", self.reset, "Ctrl+0")
        tb.addSeparator()

        # Rotation
        add_action("Rotate Left", "icons/rotate_left.png", self.rotate_left, "Ctrl+L")
        add_action("Rotate Right", "icons/rotate_right.png", self.rotate_right, "Ctrl+R")
        add_action("Rotate 180", "icons/rotate_180.png", self.rotate_180)
        tb.addSeparator()

        # Annotations
        add_action("Highlight", "icons/highlight.png", lambda: self.set_annotation_mode("highlight"))
        add_action("Underline", "icons/underline.png", lambda: self.set_annotation_mode("underline"))
        add_action("Strikeout", "icons/strikeout.png", lambda: self.set_annotation_mode("strikeout"))
        add_action("Note", "icons/note.png", lambda: self.set_annotation_mode("note"))
        add_action("Add Text", "icons/text.png", lambda: self.set_annotation_mode("text"))
        add_action("Remove Text", "icons/remove_text.png", lambda: self.set_annotation_mode("remove_text"))
        add_action("Erase", "icons/erase.png", lambda: self.set_annotation_mode("erase"))
        add_action("Select", "icons/select.png", lambda: self.set_annotation_mode(None))
        tb.addSeparator()

        # Page operations
        add_action("Delete Page", "icons/delete.png", self.delete_page)
        add_action("Delete Multiple", "icons/delete_multiple.png", self.delete_multiple_pages)
        add_action("Add Page", "icons/add.png", self.show_add_page_dialog)
        add_action("Insert After", "icons/add.png", self.insert_page_after)
        add_action("Insert Before", "icons/add.png", self.insert_page_before)
        tb.addSeparator()

        # Search & AI
        add_action("Search", "icons/search.png", self.show_search_dialog, "Ctrl+F")
        add_action("Translate", "icons/translate.png", lambda: self.set_annotation_mode("translate"))
        add_action("Summarize", "icons/summarize.png", self.show_summarize_dialog, "Ctrl+Shift+A")

        self.find_prev_action = add_action("Prev Match", "icons/prev_match.png", self.find_previous, "Shift+F3")
        self.find_next_action = add_action("Next Match", "icons/next_match.png", self.find_next, "F3")

        self.find_prev_action.setEnabled(False)
        self.find_next_action.setEnabled(False)

    def setup_statusbar(self):
        self.status_label = QLabel("No file")
        self.page_input = QLineEdit()
        self.page_input.setFixedWidth(80)
        self.page_input.setPlaceholderText("Go to page")
        self.page_input.returnPressed.connect(self.goto_page_from_input)

        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.status_label)
        lay.addStretch()
        lay.addWidget(self.page_input)
        self.statusBar().addPermanentWidget(container)

    # ===== PDF Operations =====
    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf_model.load_pdf(path)
            self.load_thumbnails()
            self.show_page()
            self.setWindowTitle(f"PDF Editor Pro - {os.path.basename(path)}")

            last_page = self.pdf_model.current_page + 1
            if last_page > 1:
                self.statusBar().showMessage(f"Opened at last read page: {last_page}", 3000)

    def load_thumbnails(self):
        self.list_widget.clear()
        if not self.pdf_model.doc:
            return

        for i in range(self.pdf_model.get_page_count()):
            pix = self.pdf_model.get_pixmap_by_index(i, zoom=0.15)
            if pix:
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                icon = QIcon(QPixmap.fromImage(img))
                item = QListWidgetItem(icon, f"Page {i + 1}")
                item.setToolTip(f"Page {i + 1}")
                self.list_widget.addItem(item)

    def on_thumbnail_clicked(self, item: QListWidgetItem):
        index = self.list_widget.row(item)
        if 0 <= index < self.pdf_model.get_page_count():
            self.pdf_model.current_page = index
            self.pdf_model.save_bookmark(self.pdf_model.file_path, index)
            self.show_page()

    def update_thumbnail_selection(self):
        if not hasattr(self, 'list_widget') or not self.list_widget.count():
            return

        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        current_index = self.pdf_model.current_page
        if 0 <= current_index < self.list_widget.count():
            item = self.list_widget.item(current_index)
            if item:
                item.setSelected(True)
                self.list_widget.setCurrentRow(current_index)
                self.list_widget.scrollToItem(item)
        self.list_widget.blockSignals(False)

    def show_page(self):
        if not self.pdf_model.doc:
            self.pdf_view.clear()
            self.status_label.setText("No file")
            return

        pix = self.pdf_model.get_current_page_pixmap(self.pdf_view.zoom)
        if pix:
            text_rects, page_rect = self.pdf_model.get_text_regions()
            self.pdf_view.set_text_regions(text_rects, page_rect)
            self.pdf_view.show_page(pix)

        rotation = self.pdf_model.get_page_rotation()
        self.status_label.setText(
            f"Page {self.pdf_model.current_page + 1}/{self.pdf_model.get_page_count()} | Rotation: {rotation}°"
        )
        self.update_thumbnail_selection()

        # Re-highlight current search match if on same page
        current_match = self.pdf_model.get_current_search_match()
        if current_match and current_match['page'] == self.pdf_model.current_page:
            page = self.pdf_model.get_current_page()
            if page:
                scale_x = self.pdf_view.displayed_width / page.rect.width
                scale_y = self.pdf_view.displayed_height / page.rect.height

                pdf_rect = current_match['rect']
                from PyQt5.QtCore import QRectF
                view_rect = QRectF(
                    pdf_rect.x0 * scale_x,
                    pdf_rect.y0 * scale_y,
                    pdf_rect.width * scale_x,
                    pdf_rect.height * scale_y
                )

                self.pdf_view.highlight_search_rect(view_rect)

    # ===== Navigation =====
    def next_page(self):
        if self.pdf_model.next_page():
            self.show_page()

    def prev_page(self):
        if self.pdf_model.prev_page():
            self.show_page()

    def goto_page_from_input(self):
        try:
            page_num = int(self.page_input.text())
            if self.pdf_model.go_to_page(page_num):
                self.show_page()
        except ValueError:
            self.statusBar().showMessage("Invalid page number", 3000)
        finally:
            self.page_input.clear()

    # ===== Zoom =====
    def zoom_in(self):
        self.pdf_view.zoom *= 1.25
        self.show_page()

    def zoom_out(self):
        self.pdf_view.zoom = max(0.2, self.pdf_view.zoom / 1.25)
        self.show_page()

    def reset(self):
        self.pdf_view.zoom = 1.5
        self.show_page()

    # ===== Rotation =====
    def rotate_left(self):
        if not self.pdf_model.doc:
            return
        current_rotation = self.pdf_model.get_page_rotation()
        new_rotation = (current_rotation - 90) % 360
        if self.pdf_model.rotate_current_page(new_rotation):
            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Rotated page to {new_rotation}°", 2000)

    def rotate_right(self):
        if not self.pdf_model.doc:
            return
        current_rotation = self.pdf_model.get_page_rotation()
        new_rotation = (current_rotation + 90) % 360
        if self.pdf_model.rotate_current_page(new_rotation):
            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Rotated page to {new_rotation}°", 2000)

    def rotate_180(self):
        if not self.pdf_model.doc:
            return
        current_rotation = self.pdf_model.get_page_rotation()
        new_rotation = (current_rotation + 180) % 360
        if self.pdf_model.rotate_current_page(new_rotation):
            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Rotated page to {new_rotation}°", 2000)

    # ===== Save & Print =====
    def save_pdf(self):
        if not self.pdf_model.file_path:
            return self.save_as_pdf()
        if self.pdf_model.save():
            QMessageBox.information(self, "Success", "File saved!")
            return None
        else:
            QMessageBox.critical(self, "Error", "Cannot save file!")
            return None

    def save_as_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "PDF Files (*.pdf)")
        if path:
            if self.pdf_model.save_as(path):
                QMessageBox.information(self, "Success", f"Saved to:\n{path}")
                self.setWindowTitle(f"PDF Editor Pro - {os.path.basename(path)}")
            else:
                QMessageBox.critical(self, "Error", "Cannot save file!")

    def print_pdf(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "No PDF file loaded!")
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.NativeFormat)
        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("Print PDF")

        if print_dialog.exec_() == QPrintDialog.Accepted:
            self._do_print(printer)

    def _do_print(self, printer):
        try:
            from PyQt5.QtGui import QPainter
            painter = QPainter()
            painter.begin(printer)

            for i in range(self.pdf_model.get_page_count()):
                if i > 0:
                    printer.newPage()

                pix = self.pdf_model.get_pixmap_by_index(i, zoom=2.0)
                if pix:
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                    target_rect = printer.pageRect()
                    scaled_img = QPixmap.fromImage(img).scaled(
                        target_rect.width(), target_rect.height(),
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    painter.drawPixmap(0, 0, scaled_img)

            painter.end()
            QMessageBox.information(self, "Success", "Document printed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing: {e}")

    def show_export_dialog(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "No PDF file loaded!")
            return
        dialog = ExportDialog(self, self.pdf_model)
        dialog.exec_()

    # ===== Annotations =====
    def set_annotation_mode(self, mode):
        self.annotation_mode = mode
        self.pdf_view.set_selection_mode(mode is not None)
        mode_name = mode.capitalize() if mode else "Text Selection"
        if mode == "remove_text":
            mode_name = "Remove Text"
        elif mode == "translate":
            mode_name = "Translate Text"
        self.statusBar().showMessage(f"{mode_name} mode", 3000)

    def annotation_rect(self, rect):
        if not self.pdf_model.doc or rect.isEmpty():
            return

        page = self.pdf_model.get_current_page()
        if not page:
            return

        scale_x = page.rect.width / self.pdf_view.displayed_width
        scale_y = page.rect.height / self.pdf_view.displayed_height

        pdf_rect = fitz.Rect(
            rect.left() * scale_x, rect.top() * scale_y,
            rect.right() * scale_x, rect.bottom() * scale_y
        )

        if pdf_rect.is_empty or pdf_rect.is_infinite:
            return

        try:
            if self.annotation_mode == "erase":
                removed_count = self.pdf_model.erase_annotations_in_rect(pdf_rect)
                if removed_count > 0:
                    self.show_page()
                    self.statusBar().showMessage(f"Deleted {removed_count} annotation(s)", 2000)
                else:
                    self.statusBar().showMessage("No annotations found in selected area", 2000)
                return

            elif self.annotation_mode == "remove_text":
                if rect.width() < 10 or rect.height() < 10:
                    return
                annot = self.pdf_model.remove_text_in_rect(pdf_rect)
                if annot:
                    self.show_page()
                    self.statusBar().showMessage("Text removed in selected area", 2000)
                else:
                    self.statusBar().showMessage("Cannot remove text", 2000)
                return

            elif self.annotation_mode == "translate":
                if rect.width() < 10 or rect.height() < 10:
                    return
                text = self.pdf_model.get_selected_text(pdf_rect)
                if not text or not text.strip():
                    self.statusBar().showMessage("No text found in selected area", 2000)
                    return
                dialog = TranslateDialog(self, text.strip())
                dialog.exec_()
                return

            if rect.width() < 10 or rect.height() < 10:
                return

            annot = None
            if self.annotation_mode == "highlight":
                annot = self.pdf_model.add_highlight_annotation(pdf_rect)
            elif self.annotation_mode == "underline":
                annot = self.pdf_model.add_underline_annotation(pdf_rect)
            elif self.annotation_mode == "strikeout":
                annot = self.pdf_model.add_strikeout_annotation(pdf_rect)
            elif self.annotation_mode == "note":
                text, ok = QInputDialog.getText(self, "Add Note", "Enter note:")
                if ok and text.strip():
                    annot = self.pdf_model.add_text_annotation(pdf_rect, text.strip())
            elif self.annotation_mode == "text":
                text, ok = QInputDialog.getMultiLineText(self, "Add Text", "Enter text to add to PDF:")
                if ok and text.strip():
                    annot = self.pdf_model.add_freetext(
                        pdf_rect, text.strip(), fontsize=12,
                        color=(0, 0, 0), bg_color=(1, 1, 0.8), border_width=1
                    )

            if annot:
                self.show_page()
                self.statusBar().showMessage("Annotation added", 2000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot add/remove annotation: {e}")

    # ===== Page Operations =====
    def delete_page(self):
        if not self.pdf_model.doc:
            return

        current_page = self.pdf_model.current_page + 1
        reply = QMessageBox.question(
            self, "Delete Page", f"Delete page {current_page}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.pdf_model.delete_current_page():
                self.load_thumbnails()
                self.show_page()

    def delete_multiple_pages(self):
        if not self.pdf_model.doc:
            return

        text, ok = QInputDialog.getText(
            self, "Delete Multiple Pages",
            "Enter page numbers (e.g. 1,3,5-7):"
        )

        if not ok or not text.strip():
            return

        try:
            nums = []
            for part in text.split(','):
                part = part.strip()
                if '-' in part:
                    a, b = map(int, part.split('-'))
                    nums.extend(range(a - 1, b))
                else:
                    nums.append(int(part) - 1)

            if nums:
                self.pdf_model.delete_pages(nums)
                self.load_thumbnails()
                self.show_page()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid input: {e}")

    def show_add_page_dialog(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "Please open a PDF file first!")
            return

        from PyQt5.QtWidgets import QDialog, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Page")
        dialog.setModal(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose where to add new page:"))

        btn_end = QPushButton("Add at End")
        btn_end.clicked.connect(lambda: self.add_page_at_position(-1, dialog))
        layout.addWidget(btn_end)

        btn_after = QPushButton(f"Insert After Page {self.pdf_model.current_page + 1}")
        btn_after.clicked.connect(lambda: self.add_page_at_position(self.pdf_model.current_page + 1, dialog))
        layout.addWidget(btn_after)

        btn_before = QPushButton(f"Insert Before Page {self.pdf_model.current_page + 1}")
        btn_before.clicked.connect(lambda: self.add_page_at_position(self.pdf_model.current_page, dialog))
        layout.addWidget(btn_before)

        btn_start = QPushButton("Add at Beginning")
        btn_start.clicked.connect(lambda: self.add_page_at_position(0, dialog))
        layout.addWidget(btn_start)

        btn_custom = QPushButton("Custom Position...")
        btn_custom.clicked.connect(lambda: self.add_page_custom(dialog))
        layout.addWidget(btn_custom)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        layout.addWidget(btn_cancel)

        dialog.setLayout(layout)
        dialog.exec_()

    def add_page_at_position(self, position, dialog=None):
        if self.pdf_model.add_new_page(position):
            if position == -1:
                self.pdf_model.current_page = self.pdf_model.get_page_count() - 1
            else:
                self.pdf_model.current_page = position

            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Added page at position {position + 1}", 2000)

            if dialog:
                dialog.accept()
        else:
            QMessageBox.warning(self, "Error", "Cannot add page!")

    def add_page_custom(self, dialog=None):
        total_pages = self.pdf_model.get_page_count()
        position, ok = QInputDialog.getInt(
            self, "Custom Position",
            f"Enter position (1-{total_pages + 1}):\n1 = beginning, {total_pages + 1} = end",
            self.pdf_model.current_page + 2, 1, total_pages + 1
        )

        if ok:
            if position == total_pages + 1:
                self.add_page_at_position(-1, dialog)
            else:
                self.add_page_at_position(position - 1, dialog)

    def insert_page_after(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "Please open a PDF file first!")
            return

        if self.pdf_model.insert_page_after_current():
            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Inserted page after page {self.pdf_model.current_page}", 2000)

    def insert_page_before(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "Please open a PDF file first!")
            return

        if self.pdf_model.insert_page_before_current():
            self.load_thumbnails()
            self.show_page()
            self.statusBar().showMessage(f"Inserted page before page {self.pdf_model.current_page + 2}", 2000)

    # ===== Search =====
    def show_search_dialog(self):
        from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Search PDF")
        dialog.setModal(False)  # Non-modal để có thể tương tác với PDF
        dialog.setFixedSize(400, 150)

        layout = QVBoxLayout()

        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setText(self.pdf_model.last_search_text)
        self.search_input.setPlaceholderText("Enter text to search...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Result label
        self.search_result_label = QLabel("Enter text and click Search")
        self.search_result_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.search_result_label)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(lambda: self.perform_search(dialog))
        btn_search.setDefault(True)

        btn_prev = QPushButton("◀ Previous")
        btn_prev.clicked.connect(self.find_previous)
        btn_prev.setEnabled(False)
        self.dialog_prev_btn = btn_prev

        btn_next = QPushButton("Next ▶")
        btn_next.clicked.connect(self.find_next)
        btn_next.setEnabled(False)
        self.dialog_next_btn = btn_next

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.close)

        btn_layout.addWidget(btn_search)
        btn_layout.addWidget(btn_prev)
        btn_layout.addWidget(btn_next)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        # Connect Enter key
        self.search_input.returnPressed.connect(lambda: self.perform_search(dialog))

        dialog.show()

    def perform_search(self, dialog):
        search_text = self.search_input.text().strip()

        if not search_text:
            self.search_result_label.setText("Please enter text to search")
            self.search_result_label.setStyleSheet("color: #d9534f;")
            return

        if not self.pdf_model.doc:
            self.search_result_label.setText("No PDF loaded")
            self.search_result_label.setStyleSheet("color: #d9534f;")
            return

        self.search_result_label.setText("Searching...")
        self.search_result_label.setStyleSheet("color: #0275d8;")
        dialog.repaint()

        results = self.pdf_model.search_text(search_text)

        if results:
            total = self.pdf_model.get_search_result_count()
            self.search_result_label.setText(f"Found {total} match{'es' if total > 1 else ''}")
            self.search_result_label.setStyleSheet("color: #5cb85c; font-weight: bold;")

            self.highlight_current_search_match()
            self.find_prev_action.setEnabled(True)
            self.find_next_action.setEnabled(True)
            self.dialog_prev_btn.setEnabled(True)
            self.dialog_next_btn.setEnabled(True)
        else:
            self.search_result_label.setText("No matches found")
            self.search_result_label.setStyleSheet("color: #d9534f;")
            self.find_prev_action.setEnabled(False)
            self.find_next_action.setEnabled(False)
            self.dialog_prev_btn.setEnabled(False)
            self.dialog_next_btn.setEnabled(False)

    def search_text(self, search_text):
        if not self.pdf_model.doc:
            self.statusBar().showMessage("No PDF loaded", 2000)
            return

        self.statusBar().showMessage("Searching...", 1000)
        results = self.pdf_model.search_text(search_text)

        if results:
            total = self.pdf_model.get_search_result_count()
            self.statusBar().showMessage(f"Found {total} match{'es' if total > 1 else ''}", 3000)
            self.highlight_current_search_match()
            self.find_prev_action.setEnabled(True)
            self.find_next_action.setEnabled(True)
        else:
            self.statusBar().showMessage("No matches found", 3000)
            self.find_prev_action.setEnabled(False)
            self.find_next_action.setEnabled(False)

    def highlight_current_search_match(self):
        match = self.pdf_model.get_current_search_match()
        if not match:
            return

        # Navigate to page if needed
        if match['page'] != self.pdf_model.current_page:
            self.pdf_model.current_page = match['page']
            self.show_page()

        # Highlight in model (for persistence)
        self.pdf_model.highlight_search_match(match)

        # Get page and scale factors
        page = self.pdf_model.get_current_page()
        if page:
            scale_x = self.pdf_view.displayed_width / page.rect.width
            scale_y = self.pdf_view.displayed_height / page.rect.height

            # Convert PDF rect to view coordinates
            pdf_rect = match['rect']
            from PyQt5.QtCore import QRectF
            view_rect = QRectF(
                pdf_rect.x0 * scale_x,
                pdf_rect.y0 * scale_y,
                pdf_rect.width * scale_x,
                pdf_rect.height * scale_y
            )

            # Highlight immediately on view
            self.pdf_view.highlight_search_rect(view_rect)

            # Scroll to make visible
            self.scroll_to_rect(view_rect)

        # Update status
        total = self.pdf_model.get_search_result_count()
        current_idx = self.pdf_model.current_search_index
        self.statusBar().showMessage(
            f"Match {current_idx + 1}/{total} on page {match['page'] + 1}"
        )

        # Update search dialog if exists
        if hasattr(self, 'search_result_label') and self.search_result_label:
            self.search_result_label.setText(
                f"Match {current_idx + 1} of {total} (Page {match['page'] + 1})"
            )
            self.search_result_label.setStyleSheet("color: #5cb85c; font-weight: bold;")

    def scroll_to_rect(self, rect):
        """Scroll to make the rect visible in the center of viewport"""
        from PyQt5.QtCore import QPoint

        # Calculate center point of rect
        center_x = rect.center().x()
        center_y = rect.center().y()

        # Get viewport size
        viewport = self.scroll_area.viewport()
        viewport_width = viewport.width()
        viewport_height = viewport.height()

        # Calculate scroll position to center the rect
        scroll_x = int(center_x - viewport_width / 2)
        scroll_y = int(center_y - viewport_height / 2)

        # Apply scroll
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()

        h_scrollbar.setValue(max(0, scroll_x))
        v_scrollbar.setValue(max(0, scroll_y))

    def find_next(self):
        match = self.pdf_model.next_search_result()
        if match:
            self.highlight_current_search_match()

    def find_previous(self):
        match = self.pdf_model.prev_search_result()
        if match:
            self.highlight_current_search_match()

    def show_summarize_dialog(self):
        if not self.pdf_model.doc:
            QMessageBox.warning(self, "Warning", "No PDF file loaded!")
            return
        dialog = SummarizeDialog(self, self.pdf_model)
        dialog.exec_()