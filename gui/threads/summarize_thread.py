from PyQt5.QtCore import QThread, pyqtSignal
from google import genai


class GeminiSummarizeThread(QThread):
    finished = pyqtSignal(str, bool, str)  # summary, success, error_message

    def __init__(self, text, api_key, summary_type, language):
        super().__init__()
        self.text = text
        self.api_key = api_key
        self.summary_type = summary_type
        self.language = language

    def run(self):
        try:
            client = genai.Client(api_key=self.api_key)

            prompts = {
                'brief': {
                    'en': f"Summarize the following text briefly in a few sentences:\n\n{self.text}",
                    'vi': f"Tóm tắt ngắn gọn văn bản sau trong vài câu:\n\n{self.text}"
                },
                'detailed': {
                    'en': f"Provide a detailed summary of the following text, including main points and key details:\n\n{self.text}",
                    'vi': f"Tóm tắt chi tiết văn bản sau, bao gồm các điểm chính và chi tiết quan trọng:\n\n{self.text}"
                },
                'bullet': {
                    'en': f"Summarize the following text in bullet points:\n\n{self.text}",
                    'vi': f"Tóm tắt văn bản sau dưới dạng danh sách gạch đầu dòng:\n\n{self.text}"
                },
                'key_points': {
                    'en': f"Extract the key points from the following text:\n\n{self.text}",
                    'vi': f"Trích xuất các điểm chính từ văn bản sau:\n\n{self.text}"
                }
            }

            prompt = (
                prompts
                .get(self.summary_type, prompts['brief'])
                .get(self.language, prompts['brief']['en'])
            )

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            if response and response.text:
                self.finished.emit(response.text.strip(), True, "")
            else:
                self.finished.emit("", False, "No response from Gemini")

        except Exception as e:
            self.finished.emit("", False, f"Error: {str(e)}")
