import socket
import threading
import json

# Sunucuya bağlanmak için ayarlar (Server ile aynı olmalı)
HOST = '127.0.0.1'
PORT = 12345

def receive_messages(client_socket):
    """Sunucudan gelen mesajları arka planda sürekli dinleyen fonksiyon."""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            
            # Gelen byte verisini sözlüğe (dict) çevir
            message_dict = json.loads(data.decode('utf-8'))
            print(f"\n[{message_dict['sender']}]: {message_dict['content']}")
            
        except Exception as e:
            print("[HATA] Sunucu ile bağlantı koptu!")
            client_socket.close()
            break

def start_client():
    """İstemciyi başlatır ve sunucuya bağlar."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((HOST, PORT))
        print("[BAŞARILI] Sunucuya bağlanıldı!")
    except ConnectionRefusedError:
        print("[HATA] Sunucu bulunamadı. Lütfen önce server.py dosyasını çalıştırın.")
        return

    # Kullanıcıdan isim al (Senin projende bu arayüzden logReg_service üzerinden gelecek)
    username = input("Kullanıcı adınızı girin: ")

    # Sunucudan gelen mesajları dinlemek için ayrı bir thread başlat
    # Aksi takdirde input() fonksiyonu mesaj gelmesini engeller (Uygulama donar)
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    # Kullanıcıdan sürekli mesaj alıp sunucuya gönder
    while True:
        msg_content = input("")
        if msg_content.lower() == 'cikis':
            client.close()
            break
            
        # Gönderilecek veriyi JSON protokolü şeklinde paketle
        message_packet = {
            "type": "chat_message",
            "sender": username,
            "content": msg_content
        }
        
        # Paketlenen veriyi stringe ve ardından byte'a çevirip gönder
        json_data = json.dumps(message_packet)
        client.send(json_data.encode('utf-8'))

if __name__ == "__main__":
    start_client()