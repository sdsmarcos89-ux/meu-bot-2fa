import discord
import pyotp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- SERVIDOR PARA O RENDER NÃO DORMIR ---
class HealthCheckHandler(BaseHTTPRequestHandler ):
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
async def twofa(ctx, secret: discord.Option(str, "Cole sua SECRET aqui")):
    try:
        totp = pyotp.TOTP(secret.replace(" ", "").upper())
        await ctx.respond(f"🔑 Seu código é: **{totp.now()}**", ephemeral=True)
    except:
        await ctx.respond("❌ Chave inválida!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot 2FA Online como {bot.user}")

if token:
    bot.run(token)
