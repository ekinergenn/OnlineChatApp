class ChatbotController:
    def __init__(self, main_page, chatbot_service):
        self.main_page = main_page
        self.chatbot_service = chatbot_service

        self.main_page.send_chatbot_message_signal.connect(self.handle_user_message)
        self.main_page.reset_chatbot_signal.connect(self.chatbot_service.reset_conversation)
        self.chatbot_service.response_signal.connect(self.on_bot_response)

    def handle_user_message(self, text: str):
        self.main_page.add_chatbot_message_to_ui(text, is_mine=True)
        self.main_page.add_chatbot_message_to_ui("⏳ Yanıt bekleniyor...", is_mine=False, is_typing=True)
        self.chatbot_service.send_message(text)

    def on_bot_response(self, response: str):
        self.main_page.remove_chatbot_typing_indicator()
        self.main_page.add_chatbot_message_to_ui(response, is_mine=False)