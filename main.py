import discord
from discord.ext import commands
import google.generativeai as genai
import os, asyncio, random, requests, sqlite3
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# --- KEEP_ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Junkrat está VIVO! 💥"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def keep_alive(): Thread(target=run).start()

# --- CONFIGURAÇÕES ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
DB_PATH = 'junkrat_data.db'

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- BANCO DE DADOS ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Bios (Heróis) - Padronizado id_nome
        cursor.execute('''CREATE TABLE IF NOT EXISTS bios 
                          (id_nome TEXT PRIMARY KEY, info TEXT, funcao TEXT)''')
        # Usuários
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                          (discord_id TEXT PRIMARY KEY, nome_preferido TEXT, ouro INTEGER DEFAULT 0)''')
        # Mains
        cursor.execute('''CREATE TABLE IF NOT EXISTS mains 
                          (discord_id TEXT PRIMARY KEY, main_tank TEXT, main_dano TEXT, main_sup TEXT)''')
        conn.commit()

init_db()

# --- UTILITÁRIOS ---
def db_get_herois(funcao):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_nome FROM bios WHERE funcao = ?", (funcao,))
        return [row[0].title() for row in cursor.fetchall()]

def db_salvar_main(discord_id, heroi_nome, coluna):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Valida se o herói existe (ignorando formatação)
        n = heroi_nome.lower().replace(" ", "").replace(":", "").replace("-", "")
        cursor.execute("SELECT id_nome FROM bios WHERE id_nome = ?", (n,))
        res = cursor.fetchone()
        if not res: return None
        
        heroi_oficial = res[0].title()
        cursor.execute(f"INSERT INTO mains (discord_id, {coluna}) VALUES (?, ?) "
                       f"ON CONFLICT(discord_id) DO UPDATE SET {coluna} = excluded.{coluna}", 
                       (str(discord_id), heroi_oficial))
        conn.commit()
        return heroi_oficial

def get_gif(search_term):
    if not GIPHY_API_KEY: return None
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={search_term}&limit=1&rating=g"
    try:
        r = requests.get(url, timeout=5).json()
        return r['data'][0]['images']['original']['url'] if r['data'] else None
    except: return None

# --- IA SETUP ---
chat_sessions = {}
PERSONALITY = """Você é Junkrat de Overwatch. Caótico, maníaco e ruidoso. 
Responda curto. Use "WOOHOO!", "BOOOOM!". Use o nome do usuário se souber.
Gere reações com [GIF: termo_em_ingles]."""

def get_chat(channel_id):
    if channel_id not in chat_sessions:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=PERSONALITY)
        chat_sessions[channel_id] = model.start_chat(history=[])
    return chat_sessions[channel_id]

# --- CACHE DE USUÁRIOS ---
user_cache = {}  # Guarda {discord_id: nome_preferido}
def get_user_name(discord_id):
    # Se já estiver no cache, retorna direto (RÁPIDO!)
    if discord_id in user_cache:
        return user_cache[discord_id]
    
    # Se não estiver, busca no banco uma única vez
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT nome_preferido FROM usuarios WHERE discord_id = ?", (str(discord_id),)).fetchone()
    
    if res:
        user_cache[discord_id] = res[0]
        return res[0]
    return None

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Explodindo tudo! | >help"))
    print("Junkrat PRONTO PARA O CAOS! 💥")

# --- COMANDOS ---

@bot.command(name='help')
async def jk_help(ctx):
    e = discord.Embed(title="💥 MANUAL DE DETONAÇÃO! 💥", color=0xFF4500)
    e.add_field(name="👤 Cadastro", value="`>meunome` | `>minhainfo`", inline=True)
    e.add_field(name="📖 Info", value="`>bio [herói]`", inline=True)
    e.add_field(name="🎲 Sorteios", value="`>time5` | `>time6` | `>tank` | `>dano` | `>sup`", inline=False)
    e.add_field(name="⭐ Mains", value="`>main_tank` | `>main_dano` | `>main_sup`", inline=True)
    e.add_field(name="🧹 Reset", value="`>limpar`", inline=True)
    e.set_footer(text=f"Fala aí, {ctx.author.name}!")
    await ctx.send(embed=e)

@bot.command()
async def minhainfo(ctx):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT u.nome_preferido, m.main_tank, m.main_dano, m.main_sup "
                       "FROM usuarios u LEFT JOIN mains m ON u.discord_id = m.discord_id "
                       "WHERE u.discord_id = ?", (str(ctx.author.id),))
        res = cursor.fetchone()
    
    if not res:
        return await ctx.send("💥 Não te conheço! Use `>meunome` primeiro!")
    
    nome, t, d, s = res
    e = discord.Embed(title=f"📋 Ficha: {nome}", color=0x00FF00)
    e.add_field(name="🛡️ Tank", value=t or "Vazio", inline=True)
    e.add_field(name="⚔️ Dano", value=d or "Vazio", inline=True)
    e.add_field(name="💉 Sup", value=s or "Vazio", inline=True)
    await ctx.send(embed=e)

async def handle_main(ctx, heroi, coluna, msg_sucesso):
    res = db_salvar_main(ctx.author.id, heroi, coluna)
    if res: await ctx.send(f"{msg_sucesso} **{res}**!")
    else: await ctx.send(f"💥 Herói '{heroi}' não encontrado!")

@bot.command()
async def main_tank(ctx, *, h): await handle_main(ctx, h, "main_tank", "🚀 Tank definido:")
@bot.command()
async def main_dano(ctx, *, h): await handle_main(ctx, h, "main_dano", "🔥 Dano definido:")
@bot.command()
async def main_sup(ctx, *, h): await handle_main(ctx, h, "main_sup", "💉 Suporte definido:")

@bot.command()
async def meunome(ctx, *, nome: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO usuarios (discord_id, nome_preferido) VALUES (?, ?) "
                     "ON CONFLICT(discord_id) DO UPDATE SET nome_preferido = excluded.nome_preferido", 
                     (str(ctx.author.id), nome))
    
    # Atualiza o cache imediatamente!
    user_cache[str(ctx.author.id)] = nome
    await ctx.send(f"WOOHOO! Nome salvo e memorizado, **{nome}**! 🧨")

@bot.command()
async def bio(ctx, *, heroi: str):
    n = heroi.lower().replace(" ", "").replace(":", "").replace("-", "")
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT info, funcao FROM bios WHERE id_nome = ?", (n,)).fetchone()
    if res:
        e = discord.Embed(title=f"📁 {heroi.title()}", description=res[0], color=0xFF4500)
        e.set_footer(text=f"Classe: {res[1]}")
        await ctx.send(embed=e)
    else: await ctx.send("Não achei esse sujeito! 🧨")

@bot.command()
async def time5(ctx):
    t, d, s = db_get_herois('Tanque'), db_get_herois('Dano'), db_get_herois('Suporte')
    e = discord.Embed(title="💥 5v5!", color=0xFF4500)
    e.add_field(name="🛡️", value=random.choice(t))
    e.add_field(name="⚔️", value=", ".join(random.sample(d, 2)))
    e.add_field(name="🩺", value=", ".join(random.sample(s, 2)))
    await ctx.send(embed=e)

@bot.command()
async def tank(ctx): await ctx.send(f"🛡️ Tank: **{random.choice(db_get_herois('Tanque'))}**")
@bot.command()
async def dano(ctx): await ctx.send(f"⚔️ Dano: **{random.choice(db_get_herois('Dano'))}**")
@bot.command()
async def sup(ctx): await ctx.send(f"🩺 Suporte: **{random.choice(db_get_herois('Suporte'))}**")

@bot.command()
async def limpar(ctx):
    chat_sessions.pop(ctx.channel.id, None)
    await ctx.send("💥 Esqueci de tudo!")

# --- EVENTO IA ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

    # 1. Verifica se é resposta ao bot ou menção
    is_reply_to_bot = False
    if message.reference and message.reference.resolved:
        resolved_msg = message.reference.resolved
        if hasattr(resolved_msg, 'author') and resolved_msg.author.id == bot.user.id:
            is_reply_to_bot = True

    if bot.user.mentioned_in(message) or is_reply_to_bot:
        clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        
        # Se a mensagem estiver vazia (só o ping), ignora
        if not clean_text and not is_reply_to_bot: return

        # 2. BUSCA NO CACHE (MUITO MAIS RÁPIDO!)
        user_ref = get_user_name(str(message.author.id)) or message.author.display_name
        
        chat = get_chat(message.channel.id)

        try:
            async with message.channel.typing():
                # 3. Envia para a IA
                response = await asyncio.to_thread(chat.send_message, f"{user_ref} diz: {clean_text}")
                txt = response.text.split('\n')[-1] if "THINKING:" in response.text else response.text
                
                msg_final = txt.split("[GIF:")[0].strip()
                await message.reply(msg_final if msg_final else "WOOHOO! EXPLOSÃO! 🧨")

                # 4. Processa o GIF (se houver)
                if "[GIF:" in txt and random.random() < 0.6:
                    gif_tag = txt.split("[GIF:")[1].split("]")[0]
                    gif = get_gif(gif_tag)
                    if gif: await message.channel.send(gif)
        except Exception as e:
            print(f"Erro na IA: {e}")
            await message.channel.send("Ih, minha cabeça deu curto-circuito! Tenta de novo! 🧨")

keep_alive()
if DISCORD_BOT_TOKEN: bot.run(DISCORD_BOT_TOKEN)