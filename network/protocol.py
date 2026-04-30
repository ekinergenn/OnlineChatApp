import json

class Protocol:
    """Ağ üzerinden gidecek verilerin standart paket yapısını tanımlar."""
    
    @staticmethod
    def create_packet(packet:dict) -> bytes:
        """Sözlük yapısındaki veriyi ağda taşınacak byte formatına çevirir."""
        # JSON'a çevir ve sonuna özel bir ayırıcı ekle (paketlerin birbirine karışmaması için)
        json_str = json.dumps(packet) + "<END>"
        return json_str.encode('utf-8')

    @staticmethod
    def parse_packet(data) -> dict:
        """Ağdan gelen veriyi anlamlı bir Python sözlüğüne çevirir."""
        try:
            # Gelen veri bytes ise stringe çevir, zaten str ise olduğu gibi kullan
            if isinstance(data, bytes):
                json_str = data.decode('utf-8')
            else:
                json_str = data
            
            # Not: Veri zaten handler tarafında <END> ile bölündüğü için tekrar bölmeye gerek yok
            return json.loads(json_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[PROTOKOL HATASI] Bozuk paket alındı: {e}")
            return {"type": "error", "payload": {}}