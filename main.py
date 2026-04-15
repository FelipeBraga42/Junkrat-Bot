import discord
from discord.ext import commands
import google.generativeai as genai
import os
import asyncio
import random
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- KEEP_ALIVE (Render.com) ---
app = Flask('')
@app.route('/')
def home(): return "Junkrat está ONLINE! 💥"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():  
    Thread(target=run).start()

# --- 1. CONFIGURAÇÃO IA (FORÇANDO V1) ---

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    # Configura a chave e garante que não usemos a v1beta por acidente
    genai.configure(api_key=GEMINI_API_KEY)
    print("IA Junkrat configurada!")

# --- 2. PERSONALIDADE E MEMÓRIA ---
chat_sessions = {}

Junkrat_Personality = """
Você é Junkrat, o mercenário explosivo de Overwatch. 
Sua personalidade é caótica, maníaca e obcecada por explosões e ouro.
Responda sempre como Junkrat. Use gírias como "WOOHOO!", "BOOOOM!", "HA-HA-HA!".
Você tem memória das conversas! Seja sucinto e muito entusiasmado.
"""

def get_or_create_chat(user_id):
    if user_id not in chat_sessions:
        try:
            # SOLUÇÃO DO 404: Definimos o modelo e a instrução de sistema
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", # Se o erro persistir, tente "gemini-1.5-flash-002"
                system_instruction=Junkrat_Personality
            )
            # Iniciamos o chat com histórico vazio
            chat_sessions[user_id] = model.start_chat(history=[])
            print(f"Memória iniciada para: {user_id}")
        except Exception as e:
            print(f"Erro ao iniciar IA: {e}")
            return None
    return chat_sessions[user_id]

# --- 3. DADOS DOS HERÓIS ---

herois = {
    "Tank": ["D.Va", "Doomfist", "Junker Queen", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya", "Domina"],
    "Damage": ["Ashe", "Bastion", "Cassidy", "Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Venture", "Widowmaker", "Vendetta", "Anran", "Emre", "Sierra"],
    "Support": ["Ana", "Baptiste", "Brigitte", "Illari", "Kiriko", "Lifeweaver", "Lúcio", "Mercy", "Moira", "Zenyatta", "Wuyang", "Mizuki", "Jetpack Cat"]
}

# --- 4. CONFIGURAÇÃO DISCORD ---

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

@bot.event
async def on_ready():
    print(f"Pronto! Junkrat na área!")
    await bot.change_presence(activity=discord.Game(name="Lançando Granadas | >help"))

@bot.command(name='help')
async def junkrat_help(ctx):
    embed = discord.Embed(title="💥 AJUDA DO JUNKRAT! 💥", color=0xFF4500)
    embed.add_field(name="🧠 Conversar", value=f"Apenas me mencione: `@{bot.user.name}`", inline=False)
    embed.add_field(name="🎮 Comandos", value="`>time5`, `>time6`, `>tank`, `>dano`, `>sup`", inline=True)
    embed.add_field(name="🧹 Memória", value="`>limpar` reseta o papo", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='limpar')
async def clear_memory(ctx):
    if ctx.author.id in chat_sessions:
        del chat_sessions[ctx.author.id]
        await ctx.send("💥 **BOOOOM!** Esqueci tudo o que a gente conversou! HA-HA!")

# --- COMANDOS DE SORTEIO ---
@bot.command(name='tank')
async def pick_tank(ctx): await ctx.send(f"🛡️ Vá de **{random.choice(herois['Tank'])}**!")
@bot.command(name='dano')
async def pick_damage(ctx): await ctx.send(f"⚔️ Vá de **{random.choice(herois['Damage'])}**!")
@bot.command(name='sup')
async def pick_support(ctx): await ctx.send(f"🩺 Vá de **{random.choice(herois['Support'])}**!")

@bot.command(name='time5')
async def team_5v5(ctx):
    t, d, s = random.choice(herois["Tank"]), random.sample(herois["Damage"], 2), random.sample(herois["Support"], 2)
    embed = discord.Embed(title="💥 TIME 5v5! 💥", color=0xFF4500)
    embed.add_field(name="🛡️ Tank", value=t, inline=False)
    embed.add_field(name="⚔️ Danos", value=f"{d[0]}, {d[1]}", inline=True)
    embed.add_field(name="🩺 Suportes", value=f"{s[0]}, {s[1]}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='time6')
async def team_6v6(ctx):
    t, d, s = random.sample(herois["Tank"], 2), random.sample(herois["Damage"], 2), random.sample(herois["Support"], 2)
    embed = discord.Embed(title="💣 TIME 6v6! 💣", color=0xDC143C)
    embed.add_field(name="🛡️ Tanks", value=f"{t[0]}, {t[1]}", inline=False)
    embed.add_field(name="⚔️ Danos", value=f"{d[0]}, {d[1]}", inline=True)
    embed.add_field(name="🩺 Suportes", value=f"{s[0]}, {s[1]}", inline=True)
    await ctx.send(embed=embed)

# --- 5. LÓGICA DE MENSAGENS (COM IA) ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

    if bot.user.mentioned_in(message):
        user_msg = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        if not user_msg: return

        chat = get_or_create_chat(message.author.id)
        if not chat:
            return await message.channel.send("Mina falhou! Não consegui conectar com meu cérebro! 🧨")

        try:
            async with message.channel.typing():
                # Envia a mensagem para o histórico da sessão
                response = await asyncio.to_thread(chat.send_message, user_msg)
            await message.channel.send(response.text)
        except Exception as e:
            print(f"Erro IA: {e}")
            if "429" in str(e):
                await message.channel.send("Calma aí, Mate! Muitas mensagens! Espera 10 segundos! 🧨")
            else:
                await message.channel.send("Curto-circuito na mina! Tenta de novo! BOOOOM!")

# --- 6. EXECUÇÃO ---
keep_alive() 
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("ERRO: Token do Discord não encontrado no arquivo .env!")
