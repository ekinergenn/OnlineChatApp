""" 
+---------------------------+
|           User            |
+---------------------------+
| - name: String            |
| - password: String        |
| - surname: String         |
| - email: String           |
| - tel: String             |
| - my_chats: List<Chat>    |
| - my_comm: List<Community>|
| - my_roles: Dict          |
+---------------------------+
             | 1
             |
             | ∞ (sahiptir)
             v
+---------------------------+             +---------------------------+
|           Chat            | 1         ∞ |          Message          |
+---------------------------+------------>+---------------------------+
| - chat_id: int            | (içerir)    | - content: String         |
| - messages: List<Message> |             | - sender_id: int          |
+---------------------------+             | - img_url: String         |
                                          | - timestamp: int          |
                                          | - is_read_id: List<int>   |
             ^                            +---------------------------+
             | (Kalıtım / Extends)
             |
+---------------------------+
|         Community         |
+---------------------------+
| - community_id: int       |
| - users: List<User>       |
+---------------------------+


1. models/ Katmanı (Veri Yapıları)
Burası uygulamanızın **"İsimler Sözlüğü"**dür. Sadece veri tutarlar, aksiyon almazlar.

Nasıl Kodlanmalı?

- Buradaki dosyalar (user.py, message.py, chat.py) sadece Sınıflardan (Class) oluşmalıdır.

- Python'daki @dataclass yapısını kullanmanız kodunuzu çok temizleştirir.

- Örnek message.py Planı: Sadece id, sender_id, receiver_id, content, timestamp, is_read gibi özellikleri (attribute) olmalı.

KESİNLİKLE YAPILMAMASI GEREKEN: Bu klasördeki hiçbir dosya veritabanına bağlanmamalı, ağa veri göndermemeli veya UI değiştirmemelidir. Sadece veriyi paketlemek veya açmak için kullanılırlar.

"""

