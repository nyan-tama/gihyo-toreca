# 使用方法
### 起動方法

```
docker-compose up
```

```
# requirements.txtを修正した場合は一度buildし直し直してから起動する
docker-compose build --no-cache
docker-compose up
```

### 起動確認
コンテナ起動後にコンソール上にHello World!が表示されれば準備OK
アプリはHello World!が表示されて自動で終了する