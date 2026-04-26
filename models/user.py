from dataclasses import dataclass, field
from typing import List, Dict
from models.chat import Chat
from models.community import Community


@dataclass
class User:
    # Veritabanında eşleşmesi için user_id eklemek önemlidir
    user_id: int
    name: str
    surname: str
    email: str
    password: str
    tel: str

    # Kullanıcının dahil olduğu birebir sohbetler ve topluluklar
    my_chats: List[Chat] = field(default_factory=list)
    my_comm: List[Community] = field(default_factory=list)

    # Kullanıcının rolleri (Örn: {"admin": "true", "moderator": "false"})
    my_roles: Dict[str, str] = field(default_factory=dict)