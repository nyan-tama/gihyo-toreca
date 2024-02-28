import boto3  # AWSのサービスにアクセスするためのライブラリ
import json  # JSONデータを扱うためのライブラリ
import re  # 正規表現を使用するためのライブラリ

# AWSのBoto3クライアントを初期化して、Bedrock Runtimeサービスにアクセスする準備
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

# テキスト生成モデルを呼び出し、指定されたプロンプトに基づいてテキストを生成する関数
def invoke_text_model(prompt):

    # 文章生成に必要なパラメータを設定
    body = json.dumps({
        'prompt': prompt,
        'temperature': 0.9,
        'top_p': 0.9,
        'top_k': 180,
        'max_tokens_to_sample': 200,
    })

    # 指定した基盤モデル『anthropic.claude-v2』でBedrockに生成をリクエスト
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-v2',
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    # Bedrockからの応答を読み込み、JSONオブジェクトとして解析
    response_body = json.loads(response['body'].read())

    # <answer></answer>タグで囲まれたテキストを抽出
    match = re.search(r'<answer>(.*?)</answer>', response_body['completion'], re.DOTALL)
    if match:
        return match.group(1).strip()  # タグ内の『回答テキスト』のみを返す
    else:
        return ""  # マッチしない場合は空文字を返す

# モンスターの名前を生成するためのプロンプトを作成
def generate_prompt_for_name(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "人間らしいファーストネームとミドルネームを持つ、このモンスターの名前を考えて、<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した名前があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# モンスターの強さのレベル（1から10まで）を決定するためのプロンプトを作成
def generate_prompt_for_level(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "1から10までの強さがあり、その数値を<answer></answer>タグ内に記入してください。強さが大きいほど、モンスターは強力です。"
        "ユーザーが指定した強さがあるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# モンスターの属性（火、水、風、土、光、闇）を決定するためのプロンプトを作成
def generate_prompt_for_element(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "火、水、風、土、光、闇の中から、最も適した属性を選び、その属性を<answer></answer>タグ内に記入してください。"
        "ユーザーが指定した属性があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# モンスターの特殊能力とその説明を生成するためのプロンプトを作成
def generate_prompt_for_ability(role_setting, user_request):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        "モンスターの特殊能力とその説明を<answer>【特殊能力】：説明</answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した特殊能力があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# モンスターの伝説や背景ストーリーを生成するためのプロンプトを作成
def generate_prompt_for_episode(role_setting, user_request, prompt_level, monster_element, prompt_ability):
    return (
        f"\n\nHuman: {role_setting}、ユーザーが{user_request}をリクエストしています。"
        f"モンスターの属性である{monster_element}、数値が大きいほど強い1~10段階ある強さの中でレベル{prompt_level}、特殊能力が{prompt_ability}であることを考慮してください。"
        "このモンスターの不気味で悲しく謎に満ちた伝説を<answer></answer>タグ内に100文字程度で記述してください。"
        "ユーザーが指定した伝説があるならばそれを最優先で反映してください。"
        "\n\nAssistant: "
    )

# generate_ai.pyにおいてのメイン関数
def generate_monster_bedrock(user_request):
    # 役割の設定 このあとのプロンプト成形の際に必要なテクニック
    role_setting = "あなたはファンタジーに詳しいクリエイターです"

    # 生成したい項目ごとに『generate_prompt_for_xxxx』としてプロンプト成形関数を用意している
    # 下記はモンスター名をの生成するためのプロンプトを作成
    prompt_name = generate_prompt_for_name(role_setting, user_request)
    # 基盤モデルにプロンプトを送信し、生成されたテキストからモンスターの名前生成
    monster_name = invoke_text_model(prompt_name)

    # モンスターの強さを生成するためのプロンプトを作成  
    prompt_level = generate_prompt_for_level(role_setting, user_request)
    # モンスターの強さを生成
    monster_level = invoke_text_model(prompt_level)

    # モンスターの属性を生成するためのプロンプトを作成  
    prompt_element = generate_prompt_for_element(role_setting, user_request)
    # モンスターの属性を生成
    monster_element = invoke_text_model(prompt_element)

    # モンスターの能力を生成するためのプロンプトを作成  
    prompt_ability = generate_prompt_for_ability(role_setting, user_request)
    # モンスターの能力を生成
    monster_ability = invoke_text_model(prompt_ability)

    # モンスターの伝説を生成するためのプロンプトを作成  
    prompt_episode = generate_prompt_for_episode(role_setting, user_request, monster_level, monster_element, monster_ability)
    # モンスターの伝説を生成
    monster_episode = invoke_text_model(prompt_episode)

    # 呼び出し元(app.py）へ生成結果のレスポンス
    return {
        "monster_name": monster_name,
        "monster_level": monster_level,
        "monster_element": monster_element,
        "monster_ability": monster_ability,
        "monster_episode": monster_episode,
    }