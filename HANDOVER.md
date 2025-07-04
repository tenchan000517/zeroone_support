# HANDOVER - 時間別オンラインユーザー収集機能

## 🎯 実装完了事項

### 実装した機能
- **1時間ごとのオンラインユーザー収集システム**
- **FIND to DOロール限定データ収集** (ID: 1332242428459221046)
- **フロントエンド用ガントチャート形式データ構造**
- **24時間分データ統合機能**
- **Discord管理者コマンド** でリアルタイム確認
- **メモリ最適化** (25時間自動削除)

### 📊 データ収集仕様
- **収集間隔**: 1時間ごと (毎時0分)
- **対象ユーザー**: FIND to DOロール所持者のみ
- **データ保持**: 24時間分をメモリ上で管理
- **統合タイミング**: 日次KPI収集時 (毎日0:00)

### 🔧 実装ファイル
- `cogs/metrics_collector.py` - メイン機能 (716行追加)
- `config/config.py` - ガントチャート設定追加

### 📋 利用可能なDiscordコマンド
- `/online_gantt_test` - 現在のオンライン状況をガントチャート形式で表示
- `/hourly_gantt_status` - 24時間分の蓄積データ状況確認
- `/role_filter_test` - 特定ロールのオンライン状況テスト
- `/metrics_live` - ライブメトリクス表示

## 🧪 次のステップ: 動作テスト

### 1. 基本動作確認
```bash
# サーバーでボット再起動
ssh find-to-do "cd zeroone_support && git pull origin main"
ssh find-to-do "sudo systemctl restart discord-bot && sleep 3 && sudo systemctl status discord-bot"
```

### 2. Discordコマンドテスト
- `/online_gantt_test` - 現在のデータ取得テスト
- `/hourly_gantt_status` - 蓄積状況確認
- `/metrics_config` - 設定確認

### 3. 確認ポイント
- [ ] 1時間ごとのデータ収集が正常動作しているか
- [ ] FIND to DOロールユーザーのみ収集されているか
- [ ] メモリ使用量が適切か (25時間で自動削除)
- [ ] データ構造がフロントエンド用に適切か
- [ ] 日次KPI収集との連携が正常か

### 4. ログ確認
```bash
# ボットログでガントチャート関連の動作確認
ssh find-to-do "sudo journalctl -u discord-bot -f | grep -i gantt"
```

## 🔄 システム動作フロー

1. **初期化時**: 現在時刻のデータを即座に収集
2. **毎時0分**: 自動的にオンラインユーザー収集
3. **データ蓄積**: メモリ上で24時間分保持
4. **日次統合**: 毎日0:00に24時間分を統合してKPI保存
5. **メモリ最適化**: 25時間より古いデータは自動削除

## 📈 データ形式

### 時間別スナップショット
```json
{
  "date": "2025-01-01",
  "timestamp": "2025-01-01T15:00:00Z",
  "total_online_users": 5,
  "status_breakdown": {"online": 3, "idle": 2, "dnd": 0},
  "activity_breakdown": {"gaming": 2, "streaming": 1},
  "role_breakdown": {"1332242428459221046": {"role_name": "FIND to DO", "online_count": 5}},
  "online_users": [
    {
      "user_id": "123456789",
      "display_name": "ユーザー名",
      "status": "online",
      "role_ids": ["1332242428459221046"],
      "activity_type": "gaming",
      "timestamp": "2025-01-01T15:00:00Z"
    }
  ]
}
```

## 🎛️ 設定情報

### config.py設定
```python
"gantt_chart_collection": {
    "enabled": True,
    "target_roles": [1332242428459221046],  # FIND to DO
    "collection_interval_hours": 1,
    "data_retention_hours": 25,
    "include_all_users_fallback": False
}
```

## 🚨 トラブルシューティング

### よくある問題
1. **データが収集されない**: 対象ロールが正しく設定されているか確認
2. **メモリ使用量増加**: 25時間での自動削除が正常動作しているか確認
3. **コマンドが応答しない**: 管理者権限があるか確認

### デバッグ方法
- Discord管理者コマンドでリアルタイム確認
- サーバーログでタスク実行状況確認
- メモリ使用量監視

## 📝 最終コミット情報

- **コミットID**: 57c526e
- **コミットメッセージ**: `feat: 時間別オンラインユーザー収集機能とガントチャート用データ収集機能を追加`
- **変更統計**: 716行追加, 2ファイル変更

---

**次のClaude Codeセッションでは、上記の動作テストを実行してシステムの正常動作を確認してください。**