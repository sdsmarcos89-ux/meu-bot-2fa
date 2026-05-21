from dotenv import load_dotenv
load_dotenv()
# # bot.py
import discord
import pyotp
import os
import json

# Carrega o token do bot do Discord de uma variável de ambiente
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Define o caminho para o arquivo de armazenamento de segredos
SECRETS_FILE = 'totp_secrets.json'

# Função para carregar segredos de um arquivo
def load_secrets():
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Função para salvar segredos em um arquivo
def save_secrets(secrets):
    with open(SECRETS_FILE, 'w') as f:
        json.dump(secrets, f, indent=4)

# Carrega os segredos existentes ao iniciar o bot
TOTP_SECRETS = load_secrets()

# Inicializa o cliente do Discord com as intenções necessárias
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('Pronto para gerar códigos 2FA!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Comando para gerar um código 2FA
    if message.content.startswith('!2fa'):
        parts = message.content.split(' ')
        if len(parts) == 2:
            service_name = parts[1].lower()
            if service_name in TOTP_SECRETS:
                secret = TOTP_SECRETS[service_name]
                try:
                    totp = pyotp.TOTP(secret)
                    current_otp = totp.now()
                    await message.channel.send(f'O código 2FA para **{service_name}** é: `{current_otp}`')
                except Exception as e:
                    await message.channel.send(f'Erro ao gerar código 2FA para {service_name}: {e}')
            else:
                await message.channel.send(f'Serviço **{service_name}** não encontrado. Use `!list2fa` para ver os serviços configurados ou `!add2fa <nome_do_serviço>` para adicionar um novo.')
        else:
            await message.channel.send('Uso: `!2fa <nome_do_serviço>`')

    # Comando para adicionar um novo serviço 2FA (gera um novo segredo)
    elif message.content.startswith('!add2fa'):
        parts = message.content.split(' ')
        if len(parts) == 2:
            service_name = parts[1].lower()
            if service_name in TOTP_SECRETS:
                await message.channel.send(f'O serviço **{service_name}** já existe. Use `!update2fa <nome_do_serviço> <novo_segredo>` para atualizar ou `!remove2fa <nome_do_serviço>` para remover.')
            else:
                new_secret = pyotp.random_base32()
                TOTP_SECRETS[service_name] = new_secret
                save_secrets(TOTP_SECRETS)
                await message.channel.send(f'Novo serviço **{service_name}** adicionado com sucesso!\nSeu segredo 2FA é: `{new_secret}`\n**ATENÇÃO: Guarde este segredo em um local seguro! Ele não será exibido novamente.**')
        else:
            await message.channel.send('Uso: `!add2fa <nome_do_serviço>`')

    # Comando para remover um serviço 2FA
    elif message.content.startswith('!remove2fa'):
        parts = message.content.split(' ')
        if len(parts) == 2:
            service_name = parts[1].lower()
            if service_name in TOTP_SECRETS:
                del TOTP_SECRETS[service_name]
                save_secrets(TOTP_SECRETS)
                await message.channel.send(f'Serviço **{service_name}** removido com sucesso.')
            else:
                await message.channel.send(f'Serviço **{service_name}** não encontrado.')
        else:
            await message.channel.send('Uso: `!remove2fa <nome_do_serviço>`')

    # Comando para listar os serviços 2FA configurados
    elif message.content.startswith('!list2fa'):
        if TOTP_SECRETS:
            services = '\n'.join([f'- {s}' for s in TOTP_SECRETS.keys()])
            await message.channel.send(f'Serviços 2FA configurados:\n{services}')
        else:
            await message.channel.send('Nenhum serviço 2FA configurado ainda. Use `!add2fa <nome_do_serviço>` para adicionar um.')

# Executa o bot com o token
if DISCORD_BOT_TOKEN:
    client.run(DISCORD_BOT_TOKEN)
else:
    print("Erro: O token do bot do Discord não foi encontrado. Por favor, defina a variável de ambiente 'DISCORD_BOT_TOKEN'.")
