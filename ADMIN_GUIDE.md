# DJアイズ 管理者クイックガイド

## 🚀 初期設定（3ステップ）

### 1. 送信先チャンネル設定
```
/weekly_config channel #general
```

### 2. 地域設定（デフォルト：愛知県）
```
/weekly_config regions 愛知県,東京都,大阪府
```

### 3. 設定確認
```
/weekly_config show
```

## 📅 スケジュール変更

### 配信時刻の変更例（月曜9時に変更）
```
/weekly_config schedule weekday:monday hour:9 minute:0
```

### コンテンツ種類の変更例（月曜をビジネストレンドに）
```
/weekly_config schedule weekday:monday content_type:trends
```

### 特定曜日の配信停止
```
/weekly_config schedule weekday:sunday enabled:False
```

## 🧪 テスト配信

```
/weekly_test events     # イベント情報テスト
/weekly_test quotes     # 格言テスト
/weekly_test tech       # テックニュース（リアルタイム）
```

## 📌 メンション設定

```
/weekly_config mention @everyone    # 全員にメンション
/weekly_config mention @起業家      # 特定ロールにメンション
/weekly_config mention none         # メンションなし
```

## ❓ ヘルプ

```
/help_admin            # この管理者ガイドを表示
```

## ⚡ トラブルシューティング

- **配信されない**: `/weekly_config show`で設定確認
- **時刻がずれる**: JST（日本時間）で設定されているか確認
- **エラー発生**: bot.logファイルを確認

---
💡 **Tips**: 配信は設定時刻から10分以内に実行されます（10分間隔チェック）