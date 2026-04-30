from PyQt5.QtCore import QObject, pyqtSignal, QThread
from chatbot.chatbot import Chatbot


class ChatbotWorker(QThread):
    """Gemini API çağrısını ayrı thread'de yapar, UI donmasın diye."""
    response_ready = pyqtSignal(str)

    def __init__(self, chatbot: Chatbot, message: str):
        super().__init__()
        self.chatbot = chatbot
        self.message = message

    def run(self):
        response = self.chatbot.send_message(self.message)
        self.response_ready.emit(response)


class ChatbotService(QObject):
    response_signal = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        self.chatbot = Chatbot(api_key)
        self._worker = None

    def send_message(self, message: str):
        """Mesajı Gemini'ye gönderir, yanıt gelince response_signal fırlatır."""
        self._worker = ChatbotWorker(self.chatbot, message)
        self._worker.response_ready.connect(self.response_signal.emit)
        self._worker.start()

    def reset_conversation(self):
        self.chatbot.reset()