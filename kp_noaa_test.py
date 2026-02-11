import requests

URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

def get_latest_kp():
    response = requests.get(URL, timeout=5)
    response.raise_for_status()
    data = response.json()
    return float(data[-1][1])

if __name__ == "__main__":
    kp = get_latest_kp()
    print("Latest Kp:", kp)

