# Discord → LINE Bot 通知システム設計書

## 📋 概要
特定のDiscordチャンネルでの活動を監視し、LINEボットを通じてリマインド通知を送信するシステムの設計仕様です。

## 🎯 監視対象チャンネルと通知条件

### 1. WELCOM チャンネル (ID: 1236341987272032316)
**通知条件**: メンバーが新規参入した時
- ✅ ボット除外
- 📢 通知内容: 新規メンバー情報

### 2. 自己紹介チャンネル (ID: 1373946891334844416)
**通知条件**: メンバーが自己紹介を投稿した時
- ✅ ボット除外
- ✅ リプライ除外（新規投稿のみ）
- 📢 通知内容: 自己紹介投稿情報

### 3. 雑談チャンネル (ID: 1236344090086342798)
**通知条件**: メンバー発言後、運営が1時間以上応答しない場合
- ✅ ボット除外
- ⏰ 監視間隔: 10分ごと
- ⚠️ アラート: 運営不在1時間以上
- 📢 通知内容: 運営不在アラート

### 4. 誰でも告知チャンネル (ID: 1330790111259922513)
**通知条件**: メンバーが告知を投稿した時
- ✅ ボット除外
- 📢 通知内容: 新規告知投稿情報

## 📊 通知データ構造

### 基本通知フォーマット
```json
{
  "type": "notification_type",
  "channel": "チャンネル名",
  "user": {
    "name": "ユーザー表示名",
    "id": "ユーザーID",
    "avatar": "アバターURL"
  },
  "message": {
    "content": "メッセージ内容（切り詰め版）",
    "timestamp": "2025-06-25T09:30:00",
    "jump_url": "https://discord.com/channels/..."
  },
  "notification_message": "LINE表示用メッセージ"
}
```

### 1. 新規参入通知 (new_member)
```json
{
  "type": "new_member",
  "channel": "WELCOM",
  "user": {
    "name": "新規ユーザー",
    "id": "123456789",
    "avatar": "https://cdn.discordapp.com/avatars/..."
  },
  "message": {
    "content": "はじめまして！よろしくお願いします！",
    "timestamp": "2025-06-25T09:30:00",
    "jump_url": "https://discord.com/channels/..."
  },
  "notification_message": "🎉 新しいメンバーが WELCOM チャンネルに参加しました！"
}
```

### 2. 自己紹介通知 (introduction)
```json
{
  "type": "introduction",
  "channel": "自己紹介",
  "user": {
    "name": "ユーザー名",
    "id": "123456789",
    "avatar": "https://cdn.discordapp.com/avatars/..."
  },
  "message": {
    "content": "初めまして！エンジニアをしています。プログラミングが好きで...",
    "timestamp": "2025-06-25T10:15:00",
    "jump_url": "https://discord.com/channels/..."
  },
  "notification_message": "📝 新しい自己紹介が投稿されました！"
}
```

### 3. 運営不在アラート (staff_absence)
```json
{
  "type": "staff_absence",
  "channel": "雑談",
  "absence_duration": {
    "hours": 1,
    "minutes": 30,
    "total_minutes": 90
  },
  "notification_message": "⚠️ 雑談チャンネルで運営の応答が1時間以上ありません (1時間30分経過)"
}
```

### 4. 告知投稿通知 (announcement)
```json
{
  "type": "announcement",
  "channel": "誰でも告知",
  "user": {
    "name": "告知者",
    "id": "123456789",
    "avatar": "https://cdn.discordapp.com/avatars/..."
  },
  "message": {
    "content": "【重要】来月のイベントについてお知らせです。日時：7月15日（土）...",
    "timestamp": "2025-06-25T14:00:00",
    "jump_url": "https://discord.com/channels/..."
  },
  "notification_message": "📢 新しい告知が投稿されました！"
}
```

### 5. テスト通知 (test)
```json
{
  "type": "test",
  "channel": "テストチャンネル",
  "user": {
    "name": "管理者",
    "id": "987654321",
    "avatar": "https://cdn.discordapp.com/avatars/..."
  },
  "message": {
    "content": "これはテスト通知です",
    "timestamp": "2025-06-25T12:00:00",
    "jump_url": "https://discord.com/channels/test"
  },
  "notification_message": "🧪 テスト通知が送信されました"
}
```

## 🔧 設定項目

### config.py の設定
```python
CHANNEL_NOTIFICATIONS = {
    "enabled": True,
    "line_webhook_url": "https://your-line-bot-webhook-url",  # LINE Bot WebhookURL
    
    "monitored_channels": {
        "1236341987272032316": {  # WELCOM
            "name": "WELCOM",
            "type": "new_member",
            "exclude_bots": True,
            "notification_message": "🎉 新しいメンバーが WELCOM チャンネルに参加しました！"
        },
        "1373946891334844416": {  # 自己紹介
            "name": "自己紹介",
            "type": "new_post", 
            "exclude_bots": True,
            "exclude_replies": True,
            "notification_message": "📝 新しい自己紹介が投稿されました！"
        },
        "1236344090086342798": {  # 雑談
            "name": "雑談",
            "type": "staff_absence_monitoring",
            "exclude_bots": True,
            "staff_absence_hours": 1,
            "notification_message": "⚠️ 雑談チャンネルで運営の応答が1時間以上ありません"
        },
        "1330790111259922513": {  # 誰でも告知
            "name": "誰でも告知",
            "type": "announcement",
            "exclude_bots": True,
            "notification_message": "📢 新しい告知が投稿されました！"
        }
    }
}
```

## 🚀 実装機能

### Discord Bot側 (cogs/channel_notifications.py)

#### イベントリスナー
- `on_message`: メッセージ監視と分類処理
- 各チャンネルタイプ別の処理メソッド

#### 定期タスク
- `staff_absence_monitor`: 10分間隔での運営不在監視

#### 管理コマンド
- `/notifications_status`: 通知機能の状態確認
- `/notifications_test`: テスト通知送信

#### 主要メソッド
```python
async def _send_notification(self, notification_data)
    # LINE Bot Webhookに通知データを送信

async def _handle_welcome_message(self, message, channel_config)
    # WELCOM チャンネル処理

async def _handle_introduction_message(self, message, channel_config)
    # 自己紹介チャンネル処理

async def _handle_chat_monitoring(self, message, channel_config, is_staff)
    # 雑談チャンネル監視

async def _handle_announcement_message(self, message, channel_config)
    # 告知チャンネル処理

async def _send_staff_absence_alert(self, channel_config, absence_duration)
    # 運営不在アラート送信
```

## 🔄 LINE Bot側の実装要件

### Webhook受信エンドポイント
LINE Bot側では以下のエンドポイントでDiscordからの通知を受信します：

```
POST /webhook/discord-notifications
Content-Type: application/json
```

### 推奨実装フロー
1. **通知受信**: Discord Botからの通知データを受信
2. **データ検証**: 必須フィールドの存在確認
3. **フォーマット変換**: LINEメッセージ形式に変換
4. **配信**: 管理者やスタッフグループに送信
5. **ログ記録**: 通知履歴の保存

### LINE メッセージフォーマット例

#### 新規参入通知
```
🎉 新しいメンバーが参加しました！

👤 ユーザー: 新規ユーザー
📍 チャンネル: WELCOM
💬 メッセージ: "はじめまして！よろしくお願いします！"
🔗 Discordで確認: https://discord.com/channels/...

⏰ 2025-06-25 09:30
```

#### 運営不在アラート
```
⚠️ 運営応答アラート

📍 チャンネル: 雑談
⏱️ 不在時間: 1時間30分
📝 メンバーからの発言に運営の応答がありません

対応をお願いします 🙏

⏰ 2025-06-25 10:45
```

## 📈 監視とログ

### Discord Bot側ログ
```
📢 [NOTIFICATIONS] メッセージ検知: ユーザー名 in チャンネル名 (運営: False)
🎉 [NOTIFICATIONS] 新規参入通知送信: ユーザー名
👮 [NOTIFICATIONS] 運営発言記録: 運営者名
⚠️ [NOTIFICATIONS] 運営不在アラート送信: 1時間30分
✅ LINE通知送信成功: introduction
❌ LINE通知送信失敗(500): Internal Server Error
```

### 設定可能項目
- `staff_absence_hours`: 運営不在アラートの閾値時間
- `monitoring_interval`: 監視タスクの実行間隔
- `message_content_limit`: 通知メッセージの文字数制限
- `retry_attempts`: LINE送信のリトライ回数

## 🔧 運用・保守

### 管理者向け機能
1. **`/notifications_status`**: 現在の通知状態確認
2. **`/notifications_test`**: LINE連携テスト
3. **設定変更**: config.pyでの細かな調整

### トラブルシューティング
1. **LINE送信失敗**: Webhook URL、ネットワーク接続確認
2. **通知が来ない**: チャンネルIDの確認、Bot権限チェック
3. **重複通知**: 監視ロジックのデバッグ

### セキュリティ考慮事項
- LINE Webhook URLの適切な管理
- 通知データに個人情報が含まれる場合の配慮
- Bot権限の最小限化

---

**実装完了日**: 2025-06-25  
**作成者**: Claude Code  
**対象システム**: Discord Bot (zeroone_support) → LINE Bot  
**バージョン**: 1.0