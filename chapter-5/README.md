## 使用方法

### アプリの起動方法（Dockerの起動）
```
docker-compose up
```

```
※もしDockerfileおよびrequirements.txtを修正した場合はbuildし直し、起動し直す
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

### Dockerの起動
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