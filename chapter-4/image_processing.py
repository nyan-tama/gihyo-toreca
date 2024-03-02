import boto3
import os
from jinja2 import Environment, FileSystemLoader # HTMLのテンプレートを使えるようになるライブラリ
from weasyprint import HTML # HTMLをPDF保存できるライブラリ
from pdf2image import convert_from_bytes # PDFを画像形式で保存できるライブラリ
from io import BytesIO # バイトデータを扱う際に、ファイルのように読み書きするためのライブラリ
import logging

# AWS S3クライアントを初期化
s3_client = boto3.client('s3')

# 環境変数からS3バケット名を取得
bucket_name = os.getenv('S3_BUCKET_NAME')

# 画像をAWS S3バケットにアップロードする関数。
def upload_image_to_s3(image, bucket_name, object_name):
    img_byte_arr = BytesIO() # BytesIOオブジェクトを使用して画像をメモリ上に一時保存
    image.save(img_byte_arr, format='PNG') # 画像をPNG形式で保存
    img_byte_arr = img_byte_arr.getvalue() # BytesIOオブジェクトからバイト列を取得

    # 取得したバイト列を使用してS3に画像をアップロード
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=img_byte_arr, ContentType='image/png')

# モンスター情報をもとにカードを生成し、画像としてAWS S3にアップロードする関数。
def generate_card_and_upload_image(monster_info):    
    template_dir = './templates' # テンプレートファイルが格納されているディレクトリを指定
    env = Environment(loader=FileSystemLoader(template_dir)) # Jinja2テンプレートエンジンを初期化してテンプレートをロード
    template = env.get_template('monster_card_template.html') # 使用するテンプレートを指定

    # テンプレートにモンスター情報を渡してHTMLコンテンツを生成
    html_content = template.render(monster_info=monster_info) 

    # HTMLからPDFを生成
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()
    
    # PDFを画像に変換
    image = convert_from_bytes(pdf_bytes)[0]  # 最初の1ページを指定
    
    # 最初をS3にアップロード
    object_name = f"{monster_info['monster_name'].replace(' ', '_')}.png"  # スペースをアンダースコアに置換
    print(f'{bucket_name}')
    upload_image_to_s3(image, bucket_name, object_name)
    logging.info(f'画像が正常にアップロードされました: s3://{bucket_name}/{object_name}')
