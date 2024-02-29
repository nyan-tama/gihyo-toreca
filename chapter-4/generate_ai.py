import boto3
import json
import re

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
# AWS Translateサービスにアクセスするため、Boto3を使って連携します。
translate_client = boto3.client('translate')

def invoke_text_model(prompt):

    body = json.dumps({
        'prompt': prompt,
        'temperature': 0.9,
        'top_p': 0.9,
        'top_k': 180,
        'max_tokens_to_sample': 200,
    })

    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-v2',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())

    match = re.search(r'<answer>(.*?)</answer>', response_body['completion'], re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return ""

# 画像生成モデルを呼び出し、指定されたプロンプトに基づいて画像を生成する関数です。
def invoke_image_model(prompt):
    # 画像生成に必要なパラメータを指定します。
    body = json.dumps({
        'text_prompts': [{'text': prompt}],
        'cfg_scale': 9,
        'steps': 150,
        'seed': 40,
    })
    # Bedrock Runtimeのinvoke_modelメソッドを使用して、画像生成モデルにリクエストを送信します。
    response = bedrock_runtime.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    # レスポンスボディをJSONオブジェクトとして読み込み、画像データ（Base64化されている）を返します。
    response_body = json.loads(response['body'].read())
    
    return response_body['artifacts'][0]['base64']

# AWS Translateを利用してテキストを翻訳する関数です。
def translate_text(text, source_language_code, target_language_code):
    # Translateサービスのtranslate_textメソッドを使用して翻訳を実行します。
    response = translate_client.translate_text(
        Text=text,
        SourceLanguageCode=source_language_code,
        TargetLanguageCode=target_language_code
    )
    # 翻訳されたテキストを返します。
    return response['TranslatedText']

def generate_prompt_for_name(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "人間らしいファーストネームとミドルネームを持つ、このモンスターの名前を考えて、<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した名前があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

def generate_prompt_for_level(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "1から10までの強さがあり、その数値を<answer></answer>タグ内に記入してください。強さが大きいほど、モンスターは強力です。"
        "ユーザーが指定した強さがあるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

def generate_prompt_for_element(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "火、水、風、土、光、闇の中から、最も適した属性を選び、その属性を<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した属性があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

def generate_prompt_for_ability(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "モンスターの特殊能力とその説明を<answer>【特殊能力】：説明</answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した特殊能力があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

def generate_prompt_for_episode(role_setting, user_request, prompt_level, monster_element, prompt_ability):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        f"モンスターの属性である{monster_element}、数値が大きいほど強い1~10段階ある強さの中でレベル{prompt_level}、特殊能力が{prompt_ability}であることを考慮してください。"
        "このモンスターの不気味で悲しく謎に満ちた伝説を<answer></answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した伝説があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# モンスターの画像を生成するためのプロンプトを成形する関数
def generate_prompt_for_image(role_setting, user_request, monster_episode):
    return (
        f"{role_setting}として、{user_request}の画像を生成してください。"
        "彩度が強く鮮やかな色彩と、緻密で詳細なテクスチャを持つファンタジースタイルを希望します。"
        f"モンスターは絵の中心に配置され、背景はモンスターの物語である{monster_episode}の物語を表現する要素で満たされています。"
    )

def generate_monster_bedrock(user_request):
    role_setting = "あなたはファンタジーに詳しいクリエイターです"

    prompt_name = generate_prompt_for_name(role_setting, user_request)
    monster_name = invoke_text_model(prompt_name)

    prompt_level = generate_prompt_for_level(role_setting, user_request)
    monster_level = invoke_text_model(prompt_level)

    prompt_element = generate_prompt_for_element(role_setting, user_request)
    monster_element = invoke_text_model(prompt_element)

    prompt_ability = generate_prompt_for_ability(role_setting, user_request)
    monster_ability = invoke_text_model(prompt_ability)

    prompt_episode = generate_prompt_for_episode(role_setting, user_request, monster_level, monster_element, monster_ability)
    monster_episode = invoke_text_model(prompt_episode)

    # モンスターの画像を生成するためのプロンプトを作成  
    prompt_image = generate_prompt_for_image(role_setting, user_request, monster_episode)
    # AWS Translateを利用して英訳する
    translated_prompt = translate_text(prompt_image, 'ja', 'en')

    # イメージを生成
    monster_image = invoke_image_model(translated_prompt)


    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
        "monster_image": monster_image # 生成イメージの返却を追加

    }