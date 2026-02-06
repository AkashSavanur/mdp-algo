import requests

URL = "http://192.168.56.1:8000/run"

payload = {
    "data": "75,25,T,2;125,75,L,3;35,145,T,4;95,155,R,5"
}

response = requests.post(URL, json=payload)

print("Status:", response.status_code)
print("Response:", response.json())
