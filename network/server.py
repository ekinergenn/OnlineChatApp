import socket
import threading
import json

# Sunucu Ayarları
HOST = '127.0.0.1' # Kendi bilgisayarında test etmek için (Localhost)
PORT = 12345       # Boşta olan herhangi bir port numarası

# Bağlı olan tüm istemcileri (client) tutacağımız liste
clients = []

def broadcast(message, sender_socket):
    """Gelen mesajı mesajı gönderen hariç herkese iletir."""
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                # Eğer gönderirken hata çıkarsa (istemci aniden koptuysa) listeden çıkar
                clients.remove(client)

def handle_client(client_socket, address):
    """Her bir istemci için ayrı ayrı çalışacak dinleme fonksiyonu."""
    print(f"[YENİ BAĞLANTI] {address} bağlandı.")
    
    while True:
        try:
            # İstemciden veri bekle (1024 byte'a kadar)
            data = client_socket.recv(1024)
            if not data:
                break # Veri boş gelirse bağlantı kopmuş demektir
            
            # Gelen byte verisini JSON'a çevir (Opsiyonel ama profesyonel)
            decoded_data = data.decode('utf-8')
            print(f"[MESAJ ALINDI] {address}: {decoded_data}")
            
            # Mesajı diğer herkese dağıt
            broadcast(data, client_socket)
            
        except ConnectionResetError:
            break
            
    print(f"[BAĞLANTI KOPTU] {address} ayrıldı.")
    clients.remove(client_socket)
    client_socket.close()

def start_server():
    """Sunucuyu başlatır ve bağlantıları dinler."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[BAŞLATILDI] Sunucu {HOST}:{PORT} adresinde dinleniyor...")

    while True:
        # Yeni bir bağlantı gelene kadar burada bekler
        client_socket, address = server.accept()
        clients.append(client_socket)
        
        # Yeni istemci için yeni bir thread (iş parçacığı) başlat
        # Bu sayede sunucu donmadan diğer istemcileri de bekleyebilir
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()
        print(f"[AKTİF BAĞLANTI SAYISI] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()