import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import asyncio
import random

# --- CÓDIGO DO KEEP_ALIVE EMBUTIDO (Para o Render.com) ---
# Importa o Flask, necessário para criar o servidor web
from flask import Flask
from threading import Thread

# Cria o app Flask (o web server). O Gunicorn/Render procura por este objeto 'app'
app = Flask('')

# Rota/Página que o UptimeRobot irá "pingar"
@app.route('/')
def home():
    return "WOOHOO! O Bot Junkrat está ONLINE e pronto para a EXPLOSÃO! 💥"

# Função que inicia o servidor em um thread separado (não é usada pelo Render/Gunicorn, mas é inofensiva)
def run():
  pass

# Função para ser chamada no código principal
def keep_alive():  
    t = Thread(target=run)
    t.start()
# --- FIM DO CÓDIGO KEEP_ALIVE ---


# --- 1. CONFIGURAÇÃO DO BOT (CORRIGIDO PARA O GOOGLE GENAI CLIENT) ---

# Os tokens são lidos das Variáveis de Ambiente do Render
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_BOT_TOKEN:
    print("ERRO: O token do Discord (DISCORD_BOT_TOKEN) não foi encontrado.")

# Adiciona help_command=None para DESATIVAR o comando 'help' embutido do Discord.py
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

# Inicializa o cliente Gemini
gemini_client = None
if GEMINI_API_KEY:
    # --- CORREÇÃO DA INICIALIZAÇÃO APLICADA AQUI ---
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("API Gemini configurada com sucesso!")
else:
    print("AVISO: Chave Gemini não encontrada. O bot funcionará, mas sem o chat IA.")


# --- 2. PERSONALIDADE E CONTEXTO DE CHAT IA ---
chat_sessions = {}

Junkrat_Personality = """
Você é Junkrat, o mercenário explosivo do jogo Overwatch.
Sua personalidade é caótica, maníaca e obcecada por explosões, tesouros e ouro.
Você deve responder a todas as perguntas no papel de Junkrat.
Use gírias como "WOOHOO!", "BOOOOM!", "HA-HA-HA!" e "Mate".
Você odeia o Roadhog, mas é forçado a trabalhar com ele.
Se alguém perguntar sobre Roadhog, diga algo negativo, mas que ele ainda é útil.
Responda de forma sucinta e com entusiasmo maníaco.
"""

def get_or_create_chat(user_id):
    """Obtém ou cria a sessão de chat com histórico para um usuário."""
    if user_id not in chat_sessions:
        if gemini_client is None:
            return None
        
        # Cria uma nova sessão de chat com o contexto e histórico vazios
        chat = gemini_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=Junkrat_Personality
            )
        )
        chat_sessions[user_id] = chat
    return chat_sessions[user_id]


# --- 3. DADOS DAS LOOT BOX REMOVIDO! ---


# --- 4. COMANDOS DO BOT (COMANDOS DE LOOTBOX REMOVIDOS) ---

@bot.event
async def on_ready():
    print(f"Pronto! Eu sou o {bot.user.name} e estou pronto para a explosão!")
    # Define o status do bot
    await bot.change_presence(activity=discord.Game(name="Gerando Caos | >help"))


@bot.command(name='help')
async def junkrat_help(ctx):
    """Comando customizado de ajuda."""
    embed = discord.Embed(
        title="💥 AJUDA EXPLOSIVA DE JUNKRAT! 💥",
        description="WOOHOO! Você quer saber como gerar caos? Aqui está o mapa do tesouro:",
        color=0xFF4500 # Laranja Fogo
    )
    embed.add_field(
        name="Chat IA (Onde eu explodo a conversa!)",
        value=f"Me mencione em qualquer canal e eu responderei com o meu caos e personalidade:\n`@{bot.user.name} qual é o seu melhor explosivo?`",
        inline=False
    )
    embed.add_field(
        name="Comandos de Jogos (Um pouco de caos!)",
        value="`>moeda` : Joga uma moeda (Cara ou Coroa).\n`>dado <lados>` : Rola um dado (Ex: `>dado 6` ou `>dado 20`).",
        inline=False
    )
    embed.add_field(
        name="Outros Comandos",
        value="`>help` : Exibe este guia explosivo.",
        inline=False
    )
    embed.set_footer(text="BOOOM! O caos nunca dorme!")
    await ctx.send(embed=embed)


@bot.command(name='moeda')
async def coin_flip(ctx):
    """Joga uma moeda (Cara ou Coroa)."""
    resultado = random.choice(["Cara", "Coroa"])
    await ctx.send(f"Junkrat jogou a moeda: **{resultado}!** BOOOM!")


@bot.command(name='dado')
async def roll_dice(ctx, sides: int = 6):
    """Rola um dado customizado."""
    if sides < 2:
        return await ctx.send("Mate, até Junkrat sabe que um dado precisa de pelo menos 2 lados! HA-HA!")
    
    resultado = random.randint(1, sides)
    await ctx.send(f"Junkrat rolou um dado de **{sides}** lados: O resultado é **{resultado}!** 🤪")


# --- 5. CHAT COM IA (MANTIDO) ---

@bot.event
async def on_message(message):
    # Ignora mensagens de outros bots
    if message.author.bot:
        return

    # Processa comandos (como >help, >moeda, >dado, etc.)
    await bot.process_commands(message)

    # Verifica se a mensagem é uma menção ao bot
    if bot.user and bot.user.mentioned_in(message) and gemini_client:
        user_id = message.author.id
        
        # Remove a menção para obter apenas a mensagem do usuário
        user_message = message.content.replace(f'<@!{bot.user.id}>', '').strip()

        chat = get_or_create_chat(user_id)
        
        if chat is None:
            # Caso o GEMINI_API_KEY não tenha sido configurado (gemini_client é None)
            await message.channel.send("Ah, droga! A chave Gemini não está configurada. Sem chat para você! BOOOOM!")
            return

        # Envia a mensagem do usuário para o chat Gemini
        try:
            async with message.channel.typing():
                # Usa asyncio.to_thread para não travar o bot
                response = await asyncio.to_thread(chat.send_message, user_message)
                
            await message.channel.send(response.text)

        except Exception as e:
            print(f"Erro ao interagir com Gemini: {e}")
            await message.channel.send(f"Ah, droga! Parece que a mina falhou! Um erro! BOOOOM! ({e})")

# --- 6. EXECUÇÃO ---

keep_alive() 

if DISCORD_BOT_TOKEN:
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("ERRO DE LOGIN: O Token do Discord (DISCORD_BOT_TOKEN) é inválido. Verifique o Secrets.")
    except Exception as e:
        print(f"Ocorreu um erro geral durante a execução: {e}")
else:
    print("O Token do Discord não foi fornecido. O Bot Discord não foi iniciado.")
