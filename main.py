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

# --- KEEP_ALIVE (Para manter o bot online no Render/Replit) ---
app = Flask('')
@app.route('/')
def home(): return "Junkrat está ONLINE e pronto para explodir! 💥"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():  
    Thread(target=run).start()

# --- 1. CONFIGURAÇÃO DA IA ---

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("IA Junkrat configurada com sucesso!")

# --- 2. PERSONALIDADE E MEMÓRIA ---
chat_sessions = {}

Junkrat_Personality = """
Você é Junkrat, o mercenário explosivo de Overwatch. 
Sua personalidade é caótica, maníaca e obcecada por explosões e ouro.
Responda sempre como Junkrat. Use gírias como "WOOHOO!", "BOOOOM!", "HA-HA-HA!".
Cite o Roadhog às vezes. Você tem memória das conversas!
Seja sucinto e muito entusiasmado.
"""

def get_or_create_chat(user_id):
    if user_id not in chat_sessions:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", 
                system_instruction=Junkrat_Personality
            )
            chat_sessions[user_id] = model.start_chat(history=[])
            print(f"Memória iniciada para o usuário: {user_id}")
        except Exception as e:
            print(f"Erro ao iniciar IA: {e}")
            return None
    return chat_sessions[user_id]

# --- 3. BANCO DE DADOS (HERÓIS E BIOS) ---

herois = {
    "Tank": ["D.Va", "Doomfist", "Junker Queen", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya", "Domina", "Hazard"],
    "Damage": ["Ashe", "Bastion", "Cassidy", "Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Venture", "Widowmaker", "Vendetta", "Anran", "Emre", "Sierra", "Freja"],
    "Support": ["Ana", "Baptiste", "Brigitte", "Illari", "Kiriko", "Lifeweaver", "Lúcio", "Mercy", "Moira", "Zenyatta", "Wuyang", "Mizuki", "Jetpack Cat", "Juno"]
}

bios = {
    "ana": "🎂 **Nascimento:** 1º de janeiro\n👤 **Nome:** Ana Amari\n⚔️ **Classe:** Suporte\n🌍 **Local:** Egito",
    "anran": "🎂 **Nascimento:** 8 de agosto\n👤 **Nome:** Anran Ye\n⚔️ **Classe:** Dano\n🌍 **Local:** China",
    "ashe": "🎂 **Nascimento:** 1º de outubro\n👤 **Nome:** Elizabeth Ashe\n⚔️ **Classe:** Dano\n🌍 **Local:** Estados Unidos",
    "baptiste": "🎂 **Nascimento:** 12 de março\n👤 **Nome:** Jean-Baptiste Augustin\n⚔️ **Classe:** Suporte\n🌍 **Local:** Haiti",
    "bastion": "🎂 **Nascimento:** Desconhecido\n👤 **Nome:** Bastion\n⚔️ **Classe:** Dano\n🌍 **Local:** Origem Desconhecida",
    "brigitte": "🎂 **Nascimento:** 22 de setembro\n👤 **Nome:** Brigitte Lindholm\n⚔️ **Classe:** Suporte\n🌍 **Local:** Suécia",
    "cassidy": "🎂 **Nascimento:** 31 de julho\n👤 **Nome:** Cole Cassidy\n⚔️ **Classe:** Dano\n🌍 **Local:** Estados Unidos",
    "domina": "🎂 **Nascimento:** 28 de agosto\n👤 **Nome:** Vaira Singhania\n⚔️ **Classe:** Tanque\n🌍 **Local:** Índia",
    "d.va": "🎂 **Nascimento:** 22 de junho\n👤 **Nome:** Hana Song\n⚔️ **Classe:** Tanque\n🌍 **Local:** Coreia do Sul",
    "doomfist": "🎂 **Nascimento:** 25 de maio\n👤 **Nome:** Akande Ogundimu\n⚔️ **Classe:** Tanque\n🌍 **Local:** Nigéria",
    "echo": "🎂 **Nascimento:** 5 de fevereiro\n👤 **Nome:** Echo\n⚔️ **Classe:** Dano\n🌍 **Local:** Cingapura",
    "emre": "🎂 **Nascimento:** 8 de novembro\n👤 **Nome:** Emre Sarıoğlu\n⚔️ **Classe:** Dano\n🌍 **Local:** Turquia",
    "freja": "🎂 **Nascimento:** 26 de setembro\n👤 **Nome:** Freja Skov\n⚔️ **Classe:** Dano\n🌍 **Local:** Dinamarca",
    "genji": "🎂 **Nascimento:** 28 de outubro\n👤 **Nome:** Genji Shimada\n⚔️ **Classe:** Dano\n🌍 **Local:** Japão",
    "hanzo": "🎂 **Nascimento:** 3 de novembro\n👤 **Nome:** Hanzo Shimada\n⚔️ **Classe:** Dano\n🌍 **Local:** Japão",
    "hazard": "🎂 **Nascimento:** 11 de novembro\n👤 **Nome:** Findlay Docherty\n⚔️ **Classe:** Tanque\n🌍 **Local:** Escócia",
    "illari": "🎂 **Nascimento:** 21 de dezembro\n👤 **Nome:** Illari Quispe Ruiz\n⚔️ **Classe:** Suporte\n🌍 **Local:** Peru",
    "jetpack cat": "🎂 **Nascimento:** Desconhecido\n👤 **Nome:** Fika\n⚔️ **Classe:** Suporte\n🌍 **Local:** Desconhecido",
    "juno": "🎂 **Nascimento:** 22 de março\n👤 **Nome:** Juno Teo Minh\n⚔️ **Classe:** Suporte\n🌍 **Local:** Marte",
    "junker queen": "🎂 **Nascimento:** 14 de junho\n👤 **Nome:** Odessa Stone\n⚔️ **Classe:** Tanque\n🌍 **Local:** Austrália",
    "junkrat": "🎂 **Nascimento:** 29 de fevereiro\n👤 **Nome:** Jamison Fawkes\n⚔️ **Classe:** Dano\n🌍 **Local:** Austrália",
    "kiriko": "🎂 **Nascimento:** 7 de julho\n👤 **Nome:** Kiriko Kamori\n⚔️ **Classe:** Suporte\n🌍 **Local:** Japão",
    "lifeweaver": "🎂 **Nascimento:** 28 de abril\n👤 **Nome:** Niran Pruksamanee\n⚔️ **Classe:** Suporte\n🌍 **Local:** Tailândia",
    "lucio": "🎂 **Nascimento:** 20 de março\n👤 **Nome:** Lúcio Correia dos Santos\n⚔️ **Classe:** Suporte\n🌍 **Local:** Brasil",
    "mauga": "🎂 **Nascimento:** 19 de agosto\n👤 **Nome:** Maugaloa Malosi\n⚔️ **Classe:** Tanque\n🌍 **Local:** Samoa",
    "mei": "🎂 **Nascimento:** 5 de setembro\n👤 **Nome:** Mei-Ling Zhou\n⚔️ **Classe:** Dano\n🌍 **Local:** China",
    "mercy": "🎂 **Nascimento:** 13 de maio\n👤 **Nome:** Angela Ziegler\n⚔️ **Classe:** Suporte\n🌍 **Local:** Suíça",
    "mizuki": "🎂 **Nascimento:** 9 de abril\n👤 **Nome:** Mizuki Kawano\n⚔️ **Classe:** Suporte\n🌍 **Local:** Japão",
    "moira": "🎂 **Nascimento:** 4 de abril\n👤 **Nome:** Moira O'Deorain\n⚔️ **Classe:** Suporte\n🌍 **Local:** Irlanda",
    "orisa": "🎂 **Nascimento:** 9 de maio\n👤 **Nome:** Orisa\n⚔️ **Classe:** Tanque\n🌍 **Local:** Numbani",
    "pharah": "🎂 **Nascimento:** 15 de abril\n👤 **Nome:** Fareeha Amari\n⚔️ **Classe:** Dano\n🌍 **Local:** Egito",
    "ramattra": "🎂 **Nascimento:** 29 de março\n👤 **Nome:** Ramattra\n⚔️ **Classe:** Tanque\n🌍 **Local:** Nepal",
    "reaper": "🎂 **Nascimento:** 14 de dezembro\n👤 **Nome:** Gabriel Reyes\n⚔️ **Classe:** Dano\n🌍 **Local:** Estados Unidos",
    "reinhardt": "🎂 **Nascimento:** 26 de junho\n👤 **Nome:** Reinhardt Wilhelm\n⚔️ **Classe:** Tanque\n🌍 **Local:** Alemanha",
    "roadhog": "🎂 **Nascimento:** 12 de setembro\n👤 **Nome:** Mako Rutledge\n⚔️ **Classe:** Tanque\n🌍 **Local:** Austrália",
    "sierra": "🎂 **Nascimento:** 17 de abril\n👤 **Nome:** Sierra Turner Woods\n⚔️ **Classe:** Dano\n🌍 **Local:** Estados Unidos",
    "sigma": "🎂 **Nascimento:** 15 de março\n👤 **Nome:** Siebren de Kuiper\n⚔️ **Classe:** Tanque\n🌍 **Local:** Holanda",
    "sojourn": "🎂 **Nascimento:** 12 de janeiro\n👤 **Nome:** Vivian Chase\n⚔️ **Classe:** Dano\n🌍 **Local:** Canadá",
    "soldier: 76": "🎂 **Nascimento:** 27 de janeiro\n👤 **Nome:** Jack Morrison\n⚔️ **Classe:** Dano\n🌍 **Local:** Estados Unidos",
    "sombra": "🎂 **Nascimento:** 31 de dezembro\n👤 **Nome:** Olivia Colomar\n⚔️ **Classe:** Dano\n🌍 **Local:** México",
    "symmetra": "🎂 **Nascimento:** 2 de outubro\n👤 **Nome:** Satya Vaswani\n⚔️ **Classe:** Dano\n🌍 **Local:** Índia",
    "torbjorn": "🎂 **Nascimento:** 21 de setembro\n👤 **Nome:** Torbjörn Lindholm\n⚔️ **Classe:** Dano\n🌍 **Local:** Suécia",
    "tracer": "🎂 **Nascimento:** 17 de fevereiro\n👤 **Nome:** Lena Oxton\n⚔️ **Classe:** Dano\n🌍 **Local:** Inglaterra",
    "vendetta": "🎂 **Nascimento:** 15 de fevereiro\n👤 **Nome:** Marzia Bartalotti\n⚔️ **Classe:** Dano\n🌍 **Local:** Itália",
    "venture": "🎂 **Nascimento:** 6 de agosto\n👤 **Nome:** Sloan Cameron\n⚔️ **Classe:** Dano\n🌍 **Local:** Canadá",
    "widowmaker": "🎂 **Nascimento:** 19 de novembro\n👤 **Nome:** Amélie Lacroix\n⚔️ **Classe:** Dano\n🌍 **Local:** França",
    "winston": "🎂 **Nascimento:** 6 de junho\n👤 **Nome:** Winston\n⚔️ **Classe:** Tanque\n🌍 **Local:** Lua",
    "wrecking ball": "🎂 **Nascimento:** 15 de outubro\n👤 **Nome:** Hammond\n⚔️ **Classe:** Tanque\n🌍 **Local:** Lua",
    "wuyang": "🎂 **Nascimento:** 1º de maio\n👤 **Nome:** Wuyang Ye\n⚔️ **Classe:** Suporte\n🌍 **Local:** China",
    "zarya": "🎂 **Nascimento:** 4 de dezembro\n👤 **Nome:** Aleksandra Zaryanova\n⚔️ **Classe:** Tanque\n🌍 **Local:** Rússia",
    "zenyatta": "🎂 **Nascimento:** 14 de julho\n👤 **Nome:** Tekhartha Zenyatta\n⚔️ **Classe:** Suporte\n🌍 **Local:** Nepal"
}

# --- 4. CONFIGURAÇÃO DISCORD ---

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

@bot.event
async def on_ready():
    print(f"Pronto! Junkrat na área!")
    await bot.change_presence(activity=discord.Game(name="Lançando Granadas | >help"))

# --- COMANDOS ---

@bot.command(name='help')
async def junkrat_help(ctx):
    embed = discord.Embed(title="💥 AJUDA DO JUNKRAT! 💥", color=0xFF4500)
    embed.add_field(name="🧠 IA", value=f"Mencione `@{bot.user.name}`", inline=False)
    embed.add_field(name="📖 Bios", value="`>bio [nome]`", inline=True)
    embed.add_field(name="🎮 Sorteios", value="`>time5`, `>time6`, `>tank`, `>dano`, `>sup`", inline=True)
    embed.add_field(name="🎲 Diversão", value="`>moeda`, `>dado [lados]`", inline=True)
    embed.add_field(name="🧹 Memória", value="`>limpar`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='bio')
async def show_bio(ctx, *, nome: str):
    nome_busca = nome.lower().strip()
    if nome_busca in bios:
        embed = discord.Embed(title=f"📁 Arquivo: {nome.title()}", description=bios[nome_busca], color=0xFF4500)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Nunca ouvi falar de '{nome}'. Ele tem ouro?")

@bot.command(name='limpar')
async def clear_memory(ctx):
    if ctx.author.id in chat_sessions:
        del chat_sessions[ctx.author.id]
        await ctx.send("💥 **BOOOOM!** Memória explodida!")

@bot.command(name='tank')
async def pick_tank(ctx): await ctx.send(f"🛡️ Vá de **{random.choice(herois['Tank'])}**!")
@bot.command(name='dano')
async def pick_damage(ctx): await ctx.send(f"⚔️ Vá de **{random.choice(herois['Damage'])}**!")
@bot.command(name='sup')
async def pick_support(ctx): await ctx.send(f"🩺 Vá de **{random.choice(herois['Support'])}**!")

# --- NOVOS COMANDOS ADICIONADOS ---
@bot.command(name='moeda')
async def coin(ctx):
    resultado = random.choice(['Cara', 'Coroa'])
    await ctx.send(f"🪙 Girando... Deu **{resultado}**!")

@bot.command(name='dado')
async def dice(ctx, sides: int = 6):
    resultado = random.randint(1, sides)
    await ctx.send(f"🎲 Rolando um dado de {sides} lados... Deu **{resultado}**!")

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

# --- 5. LÓGICA DE MENSAGENS ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

    if bot.user.mentioned_in(message):
        user_msg = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        if not user_msg: return

        chat = get_or_create_chat(message.author.id)
        if not chat: return

        try:
            async with message.channel.typing():
                response = await asyncio.to_thread(chat.send_message, user_msg)
            await message.channel.send(response.text)
        except Exception as e:
            print(f"Erro IA: {e}")
            await message.channel.send("Curto-circuito na mina! Tenta de novo! 🧨")

# --- 6. EXECUÇÃO ---
keep_alive() 
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
