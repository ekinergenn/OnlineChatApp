from dataclasses import dataclass, field
from typing import List, Optional
from models.message import Message


@dataclass
class Chat:
    chat_id: int=0
    # UI'da göstermek için bir isim alanı eklemek iyi bir pratiktir
    name: str = ""

    # Sohbetin içindeki mesajların listesi
    messages: List[Message] = field(default_factory=list)

    def add_message(self, message: Message):
        """Sohbete yeni bir mesaj ekler."""
        self.messages.append(message)

    def get_last_message(self) -> Optional[Message]:
        """Arayüzde son mesajı göstermek için yardımcı fonksiyon."""
        if self.messages:
            return self.messages[-1]
        return None