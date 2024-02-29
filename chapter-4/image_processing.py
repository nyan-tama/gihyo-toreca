import boto3
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pdf2image import convert_from_bytes
from io import BytesIO
import logging


# AWS S3クライアントを初期化
s3_client = boto3.client('s3')

def upload_image_to_s3(image, bucket_name, object_name):
    # BytesIOオブジェクトを作成して画像を保存
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # 画像をS3バケットにアップロード
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=img_byte_arr, ContentType='image/jpeg')

def generate_card_and_upload_image(monster_info):
    # バケット名とオブジェクト名のプレフィックスを静的に指定
    bucket_name = "upload-image-20240229-1030"
    
    try:
        # テンプレートエンジンを設定
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('monster_card_template.html')

        # HTMLコンテンツを生成
        html_content = template.render(monster_info=monster_info)

        # HTMLからPDFを生成
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # PDFを画像に変換
        images = convert_from_bytes(pdf_bytes)
        
        # 生成された最初の画像をS3にアップロード
        if images:
            image = images[0]
            object_name = f"{monster_info['monster_name'].replace(' ', '_')}.png"  # スペースをアンダースコアに置換
            upload_image_to_s3(image, bucket_name, object_name)
            logging.info(f'画像が正常にアップロードされました: s3://{bucket_name}/{object_name}')
    except Exception as e:
        logging.error(f'PDF生成または画像のS3へのアップロード中にエラーが発生しました: {e}')
