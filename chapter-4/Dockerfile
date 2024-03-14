# Python 3.9のベースイメージを使用
FROM python:3.9

# 作業ディレクトリを設定
WORKDIR /app

# 第4回用のpoppler-utilsのインストール
RUN apt-get update && \
    apt-get install -y poppler-utils

# AWS認証ファイル格納ディレクトリを作成
RUN mkdir ~/.aws

# 依存関係をコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install -r requirements.txt

# AWSのデフォルトリージョンを設定
ENV AWS_DEFAULT_REGION=ap-northeast-1  

# タイムゾーンを日本時間に設定
ENV TZ=Asia/Tokyo

# コンソールの表示を変えてわかりやすく
RUN echo "alias ls='ls --color=auto'" >> /root/.bashrc
RUN echo "PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@app-container\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> /root/.bashrc

# アプリの実行
CMD ["python", "app.py"]
