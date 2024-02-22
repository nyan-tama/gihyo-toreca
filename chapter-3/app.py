import discord
from discord.ext import commands
import logging
import os
import boto3  # ローカルの開発環境からもAWSのサービスを利用するためのライブラリBoto3をインポートします。
import json  # JSON形式のデータの扱いに必要なライブラリをインポートします。
from concurrent.futures import ThreadPoolExecutor ## 非同期実行に必要なThreadPoolExecutorをインポートします。
from io import BytesIO # メモリ上で画像のバイナリデータを扱うためのBytesIOをインポートします。
import base64 # Base64エンコーディング・デコーディングに使用するライブラリをインポートします。同じくイメージ描画の際に使用。


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

    embed_creating = discord.Embed(description="ただいま作成中...", color=discord.Color.gold()) #DiscordにあるEmbed形式はメッセージを見やすくするもの
    await ctx.send(embed=embed_creating)

    # ユーザーのリクエストに基づいてモンスターの情報（テキストと画像）をBedrockで生成します
    monster_info = bedrock(text)

    # 第3回では一旦、生成したモンスターの情報をそのままDiscord上で表示します
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
    # BytesIOオブジェクトを使って、メモリ上に画像を保持します
    with BytesIO(image_data) as image_file:
        # discord.Fileオブジェクトを作成し、画像ファイルとして送信します
        discord_file = discord.File(image_file, filename="monster_image.png")
        await ctx.send(file=discord_file)


# Bedrockに文章生成のリクエストを送信する関数を定義します
def request_bedrock(prompt):
    # AWS Bedrock Runtimeのクライアントを作成します。このクライアントを通じてAWSのサービスにアクセスします
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

    # Bedrock Runtimeのinvoke_modelメソッドを使用してモデルを呼び出します。リクエストボディとモデルIDを指定します。
    response = bedrock_runtime.invoke_model(
    modelId='anthropic.claude-v2',  # 使用するモデルのID。この例では、日本語に強いclaude-v2モデルを指定。
    body=json.dumps({
        'prompt': prompt,  # 生成したい内容の概要や指示を引数から取得
        'max_tokens_to_sample': 200,  # 生成するテキストの最大トークン数（トークン数は文字数に近い）
        'temperature': 0.9,  # 値が大きいほど生成の際に多様性が増します。
        'top_k': 150,  # 値が大きいほど生成の際に多様性が増します
        'top_p': 0.7  # 値が大きいほど生成の際に多様性が増します
    }),
    accept='application/json',  # 応答データの形式。ここではJSON形式を指定します。
    contentType='application/json'  # リクエストデータの形式。このリクエストのボディがJSON形式であることを示します。
)

    # JSON形式に変換
    response_body = json.loads(response['body'].read())

    # リクエストの結果を返します
    return response_body


# Bedrockに画像生成のリクエストを送信する関数を定義します
def request_image_bedrock(prompt):
    # boto3クライアントを初期化します。このクライアントを通じてAWSのサービスにアクセスします。
    client = boto3.client('bedrock-runtime', region_name='us-east-1')

    # Bedrock Runtimeのinvoke_modelメソッドを使用してモデルを呼び出します。リクエストボディとモデルIDを指定します。
    response = client.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',  # 呼び出すモデルのID。ここでは、画像生成に強いStable Diffusionモデルを使用
        body=json.dumps({
            'text_prompts': [{'text': prompt}],  # 生成したい内容の概要や指示を引数から取得
            'cfg_scale': 5,  #値が大きいほどランダム性が高まる
            'seed': 30,  # 生成結果の再現性を保証するためのシード値
            'steps': 120  # 画像生成の品質と精度を高めるためのステップ数
        }),
        contentType='application/json'  # リクエストボディの形式を指定
    )
    
    # JSON形式に変換
    response_body = json.loads(response['body'].read())

    # リクエストの結果を返します
    return response_body


# AWS Translateを使用してテキスト翻訳を行う関数です
def translate_text(text, source_language_code, target_language_code):
    # Boto3ライブラリを使用して、AWSのTranslateサービスにアクセスするためのクライアントオブジェクトを生成します
    translate_client = boto3.client('translate')

    # translate_textメソッドを呼び出して、翻訳を行います
    response = translate_client.translate_text(
        Text=text,
        SourceLanguageCode=source_language_code,
        TargetLanguageCode=target_language_code
    )

    # 翻訳されたテキストをレスポンスから取得して返します
    return response['TranslatedText']


def bedrock(user_request): 
    role_setting = "西洋ファンタジーのクリエイターです"

    # モンスター名生成プロンプト
    prompt1 = (
        "Human: あなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。"
        "ファーストネーム・ミドルネームを持つ人間のようなモンスターの名前を生成し、"
        "<answer></answer>タグに出力してください。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    # request_bedrock関数から結果を取得します
    response1 = request_bedrock(prompt1)
    # AIモデルからのレスポンスのうち、'completion'フィールドに含まれるテキストから、生成されたモンスターの名前だけを取得できます。
    monster_name = response1['completion'].strip(" <answer></answer>")

    # モンスターレベル生成プロンプト
    prompt2 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。"
        "レベルを10段階で数値にして生成してくれます。『1,2,3,4,5,6,7,8,9,10』の中からリクエストに合った強さを選んでください。"
        "レベルは小さいほど弱く、大きほど強いです。モンスターのレベルを<answer></answer>タグに数値で出力してください。</answer>以降の解説は入りません\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    response2 = request_bedrock(prompt2)
    monster_level = response2['completion'].strip(" <answer></answer>")

    # モンスター属性生成プロンプト
    prompt3 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。"
        "属性を『火、水、風、土、光、闇』の中からリクエストに合った属性を選んでください。選んだ属性を<answer></answer>タグに出力してください。</answer>以降の解説は入りません\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request)
    response3 = request_bedrock(prompt3)
    monster_element = response3['completion'].strip(" <answer></answer>")
    
    # モンスター能力生成プロンプト
    prompt4 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。"
        "{monster_name}というモンスターの名前、モンスターの属性である{monster_element}を資料にし、"
        "モンスターの特殊能力と特殊能力の説明を<answer>【特殊能力】：特殊能力の説明</answer>タグに100文字以内で出力してください。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request, monster_name=monster_name, monster_element=monster_element)
    response4 = request_bedrock(prompt4)
    monster_ability = response4['completion'].strip(" <answer></answer>")
    
    # モンスターエピソード生成プロンプト
    prompt5 = (
        "Human: あたなたは{role}。ユーザーは{monster}というモンスターをリクエストしています。"
        "{monster_name}というモンスターの名前、モンスターの属性である{monster_element}、モンスターの特殊能力である{monster_ability}を資料にし、"
        "モンスターのバックグラウンドがわかる悲しく恐ろしい伝説の言い伝えを<answer></answer>タグに100文字以内でお願いします。\n"
        "Assistant: "
    ).format(role=role_setting, monster=user_request, monster_name=monster_name, monster_element=monster_element, monster_ability=monster_ability)
    response5 = request_bedrock(prompt5)
    monster_episode = response5['completion'].strip(" <answer></answer>")

    # モンスター画像生成プロンプト
    prompt6 = (
        "あたなたは{role}。トレーディングカードにふさわしい鮮やかな色彩と、詳細なテクスチャを持つファンタジースタイルを希望します。"
        "ユーザーがリクエストした{monster}というモンスターはカードの中心に配置され、背景はモンスターの物語である{monster_episode}を象徴する要素で満たされています。"
        "モンスターのポーズはモンスターの特殊能力である{monster_ability}を参考に描いて下さい。\n"
    ).format(role=role_setting, monster=user_request, monster_ability=monster_ability, monster_episode=monster_episode)
    # 日本語のプロンプトを英語に翻訳
    en_prompt6 = translate_text(prompt6, 'ja', 'en')
    # 英訳したプロンプトでイメージをリクエスト
    with ThreadPoolExecutor() as executor:
        generate_image_future = executor.submit(request_image_bedrock, en_prompt6)
        generate_image = generate_image_future.result()

    # Base64エンコーディングされたイメージデータを取得
    image_data = generate_image['artifacts'][0]['base64']  # 必要に応じて構造を確認してください

    # 生成したモンスター情報を返す
    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
        "monster_image": image_data,
    }

bot.run(TOKEN)
