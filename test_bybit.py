import time
import hmac
import hashlib
import requests

API_KEY = "G61cpkA8yoSIAKSgvd"
API_SECRET = "pEC57xZpc9XZs6wpNj6uNRcn8RjVa2RaIBaQ"

print("\n🚨 LECTURE DU PARE-FEU BRUT 🚨")

timestamp = str(int(time.time() * 1000))
recv_window = "5000"
params = "accountType=UNIFIED"

payload = timestamp + API_KEY + recv_window + params
signature = hmac.new(
    bytes(API_SECRET, 'utf-8'), 
    bytes(payload, 'utf-8'), 
    hashlib.sha256
).hexdigest()

headers = {
    'X-BAPI-API-KEY': API_KEY,
    'X-BAPI-SIGN': signature,
    'X-BAPI-TIMESTAMP': timestamp,
    'X-BAPI-RECV-WINDOW': recv_window,
}

url = "https://api-testnet.bybit.com/v5/account/wallet-balance?" + params

try:
    response = requests.get(url, headers=headers)
    print(f"Code HTTP renvoyé : {response.status_code}")
    print(f"Texte brut renvoyé par Bybit :\n{response.text[:500]}") # On affiche les 500 premiers caractères
except Exception as e:
    print(f"Erreur : {e}")