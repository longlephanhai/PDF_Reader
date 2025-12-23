from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QMessageBox, QApplication
)
from gui.threads.translate_thread import TranslateThread


class TranslateDialog(QDialog):
    def __init__(self, parent, selected_text):
        super().__init__(parent)
        self.label_status = None
        self.text_translated = None
        self.text_original = None
        self.selected_text = selected_text
        self.translated_text = ""
        self.translate_thread = None

        self.setWindowTitle("Translate Text")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Language selection
        lang_layout = QHBoxLayout()

        lang_layout.addWidget(QLabel("From:"))
        self.combo_source = self.create_language_combo()
        self.combo_source.setCurrentText("English")
        lang_layout.addWidget(self.combo_source)

        lang_layout.addWidget(QLabel("To:"))
        self.combo_target = self.create_language_combo()
        self.combo_target.setCurrentText("Vietnamese")
        lang_layout.addWidget(self.combo_target)

        # Swap button
        btn_swap = QPushButton("⇄")
        btn_swap.setMaximumWidth(40)
        btn_swap.clicked.connect(self.swap_languages)
        lang_layout.addWidget(btn_swap)

        layout.addLayout(lang_layout)

        # Original text
        layout.addWidget(QLabel("Original Text:"))
        self.text_original = QTextEdit()
        self.text_original.setPlainText(self.selected_text)
        self.text_original.setMaximumHeight(150)
        layout.addWidget(self.text_original)

        # Translate button
        btn_translate = QPushButton("🌐 Translate")
        btn_translate.clicked.connect(self.do_translate)
        layout.addWidget(btn_translate)

        # Translated text
        layout.addWidget(QLabel("Translated Text:"))
        self.text_translated = QTextEdit()
        self.text_translated.setReadOnly(True)
        self.text_translated.setPlaceholderText("Translation will appear here...")
        layout.addWidget(self.text_translated)

        # Status label
        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        # Buttons
        button_layout = QHBoxLayout()

        btn_copy = QPushButton("Copy Translation")
        btn_copy.clicked.connect(self.copy_translation)
        button_layout.addWidget(btn_copy)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        button_layout.addWidget(btn_close)

        layout.addLayout(button_layout)

    def create_language_combo(self):
        combo = QComboBox()

        languages = [
            ("English", "en"),
            ("Vietnamese", "vi"),
            ("Chinese (Simplified)", "zh-CN"),
            ("Chinese (Traditional)", "zh-TW"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("French", "fr"),
            ("German", "de"),
            ("Spanish", "es"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Russian", "ru"),
            ("Arabic", "ar"),
            ("Thai", "th"),
            ("Indonesian", "id"),
            ("Hindi", "hi"),
        ]

        for name, code in languages:
            combo.addItem(name, code)

        return combo

    def swap_languages(self):
        source_idx = self.combo_source.currentIndex()
        target_idx = self.combo_target.currentIndex()

        self.combo_source.setCurrentIndex(target_idx)
        self.combo_target.setCurrentIndex(source_idx)

        # Swap texts
        self.text_original.toPlainText()
        translated = self.text_translated.toPlainText()

        if translated:
            self.text_original.setPlainText(translated)
            self.text_translated.clear()

    def do_translate(self):
        text = self.text_original.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Warning", "Please enter text to translate!")
            return

        if len(text) > 5000:
            QMessageBox.warning(self, "Warning", "Text too long! Maximum 5000 characters.")
            return

        source_lang = self.combo_source.currentData()
        target_lang = self.combo_target.currentData()

        if source_lang == target_lang:
            QMessageBox.warning(self, "Warning", "Source and target languages are the same!")
            return

        # Show loading status
        self.label_status.setText("translating...")
        self.text_translated.clear()

        # Start translation in separate thread
        self.translate_thread = TranslateThread(text, source_lang, target_lang)
        self.translate_thread.finished.connect(self.on_translate_finished)
        self.translate_thread.start()

    def on_translate_finished(self, translated_text, success, error_message):
        if success:
            self.text_translated.setPlainText(translated_text)
            self.translated_text = translated_text
            self.label_status.setText("Translation complete!")
        else:
            self.label_status.setText(f"Error: {error_message}")
            QMessageBox.warning(self, "Translation Error", error_message)

    def copy_translation(self):
        translated = self.text_translated.toPlainText()

        if translated:
            clipboard = QApplication.clipboard()
            clipboard.setText(translated)
            self.label_status.setText("Copied to clipboard!")
        else:
            QMessageBox.warning(self, "Warning", "No translation to copy!")