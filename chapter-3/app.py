import discord
from discord.ext import commands
import logging
import os
from io import BytesIO # メモリ上で画像のバイナリデータを扱うためのBytesIOをインポートします。動作確認用のコードで使用
import base64 # Base64エンコーディング・デコーディングに使用するライブラリをインポートします。同じくイメージ描画の際に使用
from generate_ai import generate_monster_bedrock # generate_ai.pyに作った『generate_monster_bedrock』を呼び出す


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

    # Discordから受け取った『text』のメッセージを『generate_monster_bedrock』関数に渡して、文章と画像を生成
    monster_info = generate_monster_bedrock(text)

    # 第3回では動作確認のため、生成したモンスターの情報をそのままDiscord上で表示してみます
    # 以降のプログラムは第3回の動作確認用のプログラムなので、第4回以降は削除されます。
    # -------------------------------------------------------------------------
    monster_details = (
        f"**モンスター名**: {monster_info['monster_name']}\n"
        f"**強さ**: {monster_info['monster_level']}\n"
        f"**属性**: {monster_info['monster_element']}\n"
        f"**特殊能力**: {monster_info['monster_ability']}\n"
        f"**伝説**: {monster_info['monster_episode']}"
    )

    # テキスト結果をDiscordに送信
    await ctx.send(monster_details)

    # イメージ結果をDiscordに送信
    image_data_base64 = monster_info['monster_image']
    image_data = base64.b64decode(image_data_base64)
    # BytesIOオブジェクトを使って、メモリ上に画像を保持します
    with BytesIO(image_data) as image_file:
        # discord.Fileオブジェクトを作成し、画像ファイルとして送信します
        discord_file = discord.File(image_file, filename="monster_image.png")
        await ctx.send(file=discord_file)
    # -------------------------------------------------------------------------
        
bot.run(TOKEN)
