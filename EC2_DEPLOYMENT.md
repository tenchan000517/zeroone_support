# EC2でDJアイズを永続稼働させる手順

## 1. EC2にSSH接続
```bash
ssh find-to-do
```

## 2. 必要なソフトウェアのインストール

### Python 3.8以上の確認・インストール
```bash
python3 --version
# もし3.8未満なら以下を実行
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

### Git・その他必要なパッケージ
```bash
sudo apt install git tmux htop
```

## 3. Botのセットアップ

### リポジトリのクローン
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/zeroone_support.git
cd zeroone_support
```

### 仮想環境の作成と有効化
```bash
python3 -m venv venv
source venv/bin/activate
```

### 依存関係のインストール
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 環境変数の設定
```bash
cp .env.example .env
nano .env
```

以下の値を設定：
```
DISCORD_BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_discord_user_id
WEATHER_API_KEY=your_weather_api_key
GEMINI_API_KEY=your_gemini_api_key
DOORKEEPER_API_TOKEN=NC-ZoRfPLtR3xFZaHiEM

# チャンネルIDは実際のDiscordサーバーから取得
MAIN_CHAT_CHANNEL=channel_id
BOT_SALON_CHANNEL=channel_id
# ... 他のチャンネルID
```

## 4. データベースの初期化
```bash
python3 -c "from models.database import init_db; init_db()"
```

## 5. 動作テスト
```bash
python3 main.py
```
正常に起動したらCtrl+Cで停止

## 6. tmuxで永続稼働

### tmuxセッション作成
```bash
tmux new -s dj-eyes
```

### Bot起動
```bash
cd ~/zeroone_support
source venv/bin/activate
python3 main.py
```

### tmuxセッションから離脱
`Ctrl+B` → `D`

### セッションに再接続する場合
```bash
tmux attach -t dj-eyes
```

## 7. systemdサービス化（推奨）

### サービスファイル作成
```bash
sudo nano /etc/systemd/system/dj-eyes.service
```

内容：
```ini
[Unit]
Description=DJ Eyes Discord Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/zeroone_support
Environment=PATH=/home/ubuntu/zeroone_support/venv/bin
ExecStart=/home/ubuntu/zeroone_support/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### サービスの有効化と起動
```bash
sudo systemctl daemon-reload
sudo systemctl enable dj-eyes
sudo systemctl start dj-eyes
```

### サービス状態確認
```bash
sudo systemctl status dj-eyes
```

### ログ確認
```bash
sudo journalctl -u dj-eyes -f
```

## 8. メンテナンス

### 更新手順
```bash
cd ~/zeroone_support
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart dj-eyes
```

### バックアップ
```bash
# データベースのバックアップ
cp bot_data.db bot_data.db.backup.$(date +%Y%m%d)

# ログのバックアップ
cp bot.log bot.log.backup.$(date +%Y%m%d)
```

## 9. 監視設定（オプション）

### 自動再起動スクリプト
```bash
nano ~/check_bot.sh
```

内容：
```bash
#!/bin/bash
if ! systemctl is-active --quiet dj-eyes; then
    echo "DJ Eyes is down. Restarting..."
    sudo systemctl restart dj-eyes
    echo "Restarted at $(date)" >> ~/dj-eyes-restart.log
fi
```

### crontabに追加
```bash
chmod +x ~/check_bot.sh
crontab -e
# 以下を追加
*/5 * * * * /home/ubuntu/check_bot.sh
```

## トラブルシューティング

### Botが起動しない
1. トークンが正しいか確認
2. Python環境を確認
3. エラーログを確認: `cat bot.log`

### メモリ不足
```bash
# スワップファイル作成
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### ポート開放が必要な場合
EC2のセキュリティグループでHTTPS(443)を開放（通常は不要）