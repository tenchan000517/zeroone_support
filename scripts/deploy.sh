#!/bin/bash

# AWS EC2デプロイスクリプト

echo "=== Kumosan Bot Deployment Script ==="
echo "1. システムパッケージの更新..."
sudo apt update && sudo apt upgrade -y

echo "2. Python環境のセットアップ..."
sudo apt install -y python3 python3-pip python3-venv git

echo "3. プロジェクトディレクトリのセットアップ..."
cd /home/ubuntu
if [ ! -d "zeroone_support" ]; then
    git clone https://github.com/your-username/zeroone_support.git
fi

cd zeroone_support

echo "4. 仮想環境の作成..."
python3 -m venv venv
source venv/bin/activate

echo "5. 依存関係のインストール..."
pip install --upgrade pip
pip install -r requirements.txt

echo "6. 環境変数の設定..."
if [ ! -f ".env" ]; then
    echo "=== .envファイルを作成してください ==="
    echo "cp .env.example .env"
    echo "nano .env"
    exit 1
fi

echo "7. systemdサービスの設定..."
sudo cp systemd/discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-bot.service

echo "8. サービスの起動..."
sudo systemctl start discord-bot.service
sudo systemctl status discord-bot.service

echo "=== デプロイ完了 ==="
echo "ログを確認: sudo journalctl -u discord-bot.service -f"