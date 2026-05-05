import requests

# Twój adres URL z API Gateway
URL = "https://2m33d7cna7.execute-api.eu-central-1.amazonaws.com/predict"

data = {
    "car_data": {
        "year": 2014,
        "make": "Ford",
        "model": "Fusion",
        "body": "sedan",
        "state": "ca",
        "condition": 4,
        "odometer": 50000
    }
}

print("Wysyłam zapytanie do AWS...")
response = requests.post(URL, json=data)

if response.status_code == 200:
    # API Gateway HTTP API czasami zwraca body jako string wewnątrz JSONa
    # zależy jak Lambda sformatowała odpowiedź
    print(f"Sukces! Przewidywana cena: {response.json()}")
else:
    print(f"Błąd {response.status_code}: {response.text}")