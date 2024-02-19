## 使用方法

### Discordのボットトークンをコンソール上から設定
```
export DISCORD_BOT_TOKEN='あなたのボットのトークン'
```

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
コンテナ起動後にコンソール上にHello World!が表示されれば準備OK
アプリはHello World!が表示されて自動で終了する