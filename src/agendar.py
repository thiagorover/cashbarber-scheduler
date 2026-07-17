# agendar.py
# Automated barbershop appointment scheduler via CashBarber API
import os
import requests
from notifiers import Notifier
from datetime import datetime, timedelta

# =============================================
# CONFIGURATION - all via environment variables
# =============================================

EMAIL       = os.environ.get("CASHBARBER_EMAIL", "")
PASSWORD    = os.environ.get("CASHBARBER_PASSWORD", "")
TENANT      = os.environ.get("CASHBARBER_TENANT", "")
BRANCH_ID   = int(os.environ.get("CASHBARBER_BRANCH_ID", "0"))
BARBER_NAME = os.environ.get("CASHBARBER_BARBER_NAME", "")
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
    if not BARBER_NAME: missing.append("CASHBARBER_BARBER_NAME")
    if not SERVICES:    missing.append("CASHBARBER_SERVICES")
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        exit(1)

    print("Configuration validated. Proceeding...")


# Class authentication to CashBarber
class CashBarberAuth:

    def __init__(self, email, password, tenant, notifier):
        self._email = email
        self._password = password
        self._tenant = tenant
        self._token = None
        self._notifier = notifier

    @property
    def headers(self):
        if not self._token:
            raise ValueError("Token is not set. Please login first.")
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://cashbarber.com.br",
            "Referer": "https://cashbarber.com.br/",
            "X-Context": "cliente",
            "X-Tenant": self._tenant,
        }
    
    def _login_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://cashbarber.com.br",
            "Referer": "https://cashbarber.com.br/",
            "X-Context": "cliente",
            "X-Tenant": self._tenant,
        }

    def login(self):
        print("Logging in...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": self._email,
                    "password": self._password,
                    "captchaToken": None
                },
                headers= self._login_headers()
            )
        except requests.exceptions.RequestException as e:
            print(f"Network error during login: {e}")
            self._notifier.notify(f"⚠️ Erro de conexão durante o login: {e}")
            exit(1)

        if response.status_code != 200:
            print(f"Login failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            self._notifier.notify(f"⚠️ Falha no login. Status: {response.status_code}")
            exit(1)
        
        self._token = response.headers.get("X-Session-Token")
        if not self._token:
            print("Token not found in login response.")
            self._notifier.notify("⚠️ Token não encontrado na resposta do login.")
            exit(1)

        print("Login successful.")
        return self._token


# Class to manage appointments
class AppointmentManager:
    
    def __init__(self, branch_id, barber_name, services, start_time, end_time, tenant, auth, notifier):
        self._branch_id = branch_id
        self._barber_name = barber_name
        self._services = services
        self._start_time = start_time
        self._end_time = end_time
        self._tenant = tenant
        self._auth = auth
        self._notifier = notifier

    @staticmethod
    def next_saturday():
        today = datetime.now()
        days_until_saturday = (5 - today.weekday() + 7) % 7
        
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = today + timedelta(days=days_until_saturday)
        
        return saturday.strftime("%Y-%m-%d")

    @staticmethod
    def format_datetime(dt_string):
        # Converte "2026-06-13 12:00:00" em objeto datetime
        dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
        # Formata como "13/06/2026 às 12:00"
        return dt.strftime("%d/%m/%Y às %H:%M") 
    
    def _resolve_barber_id(self) -> int:
        url = f"{BASE_URL}/api/{self._tenant}/web/filiais/{self._branch_id}/barbeiros"

        try:
            response = requests.get(url, headers=self._auth.headers)
        except requests.exceptions.RequestException as e:
            print(f"Network error while fetching barbers: {e}")
            self._notifier.notify(f"⚠️ Erro de conexão ao buscar barbeiros: {e}")
            exit(1)

        if response.status_code != 200:
            print(f"Error fetching barbers. Status: {response.status_code}")
            print("Aborting for safety. Please check manually.")
            exit(1)
        
        for barber in response.json():
            if barber['usu_name'].lower() == self._barber_name.lower():
                return barber['id']

        print(f"Barber '{self._barber_name}' not found.")
        self._notifier.notify(f"⚠️ Barbeiro '{self._barber_name}' não encontrado.")
        exit(1)



    def already_scheduled(self, date):
        url = f"{BASE_URL}/api/{self._tenant}/web/agendamentos/list?page=1"
        
        try:
            response = requests.post(url, json={}, headers=self._auth.headers)
        except requests.exceptions.RequestException as e:
            print(f"Network error while fetching appointments: {e}")
            self._notifier.notify(f"⚠️ Erro de conexão ao buscar agendamentos: {e}")
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
    

    def schedule(self):
        print("=" * 50)
        print("CASHBARBER - AUTOMATED SCHEDULER")
        print("=" * 50)

        date = AppointmentManager.next_saturday()

        date_datetime = datetime.strptime(date, "%Y-%m-%d")
        date_formatted = date_datetime.strftime('%d/%m/%Y')
        print(f"\nNext Saturday: {date_formatted}")

        existing = self.already_scheduled(date)
        
        if existing:
            self._notifier.notify(
                f"📅 O Agendamento para {date_formatted} já existe!\n"
                f"🆔 ID: {existing.get('id')}\n"
                f"🕐 Horário: {AppointmentManager.format_datetime(existing.get('age_inicio'))}"
            )
            exit(0)
            
        start = f"{date} {self._start_time}:00"
        end   = f"{date} {self._end_time}:00"

        print(f"No existing appointment found. Scheduling from {self._start_time} to {self._end_time}...")

        payload = {
            "age_id_filial": self._branch_id,
            "age_id_user": self._resolve_barber_id(),
            "age_inicio": start,
            "age_fim": end,
            "age_sem_preferencia": 0,
            "servicos": self._services
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/{self._tenant}/web/agendamentos",
                json=payload,
                headers=self._auth.headers
            )
        except requests.exceptions.RequestException as e:
            print(f"Network error while scheduling appointment: {e}")
            self._notifier.notify(f"⚠️ Erro de conexão ao agendar: {e}")
            exit(1)

        print(f"\nStatus: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            print("Appointment successfully scheduled!")
            print(f"ID: {result.get('id')}")
            print(f"Status: {result.get('age_status')}")
            print(f"Start: {AppointmentManager.format_datetime(result.get('age_inicio'))}")
            print(f"End: {AppointmentManager.format_datetime(result.get('age_fim'))}")

            self._notifier.notify(
                f"✅ Agendamento Realizado com Sucesso!\n"
                f"📅 Data: {AppointmentManager.format_datetime(result.get('age_inicio'))}\n"
                f"🕐 Término: {AppointmentManager.format_datetime(result.get('age_fim'))}\n"
                f"🆔 ID: {result.get('id')}"
            )
        elif response.status_code == 401:
            print("Invalid credentials.")
        else:
            print("Scheduling failed.")
            print(f"Response: {response.text}")
            self._notifier.notify(
                f"⚠️ Horário das {self._start_time} indisponível para {date_formatted}.\n"
                f"Acesse o site para escolher outro horário:\n"
                "https://cashbarber.com.br/barbeariadeluno/inicio"
            )


# Class for Telegram notifications
class TelegramNotifier(Notifier):
    
    # Constructor for TelegramNotifier
    def __init__(self, bot_token, chat_id):
        
        self._bot_token = bot_token
        self._chat_id = chat_id
        
    # Overridden method to send a notification via Telegram
    def notify(self, message):
        payload = {
            "chat_id": self._chat_id,
            "text": message
        }
        try:
            response = requests.post(f"https://api.telegram.org/bot{self._bot_token}/sendMessage", json=payload)
            if response.status_code != 200:
                print(f"Erro ao enviar notificação: {response.text}")
            return response
        except requests.exceptions.RequestException as e:
            print(f"Network error while sending Telegram message: {e}")


# Class for console notifications (for testing purposes)
class ConsoleNotifier(Notifier):
    
    # Overridden method to print notifications to the console
    def notify(self, message):
        print(f"Notification: {message}")


# Main orchestrator
if __name__ == "__main__":
   
    # Method to validate configuration before proceeding
    validate_config()

    # Decide to use Telegram or Console Local for notifications (Polymorphism)
    if BOT_TOKEN and CHAT_ID:
        notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)
        print("Using Telegram for notifications.")
    else:
        notifier = ConsoleNotifier()
        print("Using console for notifications.")

    # Initialize authentication and appointment manager
    auth = CashBarberAuth(EMAIL, PASSWORD, TENANT, notifier)
    
    # Initialize appointment manager with configuration
    appoint = AppointmentManager(BRANCH_ID, BARBER_NAME, SERVICES, START_TIME, END_TIME, TENANT, auth, notifier)

    # Call login and schedule methods
    auth.login()
    appoint.schedule()

