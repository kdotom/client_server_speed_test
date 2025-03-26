# Network Speed Test Tool

A lightweight client-server Python utility for measuring network speeds between two systems on your network.

## Overview

This tool provides a straightforward way to measure upload and download speeds between two computers on the same network. It works by establishing a TCP connection between a server and client, then transferring a fixed amount of data (1GB by default) to measure throughput in both directions.

## Features

- Simple client-server architecture
- Measures both download and upload speeds
- Progress bar visualization with tqdm
- Clean shutdown handling with signal interrupts
- Customizable data transfer size
- Companion shell script for file transfer over SSH

## Requirements

- Python 3.x
- tqdm library (`pip install tqdm`)
- For shell script: 
  - Linux/macOS: SSH access and rsync installed on both systems
  - Windows: SSH access and one of: WSL, Git Bash, PowerShell with OpenSSH, or PuTTY tools

## Usage

### Setting up the Server

Run the script in server mode on the computer that will act as the speed test server:

```bash
python speedtest.py server
```

To find the server's IP address (needed by clients):

```bash
hostname -I
```

### Running the Client

On another computer, run the script in client mode, specifying the server's IP address:

```bash
python speedtest.py <server_ip>
```

For example:

```bash
python speedtest.py 192.168.1.100
```

If running locally for testing:

```bash
python speedtest.py localhost
```

## How It Works

1. The server listens for incoming connections on port 5000 (default)
2. The client connects to the server and requests a download test
3. The server sends 1GB of data to the client, which measures the speed
4. The client then requests an upload test and sends 1GB of data to the server
5. Results are displayed in Mbps (Megabits per second)

## Configuration

You can modify the following constants in the script:

- `CHUNK_SIZE`: Size of data chunks transferred (default: 8192 bytes)
- `TOTAL_SIZE`: Total amount of data to transfer (default: 1GB)

## Troubleshooting

- **Connection refused**: Make sure the server is running and the IP address is correct
- **Low speeds**: Check for network congestion or other bandwidth-intensive applications
- **Script crashes**: Ensure you have the latest version of Python and tqdm installed

## File Transfer Script

A companion shell script `shell_script.sh` is included for easy file transfers over SSH:

```bash
# Simple shell script which copies a file to an IP + specific directory over a network connection.
# Note: ssh should be enabled for the target machine. 
rsync --progress -h filename user@address:/path/for/file
```

### Usage on Linux/macOS:

1. Make the script executable:
   ```bash
   chmod +x shell_script.sh
   ```

2. Edit the script to replace:
   - `filename` with the name of the file you want to transfer
   - `user` with the username on the target machine
   - `address` with the IP address of the target machine
   - `/path/for/file` with the destination directory

3. Run the script:
   ```bash
   ./shell_script.sh
   ```

### Usage on Windows:

Windows users can use one of the following approaches:

1. **Using WSL (Windows Subsystem for Linux)**:
   - Install WSL and a Linux distribution
   - Follow the Linux instructions above

2. **Using Git Bash**:
   - Install Git for Windows which includes Git Bash
   - Use the same rsync command in the Git Bash terminal

3. **Using PowerShell**:
   - Install OpenSSH for Windows
   - Use SCP instead of rsync:
   ```powershell
   scp -r filename user@address:/path/for/file
   ```

4. **Using Windows native command prompt with pscp** (PuTTY SCP):
   - Download PuTTY tools including pscp
   - Use the following command:
   ```cmd
   pscp -r filename user@address:/path/for/file
   ```

The Linux/macOS script uses rsync with the `--progress` flag to show transfer progress and `-h` to display file sizes in a human-readable format. Windows alternatives like scp and pscp provide similar functionality but with slightly different syntax.

## Notes

- This tool measures raw TCP throughput, which may differ from application-specific speeds
- Results can vary based on network conditions, system load, and other factors
- For accurate results, minimize other network activity during testing
- The file transfer scripts require SSH access to be configured between the machines
- Windows users may need to install additional tools for SSH file transfers