# setup_session.py
# Usa o perfil real do Chrome já logado no Google
from playwright.sync_api import sync_playwright
import time

# Caminho do perfil do Chrome no Windows
CHROME_PROFILE = r"C:\Users\thiago.rover\AppData\Local\Google\Chrome\User Data"

print("Abrindo o Chrome com seu perfil real...")
print("O site vai abrir já logado. Faça o agendamento normalmente.")
print("Você tem 90 segundos.\n")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=CHROME_PROFILE,
        channel="chrome",
        headless=False,
    )

    page = context.new_page()
    page.goto('https://cashbarber.com.br/barbeariadeluno/inicio')
    page.wait_for_load_state('networkidle')

    time.sleep(90)

    context.storage_state(path='session.json')
    print("\nSessão salva com sucesso em session.json")

    context.close()