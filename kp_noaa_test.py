import requests

URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

response = requests.get(URL)
print(response.status_code)

data = response.json()
print(data[:5])
