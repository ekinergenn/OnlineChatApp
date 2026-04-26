from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:

    content: str
    sender_id: int
    timestamp: int

    message_id: Optional[int] = None

    # İsteğe bağlı alanlar (Opsiyonel)
    img_url: Optional[str] = None

    # Mesajı okuyanların ID'lerini tutacak liste. Başlangıçta boş.
    is_read_id: List[int] = field(default_factory=list)