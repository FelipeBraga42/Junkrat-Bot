import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import asyncio
import random

# --- CÓDIGO DO KEEP_ALIVE EMBUTIDO (Para o Render.com) ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "WOOHOO! O Bot Junkrat está ONLINE e pronto para a EXPLOSÃO! 💥"

def run():
    # Garante que o Flask use a porta definida pelo Render (geralmente 10000)
    # Nota: Ao usar gunicorn, esta função run() pode não ser estritamente necessária, 
    # mas a mantemos para clareza
    port = int(os.environ.get("PORT", 5000)) # Pega a porta do ambiente Render
    app.run(host="0.0.0.0", port=port)

def keep_alive():  
    t = Thread(target=run)
    t.start()
# --- FIM DO CÓDIGO KEEP_ALIVE ---


# --- 1. CONFIGURAÇÃO DO BOT (CORRIGIDO PARA O GOOGLE GENAI CLIENT) ---

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_BOT_TOKEN:
    print("ERRO: O token do Discord (DISCORD_BOT_TOKEN) não foi encontrado.")

intents = discord.Intents.default()
intents.message_content = True 
# DESATIVA O COMANDO HELP PADRÃO
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None) 

gemini_client = None
if GEMINI_API_KEY:
    # CORREÇÃO DA INICIALIZAÇÃO APLICADA
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
Use gírias como "WOOHOO!", "BOOOOM!", "HA-HA-HA!".
Seu parceiro é o Roadhog. Cite ele as vezes.
Responda de forma sucinta e com entusiasmo maníaco.
"""

def get_or_create_chat(user_id):
    """Obtém ou cria a sessão de chat com histórico para um usuário."""
    if user_id not in chat_sessions:
        if gemini_client is None:
            return None
        
        chat = gemini_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=Junkrat_Personality
            )
        )
        chat_sessions[user_id] = chat
    return chat_sessions[user_id]


# --- 3. DADOS PARA COMANDO DE TIME (ATUALIZADO) ---

# DADOS DOS HERÓIS PARA O COMANDO >TIME
herois = {
    "Tank": ["D.Va", "Doomfist", "Junker Queen", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya"],
    "Damage": ["Ashe", "Bastion", "Cassidy", "Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Venture", "Widowmaker", "Vendetta"],
    "Support": ["Ana", "Baptiste", "Brigitte", "Illari", "Kiriko", "Lifeweaver", "Lúcio", "Mercy", "Moira", "Zenyatta", "Wuyang"]
}


# --- 4. COMANDOS DO BOT (COMANDOS DE TIME NOVOS E ATUALIZADOS) ---

@bot.event
async def on_ready():
    print(f"Pronto! Eu sou o {bot.user.name} e estou pronto para a explosão!")
    await bot.change_presence(activity=discord.Game(name="Gerando Caos | >help"))


@bot.command(name='help')
async def junkrat_help(ctx):
    """Comando customizado de ajuda (ATUALIZADO)."""
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
        name="Comandos de Times e Heróis (Caos Organizado!)",
        value="`>time5` : Gera uma composição de time **5v5** (1 Tank, 2 Danos, 2 Suportes).\n`>time6` : Gera uma composição de time **6v6** (2 Tanks, 2 Danos, 2 Suportes).\n`>tank` : Escolhe 1 herói **Tank** aleatório.\n`>dano` : Escolhe 1 herói **Damage (Dano)** aleatório.\n`>sup` : Escolhe 1 herói **Support (Suporte)** aleatório.",
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


# --- NOVOS COMANDOS DE ESCOLHA INDIVIDUAL ---

async def pick_role(ctx, role_key, role_name, color):
    """Função auxiliar para escolher um herói de uma função específica."""
    if not herois[role_key]:
        return await ctx.send(f"Ah, droga! Sem heróis de {role_name} no mapa! HA-HA-HA!")
    
    escolhido = random.choice(herois[role_key])
    
    embed = discord.Embed(
        title=f"💥 ESCOLHA {role_name.upper()} EXPLOSIVA! 💥",
        description=f"WOOHOO! {ctx.author.mention}, você vai de **{escolhido}**!",
        color=color
    )
    await ctx.send(embed=embed)

@bot.command(name='tank')
async def pick_tank(ctx):
    """Escolhe um Tank aleatório."""
    await pick_role(ctx, "Tank", "Tank", 0x008080) # Teal

@bot.command(name='dano', aliases=['damage'])
async def pick_damage(ctx):
    """Escolhe um Damage (Dano) aleatório."""
    await pick_role(ctx, "Damage", "Dano", 0xFF4500) # Laranja Fogo

@bot.command(name='sup', aliases=['support'])
async def pick_support(ctx):
    """Escolhe um Support (Suporte) aleatório."""
    await pick_role(ctx, "Support", "Suporte", 0x00FF00) # Verde Neon


# --- COMANDOS DE COMPOSIÇÃO DE TIME (ATUALIZADOS) ---

# O comando '>time' original foi renomeado para '>time5'
@bot.command(name='time5', aliases=['5v5'])
async def team_picker_5v5(ctx):
    """Gera uma composição de time 5v5 aleatória (1 Tank, 2 Damage, 2 Support)."""
    
    if not herois["Tank"] or len(herois["Damage"]) < 2 or len(herois["Support"]) < 2:
        return await ctx.send("Os heróis sumiram! O mapa está vazio! Preciso de pelo menos 1T, 2D e 2S!")

    tank_escolhido = random.choice(herois["Tank"])
    damage_escolhidos = random.sample(herois["Damage"], 2)
    support_escolhidos = random.sample(herois["Support"], 2)
    
    embed = discord.Embed(
        title="💥 COMPOSIÇÃO DE TIME EXPLOSIVA (5v5)! 💥",
        description="WOOHOO! É hora de começar o caos com este time de 5!",
        color=0xFF4500
    )
    embed.add_field(name="🛡️ Tank (1)", value=f"**{tank_escolhido}**", inline=False)
    embed.add_field(name="⚔️ Damage (2)", value=f"**{', '.join(damage_escolhidos)}**", inline=True)
    embed.add_field(name="🩺 Support (2)", value=f"**{', '.join(support_escolhidos)}**", inline=True)
    
    embed.set_footer(text="AGORA VAI! HA-HA-HA!")
    await ctx.send(f"Escutem, {ctx.author.mention}! Seu novo time 5v5 está pronto!", embed=embed)


@bot.command(name='time6', aliases=['6v6', 'equipe6'])
async def team_picker_6v6(ctx):
    """Gera uma composição de time 6v6 aleatória (2 Tanks, 2 Damage, 2 Support)."""
    
    if len(herois["Tank"]) < 2 or len(herois["Damage"]) < 2 or len(herois["Support"]) < 2:
        return await ctx.send("Os heróis sumiram! O mapa está vazio! Preciso de pelo menos 2T, 2D e 2S para o 6v6!")

    # Escolhe 2 Tanks únicos
    tank_escolhidos = random.sample(herois["Tank"], 2)
    # Escolhe 2 Damage únicos
    damage_escolhidos = random.sample(herois["Damage"], 2)
    # Escolhe 2 Support únicos
    support_escolhidos = random.sample(herois["Support"], 2)
    
    embed = discord.Embed(
        title="💣 COMPOSIÇÃO DE TIME CLÁSSICA (6v6)! 💣",
        description="BOOOM! O caos nostálgico começou com este time de 6!",
        color=0xDC143C # Carmesim
    )
    embed.add_field(name="🛡️ Tanks (2)", value=f"**{', '.join(tank_escolhidos)}**", inline=False)
    embed.add_field(name="⚔️ Damage (2)", value=f"**{', '.join(damage_escolhidos)}**", inline=True)
    embed.add_field(name="🩺 Support (2)", value=f"**{', '.join(support_escolhidos)}**", inline=True)
    
    embed.set_footer(text="EXPLOSÃO GARANTIDA! HA-HA-HA!")
    await ctx.send(f"Escutem, {ctx.author.mention}! Seu time 6v6 está pronto para a guerra!", embed=embed)


# --- COMANDOS JÁ EXISTENTES ---

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
    if message.author.bot:
        return

    await bot.process_commands(message)

    if bot.user and bot.user.mentioned_in(message) and gemini_client:
        user_id = message.author.id
        user_message = message.content.replace(f'<@!{bot.user.id}>', '').strip()

        chat = get_or_create_chat(user_id)
        
        if chat is None:
            await message.channel.send("Ah, droga! A chave Gemini não está configurada. Sem chat para você! BOOOOM!")
            return

        try:
            async with message.channel.typing():
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


