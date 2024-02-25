import boto3
import json
from concurrent.futures import ThreadPoolExecutor

def request_bedrock(prompt):
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-v2',
        body=json.dumps({
            'prompt': prompt,
            'max_tokens_to_sample': 200,
            'temperature': 0.9,
            'top_k': 150,
            'top_p': 0.7
        }),
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body

def request_image_bedrock(prompt):
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    response = client.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',
        body=json.dumps({
            'text_prompts': [{'text': prompt}],
            'cfg_scale': 5,
            'seed': 30,
            'steps': 120
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