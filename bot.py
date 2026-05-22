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

# Definindo as cores para o tema roxo e preto
PURPLE_COLOR = 0x5865F2  # Um roxo padrão do Discord
BLACK_COLOR = 0x23272A  # Um cinza escuro que se assemelha ao preto

class SecretInputModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(
            label="Sua Chave Secreta 2FA", 
            placeholder="Cole sua chave secreta aqui...", 
            style=discord.InputTextStyle.short
        ))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        secret = self.children[0].value
        try:
            totp = pyotp.TOTP(secret.replace(" ", "").upper())
            code = totp.now()
            embed = discord.Embed(
                title="🔑 Seu Código 2FA",
                description=f"```\n{code}\n```\n\nEste código é válido por **30 segundos**. Gere um novo se expirar.",
                color=PURPLE_COLOR
            )
            embed.set_footer(text="Rockstar 2FA Bot")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except pyotp.otp.OTPError:
            embed = discord.Embed(
                title="❌ Chave Inválida!",
                description="Por favor, verifique se a chave secreta que você inseriu está correta e tente novamente.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Rockstar 2FA Bot")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro Inesperado",
                description=f"Ocorreu um erro ao gerar seu código: {e}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Rockstar 2FA Bot")
            await interaction.followup.send(embed=embed, ephemeral=True)

class Generate2FAButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None para o botão ser persistente

    @discord.ui.button(
        label="Gere 2fa code", 
        style=discord.ButtonStyle.primary, 
        custom_id="generate_2fa_button",
        emoji="🔑"
    )
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = SecretInputModal(title="Insira sua Chave Secreta 2FA")
        await interaction.response.send_modal(modal)

def get_rockstar_2fa_embed():
    embed = discord.Embed(
        title="🛡️ Rockstar Games e Autenticação de Dois Fatores (2FA)",
        description=(
            "A segurança da sua conta Rockstar Games é primordial. A Autenticação de Dois Fatores (2FA) adiciona uma camada extra de proteção, "
            "garantindo que apenas você possa acessar sua conta, mesmo que sua senha seja comprometida. "
            "Isso é crucial para proteger seus jogos, progresso e informações pessoais."
        ),
        color=PURPLE_COLOR
    )

    embed.add_field(
        name="O que é 2FA?",
        value=(
            "2FA é um método de segurança que exige duas formas de verificação para acessar uma conta. "
            "Normalmente, isso envolve algo que você sabe (sua senha) e algo que você tem (um código gerado por um aplicativo autenticador "
            "no seu celular ou gerado por este bot)."
        ),
        inline=False
    )

    embed.add_field(
        name="Como funciona o 2FA da Rockstar?",
        value=(
            "Ao ativar o 2FA na sua conta Rockstar Games, você precisará de um aplicativo autenticador "
            "para gerar códigos temporários. Cada vez que você fizer login, além da sua senha, será solicitado um desses códigos. "
            "Este bot ajuda a gerar esses códigos rapidamente através do botão abaixo."
        ),
        inline=False
    )

    embed.add_field(
        name="Sobre os Códigos 2FA e sua Duração",
        value=(
            "Os códigos 2FA são senhas de uso único baseadas em tempo. "
            "**Cada código é válido por apenas 30 segundos.** "
            "Após esse tempo, o código expira e um novo deve ser gerado. "
            "Certifique-se de inserir o código rapidamente no site da Rockstar."
        ),
        inline=False
    )

    embed.set_footer(text="Rockstar 2FA Bot | Segurança Máxima", icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Rockstar_Games_Logo.svg/1200px-Rockstar_Games_Logo.svg.png")
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Rockstar_Games_Logo.svg/1200px-Rockstar_Games_Logo.svg.png")

    return embed

bot = discord.Bot()

@bot.slash_command(name="setup2fa", description="Configura o painel interativo de 2FA")
async def setup2fa(ctx: discord.ApplicationContext):
    # Verificação básica de permissão (opcional, pode ser removida se quiser que qualquer um use)
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas administradores podem configurar o painel.", ephemeral=True)
    
    embed = get_rockstar_2fa_embed()
    view = Generate2FAButton()
    
    await ctx.respond("Painel configurado com sucesso!", ephemeral=True)
    await ctx.channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    # Registrar a view persistente para que o botão funcione após reiniciar o bot
    bot.add_view(Generate2FAButton())
    print(f"✅ Bot 2FA Online como {bot.user}")

if token:
    bot.run(token)
else:
    print("❌ Erro: DISCORD_BOT_TOKEN não encontrado.")
