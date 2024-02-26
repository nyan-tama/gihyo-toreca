import boto3
import json
import re

# boto3クライアントを初期化
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
translate_client = boto3.client('translate')

def invoke_text_model(prompt):
    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 200,
        'temperature': 0.9,
        'top_k': 180,
        'top_p': 0.9
    })
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-v2',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())

    # <answer></answer>タグで囲まれたテキストを抽出
    match = re.search(r'<answer>(.*?)</answer>', response_body['completion'], re.DOTALL)
    if match:
        return match.group(1).strip()  # タグ内のテキストのみを返す
    else:
        return ""  # マッチしない場合は空文字を返す

def invoke_image_model(prompt):
    body = json.dumps({
        'text_prompts': [{'text': prompt}],
        'cfg_scale': 9,
        'seed': 40,
        'steps': 150
    })

    response = bedrock_runtime.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body['artifacts'][0]['base64']

def translate_text(text, source_language_code, target_language_code):
    response = translate_client.translate_text(
        Text=text,
        SourceLanguageCode=source_language_code,
        TargetLanguageCode=target_language_code
    )
    return response['TranslatedText']

def generate_prompt_for_name(role_setting, user_request):
    return (
        f"Human: {role_setting}として、ユーザーが{user_request}をリクエストしています。"
        "人間らしいファーストネームとミドルネームを持つ、このモンスターの名前を考えて、<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した名前があるならばそれを最優先で反映してください。\n"
        "Assistant: "
    )

def generate_prompt_for_level(role_setting, user_request):
    return (
        f"Human: {role_setting}として、ユーザーが{user_request}をリクエストしています。"
        "1から10までの強さがあり、その数値を<answer></answer>タグ内に記入してください。強さが大きいほど、モンスターは強力です。"
        "ユーザーが指定した強さがあるならばそれを最優先で反映してください。\n"
        "Assistant: "
    )

def generate_prompt_for_element(role_setting, user_request):
    return (
        f"Human: {role_setting}として、ユーザーが{user_request}をリクエストしています。"
        "火、水、風、土、光、闇の中から、最も適した属性を選び、その属性を<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した属性があるならばそれを最優先で反映してください。\n"
        "Assistant: "
    )

def generate_prompt_for_ability(role_setting, user_request):
    return (
        f"Human: {role_setting}として、ユーザーが{user_request}をリクエストしています。"
        "モンスターの特殊能力とその説明を<answer>【特殊能力】：説明</answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した特殊能力があるならばそれを最優先で反映してください。\n"
        "Assistant: "
    )

def generate_prompt_for_episode(role_setting, user_request, prompt_level, monster_element, prompt_ability):
    return (
        f"Human: {role_setting}として、ユーザーが{user_request}をリクエストしています。"
        f"モンスターの属性である{monster_element}、数値が大きいほど強い1~10段階ある強さの中でレベル{prompt_level}、特殊能力が{prompt_ability}であることを考慮してください。"
        "このモンスターの不気味で悲しく謎に満ちた伝説を<answer></answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した伝説があるならばそれを最優先で反映してください。\n"
        "Assistant: "
    )

def generate_prompt_for_image(role_setting, user_request, monster_episode):
    return (
        f"{role_setting}として、{user_request}の画像を生成してください。"
        "彩度が強く鮮やかな色彩と、緻密で詳細なテクスチャを持つファンタジースタイルを希望します。"
        f"モンスターはカードの中心に配置され、背景はモンスターの物語である{monster_episode}の物語を表現する要素で満たされています。"
    )

def generate_monster_bedrock(user_request):
    # 役割の設定
    role_setting = "あなたはファンタジーに詳しいクリエイターです"

    # 各特性のプロンプト成形
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

    prompt_image = generate_prompt_for_image(role_setting, user_request, monster_episode)
    translated_prompt = translate_text(prompt_image, 'ja', 'en')

    monster_image = invoke_image_model(translated_prompt)

    # 結果のレスポンス
    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
        "monster_image": monster_image
    }