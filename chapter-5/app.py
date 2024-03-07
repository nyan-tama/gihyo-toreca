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

# シークレット名を指定しS3のBUCKET名を取得
BUCKET_NAME = get_secret('MY_S3_BUCKET_NAME')

# シークレット名を指定してDiscord BotのTOKENを取得
# TOKEN = os.getenv('DISCORD_BOT_TOKEN') こちらを廃止して下記に置き換え
TOKEN = get_secret('DISCORD_BOT_TOKEN') 

# S3にアップロードする関数
def upload_to_s3(file_path):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # upload_file(ファイルの場所, バケットの名前, ファイル名)
            s3_client.upload_file(file_path, BUCKET_NAME, os.path.basename(file_path))
            logging.info(f'{file_path} を {BUCKET_NAME} にアップロードしました。')
            return
        except Exception as e:
            logging.error(f"S3へのアップロード中にエラーが発生しました: {e}")
            if attempt < max_retries - 1:
                logging.info(f"リトライ {attempt + 1}/{max_retries}")
            else:
                logging.error(f"S3へのアップロードが失敗しました。リトライ上限に達しました: {file_path}")

# Discordの選択肢ボタンの機能
class ConfirmView(View):
    def __init__(self, file_path):
        # ボタンの押せる有効時間を1分間に設定
        super().__init__(timeout=60)
        # 画像パスをインスタンス変数に入れる
        self.file_path = file_path

    # 『はい』ボタンの設定 ボタンの色は緑
    @discord.ui.button(label="はい", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        # S3にアップロードの処理を呼び出し
        upload_to_s3(self.file_path)

        # ローカルファイルの削除
        os.remove(self.file_path)
        #「画像を保存しました！」というメッセージを送信
        await interaction.response.send_message("画像を保存しました！")
        # ボタン機能を終了
        self.stop()

    # 『いいえ』ボタンの設定 ボタンの色は灰
    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        # ローカルファイルの削除
        os.remove(self.file_path)
        #「画像を保存しませんでした。」というメッセージを送信
        await interaction.response.send_message("画像を保存しませんでした。")
        #ボタン機能を終了
        self.stop()

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s: %(message)s')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    logging.info(f'Botが準備できました: {bot.user}')

@bot.command()
async def make(ctx, *, text: str):
    try:
        logging.info(f'受信したメッセージ: {text}')

        await ctx.send("ただいま作成中...")

        monster_info = generate_monster_bedrock(text)
        image_path = generate_card(monster_info)

        # 生成された画像をDiscordに送信
        await ctx.send(file=discord.File(image_path, filename=os.path.basename(image_path)))

        # ConfirmViewを使ってユーザーに保存するか尋ねる
        view = ConfirmView(image_path)
        await ctx.send("S3に保存しますか？", view=view)

        # Viewが停止するのを待ちます（ユーザーがボタンを押すか、タイムアウトするまで）
        await view.wait()

    except Exception as e:
        logging.error(f"コマンドの実行中にエラーが発生しました: {e}")
        await ctx.send("エラーが発生しました。しばらく待ってから再度お試しください。")

bot.run(TOKEN)