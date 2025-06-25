# Discord Bot ↔ ダッシュボード連携ガイド

## 📋 概要
Discord Botのメトリクス収集機能とfind-to-do-management-appのダッシュボード表示を正確に連携させるための統合ガイドです。

## 🔍 現状分析

### Discord Bot側（zeroone_support）の実装
- **ファイル**: `cogs/metrics_collector.py`
- **データベース**: PostgreSQL（Neon）の`discord_metrics`テーブル
- **機能**: リアルタイムメトリクス収集、リアクション追跡、自動保存

### ダッシュボード側（find-to-do-management-app）の実装
- **API**: `/api/discord/metrics`
- **データベース**: Prisma経由でPostgreSQL
- **機能**: メトリクス表示、グラフ、サマリー統計

## 🚨 現在の課題と差異

### 1. データベースアクセス方法の違い
**Discord Bot**: 直接PostgreSQL接続
**ダッシュボード**: Prisma ORM経由

### 2. フィールド名の差異
| Discord Bot (snake_case) | Dashboard (camelCase) | 説明 |
|-------------------------|----------------------|------|
| `member_count` | `memberCount` | 総メンバー数 |
| `online_count` | `onlineCount` | オンライン数 |
| `daily_messages` | `dailyMessages` | 日次メッセージ数 |
| `daily_user_messages` | `dailyUserMessages` | ユーザーメッセージ数 |
| `daily_staff_messages` | `dailyStaffMessages` | 運営メッセージ数 |
| `active_users` | `activeUsers` | アクティブユーザー数 |
| `engagement_score` | `engagementScore` | エンゲージメントスコア |
| `channel_message_stats` | `channelMessageStats` | チャンネル別統計 |
| `staff_channel_stats` | `staffChannelStats` | 運営チャンネル統計 |
| `role_counts` | `roleCounts` | ロール別統計 |

### 3. 新機能の未反映
**Discord Bot側で実装済み、ダッシュボード側未実装:**
- `reaction_stats` - リアクション統計
- 新規ロール（最新情報、オンライン講座情報、AI・テック情報）

### 4. ロール設定の差異
**Discord Bot側（config.py）:**
```python
"tracked_roles": {
    1383347155548504175: "経営幹部",
    1383347231188586628: "学生", 
    1383347303347257486: "フリーランス",
    1383347353141907476: "エンジョイ",
    1332242428459221046: "FIND to DO",
    1381201663045668906: "イベント情報",
    1382167308180394145: "みんなの告知",
    1386267058307600525: "最新情報",        # ←新規追加
    1386289811027005511: "オンライン講座情報", # ←新規追加  
    1386366903395815494: "AI・テック情報"    # ←新規追加
}
```

**ダッシュボード側（ハードコード）:**
```typescript
// 3つの新規ロールが未反映
const roleIds = [
    '1332242428459221046', // FIND to DO
    '1381201663045668906', // イベント情報
    '1382167308180394145', // みんなの告知
    '1383347155548504175', // 経営幹部
    '1383347231188586628', // 学生
    '1383347303347257486', // フリーランス
    '1383347353141907476'  // エンジョイ
];
```

## 🔧 統合ソリューション

### 方法1: API経由でのデータ送信（推奨）

#### Discord Bot側の修正
```python
import aiohttp
import json

async def send_to_dashboard(self, metrics: dict) -> bool:
    """ダッシュボードAPIにメトリクスを送信"""
    try:
        # フィールド名をキャメルケースに変換
        dashboard_metrics = {
            'date': metrics['date'].isoformat(),
            'memberCount': metrics['member_count'],
            'onlineCount': metrics['online_count'],
            'dailyMessages': metrics['daily_messages'],
            'dailyUserMessages': metrics['daily_user_messages'],
            'dailyStaffMessages': metrics['daily_staff_messages'],
            'activeUsers': metrics['active_users'],
            'engagementScore': metrics['engagement_score'],
            'channelMessageStats': metrics['channel_message_stats'],
            'staffChannelStats': metrics['staff_channel_stats'],
            'roleCounts': metrics['role_counts'],
            'reactionStats': metrics.get('reaction_stats', {})  # 新機能
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:3000/api/discord/metrics',  # ダッシュボードURL
                json=dashboard_metrics,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    logger.info("✅ ダッシュボードへの送信成功")
                    return True
                else:
                    logger.error(f"❌ ダッシュボードへの送信失敗: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ ダッシュボード送信エラー: {e}")
        return False

# save_metrics_to_dbメソッドの修正
async def save_metrics_to_db(self, metrics: dict) -> bool:
    """メトリクスをデータベースとダッシュボードに保存"""
    # 1. 既存のDB保存
    db_success = await self._save_to_database(metrics)
    
    # 2. ダッシュボードAPI送信
    api_success = await self.send_to_dashboard(metrics)
    
    if db_success and api_success:
        logger.info("✅ データベース・ダッシュボード両方に保存成功")
        return True
    elif db_success:
        logger.warning("⚠️ データベース保存成功、ダッシュボード送信失敗")
        return True
    else:
        logger.error("❌ データベース保存失敗")
        return False
```

#### 設定の追加
```python
# config/config.py に追加
DASHBOARD_CONFIG = {
    "enabled": True,
    "api_url": "http://localhost:3000/api/discord/metrics",
    "timeout_seconds": 10,
    "retry_attempts": 3
}
```

### 方法2: ダッシュボード側の拡張

#### Prismaスキーマの更新
```prisma
model discord_metrics {
  id                  String   @id @default(cuid())
  date                DateTime @unique @db.Date
  memberCount         Int      @map("member_count")
  onlineCount         Int      @map("online_count")
  dailyMessages       Int      @map("daily_messages")
  dailyUserMessages   Int      @default(0) @map("daily_user_messages")
  dailyStaffMessages  Int      @default(0) @map("daily_staff_messages")
  activeUsers         Int      @map("active_users")
  engagementScore     Float    @map("engagement_score")
  channelMessageStats Json     @default("{}") @map("channel_message_stats")
  staffChannelStats   Json     @default("{}") @map("staff_channel_stats")
  roleCounts          Json     @default("{}") @map("role_counts")
  reactionStats       Json?    @default("{}") @map("reaction_stats") // 新規追加
  createdAt           DateTime @default(now()) @map("created_at")
  updatedAt           DateTime @updatedAt @map("updated_at")
}
```

#### ロールマッピングの更新
```typescript
// src/app/dashboard/discord-insights/page.tsx
const ROLE_MAPPING = {
  '1332242428459221046': 'FIND to DO',
  '1381201663045668906': 'イベント情報',
  '1382167308180394145': 'みんなの告知',
  '1383347155548504175': '経営幹部',
  '1383347231188586628': '学生',
  '1383347303347257486': 'フリーランス',
  '1383347353141907476': 'エンジョイ',
  '1386267058307600525': '最新情報',        // 新規追加
  '1386289811027005511': 'オンライン講座情報', // 新規追加
  '1386366903395815494': 'AI・テック情報'    // 新規追加
};
```

## 📊 データ構造仕様

### メトリクスデータの完全仕様
```typescript
interface DiscordMetrics {
  date: string;                    // ISO日付文字列
  memberCount: number;             // 総メンバー数
  onlineCount: number;             // オンライン数
  dailyMessages: number;           // 日次総メッセージ数
  dailyUserMessages: number;       // 日次ユーザーメッセージ数
  dailyStaffMessages: number;      // 日次運営メッセージ数
  activeUsers: number;             // アクティブユーザー数
  engagementScore: number;         // エンゲージメントスコア
  
  // JSON構造データ
  channelMessageStats: {
    [channelId: string]: {
      user_messages: number;
      user_count: number;
    }
  };
  
  staffChannelStats: {
    [channelId: string]: {
      staff_messages: number;
      staff_count: number;
    }
  };
  
  roleCounts: {
    [roleId: string]: {
      name: string;
      count: number;
    }
  };
  
  // 新機能: リアクション統計
  reactionStats?: {
    total_reactions: number;
    unique_emojis: number;
    reaction_users: number;
    channel_reactions: {
      [channelId: string]: {
        total_reactions: number;
        unique_emojis: number;
        emoji_breakdown: { [emoji: string]: number };
      }
    };
    top_emojis: Array<{
      emoji: string;
      count: number;
    }>;
  };
}
```

## 🚀 実装手順

### Phase 1: 基本連携の確立
1. **Discord Bot側**: API送信機能の追加
2. **テスト**: ローカル環境での動作確認
3. **ダッシュボード側**: 新規ロールの表示対応

### Phase 2: リアクション機能の統合
1. **ダッシュボード側**: Prismaスキーマ更新
2. **UI拡張**: リアクション統計の表示コンポーネント追加
3. **API拡張**: リアクションデータの受信対応

### Phase 3: 運用最適化
1. **エラーハンドリング**: API通信の冗長性確保
2. **監視**: ダッシュボード側でのデータ更新確認
3. **パフォーマンス**: データ送信の最適化

## 🔍 動作確認チェックリスト

### Discord Bot側
- [ ] `/metrics` コマンドで新規ロールが表示される
- [ ] `/metrics_reactions` でリアクション統計が表示される
- [ ] ダッシュボードAPIへの送信ログが確認できる

### ダッシュボード側
- [ ] 新規ロール（最新情報、オンライン講座情報、AI・テック情報）が表示される
- [ ] リアクション統計セクションが表示される（実装時）
- [ ] メトリクスデータがリアルタイムで更新される

## 🚨 注意事項

1. **データ整合性**: Bot側とダッシュボード側の両方でデータ保存を行う場合、整合性チェックが必要
2. **API可用性**: ダッシュボードが停止していてもBot機能に影響しないよう設計
3. **セキュリティ**: API通信の認証・認可の検討
4. **ログ監視**: 送信失敗やデータ不整合の早期発見

## 📈 期待される成果

この統合により、以下が実現されます：

1. **リアルタイム表示**: Discord Botで収集したメトリクスが即座にダッシュボードに反映
2. **包括的インサイト**: メッセージ統計とリアクション統計の統合表示
3. **運営効率化**: 1つのダッシュボードでDiscordコミュニティの全体像把握
4. **スケーラビリティ**: 新機能追加時の容易な拡張性

---

**最終更新**: 2025-06-25
**作成者**: Claude Code
**対象システム**: Discord Bot (zeroone_support) ↔ find-to-do-management-app