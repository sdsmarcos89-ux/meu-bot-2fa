import discord
from discord.ui import Button, View, Modal, TextInput
import pyotp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- CÓDIGO PARA MANTER ONLINE NO RENDER ---
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
# -------------------------------------------

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# Janela que aparece ao clicar no botão
class Get2FAModal(Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, title="Gerar Código 2FA")
        self.add_item(TextInput(
            label="Chave Secreta (SECRET)", 
            placeholder="Cole aqui a chave secreta da sua conta...", 
            required=True
        ))

    async def callback(self, interaction: discord.Interaction):
        secret = self.children[0].value.replace(" ", "").upper()
        try:
            totp = pyotp.TOTP(secret)
            codigo = totp.now()
            await interaction.response.send_message(
                f"✅ Seu código 2FA é: `{codigo}`", 
                ephemeral=True # Só você verá essa mensagem
            )
        except:
            await interaction.response.send_message(
                "❌ Erro: Chave Secreta inválida. Verifique se copiou corretamente.", 
                ephemeral=True
            )

# Botão que fica no chat
class Simple2FAView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 RESGATAR CÓDIGO 2FA", style=discord.ButtonStyle.primary, custom_id="resgatar")
    async def resgatar(self, button, interaction):
        await interaction.response.send_modal(Get2FAModal())

@bot.event
async def on_ready():
    print(f"Bot pronto! Conectado como {bot.user}")
    bot.add_view(Simple2FAView())

@bot.slash_command(name="2fa", description="Abrir menu de resgate 2FA")
async def twofa(ctx):
    await ctx.respond("Clique no botão abaixo para gerar seu código 2FA:", view=Simple2FAView())

if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
