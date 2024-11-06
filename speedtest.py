import subprocess
import re
import statistics
import argparse
from typing import List, Tuple, Dict
from datetime import datetime

class WindowsTracert:
    def __init__(self, target_ip: str, max_hops: int = 30, timeout: int = 4000):
        self.target_ip = target_ip
        self.max_hops = max_hops
        self.timeout = timeout
        self.results: Dict[int, List[Tuple[str, List[int]]]] = {}

    def run_tracert(self) -> None:
        """Execute tracert command and parse results"""
        cmd = f'tracert -h {self.max_hops} -w {self.timeout} {self.target_ip}'
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            current_hop = 0
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                    
                self._parse_tracert_line(line)

    def _parse_tracert_line(self, line: str) -> None:
        """Parse individual tracert output line"""
        # Match hop number and IP address
        hop_match = re.match(r'\s*(\d+)', line)
        if not hop_match:
            return

        hop_num = int(hop_match.group(1))
        
        # Extract latency values and IP
        latencies = []
        ip_address = "*"  # Default for timeout/failure
        
        # Look for IP address and latency values
        ip_match = re.search(r'\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', line)
        if ip_match:
            ip_address = ip_match.group(1)
            
        # Find all latency values (in ms)
        latency_matches = re.findall(r'(\d+)ms', line)
        latencies = [int(ms) for ms in latency_matches]
        
        self.results[hop_num] = (ip_address, latencies)

    def generate_report(self) -> str:
        """Generate a formatted report of the traceroute results"""
        report = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report.append(f"Traceroute Report to {self.target_ip}")
        report.append(f"Generated at: {timestamp}")
        report.append("-" * 80)
        report.append(f"{'Hop':4} {'IP Address':16} {'Min':6} {'Avg':6} {'Max':6} {'Loss%':6} {'Samples'}")
        report.append("-" * 80)
        
        for hop_num in sorted(self.results.keys()):
            ip_address, latencies = self.results[hop_num]
            
            if not latencies:  # If no successful responses
                report.append(f"{hop_num:3d}  {'*':15} {'---':6} {'---':6} {'---':6} {'100%':6} 0")
                continue
                
            loss_percent = (3 - len(latencies)) / 3 * 100  # Calculate packet loss
            
            min_latency = min(latencies)
            avg_latency = round(statistics.mean(latencies))
            max_latency = max(latencies)
            
            report.append(
                f"{hop_num:3d}  {ip_address:15} {min_latency:6d} {avg_latency:6d} "
                f"{max_latency:6d} {loss_percent:5.0f}% {len(latencies)}"
            )
            
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Windows Traceroute with Latency Analysis')
    parser.add_argument('ip', help='Target IP address')
    parser.add_argument('--max-hops', type=int, default=30, help='Maximum number of hops')
    parser.add_argument('--timeout', type=int, default=4000, help='Timeout in milliseconds')
    
    args = parser.parse_args()
    
    tracer = WindowsTracert(
        target_ip=args.ip,
        max_hops=args.max_hops,
        timeout=args.timeout
    )
    
    print(f"\nTracing route to {args.ip}...")
    tracer.run_tracert()
    print("\n" + tracer.generate_report())

if __name__ == "__main__":
    main()
