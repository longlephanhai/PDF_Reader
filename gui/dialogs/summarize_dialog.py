from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QSpinBox, QComboBox, QTextEdit, QTextBrowser, QMessageBox,
    QFileDialog, QApplication
)
from gui.threads.summarize_thread import GeminiSummarizeThread
import os


class SummarizeDialog(QDialog):
    def __init__(self, parent, pdf_model):
        super().__init__(parent)
        self.text_summary = None
        self.combo_type = None
        self.combo_language = None
        self.spin_end = None
        self.spin_start = None
        self.radio_range = None
        self.radio_all = None
        self.radio_current = None
        self.button_group = None
        self.line_api_key = None
        self.pdf_model = pdf_model
        self.summarize_thread = None

        self.setWindowTitle("Summarize with Gemini AI")
        self.setModal(True)
        self.setMinimumSize(700, 600)

        self.setup_ui()
        self.load_api_key()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # API Key section
        api_group = QGroupBox("Gemini API Configuration")
        api_layout = QVBoxLayout()

        api_input_layout = QHBoxLayout()
        api_input_layout.addWidget(QLabel("API Key:"))

        self.line_api_key = QLineEdit()
        self.line_api_key.setEchoMode(QLineEdit.Password)
        self.line_api_key.setPlaceholderText("Enter your Gemini API key")
        api_input_layout.addWidget(self.line_api_key)

        btn_show_key = QPushButton("show")
        btn_show_key.setMaximumWidth(40)
        btn_show_key.setCheckable(True)
        btn_show_key.clicked.connect(self.toggle_api_key_visibility)
        api_input_layout.addWidget(btn_show_key)

        api_layout.addLayout(api_input_layout)

        # Link to get API key
        api_info = QTextBrowser()
        api_info.setMaximumHeight(50)
        api_info.setOpenExternalLinks(True)
        api_info.setHtml(
            '<small>Get free API key at: '
            '<a href="https://makersuite.google.com/app/apikey">Google AI Studio</a>'
            '</small>'
        )
        api_layout.addWidget(api_info)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Content selection
        content_group = QGroupBox("Select Content to Summarize")
        content_layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        # Current page
        self.radio_current = QRadioButton(f"Current page ({self.pdf_model.current_page + 1})")
        self.radio_current.setChecked(True)
        self.button_group.addButton(self.radio_current)
        content_layout.addWidget(self.radio_current)

        # All pages
        self.radio_all = QRadioButton(f"All pages (1-{self.pdf_model.get_page_count()})")
        self.button_group.addButton(self.radio_all)
        content_layout.addWidget(self.radio_all)

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
        self.spin_end.setValue(min(5, self.pdf_model.get_page_count()))
        range_layout.addWidget(QLabel("To:"))
        range_layout.addWidget(self.spin_end)

        content_layout.addLayout(range_layout)

        # Custom pages
        custom_layout = QHBoxLayout()
        self.radio_custom = QRadioButton("Custom pages:")
        self.button_group.addButton(self.radio_custom)
        custom_layout.addWidget(self.radio_custom)

        self.line_custom = QLineEdit()
        self.line_custom.setPlaceholderText("e.g., 1,3,5-7")
        custom_layout.addWidget(self.line_custom)

        content_layout.addLayout(custom_layout)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # Summary options
        options_group = QGroupBox("Summary Options")
        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("Type:"))
        self.combo_type = self.create_type_combo()
        options_layout.addWidget(self.combo_type)

        options_layout.addWidget(QLabel("Language:"))
        self.combo_language = self.create_language_combo()
        options_layout.addWidget(self.combo_language)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Summarize button
        btn_summarize = QPushButton("Summarize with Gemini")
        btn_summarize.clicked.connect(self.do_summarize)
        btn_summarize.setStyleSheet(
            "QPushButton { background-color: #4285f4; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(btn_summarize)

        # Summary result
        layout.addWidget(QLabel("Summary Result:"))
        self.text_summary = QTextEdit()
        self.text_summary.setReadOnly(True)
        self.text_summary.setPlaceholderText("Summary will appear here...")
        layout.addWidget(self.text_summary)

        # Status label
        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        # Buttons
        button_layout = QHBoxLayout()

        btn_copy = QPushButton("Copy Summary")
        btn_copy.clicked.connect(self.copy_summary)
        button_layout.addWidget(btn_copy)

        btn_save = QPushButton("Save to File")
        btn_save.clicked.connect(self.save_summary)
        button_layout.addWidget(btn_save)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        button_layout.addWidget(btn_close)

        layout.addLayout(button_layout)

    def create_type_combo(self):
        combo = QComboBox()
        types = [
            ("Brief Summary", "brief"),
            ("Detailed Summary", "detailed"),
            ("Bullet Points", "bullet"),
            ("Key Points", "key_points"),
        ]
        for name, code in types:
            combo.addItem(name, code)
        return combo

    def create_language_combo(self):
        combo = QComboBox()
        combo.addItem("English", "en")
        combo.addItem("Tiếng Việt", "vi")
        combo.setCurrentIndex(1)  # Default to Vietnamese
        return combo

    def toggle_api_key_visibility(self, checked):
        if checked:
            self.line_api_key.setEchoMode(QLineEdit.Normal)
        else:
            self.line_api_key.setEchoMode(QLineEdit.Password)

    def load_api_key(self):
        try:
            key_file = "gemini_api_key.txt"
            if os.path.exists(key_file):
                with open(key_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        self.line_api_key.setText(api_key)
        except:
            pass

    def save_api_key(self, api_key):
        try:
            with open("gemini_api_key.txt", 'w') as f:
                f.write(api_key)
        except:
            pass

    def do_summarize(self):
        api_key = self.line_api_key.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter your Gemini API key!")
            return

        # Save API key for next time
        self.save_api_key(api_key)

        # Get text based on selection
        text = ""

        try:
            if self.radio_current.isChecked():
                text = self.pdf_model.extract_text_from_page(self.pdf_model.current_page)

            elif self.radio_all.isChecked():
                total_pages = self.pdf_model.get_page_count()
                if total_pages > 50:
                    reply = QMessageBox.question(
                        self, "Confirm",
                        f"Summarize all {total_pages} pages? This may take a while and cost more API credits.",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
                text = self.pdf_model.extract_text_from_all_pages()

            elif self.radio_range.isChecked():
                start = self.spin_start.value() - 1
                end = self.spin_end.value() - 1

                if start > end:
                    QMessageBox.warning(self, "Invalid Range", "Start page must be <= end page!")
                    return

                page_indices = list(range(start, end + 1))
                text = self.pdf_model.extract_text_from_pages(page_indices)

            elif self.radio_custom.isChecked():
                custom_text = self.line_custom.text().strip()
                if not custom_text:
                    QMessageBox.warning(self, "Invalid Input", "Please enter page numbers!")
                    return

                nums = []
                for part in custom_text.split(','):
                    part = part.strip()
                    if '-' in part:
                        a, b = map(int, part.split('-'))
                        nums.extend(range(a - 1, b))
                    else:
                        nums.append(int(part) - 1)

                if not nums:
                    QMessageBox.warning(self, "Invalid Input", "No valid page numbers!")
                    return

                text = self.pdf_model.extract_text_from_pages(nums)

            if not text or not text.strip():
                QMessageBox.warning(self, "Warning", "No text found to summarize!")
                return

            # Check text length
            if len(text) > 100000:
                QMessageBox.warning(
                    self, "Warning",
                    "Text too long! Please select fewer pages.\n"
                    f"Current length: {len(text)} characters\n"
                    "Maximum: 100,000 characters"
                )
                return

            # Get summary options
            summary_type = self.combo_type.currentData()
            language = self.combo_language.currentData()

            # Show loading status
            self.label_status.setText("Summarizing with Gemini AI...")
            self.text_summary.clear()

            # Start summarization in separate thread
            self.summarize_thread = GeminiSummarizeThread(text, api_key, summary_type, language)
            self.summarize_thread.finished.connect(self.on_summarize_finished)
            self.summarize_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error preparing text: {e}")

    def on_summarize_finished(self, summary, success, error_message):
        if success:
            self.text_summary.setPlainText(summary)
            self.label_status.setText("Summary complete!")
        else:
            self.label_status.setText(f"Error: {error_message}")
            QMessageBox.warning(self, "Summarization Error", error_message)

    def copy_summary(self):
        """Copy summary to clipboard"""
        summary = self.text_summary.toPlainText()

        if summary:
            clipboard = QApplication.clipboard()
            clipboard.setText(summary)
            self.label_status.setText("Copied to clipboard!")
        else:
            QMessageBox.warning(self, "Warning", "No summary to copy!")

    def save_summary(self):
        """Save summary to file"""
        summary = self.text_summary.toPlainText()

        if not summary:
            QMessageBox.warning(self, "Warning", "No summary to save!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Summary", "", "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                self.label_status.setText(f"Saved to: {file_path}")
                QMessageBox.information(self, "Success", f"Summary saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot save file: {e}")