from dataclasses import dataclass, field
from typing import List
from models.chat import Chat


@dataclass
class Community(Chat):
    community_id: int=0

    # Topluluğa üye olan kullanıcıların ID'lerini (veya nesnelerini) tutar.
    # Döngüsel içe aktarmayı (circular import) önlemek için User ID (int) tutmak en güvenlisidir.
    users: List[int] = field(default_factory=list)

    def add_user(self, user_id: int):
        if user_id not in self.users:
            self.users.append(user_id)