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
    def parse_packet(data: bytes) -> dict:
        """Ağdan gelen ham byte verisini anlamlı bir Python sözlüğüne çevirir."""
        try:
            # Gelen byte'ı stringe çevir ve ayırıcıyı temizle
            json_str = data.decode('utf-8').split("<END>")[0]
            return json.loads(json_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[PROTOKOL HATASI] Bozuk paket alındı: {e}")
            return {"type": "error", "payload": {}}