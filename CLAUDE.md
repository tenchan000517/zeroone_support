# CLAUDE.md - 開発環境とナレッジ

## SSH接続設定

### EC2サーバー接続情報
- **インスタンス名**: find-to-do
- **ホスト名**: 54.221.32.98
- **ユーザー**: ec2-user
- **SSH鍵**: find-to-do-key2.pem

### WSL環境でのSSH設定

#### 1. SSH鍵とディレクトリのセットアップ
```bash
# SSHディレクトリ作成
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# Windows側からSSH鍵をコピー
cp /mnt/c/Users/tench/.ssh/find-to-do-key2.pem ~/.ssh/

# 適切な権限設定
chmod 600 ~/.ssh/find-to-do-key2.pem
```

#### 2. SSH設定ファイル作成
```bash
# ~/.ssh/config
Host find-to-do
    HostName 54.221.32.98
    User ec2-user
    IdentityFile ~/.ssh/find-to-do-key2.pem
    ServerAliveInterval 60
```

```bash
chmod 600 ~/.ssh/config
```

### トラブルシューティング

#### 接続タイムアウトの場合
1. **基本的な接続確認**
   ```bash
   ping 54.221.32.98
   ```

2. **セキュリティグループ確認**
   - AWSコンソール → EC2 → セキュリティグループ
   - SSH (port 22) のインバウンドルールを確認
   - 現在のIPアドレスが許可されているか確認
   
3. **現在のIPアドレス確認**
   ```bash
   curl -s ifconfig.me
   ```

#### ホストキー検証エラーの場合
```bash
ssh-keyscan -H 54.221.32.98 >> ~/.ssh/known_hosts
```

### 基本的なSSH操作

#### 接続テスト
```bash
ssh find-to-do "echo 'Connection successful'; uptime"
```

#### ボットディレクトリでの作業
```bash
ssh find-to-do "cd zeroone_support && pwd && git status"
```

#### 最新コードの取得とボット再起動
```bash
# コード更新
ssh find-to-do "cd zeroone_support && git pull origin main"

# ボット再起動
ssh find-to-do "sudo systemctl restart discord-bot && sleep 3 && sudo systemctl status discord-bot"
```

## ボット開発ナレッジ

### 主要な設定ファイル
- `config/config.py` - 基本設定とロール設定
- `utils/connpass_manager.py` - オンライン講座情報取得
- `cogs/welcome.py` - Welcome機能
- `cogs/weekly_content.py` - 週間コンテンツ配信

### 最近の修正履歴
- **2025-07-02**: 週間発信機能のロール修正、ConnPass API月境界問題修正、Welcome機能タイミング改善

### 重要なロールID
- オンライン講座情報: `1386289811027005511` (火曜日)
- 最新情報: `1386267058307600525` (水曜日)
- イベント情報: `1381201663045668906` (土曜日)

### デプロイフロー
1. ローカルで修正・テスト
2. GitHubにプッシュ
3. SSH接続でサーバーに移動
4. `git pull origin main`
5. `sudo systemctl restart discord-bot`
6. ステータス確認

## tmuxセッションでのボット起動・管理

### 手動でのボット起動方法（推奨テスト環境）
```bash
# 1. tmuxセッション作成
tmux new-session -d -s discord-bot

# 2. セッションにアタッチ
tmux attach-session -t discord-bot

# 3. ボットディレクトリに移動して起動
cd zeroone_support
python main.py

# または一気に実行
tmux new-session -d -s discord-bot -c /home/ec2-user/zeroone_support 'python main.py'
```

### tmuxセッション管理コマンド
```bash
# セッション一覧確認
tmux list-sessions

# セッションにアタッチ
tmux attach-session -t discord-bot

# セッションから抜ける（ボットは動作継続）
# Ctrl+B → d

# セッションを完全に終了（ボット停止）
# セッション内で Ctrl+C または exit
```

### systemctlサービス管理
```bash
# ボット状態確認
sudo systemctl status discord-bot

# ボット開始
sudo systemctl start discord-bot

# ボット停止
sudo systemctl stop discord-bot

# ボット再起動
sudo systemctl restart discord-bot

# リアルタイムログ確認
sudo journalctl -u discord-bot -f
```

### 運用方針
- **開発・テスト**: tmuxセッション使用（手動制御）
- **本番運用**: systemctlサービス使用（自動再起動）
- **デバッグ**: tmuxセッションでリアルタイム確認