# Discord リアクション集計機能 実装引き継ぎ書

## 📋 現在の実装状況

### ✅ 完了済み機能
- **メッセージカウント機能**: ユーザー・運営別のメッセージ数集計
- **アクティブユーザー数**: メッセージ送信ベースでの正確なカウント
- **ロール別メンバー数統計**: 7つのロール（FIND to DO、イベント情報等）の自動集計
- **定期実行システム**: 毎日0:00の自動データ収集・保存
- **手動収集機能**: `/metrics`コマンドでの即座データ収集
- **ライブ監視機能**: `/metrics_live`コマンドでリアルタイム状況確認
- **設定外部化**: `config/config.py`でのロール設定管理

### 🗄️ データベース構造
現在のテーブル: `discord_metrics`

```sql
-- 主要カラム
id                    TEXT PRIMARY KEY
date                  DATE NOT NULL
member_count          INTEGER NOT NULL
daily_messages        INTEGER NOT NULL
daily_user_messages   INTEGER NOT NULL
daily_staff_messages  INTEGER NOT NULL
active_users          INTEGER NOT NULL
engagement_score      DOUBLE PRECISION NOT NULL

-- JSON統計カラム
channel_message_stats JSONB NOT NULL  -- チャンネル別メッセージ統計
staff_channel_stats   JSONB NOT NULL  -- 運営チャンネル別統計
role_counts          JSONB NOT NULL   -- ロール別メンバー数

-- タイムスタンプ
created_at           TIMESTAMP NOT NULL
updated_at           TIMESTAMP NOT NULL
```

### 📊 データベース確認方法
**重要**: Pythonスクリプトは直接実行できないため、データベース確認が必要な場合は必ずユーザーに依頼すること。

#### 確認用スクリプト例
```python
# 既存のスクリプト使用可能:
# - debug_metrics_insights.py: 基本的なデータ確認
# - comprehensive_metrics_analysis_v2.py: 詳細分析
# - realistic_metrics_analysis.py: 実用的パターン分析

# 新規確認スクリプト作成時のテンプレート:
async def check_database_structure():
    conn = await asyncpg.connect(os.getenv('NEON_DATABASE_URL'))
    
    # テーブル構造確認
    columns = await conn.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'discord_metrics'
        ORDER BY ordinal_position
    """)
    
    # 最新データ確認
    latest = await conn.fetchrow("""
        SELECT * FROM discord_metrics
        ORDER BY date DESC
        LIMIT 1
    """)
    
    await conn.close()
```

### 🔧 現在の設定値（config/config.py）
```python
METRICS_CONFIG = {
    "viewable_role_id": 1236344630132473946,  # 閲覧可能ロール
    "staff_role_id": 1236487195741913119,     # 運営ロール
    "tracked_roles": {
        1332242428459221046: "FIND to DO",      # 103人
        1381201663045668906: "イベント情報",      # 12人
        1382167308180394145: "みんなの告知",      # 8人
        1383347155548504175: "経営幹部",         # 0人
        1383347231188586628: "学生",            # 8人
        1383347303347257486: "フリーランス",      # 0人
        1383347353141907476: "エンジョイ"        # 1人
    }
}
```

## 🎯 次の目標: リアクション集計機能

### 📝 要件定義
1. **メッセージへのリアクション数を集計**
   - 絵文字別のリアクション数
   - チャンネル別のリアクション統計
   - ユーザー別のリアクション付与数

2. **既存システムとの統合**
   - 現在のメトリクス収集と同じタイミングで実行
   - 同じデータベースへの保存
   - 同じ設定システムの利用

### 🚧 実装フェーズ計画

## Phase 1: データベース設計・拡張 【最重要】

### 1.1 テーブル設計検討
**選択肢A: 既存テーブル拡張**
```sql
ALTER TABLE discord_metrics ADD COLUMN reaction_stats JSONB;
```

**選択肢B: 新規テーブル作成**
```sql
CREATE TABLE discord_reactions (
    id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    emoji_name TEXT NOT NULL,
    emoji_id TEXT,  -- カスタム絵文字用
    reaction_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (date) REFERENCES discord_metrics(date)
);
```

**推奨**: 選択肢Aで開始し、データ量に応じて選択肢Bに移行

### 1.2 データ構造設計
```json
// reaction_stats JSONBサンプル
{
  "total_reactions": 245,
  "unique_emojis": 15,
  "channel_reactions": {
    "1236344090086342798": {
      "total": 120,
      "emoji_breakdown": {
        "👍": 45,
        "❤️": 30,
        "😂": 25,
        "custom_emoji_id": 20
      }
    }
  },
  "top_emojis": [
    {"emoji": "👍", "count": 85},
    {"emoji": "❤️", "count": 67}
  ]
}
```

### 1.3 マイグレーション実行
1. **バックアップ作成必須**
   ```bash
   # 実行前に必ずユーザーに依頼
   python backup_database.py
   ```

2. **段階的実行**
   - 開発環境での事前テスト
   - 本番環境での慎重な適用

## Phase 2: リアクション収集機能実装

### 2.1 イベントハンドラー追加
```python
@commands.Cog.listener()
async def on_reaction_add(self, reaction, user):
    """リアクション追加時の処理"""
    
@commands.Cog.listener()  
async def on_reaction_remove(self, reaction, user):
    """リアクション削除時の処理"""
```

### 2.2 データ収集ロジック
```python
async def collect_reaction_metrics(self, guild):
    """日次リアクション統計を収集"""
    # チャンネル別リアクション数取得
    # 絵文字別集計
    # カスタム絵文字対応
    # 時間範囲指定での集計
```

### 2.3 設定拡張
```python
# config/config.py への追加
METRICS_CONFIG = {
    # 既存設定...
    "reaction_tracking": {
        "enabled": True,
        "track_custom_emojis": True,
        "excluded_channels": [],  # 除外チャンネル
        "max_message_age_days": 30  # 過去何日分を対象とするか
    }
}
```

## Phase 3: 既存システム統合

### 3.1 メトリクス収集の統合
```python
async def collect_daily_metrics(self):
    # 既存のメトリクス収集
    metrics = await self.collect_existing_metrics()
    
    # リアクションメトリクス追加
    reaction_metrics = await self.collect_reaction_metrics()
    metrics.update(reaction_metrics)
    
    return metrics
```

### 3.2 表示機能の拡張
- `/metrics`コマンドにリアクション統計追加
- `/metrics_live`にリアルタイムリアクション表示
- 新規コマンド: `/metrics_reactions`

## Phase 4: 品質保証・テスト

### 4.1 テストシナリオ
1. **機能テスト**
   - リアクション追加・削除の正確な検知
   - 複数ユーザーによる同時リアクション
   - カスタム絵文字の正常処理

2. **パフォーマンステスト**
   - 大量リアクションでの処理性能
   - メモリ使用量の監視
   - データベース負荷の確認

3. **エラーハンドリングテスト**
   - メッセージ削除時の対応
   - ユーザー退出時の処理
   - ネットワークエラー時の復旧

### 4.2 監視・ログ強化
```python
# デバッグログ例
print(f"[REACTIONS] リアクション検知: {reaction.emoji} by {user.name}")
logger.info(f"リアクション統計更新: {reaction_count}件")
```

## 🚨 注意点・リスクとその対策

### 1. パフォーマンスリスク
**問題**: リアクションイベントは頻繁に発生
**対策**: 
- メモリ上でのバッチ処理
- 定期的な一括DB更新
- 古いデータの自動削除

### 2. データ整合性リスク
**問題**: リアクション追加・削除の同期
**対策**:
- トランザクション処理の活用
- 定期的な整合性チェック
- 手動修正コマンドの用意

### 3. 権限・プライバシーリスク
**問題**: プライベートチャンネルのリアクション収集
**対策**:
- 既存の権限チェック機能を流用
- 除外チャンネル設定の活用

### 4. ストレージリスク
**問題**: データ量の増大
**対策**:
- JSON圧縮の活用
- 古いデータのアーカイブ
- サマリーデータでの最適化

## 📈 将来的なインサイト拡張案

### Phase 5: 高度なリアクション分析

#### 5.1 エンゲージメント分析
```python
# 新しいメトリクス
reaction_engagement_score = (total_reactions / total_messages) * 100
reaction_diversity_score = unique_emojis / total_reactions
user_reaction_activity = reactions_given / messages_sent
```

#### 5.2 感情分析
```python
# 絵文字カテゴリ分類
emotion_categories = {
    "positive": ["👍", "❤️", "😊", "🎉"],
    "negative": ["👎", "😢", "😡"],
    "neutral": ["🤔", "👀", "📝"]
}
```

#### 5.3 トレンド分析
- 人気絵文字の時系列変化
- チャンネル別リアクション傾向
- ユーザー行動パターン分析

### Phase 6: インタラクション分析

#### 6.1 コミュニティ活性度
```python
community_vitality = {
    "reaction_rate": reactions_per_message,
    "participation_rate": users_with_reactions / total_users,
    "response_speed": avg_time_to_first_reaction
}
```

#### 6.2 コンテンツ評価
- 高評価メッセージの特徴分析
- チャンネル別コンテンツ品質
- 投稿時間帯とリアクション率の相関

### Phase 7: 予測・推奨機能

#### 7.1 予測機能
- 投稿時間帯別リアクション予測
- ユーザー別好み予測
- トレンド絵文字の予測

#### 7.2 推奨機能
- 投稿最適時間の推奨
- コンテンツタイプの推奨
- エンゲージメント向上施策の提案

## 🛠️ 開発環境・ツール

### 必要なライブラリ
```python
# 既存で利用可能
import discord
import asyncpg
import json
from datetime import datetime, timedelta

# 新規追加検討
import emoji  # 絵文字処理
import re     # 正規表現
```

### テスト用コマンド
```python
# 実装時に追加予定
/reaction_test    # テスト用リアクション生成
/reaction_debug   # リアクション収集状況確認
/reaction_reset   # カウンターリセット（開発用）
```

## 📋 引き継ぎチェックリスト

### 事前準備
- [ ] 現在のメトリクス機能の動作確認
- [ ] データベース構造の理解
- [ ] 設定ファイル（config.py）の確認
- [ ] 既存コマンドの動作テスト

### Phase 1実装前
- [ ] データベースバックアップの実行依頼
- [ ] テーブル設計の最終確認
- [ ] マイグレーション手順の策定
- [ ] ロールバック手順の準備

### Phase 2実装中
- [ ] 段階的なコード追加
- [ ] 各機能の単体テスト
- [ ] ログ出力の確認
- [ ] エラーハンドリングの検証

### Phase 3統合時
- [ ] 既存機能への影響確認
- [ ] パフォーマンステスト
- [ ] データ整合性チェック
- [ ] 本番環境での動作確認

### 完了後
- [ ] ドキュメント更新
- [ ] 運用手順書作成
- [ ] 監視・アラート設定
- [ ] バックアップ戦略の見直し

## 📞 サポート体制

### 緊急時の対応
1. **機能停止が必要な場合**
   ```python
   # 緊急停止用設定
   METRICS_CONFIG["reaction_tracking"]["enabled"] = False
   ```

2. **データ修復が必要な場合**
   - ユーザーに分析スクリプト実行を依頼
   - 手動SQL実行の検討

### 問い合わせ窓口
- 技術的質問: この引き継ぎ書を参照
- データベース確認: ユーザーにスクリプト実行を依頼
- 緊急事態: 既存機能への影響最小化を最優先

---

**最後に**: この機能は既存のメトリクス収集システムの自然な拡張です。慎重な段階的実装により、安全で価値のあるインサイト機能を実現できます。不明点があれば、既存コードとこの引き継ぎ書を参照し、必要に応じてユーザーにデータベース確認を依頼してください。

**成功の鍵**: 
1. 既存システムとの一貫性維持
2. 段階的な実装とテスト
3. 十分なログとエラーハンドリング
4. ユーザーとの密な連携