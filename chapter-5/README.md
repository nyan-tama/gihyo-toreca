## 使用方法

### アプリの起動方法（Dockerの起動）
```
docker-compose up
```

```
# requirements.txtを修正した場合は一度buildし直し直してから起動する
docker-compose build --no-cache
docker-compose up
```

### 起動確認
コンテナ起動後にログが表示されれば準備OK

### アプリの停止（Dockerの停止）
```
Ctrl + C
```

---

## 本番環境での起動
### DockerfileからDockerイメージを作成
```
docker build --no-cache -t gihyo-toreca .
```

### Dockerの起動 第五回ではSecret Managerを設定したので、環境変数のオプションは不要になります。
```
# Dockerイメージを起動 
docker run --rm -it --name app-container -v "$(pwd)":/app gihyo-toreca
```
### 起動確認
コンテナ起動後にログが表示されれば準備OK

### アプリの停止（Dockerの停止）
```
Ctrl + C
```