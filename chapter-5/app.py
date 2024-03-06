import discord
from discord.ext import commands
import logging
import os
from generate_ai import generate_monster_bedrock
from image_processing import generate_card
import boto3 # AWSサービス連携用

# AWS Secrets Managerと連携
secrets_manager_client = boto3.client('secretsmanager')
# AWS S3と連携
s3_client = boto3.client('s3')

# AWS Secrets Managerからシークレット情報を取得する関数
def get_secret(secret_name):
    try:
        # AWS Secrets Managerから指定したシークレットの値を取得します。
        get_secret_value_response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        return get_secret_value_response['SecretString']
    except Exception as e:
        logging.error(f"シークレットの取得中にエラーが発生しました: {e}")
        return None

# シークレット名を指定してDiscord BotのTOKENを取得
TOKEN = get_secret('DISCORD_BOT_TOKEN') 
# シークレット名を指定しS3のBUCKET名を取得
BUCKET_NAME = get_secret('MY_S3_BUCKET_NAME')

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

    image_path = generate_card(monster_info)

    # 生成された画像をDiscordに送信
    with open(image_path, 'rb') as file:
        # Discordに画像を送信
        await ctx.send(file=discord.File(file, filename=image_path))

        # ファイルの読み込み位置を先頭に戻す
        file.seek(0)

        # 画像をS3にアップロード
        s3_client.upload_fileobj(file, BUCKET_NAME, os.path.basename(image_path))

        logging.info(f'{image_path} を {BUCKET_NAME} にアップロードしました。')

    # ローカルのファイルを削除
    os.remove(image_path)
    logging.info(f'ローカル上のファイル {image_path} は削除しました。')
    
    logging.info(f'すべての処理が完了しました。')

bot.run(TOKEN)