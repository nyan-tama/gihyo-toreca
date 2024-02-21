import discord
from discord.ext import commands
import logging
import os
import boto3  # AWS SDK for Python (Boto3) をインポートします。AWSのサービスをPythonから使うために必要です。
import json  # JSONデータのエンコード（PythonオブジェクトをJSON形式の文字列に変換）およびデコード（JSON形式の文字列をPythonオブジェクトに変換）に使用します。
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

    # ユーザーからのリクエストを基にしてモンスター情報を生成
    monster_info = bedrock(text)

    # HTMLコンテンツを生成
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Monster Details</title>
        <!-- 日本語フォントのリンクを追加 -->
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Noto Sans JP', sans-serif; /* 日本語フォントを適用 */
            }}
        </style>
    </head>
    <body>
        <h1>{monster_info['monster_name']}</h1>
        <p>Level: {monster_info['monster_level']}</p>
        <p>Element: {monster_info['monster_element']}</p>
        <p>Ability: {monster_info['monster_ability']}</p>
        <p>Legend: {monster_info['monster_episode']}</p>
    </body>
    </html>
    """

    # HTMLからPDFを生成
    HTML(string=html_content).write_pdf('monster_details.pdf')
    
    # 完成したPDFをDiscordチャットに送信
    await ctx.send(file=discord.File('monster_details.pdf'))

# Bedrockにリクエストを送信する関数を定義します。
def request_bedrock(prompt):
    # AWS Bedrock Runtimeのクライアントを作成します。このクライアントを通じてAWSのサービスにアクセスします。
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

    # モデルに送るリクエストボディをJSON形式で作成します。promptとその他のパラメータを含みます。
    body = json.dumps({
        "prompt": prompt,  # モデルに与えるプロンプト（生成AIに対する命令です）。
        "max_tokens_to_sample": 200,  # モデルが生成する最大トークン数。
        "temperature": 0.9,  # サンプリング温度。高いほどランダム性が増します。
        "top_k": 150,  # トップkサンプリングで使用。確率の高いトップkトークンのみを考慮します。
        "top_p": 0.7  # トップpサンプリングで使用。確率の累積がpを超えるまでのトークンを考慮します。
    })

    # Bedrock Runtimeのinvoke_modelメソッドを使用してモデルを呼び出します。リクエストボディとモデルIDを指定します。
    response = bedrock_runtime.invoke_model(
        body=body,  # 上で作成したリクエストボディ。
        modelId='anthropic.claude-v2',  # 呼び出すモデルのID。ここでは、日本語に強いclaude-v2を使用
        accept='application/json',  # 応答の形式としてJSONを指定します。
        contentType='application/json'  # リクエストボディの形式としてJSONを指定します。
    )

    # 応答ボディをJSON形式からPythonオブジェクトにデコードします。これにより、応答の内容をプログラムで扱いやすくなります。
    response_body = json.loads(response['body'].read())

    # デコードした応答ボディを返します。
    return response_body

def bedrock(user_request): 
    role_setting = "西洋ファンタジー専門家です"
    # user_request = "立派な顎を持ち岩も噛み砕く"

    prompt1 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。ファーストネーム・ミドルネームを持つ人間のようなモンスターの名前を生成し、<answer></answer>タグに出力してください。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    response1 = request_bedrock(prompt1)
    monster_name = response1['completion'].strip(" <answer></answer>")
    
    prompt2 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。レベルを10段階で数値にして生成してくれます。『1,2,3,4,5,6,7,8,9,10』の中から設定に合わせて選んでください。レベルは小さいほど弱く、大きほど強いです。論理的に考え、モンスターのレベルを<answer></answer>タグに数値で出力してください。</answer>以降の解説は入りません\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    response2 = request_bedrock(prompt2)
    monster_level = response2['completion'].strip(" <answer></answer>")

    prompt3 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。属性を『火、水、風、土、光、闇』の中から設定に合わせて選んでください。選んだ属性を<answer></answer>タグに出力してください。</answer>以降の解説は入りません\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    response3 = request_bedrock(prompt3)
    monster_element = response3['completion'].strip(" <answer></answer>")
    
    prompt4 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。{monster_name}というモンスターの名前、モンスターの属性である{monster_element}を資料にし、モンスターの特殊能力と特殊能力の説明を<answer>【特殊能力】：特殊能力の説明</answer>タグに100文字以内で出力してください。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request, monster_name=monster_name, monster_element=monster_element)
    response4 = request_bedrock(prompt4)
    monster_ability = response4['completion'].strip(" <answer></answer>")
    
    prompt5 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。{monster_name}というモンスターの名前、モンスターの属性である{monster_element}、モンスターの特殊能力である{monster_ability}を資料にし、モンスターのバックグラウンドがわかる悲しく恐ろしい伝説の言い伝えのエピソードを<answer></answer>タグに100文字以内でお願いします。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request, monster_name=monster_name, monster_element=monster_element, monster_ability=monster_ability)
    response5 = request_bedrock(prompt5)
    monster_episode = response5['completion'].strip(" <answer></answer>")

    # 生成したモンスター情報を辞書で返す
    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode
    }

bot.run(TOKEN)
