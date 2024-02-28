import discord
from discord.ext import commands
import logging
import os
from generate_ai import generate_monster_bedrock
from image_processing import generate_card_and_upload_image


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

    # Discordから受け取った『text』のメッセージを『generate_monster_bedrock』関数に渡して、生成開始
    monster_info = generate_monster_bedrock(text)

    # 生成したモンスター情報を使用してPDFを生成し、画像に変換してS3にアップロード
    generate_pdf_and_upload_image(monster_info)

    # 処理が完了したことをユーザーに通知
    await ctx.send("モンスターの作成が完了しました！")
bot.run(TOKEN)
