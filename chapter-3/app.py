import discord
from discord.ext import commands
import logging
import os
import boto3
import json
from concurrent.futures import ThreadPoolExecutor
from weasyprint import HTML

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
    await ctx.send('ただいま作成中...')


# HTMLコンテンツを変数に格納
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample PDF</title>
</head>
<body>
    <h1>Hello, GEEK!</h1>
    <p>This is a sample PDF file generated from HTML.</p>
</body>
</html>
"""

# HTMLコンテンツから直接PDFを生成
HTML(string=html_content).write_pdf('out.pdf')


bot.run(TOKEN)
