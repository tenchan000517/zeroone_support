# DJアイズ Discord Bot 必要権限

## 必須権限

### 基本権限
- ✅ **メッセージを読む** (View Channels)
- ✅ **メッセージを送信** (Send Messages)
- ✅ **埋め込みリンク** (Embed Links)
- ✅ **メンションの送信** (@everyone, @here, ロール)

### 高度な権限
- ✅ **メッセージ履歴を読む** (Read Message History)
- ✅ **リアクションを追加** (Add Reactions)
- ✅ **スラッシュコマンドを使用** (Use Application Commands)
- ✅ **メッセージの管理** (Manage Messages) - ロールパネル用
- ✅ **ロールの管理** (Manage Roles) - ロール付与機能用

### チャンネル権限
- ✅ **チャンネルを見る** (View Channel)
- ✅ **ウェブフックの管理** (Manage Webhooks) - オプション

## 推奨権限値
```
権限整数値: 537133184
```

## Botの招待URL例
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=537133184&scope=bot%20applications.commands
```

## 権限設定時の注意点

1. **ロール階層**: Botのロールは、管理したいロールより上位に配置
2. **チャンネル権限**: 特定チャンネルへの送信権限を個別設定可能
3. **@everyone権限**: サーバー設定で@everyoneメンションを許可する必要あり

## セキュリティ推奨事項

- 不要な権限は付与しない
- 管理者権限は付与しない
- 定期的に権限を見直す
- ボット専用のロールを作成する