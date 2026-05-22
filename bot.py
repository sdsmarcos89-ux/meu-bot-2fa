import discord
import pyotp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- SERVIDOR PARA O RENDER NÃO DORMIR ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot 2FA Online")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()
# ------------------------------------------

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
bot = discord.Bot()

@bot.slash_command(name="2fa", description="Gera código 2FA")
async def twofa(ctx: discord.ApplicationContext, secret: discord.Option(str, "Cole sua SECRET aqui")):
    # Defer a resposta para evitar timeout de interação do Discord
    await ctx.defer(ephemeral=True)
    try:
        totp = pyotp.TOTP(secret.replace(" ", "").upper())
        await ctx.followup.send(f"🔑 Seu código é: **{totp.now()}**", ephemeral=True)
    except pyotp.otp.OTPError:
        await ctx.followup.send("❌ Chave inválida! Por favor, verifique sua chave secreta e tente novamente.", ephemeral=True)
    except Exception as e:
        # Captura outras exceções inesperadas
        await ctx.followup.send(f"❌ Ocorreu um erro inesperado: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot 2FA Online como {bot.user}")

if token:
    bot.run(token)
