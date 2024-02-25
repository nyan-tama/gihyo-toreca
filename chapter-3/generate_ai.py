import boto3
import json
import logging


# boto3クライアントを初期化
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
translate_client = boto3.client('translate')

def invoke_text_model(prompt):
    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 200,
        'temperature': 0.9,
        'top_k': 150,
        'top_p': 0.7
    })
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-v2',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body['completion'].strip(" <answer></answer>")

def invoke_image_model(prompt):
    body = json.dumps({
        'text_prompts': [{'text': prompt}],
        'cfg_scale': 5,
        'seed': 30,
        'steps': 120
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
        f"Human: {role_setting}として、{user_request}に名前を付けてください。"
        "人間らしいファーストネームとミドルネームを持つ、このモンスターの名前を考えて、<answer></answer>タグ内に記入してください。\n"
        "Assistant: "
    )

def generate_prompt_for_level(role_setting, user_request):
    return (
        f"Human: {role_setting}として、{user_request}の強さのレベルを設定してください。"
        "1から10までのスケールで、適切なレベルを選び、その数値を<answer></answer>タグ内に記入してください。レベルが高いほど、モンスターは強力です。\n"
        "Assistant: "
    )

def generate_prompt_for_element(role_setting, user_request):
    return (
        f"Human: {role_setting}として、{user_request}にどの属性を与えるか決定してください。"
        "火、水、風、土、光、闇の中から、最も適した属性を選び、その属性を<answer></answer>タグ内に記入してください。\n"
        "Assistant: "
    )

def generate_prompt_for_ability(role_setting, user_request):
    return (
        f"Human: {role_setting}として、{user_request}に基づく特殊能力を100文字以内で考えてください。"
        f"モンスターの特殊能力とその説明を<answer>【特殊能力】：説明</answer>タグ内に簡潔に記述してください。\n"
        "Assistant: "
    )

def generate_prompt_for_episode(role_setting, user_request, prompt_level, monster_element, prompt_ability):
    return (
        f"Human: {role_setting}として、{user_request}のバックグラウンドがわかる悲しく恐ろしい言い伝えを100文字以内で考えてください。"
        f"モンスターの属性である{monster_element}、数値が大きいほど強い1~10段階ある強さの中でレベル{prompt_level}、特殊能力が{prompt_ability}であることを考慮してください。"
        f"作成したエピソードを<answer></answer>タグ内に記入してください。\n"
        f"Assistant: "
    )

def generate_prompt_for_image(role_setting, user_request, monster_ability, monster_episode):
    return (
        f"{role_setting}として、{user_request}の画像を生成してください。"
        f"トレーディングカードにふさわしい鮮やかな色彩と、詳細なテクスチャを持つファンタジースタイルを希望します。"
        f"モンスターはカードの中心に配置され、背景はモンスターの物語である{monster_episode}を象徴する要素で満たされています。"
        f"モンスターのポーズは特殊能力である{monster_ability}を参考に描いてください。"
    )

def bedrock(user_request):
    role_setting = "あなたはファンタジーに詳しい知識人で画家"

    # 各特性のプロンプト生成
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

    # モンスター画像生成
    image_prompt = generate_prompt_for_image(role_setting, user_request, monster_ability, monster_episode)
    translated_prompt = translate_text(image_prompt, 'ja', 'en')
    monster_image = invoke_image_model(translated_prompt)

    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
        "monster_image": monster_image
    }