import requests
import pandas as pd
from datetime import datetime
from utils.alchemy_client import get_token_transfers
from config import ALCHEMY_API_KEY, ETHERSCAN_API_KEY

ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

# ---------- UTILS ----------

def get_block_number_by_timestamp(timestamp: int) -> int:
    """
    Получает номер блока по UNIX timestamp через Etherscan API V2.
    """
    url = (
        f"https://api.etherscan.io/v2/api"
        f"?chainid=1"
        f"&module=block"
        f"&action=getblocknobytime"
        f"&timestamp={timestamp}"
        f"&closest=before"
        f"&apikey={ETHERSCAN_API_KEY}"
    )

    res = requests.get(url)
    data = res.json()

    if not data.get("status") or data["status"] != "1":
        msg = data.get("message", "Unknown error")
        result = data.get("result", "")
        raise ValueError(f"Etherscan V2 API error: {msg}. Result: {result}")

    result = data.get("result")
    if isinstance(result, dict) and "blockNumber" in result:
        return int(result["blockNumber"])
    elif isinstance(result, str) and result.isdigit():
        return int(result)
    else:
        raise ValueError(f"Unexpected Etherscan API format: {result}")

def date_to_timestamp(date_str: str) -> int:
    """Преобразует дату (YYYY-MM-DD) в UNIX timestamp"""
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

def is_valid_contract(addr: str) -> bool:
    """Проверяет, что адрес похож на корректный Ethereum контракт"""
    return addr.startswith("0x") and len(addr) == 42

# ---------- MAIN ANALYSIS ----------

def analyze_token(contract, start_date, end_date):
    # Валидация контракта
    if not is_valid_contract(contract):
        print("❌ Ошибка: некорректный адрес контракта. Пример: 0xdAC17F958D2ee523a2206206994597C13D831ec7")
        return

    # Валидация дат
    try:
        start_ts = date_to_timestamp(start_date)
        end_ts = date_to_timestamp(end_date)
    except ValueError:
        print("❌ Ошибка формата даты. Используй формат YYYY-MM-DD, например 2025-10-31.")
        return

    if end_ts <= start_ts:
        print("❌ Дата конца должна быть позже даты начала.")
        return

    print("⏳ Получаем блоки по датам...")
    try:
        start_block = get_block_number_by_timestamp(start_ts)
        end_block = get_block_number_by_timestamp(end_ts)
    except ValueError as e:
        print(f"❌ Ошибка при получении блоков: {e}")
        return

    print(f"📦 Блоки: {start_block} → {end_block}")
    print("🔍 Загружаем транзакции токена...")

    transfers = get_token_transfers(contract.lower(), start_block, end_block)
    df = pd.DataFrame(transfers)

    if df.empty:
        print("⚠️ Нет транзакций за этот период.")
        return

    # Приводим поля к стандартному виду
    df.rename(columns={"from": "fromAddress", "to": "toAddress"}, inplace=True)

    # Проверка наличия ключевых столбцов
    for col in ["fromAddress", "toAddress", "value"]:
        if col not in df.columns:
            raise KeyError(f"❌ В ответе Alchemy нет поля '{col}'. Проверь формат get_token_transfers().")

    # Заменяем None на 0 и приводим к float
    df["value"] = df["value"].fillna(0).astype(float)

    inflow = df.groupby("toAddress")["value"].sum()
    outflow = df.groupby("fromAddress")["value"].sum()

    balances = inflow.sub(outflow, fill_value=0)
    top = balances.sort_values(ascending=False).head(10)

    print("\n🏆 Топ-10 кошельков по чистому притоку токенов:")
    for i, (addr, val) in enumerate(top.items(), 1):
        print(f"{i:2d}. {addr} — {val:,.4f}")

# ---------- ENTRY POINT ----------

if __name__ == "__main__":
    print("=== 🧠 Token Flow Analyzer ===")
    contract = input("Введите адрес контракта токена: ").strip()
    start_date = input("Введите дату начала (YYYY-MM-DD): ").strip()
    end_date = input("Введите дату конца (YYYY-MM-DD): ").strip()

    analyze_token(contract, start_date, end_date)
