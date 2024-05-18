# ベースイメージ
FROM mcr.microsoft.com/appsvc/python:3.10_20240321.5.tuxprod

# 作業ディレクトリの設定
WORKDIR /app

# 必要なファイルをコピー
COPY . /app

# 必要なPythonパッケージをインストール
RUN pip install -r requirements.txt

# ポート8000を公開
EXPOSE 8000

# 起動スクリプトの実行
CMD ["./startup.sh"]
