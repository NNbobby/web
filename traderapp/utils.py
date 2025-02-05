import requests
import json

def get_bybit_p2p_rate():
    # URL для отправки запроса
    url = "https://api2.bybit.com/fiat/otc/item/online"
    # Полезная нагрузка (payload) для запроса
    payload = {
        "userId": "",
        "tokenId": "USDT",          # Валюта USDT
        "currencyId": "RUB",        # Валюта RUB
        "payment": ["585"],         # Код платежной системы (Сбербанк)
        "side": "1",                # Покупка (BUY, side=1)
        "size": "10",               # Максимальное количество предложений
        "page": "1",                # Номер страницы
        "amount": "50000",          # Сумма (в RUB)
        "vaMaker": False,
        "bulkMaker": False,
        "canTrade": False,
        "verificationFilter": 0,
        "sortType": "TRADE_PRICE",  # Сортировка по цене
        "paymentPeriod": [],
        "itemRegion": 1
    }
    
    try:
        # Отправляем POST-запрос с Payload в JSON-формате
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()  # Бросить исключение при ошибке HTTP
        data = response.json()  # Преобразуем JSON-ответ в словарь

        # Извлекаем список предложений
        offers = data.get("result", {}).get("items", [])
        if not offers:
            print("Нет доступных предложений.")
            return None

        # Берём курс самого выгодного предложения (первое в списке)
        best_rate = float(offers[0]["price"])
        print(f"Лучший курс: {best_rate} RUB")
        return best_rate

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Ошибка обработки данных: {e}")
        return None

# Для теста
rate = get_bybit_p2p_rate()
