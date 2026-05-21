import discord
from discord.ui import Button, View, Modal, TextInput
import pyotp
import os
import json
import time
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CÓDIGO PARA MANTER ONLINE ---
class HealthCheckHandler(BaseHTTPRequestHandler ):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Online")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()
# ---------------------------------

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SECRETS_FILE = "totp_secrets.json"

def load_secrets():
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_secrets(secrets):
    with open(SECRETS_FILE, "w") as f:
        json.dump(secrets, f, indent=4)

TOTP_SECRETS = load_secrets()
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

class Add2FAModal(Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, title="Configurar Novo 2FA")
        self.add_item(TextInput(label="Nome do Serviço", placeholder="Ex: EpicGames, Google", required=True))
        self.add_item(TextInput(label="Chave Secreta (Secret Key)", placeholder="Cole aqui a chave que o site te deu", required=True))

    async def callback(self, interaction: discord.Interaction):
        service = self.children[0].value.lower()
        secret = self.children[1].value.replace(" ", "").upper() # Limpa espaços e coloca em maiúsculo
        
        try:
            # Testa se a chave é válida
            pyotp.TOTP(secret).now()
            TOTP_SECRETS[service] = secret
            save_secrets(TOTP_SECRETS)
            await interaction.response.send_message(f"✅ **{service}** configurado com sucesso!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Erro: A chave secreta que você colou parece inválida. Verifique e tente de novo.", ephemeral=True)

class Get2FAModal(Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, title="Gerar Código")
        self.add_item(TextInput(label="Nome do Serviço", placeholder="Ex: google", required=True))

    async def callback(self, interaction: discord.Interaction):
        service = self.children[0].value.lower()
        if service in TOTP_SECRETS:
            # Gera o código garantindo a sincronia de tempo
            totp = pyotp.TOTP(TOTP_SECRETS[service])
            codigo = totp.now()
            
            # Calcula quanto tempo falta para o código expirar
            tempo_restante = 30 - (int(time.time()) % 30)
            
            await interaction.response.send_message(
                f"🔑 Código para **{service}**: `{codigo}`\n"
                f"⏳ Expira em: `{tempo_restante}s`", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Serviço não encontrado.", ephemeral=True)

class TwoFAView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 Gerar Código", style=discord.ButtonStyle.primary, custom_id="gen")
    async def gen(self, button, interaction):
        await interaction.response.send_modal(Get2FAModal())

    @discord.ui.button(label="⚙️ Configurar Serviço", style=discord.ButtonStyle.success, custom_id="add")
    async def add(self, button, interaction):
        await interaction.response.send_modal(Add2FAModal())

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    bot.add_view(TwoFAView())

@bot.slash_command(name="2fa", description="Menu do Gerador 2FA")
async def twofa(ctx):
    await ctx.respond("📱 **Gerenciador de Autenticação 2FA**\nUse os botões abaixo:", view=TwoFAView())

if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
