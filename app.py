from flask import Flask
import boto3

app = Flask(__name__)

# アプリの動作確認 Hello Worldが表示される
@app.route('/')
def index():
    return 'Hello World!'

# DockerfileでCMDで指定したコマンドが実行されるので、以下の基本コードは不要
# if __name__ == "__main__":
#     app.run(debug=True)
