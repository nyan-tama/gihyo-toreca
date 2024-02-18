# 使用方法
### 起動方法

```
docker-compose up
```

```
※もしDockerfileを修正した場合はbuildし直し、起動し直す
docker-compose build --no-cache
docker-compose up
```

### 起動確認

1. ブラウザで `http://localhost:5000` にアクセスする。
3. Hello Worldが表示されれば準備OK

## 本番環境での起動
```
docker build -t gihyo-toreca .
docker run --rm --name linebot-container -p 80:5000 -v "$(pwd)":/app gihyo-toreca
```