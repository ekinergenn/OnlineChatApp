from google import genai
from google.genai import types
import time


class Chatbot:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.history = []
        self.system_instruction = (
            "Sen OnlineChat uygulamasının yardımcı asistanısın. "
            "Kullanıcılara hem uygulama hakkında (sohbet başlatma, engelleme, ayarlar, profil vb.) "
            "hem de genel konularda yardımcı olabilirsin. "
            "Türkçe konuş, kısa ve net cevaplar ver."
        )


    def send_message(self, user_message: str) -> str:
        try:
            self.history.append(
                types.Content(role="user", parts=[types.Part(text=user_message)])
            )

            # 3 kez dene
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=self.history,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_instruction,
                        )
                    )
                    reply = response.text
                    self.history.append(
                        types.Content(role="model", parts=[types.Part(text=reply)])
                    )
                    return reply

                except Exception as e:
                    if "503" in str(e) and attempt < 2:
                        time.sleep(3)  # 3 saniye bekle, tekrar dene
                        continue
                    raise e

        except Exception as e:
            # Hata olursa geçmişe eklenen kullanıcı mesajını geri al
            if self.history and self.history[-1].role == "user":
                self.history.pop()
            return f"[HATA] Gemini API hatası: {e}"

    def reset(self):
        self.history = []