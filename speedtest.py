# speedtest.py

# for server:
# python speedtest.py server
# for client:
# python speedtest.py [server_ip]


import socket
import time
import threading
from datetime import datetime

class SpeedTestServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.running = False

    def start(self):
        self.running = True
        self.sock.listen(1)
        print(f"Server listening on {self.host}:{self.port}")
        
        while self.running:
            client, addr = self.sock.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client,))
            client_thread.start()

    def handle_client(self, client):
        try:
            while True:
                # Receive test type (upload or download)
                test_type = client.recv(1024).decode()
                
                if test_type == 'download':
                    # Send data for download test
                    chunk_size = 8192
                    data = b'x' * chunk_size
                    start_time = time.time()
                    
                    for _ in range(1000):  # Send approximately 8MB
                        client.send(data)
                    
                    # Wait for client acknowledgment
                    client.recv(1024)
                
                elif test_type == 'upload':
                    # Receive data for upload test
                    total_received = 0
                    start_time = time.time()
                    
                    while total_received < 8388608:  # 8MB
                        data = client.recv(8192)
                        if not data:
                            break
                        total_received += len(data)
                    
                    client.send(b'ACK')
                
                elif test_type == 'quit':
                    break
                    
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()

    def stop(self):
        self.running = False
        self.sock.close()

# client.py
class SpeedTestClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.host, self.port))

    def test_download(self):
        # Signal download test
        self.sock.send(b'download')
        
        total_received = 0
        start_time = time.time()
        
        while total_received < 8388608:  # 8MB
            data = self.sock.recv(8192)
            if not data:
                break
            total_received += len(data)
        
        duration = time.time() - start_time
        speed_mbps = (total_received * 8) / (1000000 * duration)  # Convert to Mbps
        
        # Send acknowledgment
        self.sock.send(b'ACK')
        return speed_mbps

    def test_upload(self):
        # Signal upload test
        self.sock.send(b'upload')
        
        chunk_size = 8192
        data = b'x' * chunk_size
        start_time = time.time()
        
        for _ in range(1000):  # Send approximately 8MB
            self.sock.send(data)
        
        # Wait for server acknowledgment
        self.sock.recv(1024)
        
        duration = time.time() - start_time
        speed_mbps = (8388608 * 8) / (1000000 * duration)  # Convert to Mbps
        return speed_mbps

    def close(self):
        self.sock.send(b'quit')
        self.sock.close()

def run_speed_test(server_host='localhost'):
    print("Starting speed test...")
    client = SpeedTestClient(host=server_host)
    
    try:
        client.connect()
        
        # Test download speed
        print("\nTesting download speed...")
        download_speed = client.test_download()
        print(f"Download speed: {download_speed:.2f} Mbps")
        
        # Test upload speed
        print("\nTesting upload speed...")
        upload_speed = client.test_upload()
        print(f"Upload speed: {upload_speed:.2f} Mbps")
        
    except Exception as e:
        print(f"Error during speed test: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        # Run as server
        server = SpeedTestServer()
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
        # Run as client
        server_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        run_speed_test(server_host)
