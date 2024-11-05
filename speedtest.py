# speedtest.py
# for server:
#     python speedtest.py server
# to see the IP, use:
#     hostname -I 
# for client:
#     python speedtest.py [server_ip]
import socket
import time
import threading
from datetime import datetime
from tqdm import tqdm

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
                test_type = client.recv(1024).decode()
                
                if test_type == 'download':
                    # Send size first
                    total_size = 8388608  # 8MB
                    client.send(str(total_size).encode())
                    client.recv(1024)  # Wait for ready signal
                    
                    # Send data in chunks
                    chunk_size = 8192
                    data = b'x' * chunk_size
                    bytes_sent = 0
                    
                    while bytes_sent < total_size:
                        sent = client.send(data)
                        bytes_sent += sent
                        
                    # Wait for completion acknowledgment
                    client.recv(1024)
                
                elif test_type == 'upload':
                    # Send ready for upload
                    total_size = int(client.recv(1024).decode())
                    client.send(b'ready')
                    
                    # Receive data
                    bytes_received = 0
                    while bytes_received < total_size:
                        remaining = total_size - bytes_received
                        chunk = client.recv(min(8192, remaining))
                        if not chunk:
                            break
                        bytes_received += len(chunk)
                    
                    # Send completion acknowledgment
                    client.send(b'done')
                    
                elif test_type == 'quit':
                    break
                    
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()

    def stop(self):
        self.running = False
        self.sock.close()

class SpeedTestClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.total_size = 8388608  # 8MB in bytes
        self.chunk_size = 8192

    def connect(self):
        self.sock.connect((self.host, self.port))

    def test_download(self):
        # Signal download test
        self.sock.send(b'download')
        
        # Get total size
        total_size = int(self.sock.recv(1024).decode())
        self.sock.send(b'ready')
        
        total_received = 0
        start_time = time.time()
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            while total_received < total_size:
                try:
                    chunk = self.sock.recv(min(8192, total_size - total_received))
                    if not chunk:
                        break
                    chunk_size = len(chunk)
                    total_received += chunk_size
                    pbar.update(chunk_size)
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
        
        # Send completion acknowledgment
        self.sock.send(b'done')
        
        duration = time.time() - start_time
        speed_mbps = (total_received * 8) / (1000000 * duration)
        return speed_mbps

    def test_upload(self):
        # Signal upload test
        self.sock.send(b'upload')
        
        # Send total size and wait for ready
        self.sock.send(str(self.total_size).encode())
        response = self.sock.recv(1024).decode()
        if response != 'ready':
            raise Exception("Server not ready for upload")
        
        # Prepare data chunk
        data = b'x' * self.chunk_size
        bytes_sent = 0
        start_time = time.time()
        
        with tqdm(total=self.total_size, unit='B', unit_scale=True, desc="Uploading") as pbar:
            while bytes_sent < self.total_size:
                try:
                    remaining = self.total_size - bytes_sent
                    to_send = data[:min(self.chunk_size, remaining)]
                    sent = self.sock.send(to_send)
                    bytes_sent += sent
                    pbar.update(sent)
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
        
        # Wait for completion acknowledgment
        response = self.sock.recv(1024)
        if response != b'done':
            raise Exception("Upload not properly acknowledged")
        
        duration = time.time() - start_time
        speed_mbps = (bytes_sent * 8) / (1000000 * duration)
        return speed_mbps

    def close(self):
        try:
            self.sock.send(b'quit')
        except:
            pass
        self.sock.close()

def run_speed_test(server_host='localhost'):
    print(f"Starting speed test to {server_host}...")
    client = SpeedTestClient(host=server_host)
    
    try:
        client.connect()
        print(f"Connected to server at {server_host}")
        
        # Test download speed
        print("\nTesting download speed...")
        download_speed = client.test_download()
        print(f"Download speed: {download_speed:.2f} Mbps")
        
        # Test upload speed
        print("\nTesting upload speed...")
        upload_speed = client.test_upload()
        print(f"Upload speed: {upload_speed:.2f} Mbps")
        
        # Print summary
        print("\nTest Summary:")
        print(f"{'=' * 30}")
        print(f"Download: {download_speed:.2f} Mbps")
        print(f"Upload:   {upload_speed:.2f} Mbps")
        print(f"{'=' * 30}")
        
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
            print("\nShutting down server...")
            server.stop()
    else:
        # Run as client
        server_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        run_speed_test(server_host)
