import boto3
from weasyprint import HTML
from pdf2image import convert_from_bytes
from io import BytesIO
import logging

# AWS S3クライアントを初期化
s3_client = boto3.client('s3')

def upload_image_to_s3(image, bucket_name, object_name):
    # BytesIOオブジェクトを作成して画像を保存
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    # 画像をS3バケットにアップロード
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=img_byte_arr, ContentType='image/jpeg')

def generate_card_and_upload_image(monster_info):
    # バケット名とオブジェクト名のプレフィックスを静的に指定
    bucket_name = 'your-s3-bucket-name'
    object_prefix = 'your-object-prefix'
    
    try:
        # HTMLコンテンツを生成
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Monster Details</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Noto Sans JP', sans-serif;
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
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # PDFを画像に変換
        images = convert_from_bytes(pdf_bytes)
        
        # 生成された最初の画像をS3にアップロード
        if images:
            image = images[0]
            object_name = f"{object_prefix}.jpeg"
            upload_image_to_s3(image, bucket_name, object_name)
            logging.info(f'画像が正常にアップロードされました: s3://{bucket_name}/{object_name}')
    except Exception as e:
        logging.error(f'PDF生成または画像のS3へのアップロード中にエラーが発生しました: {e}')
