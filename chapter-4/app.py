import discord
from discord.ext import commands
import logging
import os
from generate_ai import generate_monster_bedrock
# image_processing.pyに作った『generate_card』関数を呼び出す
from image_processing import generate_card

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s: %(message)s')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Botが準備できました: {bot.user}')

@bot.command()
async def make(ctx, *, text: str):
    logging.info(f'受信したメッセージ: {text}')

    await ctx.send("ただいま作成中...")

    monster_info = generate_monster_bedrock(text)

    # 生成したモンスター情報を使用してカードをレイアウトし、画像に変換
    generate_card(monster_info)
    
bot.run(TOKEN)