# agendar.py
# Automated barbershop appointment scheduler via CashBarber API
import os
import requests
from datetime import datetime, timedelta

# =========================================
# CONFIGURATION - all via environment variables
# =========================================

EMAIL       = os.environ.get("CASHBARBER_EMAIL", "")
PASSWORD    = os.environ.get("CASHBARBER_PASSWORD", "")
TENANT      = os.environ.get("CASHBARBER_TENANT", "")
BRANCH_ID   = int(os.environ.get("CASHBARBER_BRANCH_ID", "0"))
BARBER_ID   = int(os.environ.get("CASHBARBER_BARBER_ID", "0"))
SERVICES    = [int(x) for x in os.environ.get("CASHBARBER_SERVICES", "").split(",") if x]
START_TIME  = os.environ.get("CASHBARBER_START_TIME", "10:20")
END_TIME    = os.environ.get("CASHBARBER_END_TIME", "11:20")
BOT_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID     = os.environ.get("TELEGRAM_CHAT_ID", "")

BASE_URL    = "https://api.cashbarber.com.br"

# =========================================

def validate_config():
    missing = []
    if not EMAIL:       missing.append("CASHBARBER_EMAIL")
    if not PASSWORD:    missing.append("CASHBARBER_PASSWORD")
    if not TENANT:      missing.append("CASHBARBER_TENANT")
    if not BRANCH_ID:   missing.append("CASHBARBER_BRANCH_ID")
    if not BARBER_ID:   missing.append("CASHBARBER_BARBER_ID")
    if not SERVICES:    missing.append("CASHBARBER_SERVICES")
    if not BOT_TOKEN:   missing.append("TELEGRAM_BOT_TOKEN")
    if not CHAT_ID:     missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        exit(1)

    print("Configuration validated. Proceeding...")

def login():
    print("Logging in...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "captchaToken": None
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://cashbarber.com.br",
                "Referer": "https://cashbarber.com.br/",
                "X-Context": "cliente",
                "X-Tenant": TENANT,
            }
        )
    except requests.exceptions.RequestException as e:
        print(f"Network error during login: {e}")
        send_telegram(f"⚠️ Erro de conexão durante o login: {e}")
        exit(1)

    if response.status_code != 200:
        print(f"Login failed. Status: {response.status_code}")
        print(f"Response: {response.text}")
        send_telegram(f"⚠️ Falha no login. Status: {response.status_code}")
        exit(1)
    
    token = response.headers.get("X-Session-Token")
    if not token:
        print("Token not found in login response.")
        send_telegram("⚠️ Token não encontrado na resposta do login.")
        exit(1)

    print("Login successful.")
    return token

def next_saturday():
    today = datetime.now()
    days_until_saturday = (5 - today.weekday() + 7) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday = today + timedelta(days=days_until_saturday)
    return saturday.strftime("%Y-%m-%d")

def already_scheduled(headers, date):
    url = f"{BASE_URL}/api/{TENANT}/web/agendamentos/list?page=1"
    
    try:
        response = requests.post(url, json={}, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching appointments: {e}")
        send_telegram(f"⚠️ Erro de conexão ao buscar agendamentos: {e}")
        exit(1)

    if response.status_code != 200:
        print(f"Error fetching appointments. Status: {response.status_code}")
        print("Aborting for safety. Please check manually.")
        exit(1)

    data = response.json()
    upcoming = data.get("futuros", {}).get("data", [])

    for appointment in upcoming:
        if date in appointment.get("age_inicio", "") and appointment.get("age_status") == "Agendado":
            print(f"Appointment already exists for {date}.")
            print(f"Existing ID: {appointment.get('id')} | Time: {appointment.get('age_inicio')}")
            return appointment

    return None

def schedule():
    print("=" * 50)
    print("CASHBARBER - AUTOMATED SCHEDULER")
    print("=" * 50)

    validate_config()

    token = login()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-Context": "cliente",
        "X-Tenant": TENANT,
        "Origin": "https://cashbarber.com.br",
        "Referer": "https://cashbarber.com.br/",
    }

    date = next_saturday()

    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    date_formatted = date_datetime.strftime('%d/%m/%Y')
    print(f"\nNext Saturday: {date_formatted}")

    existing = already_scheduled(headers, date)
    
    if existing:
        send_telegram(
            f"📅 O Agendamento para {date_formatted} já existe!\n"
            f"🆔 ID: {existing.get('id')}\n"
            f"🕐 Horário: {format_datetime(existing.get('age_inicio'))}"
        )
        exit(0)
        
    start = f"{date} {START_TIME}:00"
    end   = f"{date} {END_TIME}:00"

    print(f"No existing appointment found. Scheduling from {START_TIME} to {END_TIME}...")

    payload = {
        "age_id_filial": BRANCH_ID,
        "age_id_user": BARBER_ID,
        "age_inicio": start,
        "age_fim": end,
        "age_sem_preferencia": 0,
        "servicos": SERVICES
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/{TENANT}/web/agendamentos",
            json=payload,
            headers=headers
        )
    except requests.exceptions.RequestException as e:
        print(f"Network error while scheduling appointment: {e}")
        send_telegram(f"⚠️ Erro de conexão ao agendar: {e}")
        exit(1)

    print(f"\nStatus: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        print("Appointment successfully scheduled!")
        print(f"ID: {result.get('id')}")
        print(f"Status: {result.get('age_status')}")
        print(f"Start: {format_datetime(result.get('age_inicio'))}")
        print(f"End: {format_datetime(result.get('age_fim'))}")

        send_telegram(
            f"✅ Agendamento Realizado com Sucesso!\n"
            f"📅 Data: {format_datetime(result.get('age_inicio'))}\n"
            f"🕐 Término: {format_datetime(result.get('age_fim'))}\n"
            f"🆔 ID: {result.get('id')}"
        )
    elif response.status_code == 401:
        print("Invalid credentials.")
    else:
        print("Scheduling failed.")
        print(f"Response: {response.text}")
        send_telegram(
            f"⚠️ Horário das {START_TIME} indisponível para {date_formatted}.\n"
            f"Acesse o site para escolher outro horário:\n"
             "https://cashbarber.com.br/barbeariadeluno/inicio"
        )


def send_telegram(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Network error while sending Telegram message: {e}")
        return None
    return response

def format_datetime(dt_string):
    # Converte "2026-06-13 12:00:00" em objeto datetime
    dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    # Formata como "13/06/2026 às 12:00"
    return dt.strftime("%d/%m/%Y às %H:%M")

if __name__ == "__main__":
   schedule()