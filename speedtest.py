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
import statistics

CHUNK_SIZE = 8192
TOTAL_SIZE = 8*(1024)**3  # 8MB
PING_COUNT = 10  # Number of pings to average

class SpeedTestServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.running = False
        self.clients = []

    def start(self):
        self.running = True
        self.sock.listen(1)
        print(f"Server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client, addr = self.sock.accept()
                self.clients.append(client)
                print(f"Connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client,))
                client_thread.start()
            except socket.error:
                break

    def handle_client(self, client):
        try:
            while True:
                test_type = client.recv(1024).decode()
                
                if test_type == 'ping':
                    # Ping test - just echo back the timestamp
                    while True:
                        data = client.recv(1024)
                        if data == b'ping_done':
                            break
                        client.send(data)
                
                elif test_type == 'download':
                    client.send(str(TOTAL_SIZE).encode())
                    client.recv(1024)  # Wait for ready
                    
                    bytes_sent = 0
                    data = b'x' * CHUNK_SIZE
                    
                    while bytes_sent < TOTAL_SIZE and self.running:
                        sent = client.send(data)
                        bytes_sent += sent
                        
                    client.recv(1024)  # Wait for completion ack
                
                elif test_type == 'upload':
                    bytes_received = 0
                    client.send(b'ready')
                    
                    while bytes_received < TOTAL_SIZE and self.running:
                        chunk = client.recv(min(CHUNK_SIZE, TOTAL_SIZE - bytes_received))
                        if not chunk:
                            break
                        bytes_received += len(chunk)
                        if bytes_received % 1048576 == 0:
                            client.send(b'ack')
                    
                    client.send(b'done')
                
                elif test_type == 'quit':
                    break
                    
        except Exception as e:
            if self.running:
                print(f"Error handling client: {e}")
        finally:
            if client in self.clients:
                self.clients.remove(client)
            client.close()

    def stop(self):
        print("\nShutting down server...")
        self.running = False
        for client in self.clients[:]:
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                self.clients.remove(client)
            except:
                pass
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.sock.close()
        print("Server shutdown complete")

class SpeedTestClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.host, self.port))
        
    def test_latency(self):
        self.sock.send(b'ping')
        latencies = []
        
        # Perform multiple pings and measure round-trip time
        for _ in range(PING_COUNT):
            start_time = time.time()
            self.sock.send(str(time.time()).encode())
            self.sock.recv(1024)
            latency = (time.time() - start_time) * 1000  # Convert to ms
            latencies.append(latency)
            time.sleep(0.1)  # Small delay between pings
            
        self.sock.send(b'ping_done')
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        return min_latency, avg_latency, max_latency

    def test_download(self):
        self.sock.send(b'download')
        total_size = int(self.sock.recv(1024).decode())
        self.sock.send(b'ready')
        
        total_received = 0
        start_time = time.time()
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            while total_received < total_size:
                chunk = self.sock.recv(min(CHUNK_SIZE, total_size - total_received))
                if not chunk:
                    break
                chunk_size = len(chunk)
                total_received += chunk_size
                pbar.update(chunk_size)
        
        self.sock.send(b'done')
        
        duration = time.time() - start_time
        return (total_received * 8) / (1000000 * duration)

    def test_upload(self):
        self.sock.send(b'upload')
        response = self.sock.recv(1024)
        if response != b'ready':
            raise Exception("Server not ready")
        
        data = b'x' * CHUNK_SIZE
        bytes_sent = 0
        start_time = time.time()
        
        with tqdm(total=TOTAL_SIZE, unit='B', unit_scale=True, desc="Uploading") as pbar:
            while bytes_sent < TOTAL_SIZE:
                remaining = TOTAL_SIZE - bytes_sent
                to_send = min(CHUNK_SIZE, remaining)
                sent = self.sock.send(data[:to_send])
                bytes_sent += sent
                pbar.update(sent)
                
                if bytes_sent % 1048576 == 0:
                    self.sock.recv(1024)
        
        response = self.sock.recv(1024)
        if response != b'done':
            raise Exception("Upload not acknowledged")
        
        duration = time.time() - start_time
        return (bytes_sent * 8) / (1000000 * duration)

    def close(self):
        try:
            self.sock.send(b'quit')
            time.sleep(0.1)
            self.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            self.sock.close()

def run_speed_test(server_host='localhost'):
    print(f"Starting speed test to {server_host}...")
    client = SpeedTestClient(host=server_host)
    
    try:
        client.connect()
        print(f"Connected to server at {server_host}")
        
        print("\nMeasuring latency...")
        min_latency, avg_latency, max_latency = client.test_latency()
        print(f"Latency: min={min_latency:.1f}ms avg={avg_latency:.1f}ms max={max_latency:.1f}ms")
        
        print("\nTesting download speed...")
        print(f"Total data to download: {TOTAL_SIZE/1024/1024:.1f} MB")
        download_speed = client.test_download()
        print(f"Download speed: {download_speed:.2f} Mbps")
        
        print("\nTesting upload speed...")
        print(f"Total data to upload: {TOTAL_SIZE/1024/1024:.1f} MB")
        upload_speed = client.test_upload()
        print(f"Upload speed: {upload_speed:.2f} Mbps")
        
        print("\nTest Summary:")
        print(f"{'=' * 50}")
        print(f"Total data transferred: {(TOTAL_SIZE*2)/1024/1024:.1f} MB")
        print(f"Latency: {avg_latency:.1f}ms (min={min_latency:.1f}ms, max={max_latency:.1f}ms)")
        print(f"Download: {download_speed:.2f} Mbps")
        print(f"Upload:   {upload_speed:.2f} Mbps")
        print(f"{'=' * 50}")
        
    except Exception as e:
        print(f"Error during speed test: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    import sys
    import signal
    
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        server = SpeedTestServer()
        
        def signal_handler(signum, frame):
            server.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
        server_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        run_speed_test(server_host)
