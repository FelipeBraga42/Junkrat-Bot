import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import asyncio
import random

# --- CÓDIGO DO KEEP_ALIVE EMBUTIDO (Para o Render.com ou Replit) ---
# Importa o Flask, necessário para criar o servidor web
from flask import Flask
from threading import Thread

# Cria o app Flask (o web server)
# O Gunicorn/Render procura por este objeto 'app'
app = Flask('')

# Rota/Página que o UptimeRobot irá "pingar"
@app.route('/')
def home():
    return "WOOHOO! O Bot Junkrat está ONLINE e pronto para a EXPLOSÃO! 💥"

# Função que inicia o servidor em um thread separado (se necessário, como no Replit)
def run():
  # Roda na porta padrão do Render (ou Replit)
  # Quando usando Gunicorn/Render, esta função 'run' não é usada diretamente.
  # O Gunicorn/Render inicia o 'app' através do Procfile: web: gunicorn main:app
  pass

# Função para ser chamada no código principal (usada se for rodar localmente ou no Replit sem Gunicorn)
def keep_alive():  
    t = Thread(target=run)
    t.start()
# --- FIM DO CÓDIGO KEEP_ALIVE ---


# --- 1. CONFIGURAÇÃO DO BOT ---

# Os tokens são lidos das Variáveis de Ambiente (Secrets do Replit ou Environment Variables do Render)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_BOT_TOKEN:
    print("ERRO: O token do Discord (DISCORD_BOT_TOKEN) não foi encontrado.")
    # Não usamos exit() para permitir que a parte web (Flask) seja iniciada, se necessário.

# Adiciona help_command=None para DESATIVAR o comando 'help' embutido do Discord.py
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

# Inicializa o cliente Gemini
gemini_client = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_client = genai.Client()
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
        # Esta é uma função síncrona, não precisa de asyncio.to_thread aqui.
        chat = gemini_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=Junkrat_Personality
            )
        )
        chat_sessions[user_id] = chat
    return chat_sessions[user_id]


# --- 3. DADOS DAS LOOT BOX (ITENS ÉPICOS E LENDÁRIOS) ---
# Listas baseadas nos dados que você forneceu.
# Usei apenas uma pequena parte de cada lista para manter o código curto e limpo.
epic_items = [
    "Na Mosca", "Girassol", "Ampulheta", "Rosa Amaldiçoada", "Balão de Rúgbi", 
    "Filhote de Lobo", "Máscara Enfurecida", "Chocolate Quente", "Macaco Gélido", 
    "Grilo de Felicitação", "Sakura", "Carinho em uma Raposa", "Agente de Missão", 
    "Gravidade Zero", "Gato Preto Alado", "Zumbí", "Dançante", "Líder Circense",
    "Chuva de balões", "Recompensa"
]

legendary_items = [
    "Huitzilopochtli", "Submarino", "Gladiador", "Vênus", "Ciborgue: 76", 
    "Grafite", "Jazzy", "Demônio", "Paconha", "Corvo Branco", "Dardo Venenoso", 
    "Gata Neon", "Junkrat", "Mágica", "Roadhog", "Demônio do Pântano", "Vulcânico", 
    "Dr. Frankenstein", "Esqueleto", "Faraó", "Dragonesa", "Wukong", "Qinglong", 
    "Tigre", "Tropical", "Krampus", "Rei Rato", "Imperatriz do Gelo", "Rainha Gladiadora",
    "Quebra-nozes", "Caranguejo"
]


# --- 4. COMANDOS DO BOT ---

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
        name="Comandos de Loot Box (Tesouros!)",
        value=f"`>loot` : Tenta abrir uma caixa de saque. Chances: Lendário (5%), Épico (15%), Raro (30%), Comum (50%).\n`>moeda` : Joga uma moeda (Cara ou Coroa).\n`>dado <lados>` : Rola um dado (Ex: `>dado 6` ou `>dado 20`).",
        inline=False
    )
    embed.add_field(
        name="Outros Comandos",
        value="`>help` : Exibe este guia explosivo.",
        inline=False
    )
    embed.set_footer(text="BOOOM! O caos nunca dorme!")
    await ctx.send(embed=embed)


@bot.command(name='loot')
async def loot_box(ctx):
    """Simula a abertura de uma caixa de saque."""
    chance = random.uniform(0, 100)
    
    if chance < 5:  # 5% de chance Lendário
        rarity = "Lendário 🟡"
        item = random.choice(legendary_items)
        cor = 0xFFD700
    elif chance < 20:  # 15% de chance Épico (5% + 15% = 20%)
        rarity = "Épico 🟣"
        item = random.choice(epic_items)
        cor = 0x8A2BE2
    elif chance < 50:  # 30% de chance Raro (20% + 30% = 50%)
        rarity = "Raro 🔵"
        item = "Créditos ou Emote Raro"
        cor = 0x1E90FF
    else: # 50% de chance Comum
        rarity = "Comum ⚪"
        item = "Spray ou Voz Comum"
        cor = 0xFFFFFF
        
    embed = discord.Embed(
        title="💥 CAIXA DE SAQUE EXPLODINDO! 💥",
        description=f"WOOHOO! Você desenterrou um tesouro!",
        color=cor
    )
    embed.add_field(name=f"Você tirou um item {rarity}!", value=f"**Item Encontrado:** {item}", inline=False)
    embed.set_footer(text="HA-HA-HA! Mais tesouros para mim!")
    await ctx.send(f"Olha só, {ctx.author.mention}!", embed=embed)


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


# --- 5. CHAT COM IA (CORREÇÃO CRÍTICA DO ASYNC) ---

@bot.event
async def on_message(message):
    # Ignora mensagens de outros bots
    if message.author.bot:
        return

    # Processa comandos (como >help, >loot, etc.)
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
            # CORREÇÃO CRÍTICA: Envolver a função síncrona com asyncio.to_thread
            # Isso impede que a função Gemini bloqueie o loop assíncrono do Discord.py
            
            async with message.channel.typing():
                # Usa asyncio.to_thread para não travar o bot
                response = await asyncio.to_thread(chat.send_message, user_message)
                
            await message.channel.send(response.text)

        except Exception as e:
            print(f"Erro ao interagir com Gemini: {e}")
            await message.channel.send(f"Ah, droga! Parece que a mina falhou! Um erro! BOOOOM! ({e})")

# --- 6. EXECUÇÃO ---

# O 'keep_alive' é chamado para iniciar o servidor web (útil no Replit, ignorado pelo Gunicorn/Render, mas inofensivo)
keep_alive() 

if DISCORD_BOT_TOKEN:
    try:
        # Tenta rodar o bot
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("ERRO DE LOGIN: O Token do Discord (DISCORD_BOT_TOKEN) é inválido. Verifique o Secrets.")
    except Exception as e:
        print(f"Ocorreu um erro geral durante a execução: {e}")
else:
    print("O Token do Discord não foi fornecido. O Bot Discord não foi iniciado.")