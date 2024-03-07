import discord
from discord.ext import commands
from discord.ui import Button, View
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

class ConfirmView(View):
    def __init__(self, file_path,):
        super().__init__(timeout=60)  # 60秒後にViewが無効になる
        self.file_path = file_path

    @discord.ui.button(label="はい", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        # S3にアップロード
        with open(self.file_path, 'rb') as file:
            self.s3_client.upload_fileobj(file, BUCKET_NAME, os.path.basename(self.file_path))
        logging.info(f'{self.file_path} を {BUCKET_NAME} にアップロードしました。')
        # ローカルファイルの削除
        os.remove(self.file_path)
        await interaction.response.send_message("画像を保存しました！", ephemeral=True)
        self.stop()

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        # ローカルファイルの削除
        os.remove(self.file_path)
        await interaction.response.send_message("画像を保存しませんでした。", ephemeral=True)
        self.stop()

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
        await ctx.send(file=discord.File(file, filename=os.path.basename(image_path)))

    # ConfirmViewを使ってユーザーに保存するか尋ねる
    view = ConfirmView(image_path)
    await ctx.send("S3に保存しますか？", view=view)

    # Viewが停止するのを待ちます（ユーザーがボタンを押すか、タイムアウトするまで）
    await view.wait()

bot.run(TOKEN)