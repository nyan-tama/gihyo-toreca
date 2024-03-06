from jinja2 import Environment, FileSystemLoader # HTMLのテンプレートを使えるようになるライブラリ
from weasyprint import HTML # HTMLをPDF保存できるライブラリ
from pdf2image import convert_from_bytes # PDFを画像形式で保存できるライブラリ
from datetime import datetime # 日付用のラブラり
import logging

# モンスター情報をもとにカードを生成し、画像として保存
def generate_card_and_upload_image(monster_info):    
    template_dir = './templates' # テンプレートファイルが格納されているディレクトリを指定
    env = Environment(loader=FileSystemLoader(template_dir)) # Jinja2テンプレートエンジンを初期化してテンプレートをロード
    template = env.get_template('monster_card_template.html') # 使用するテンプレートを指定

    # テンプレートにモンスター情報を渡してHTMLコンテンツを生成
    html_content = template.render(monster_info=monster_info) 

    # HTMLからPDFを生成
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()
    
    # PDFを画像に変換
    images = convert_from_bytes(pdf_bytes)

    # 現在の日時を取得してフォーマット (例: 2023-01-01_12-00-00)
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # ファイル名にモンスターの名前と現在の日時を組み込む
    file_name = f"{monster_info['monster_name'].replace(' ', '_')}_{current_time}.png"

    # 画像を保存
    images[0].save(file_name, format='PNG')
    logging.info(f'画像が保存されました: {file_name}')