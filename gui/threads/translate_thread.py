from PyQt5.QtCore import QThread, pyqtSignal
import requests


class TranslateThread(QThread):
    finished = pyqtSignal(str, bool, str)  # translated_text, success, error_message

    def __init__(self, text, source_lang, target_lang):
        super().__init__()
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang

    def run(self):
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': self.text,
                'langpair': f'{self.source_lang}|{self.target_lang}'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('responseStatus') == 200:
                    translated = data['responseData']['translatedText']
                    self.finished.emit(translated, True, "")
                else:
                    self.finished.emit("", False, "Translation service error")
            else:
                self.finished.emit("", False, f"HTTP Error: {response.status_code}")

        except requests.Timeout:
            self.finished.emit("", False, "Translation timeout")
        except Exception as e:
            self.finished.emit("", False, f"Error: {str(e)}")