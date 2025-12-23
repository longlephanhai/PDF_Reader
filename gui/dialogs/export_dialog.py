from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QButtonGroup, QSpinBox, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox
)


class ExportDialog(QDialog):

    def __init__(self, parent, pdf_model):
        super().__init__(parent)
        self.line_custom = None
        self.radio_custom = None
        self.spin_end = None
        self.spin_start = None
        self.radio_range = None
        self.radio_all = None
        self.button_group = None
        self.radio_current = None
        self.pdf_model = pdf_model
        self.setWindowTitle("Export PDF")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Export options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        # Current page
        self.radio_current = QRadioButton(f"Current page ({self.pdf_model.current_page + 1})")
        self.radio_current.setChecked(True)
        self.button_group.addButton(self.radio_current)
        options_layout.addWidget(self.radio_current)

        # All pages
        self.radio_all = QRadioButton(f"All pages (1-{self.pdf_model.get_page_count()})")
        self.button_group.addButton(self.radio_all)
        options_layout.addWidget(self.radio_all)

        # Page range
        range_layout = QHBoxLayout()
        self.radio_range = QRadioButton("Page range:")
        self.button_group.addButton(self.radio_range)
        range_layout.addWidget(self.radio_range)

        self.spin_start = QSpinBox()
        self.spin_start.setMinimum(1)
        self.spin_start.setMaximum(self.pdf_model.get_page_count())
        self.spin_start.setValue(1)
        range_layout.addWidget(QLabel("From:"))
        range_layout.addWidget(self.spin_start)

        self.spin_end = QSpinBox()
        self.spin_end.setMinimum(1)
        self.spin_end.setMaximum(self.pdf_model.get_page_count())
        self.spin_end.setValue(self.pdf_model.get_page_count())
        range_layout.addWidget(QLabel("To:"))
        range_layout.addWidget(self.spin_end)

        options_layout.addLayout(range_layout)

        # Custom pages
        custom_layout = QHBoxLayout()
        self.radio_custom = QRadioButton("Custom pages:")
        self.button_group.addButton(self.radio_custom)
        custom_layout.addWidget(self.radio_custom)

        self.line_custom = QLineEdit()
        self.line_custom.setPlaceholderText("e.g., 1,3,5-7")
        custom_layout.addWidget(self.line_custom)

        options_layout.addLayout(custom_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()

        btn_export = QPushButton("Export")
        btn_export.clicked.connect(self.do_export)
        button_layout.addWidget(btn_export)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)

    def do_export(self):
        global message
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF As", "", "PDF Files (*.pdf)"
        )

        if not output_path:
            return

        try:
            success = False

            if self.radio_current.isChecked():
                success = self.pdf_model.export_current_page(output_path)
                message = f"Exported current page to:\n{output_path}"

            elif self.radio_all.isChecked():
                page_indices = list(range(self.pdf_model.get_page_count()))
                success = self.pdf_model.export_pages(page_indices, output_path)
                message = f"Exported all {len(page_indices)} pages to:\n{output_path}"

            elif self.radio_range.isChecked():
                start = self.spin_start.value() - 1
                end = self.spin_end.value() - 1

                if start > end:
                    QMessageBox.warning(self, "Invalid Range", "Start page must be <= end page!")
                    return

                success = self.pdf_model.export_page_range(start, end, output_path)
                message = f"Exported pages {start + 1}-{end + 1} to:\n{output_path}"

            elif self.radio_custom.isChecked():
                text = self.line_custom.text().strip()
                if not text:
                    QMessageBox.warning(self, "Invalid Input", "Please enter page numbers!")
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

                    if not nums:
                        QMessageBox.warning(self, "Invalid Input", "No valid page numbers!")
                        return

                    success = self.pdf_model.export_pages(nums, output_path)
                    message = f"Exported {len(nums)} pages to:\n{output_path}"

                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Invalid page numbers: {e}")
                    return

            if success:
                QMessageBox.information(self, "Export Successful", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Export Failed", "Could not export PDF!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export error: {e}")