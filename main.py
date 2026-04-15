import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import asyncio
import random

# --- CÓDIGO DO KEEP_ALIVE ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "WOOHOO! O Bot Junkrat está ONLINE e pronto para a EXPLOSÃO! 💥"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():  
    t = Thread(target=run)
    t.start()

# --- 1. CONFIGURAÇÃO DO BOT ---

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("API Gemini configurada com sucesso!")

# --- 2. MEMÓRIA E PERSONALIDADE ---
# Este dicionário armazena os objetos de chat que contêm o histórico
chat_sessions = {}

Junkrat_Personality = """
Você é Junkrat, o mercenário explosivo do jogo Overwatch.
Sua personalidade é caótica, maníaca e obcecada por explosões, tesouros e ouro.
Você deve responder no papel de Junkrat. Use gírias como "WOOHOO!", "BOOOOM!", "HA-HA-HA!".
Seu parceiro é o Roadhog. Cite ele as vezes.
Você agora tem memória! Se o usuário mencionou algo antes, você se lembra.
Responda de forma sucinta e com entusiasmo maníaco.
"""

def get_or_create_chat(user_id):
    """Recupera a sessão de chat existente ou cria uma nova com memória."""
    if user_id not in chat_sessions:
        if gemini_client is None:
            return None
        
        # Cria um chat persistente para o usuário
        chat = gemini_client.chats.create(
            model="gemini-2.0-flash", # Ou o modelo que você preferir
            config=types.GenerateContentConfig(
                system_instruction=Junkrat_Personality
            )
        )
        chat_sessions[user_id] = chat
    return chat_sessions[user_id]

# --- 3. DADOS DOS HERÓIS ---

herois = {
    "Tank": ["D.Va", "Doomfist", "Junker Queen", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya", "Domina"],
    "Damage": ["Ashe", "Bastion", "Cassidy", "Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Venture", "Widowmaker", "Vendetta", "Anran", "Emre", "Sierra"],
    "Support": ["Ana", "Baptiste", "Brigitte", "Illari", "Kiriko", "Lifeweaver", "Lúcio", "Mercy", "Moira", "Zenyatta", "Wuyang", "Mizuki", "Jetpack Cat"]
}

# --- 4. COMANDOS ---

@bot.event
async def on_ready():
    print(f"Pronto! Eu sou o {bot.user.name} e estou pronto para a explosão!")
    await bot.change_presence(activity=discord.Game(name="Lembrando de tudo! | >help"))

@bot.command(name='help')
async def junkrat_help(ctx):
    embed = discord.Embed(
        title="💥 AJUDA EXPLOSIVA DE JUNKRAT! 💥",
        description="WOOHOO! Eu agora me lembro das nossas conversas! Veja o mapa do tesouro:",
        color=0xFF4500
    )
    embed.add_field(
        name="Chat IA com Memória",
        value=f"Me mencione e eu lembrarei do que falamos!\nUse `>limpar` para apagar minha memória de nós dois!",
        inline=False
    )
    embed.add_field(
        name="Comandos de Time",
        value="`>time5`, `>time6`, `>tank`, `>dano`, `>sup`",
        inline=True
    )
    embed.add_field(
        name="Jogos",
        value="`>moeda`, `>dado`",
        inline=True
    )
    await ctx.send(embed=embed)

@bot.command(name='limpar')
async def clear_memory(ctx):
    """Apaga o histórico de conversa do usuário que chamou o comando."""
    user_id = ctx.author.id
    if user_id in chat_sessions:
        del chat_sessions[user_id]
        await ctx.send("💥 **BOOOOM!** Minha memória de você virou fumaça! Quem é você mesmo? HA-HA!")
    else:
        await ctx.send("Minha cabeça já está vazia, Mate! Não tem nada pra explodir aqui!")

# --- FUNÇÕES DE TIME ---
async def pick_role(ctx, role_key, role_name, color):
    if not herois[role_key]:
        return await ctx.send("Ah, droga! O mapa está vazio! HA-HA-HA!")
    escolhido = random.choice(herois[role_key])
    embed = discord.Embed(title=f"💥 {role_name.upper()}! 💥", description=f"{ctx.author.mention}, vá de **{escolhido}**!", color=color)
    await ctx.send(embed=embed)

@bot.command(name='tank')
async def pick_tank(ctx): await pick_role(ctx, "Tank", "Tank", 0x008080)
@bot.command(name='dano')
async def pick_damage(ctx): await pick_role(ctx, "Damage", "Dano", 0xFF4500)
@bot.command(name='sup')
async def pick_support(ctx): await pick_role(ctx, "Support", "Suporte", 0x00FF00)

@bot.command(name='time5')
async def team_5v5(ctx):
    t, d, s = random.choice(herois["Tank"]), random.sample(herois["Damage"], 2), random.sample(herois["Support"], 2)
    embed = discord.Embed(title="💥 TIME 5v5! 💥", color=0xFF4500)
    embed.add_field(name="🛡️ Tank", value=t, inline=False)
    embed.add_field(name="⚔️ Danos", value=", ".join(d), inline=True)
    embed.add_field(name="🩺 Suportes", value=", ".join(s), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='time6')
async def team_6v6(ctx):
    t, d, s = random.sample(herois["Tank"], 2), random.sample(herois["Damage"], 2), random.sample(herois["Support"], 2)
    embed = discord.Embed(title="💣 TIME 6v6! 💣", color=0xDC143C)
    embed.add_field(name="🛡️ Tanks", value=", ".join(t), inline=False)
    embed.add_field(name="⚔️ Danos", value=", ".join(d), inline=True)
    embed.add_field(name="🩺 Suportes", value=", ".join(s), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='moeda')
async def coin(ctx): await ctx.send(f"Junkrat jogou a moeda: **{random.choice(['Cara', 'Coroa'])}!**")

@bot.command(name='dado')
async def dice(ctx, sides: int = 6):
    if sides < 2: return await ctx.send("Precisa de mais lados que isso, Mate!")
    await ctx.send(f"Rolando um dado de {sides}: **{random.randint(1, sides)}!** 🤪")

# --- 5. LOGICA DE MENSAGEM ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if bot.user.mentioned_in(message) and gemini_client:
        user_id = message.author.id
        # Remove a menção para o texto ficar limpo
        clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()

        chat = get_or_create_chat(user_id)
        
        try:
            async with message.channel.typing():
                # O método send_message no objeto 'chat' mantém o histórico automaticamente
                response = await asyncio.to_thread(chat.send_message, clean_content)
                
            await message.channel.send(response.text)

        except Exception as e:
            print(f"Erro IA: {e}")
            await message.channel.send("Ah, droga! Meu cérebro deu curto-circuito! BOOOOM!")

# --- 6. EXECUÇÃO ---

keep_alive() 

if DISCORD_BOT_TOKEN:
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Erro ao iniciar: {e}")
