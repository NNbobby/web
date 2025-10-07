import requests

def get_bybit_p2p_rate():
    url = "https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "amount": "50000",
        "tokenId": "USDT",       # Криптовалюта
        "currencyId": "RUB",     # Фиатная валюта
        "payment": ["382"],
        "side": "1",             # Покупка USDT
        "size": "10",              # Запрашиваем 10 предложений
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Проверим, есть ли сделки
        items = data.get("result", {}).get("items", [])
        if not items:
            print("API не возвращает предложения.")
            return None
        else:
            best_rate = float(items[0]["price"])
            print(f"Лучший курс: {best_rate} RUB")
            return best_rate

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к API: {e}")

rate = get_bybit_p2p_rate()
