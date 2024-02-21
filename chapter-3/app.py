import discord
from discord.ext import commands
import logging
import os
import boto3  # AWS SDK for Python (Boto3) をインポートします。AWSのサービスをPythonから使うために必要です。
import json  # JSONデータのエンコード（PythonオブジェクトをJSON形式の文字列に変換）およびデコード（JSON形式の文字列をPythonオブジェクトに変換）に使用します。
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import base64


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

    embed_creating = discord.Embed(description="ただいま作成中...", color=discord.Color.gold())
    await ctx.send(embed=embed_creating)

    # ユーザーからのリクエストを基にしてモンスター情報を生成
    monster_info = bedrock(text)

    # 生成した文章を Embed で作成
    embed_result = discord.Embed(title="生成できました！", color=discord.Color.green())
    embed_result.add_field(name="モンスター名", value=monster_info['monster_name'], inline=False)
    embed_result.add_field(name="レベル", value=monster_info['monster_level'], inline=False)
    embed_result.add_field(name="属性", value=monster_info['monster_element'], inline=False)
    embed_result.add_field(name="特殊能力", value=monster_info['monster_ability'], inline=False)
    embed_result.add_field(name="伝説", value=monster_info['monster_episode'], inline=False)

    # テキスト結果を送信
    await ctx.send(embed=embed_result)

    # イメージ結果を送信
    image_data_base64 = monster_info['monster_image']
    image_data = base64.b64decode(image_data_base64)
    # BytesIOオブジェクトを使って、メモリ上に画像を保持します。
    with BytesIO(image_data) as image_file:
        # discord.Fileオブジェクトを作成し、画像ファイルとして送信します。
        discord_file = discord.File(image_file, filename="monster_image.png")
        await ctx.send(file=discord_file)


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


def request_image_bedrock(prompt):
    client = boto3.client('bedrock-runtime',region_name='us-east-1')

    response = client.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',
        body=json.dumps({
            'text_prompts': [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": 5,
            "seed": 30,
            "steps": 120
        }),
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())

    return response_body


def translate_text(text, source_language_code, target_language_code):
    translate_client = boto3.client('translate')
    response = translate_client.translate_text(
        Text=text,
        SourceLanguageCode=source_language_code,
        TargetLanguageCode=target_language_code
    )
    return response['TranslatedText']

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

    # 画像生成
    prompt6 = "あたなたは{role}。トレーディングカードにふさわしい鮮やかな色彩と、詳細なテクスチャを持つファンタジースタイル。ユーザーがリクエストした{monster}というモンスターはカードの中心に配置され、背景はモンスターの物語である{monster_episode}を象徴する要素で満たされています。モンスターのポーズはモンスターの特殊能力である{monster_ability}を参考に描いて下さい。".format(
        role=role_setting,
        monster=user_request,
        monster_name=monster_name,
        monster_element=monster_element,
        monster_ability=monster_ability,
        monster_episode=monster_episode
    )
    # 日本語のプロンプトを英語に翻訳
    en_prompt6 = translate_text(prompt6, 'ja', 'en')
    # 英訳したプロンプトでイメージをリクエスト
    with ThreadPoolExecutor() as executor:
        generate_image_future = executor.submit(request_image_bedrock, en_prompt6)
        generate_image = generate_image_future.result()

    # Base64エンコーディングされたイメージデータを取得
    image_data = generate_image['artifacts'][0]['base64']  # 必要に応じて構造を確認してください

    # 生成したモンスター情報を辞書で返す
    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
        "monster_image": image_data,
    }

bot.run(TOKEN)
