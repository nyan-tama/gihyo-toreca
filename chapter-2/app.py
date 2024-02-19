import discord  # discord.pyライブラリをインポート。Discord Botの作成に必要です。
from discord.ext import commands  # commandsフレームワークをインポート。コマンドベースのBotを簡単に作成できます。
import logging  # loggingモジュールをインポート。ログ出力のために使用します。
import os  # osモジュールをインポート。環境変数へのアクセスに使用します。

# 環境変数からDiscord Botのトークンを取得
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# loggingの基本設定を行います。ログレベルをINFOに設定し、ログのフォーマットを指定します。
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s: %(message)s')

# Botクライアントの初期化。コマンドのプレフィックスを'!'に設定し、Botが受信するイベントの設定します。
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容へのアクセスを有効にします。これにより、メッセージのテキストを読み取れるようになります。

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    # BotがDiscordに接続したときに実行されるイベント。Botのログインが完了したことをログに記録します。
    logging.info(f'Botが準備できました: {bot.user}')

@bot.command()
async def make(ctx, *, text: str):
    # '!make <text>'というコマンドに反応して実行される関数。
    # 受け取ったテキストメッセージをログに記録し、ユーザーに「ただいま作成中...」というメッセージを送信します。
    logging.info(f'受信したメッセージ: {text}')
    await ctx.send('ただいま作成中...')

bot.run(TOKEN)  # Botを起動します。この関数により、BotはDiscordサーバーに接続し、コマンドの待受を開始します。
