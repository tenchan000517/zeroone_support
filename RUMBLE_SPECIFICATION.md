# ランブル機能 仕様書

## 概要
Discordサーバー内でキャリア成長をテーマにしたチーム対戦ゲーム機能。参加者が赤・青の2チームに分かれて6ラウンドのチャレンジを行い、チーム実績スコア（平均点）で勝敗を決定する。

## 基本仕様

### ゲーム形式
- **チーム数**: 2チーム（赤チーム「チャレンジャーズ」、青チーム「ビジネスチーム」）
- **ラウンド数**: 6ラウンド（奇数のため引き分けなし）
- **最低参加人数**: 2人
- **最大参加人数**: 制限なし（ただし表示は各チーム最大10人）
- **制限時間**: コマンド実行時に指定（デフォルト60秒）

### 勝敗判定
- 各ラウンドでチーム実績スコア（平均点）を比較
- 高いスコアのチームが1WIN獲得
- 6ラウンド終了時点で多くのWINを獲得したチームが勝利

## ゲームフロー

### 1. 募集フェーズ
```
/rumble [time_limit]
```
- 管理者・特定ロールのみ実行可能
- 参加者募集エンベッドを表示
- 参加ボタン・退出ボタン・準備完了ボタンを提供
- 制限時間経過後、自動的にゲーム開始

### 2. バトルフェーズ
各ラウンドで以下を実行：

1. **チャレンジ発表** (20秒間隔)
   - ランダムなシナリオを選択・表示

2. **個人パフォーマンス計算**
   - 各プレイヤーに対してランダムなパフォーマンスレベルを決定
   - レベルに応じた得点を付与

3. **チーム結果発表**
   - 各チームの活躍メンバー表示（最大10人）
   - チーム実績スコア（平均点）計算・表示

4. **ラウンド結果**
   - 勝者チーム発表
   - 現在のWIN数表示

### 3. 結果フェーズ
1. **最終結果発表**
   - 勝利チーム発表
   - 最終WIN数表示

2. **MVP表彰**
   - 全6ラウンドの累計個人得点でランキング
   - 最高得点者をMVP表彰
   - TOP5までのランキング表示

## チャレンジカテゴリ

### 1. 📊 ビジネス企画力チャレンジ
新サービス企画、マーケティング戦略、収益モデル構築など

### 2. 🤝 コミュニケーション力チャレンジ
クライアント交渉、チーム士気向上、クレーム対応など

### 3. 💡 問題解決力チャレンジ
システムトラブル解決、予算不足対応、納期遅れリカバリーなど

### 4. 🚀 リーダーシップチャレンジ
新プロジェクト推進、組織改革、困難な決断など

### 5. 🎯 戦略的思考チャレンジ
市場分析、競合動向予測、リスク管理戦略など

### 6. 💪 実行力チャレンジ
計画実行、スケジュール管理、品質効率化など

## パフォーマンス評価システム

### 評価レベルと得点
- **excellent**: 3点（出現率10%）
- **good**: 2点（出現率40%）
- **average**: 1点（出現率40%）
- **poor**: -1点（出現率10%）

### 得点計算
1. 各プレイヤーに基本得点を付与
2. -1〜+1のランダムボーナスを追加
3. 最終得点を-2〜4の範囲でクリップ
4. チーム総得点 ÷ チーム人数 = チーム実績スコア

### 表示制限システム
- **10人制限**: 各ラウンドで各チーム最大10人まで表示
- **全員保証**: 未表示メンバーを優先選出（6ラウンド×10人×2チーム=120枠）
- **履歴管理**: 表示済みメンバーを記録し、公平な露出を確保

## 技術仕様

### ファイル構成
```
cogs/
├── rumble.py          # メイン機能
├── rumble_data.py     # チャレンジ・パフォーマンスデータ
└── RUMBLE_SPECIFICATION.md  # 本仕様書
```

### 主要クラス

#### RumbleGame
ゲーム状態管理
```python
class RumbleGame:
    players: Dict[discord.Member, str]  # プレイヤー: チーム
    ready_players: List[discord.Member] # 準備完了プレイヤー
    in_progress: bool                   # ゲーム進行中フラグ
    channel: discord.TextChannel        # ゲームチャンネル
    time_limit: int                     # 制限時間
```

#### RumbleView
UI管理（参加・退出・準備完了ボタン）
```python
class RumbleView(discord.ui.View):
    game: RumbleGame
    admin_id: str
    displayed_members: Dict[str, set]   # 表示履歴管理
    round_count: int
```

#### AdminRumbleView
管理者専用UI（RumbleViewを継承）
- 準備完了強制機能
- テストユーザー追加機能

#### RumbleCog
Discord.pyコマンド管理
```python
class RumbleCog(commands.Cog):
    active_games: Dict[int, RumbleGame]  # guild_id: game
```

### データ構造

#### CAREER_CHALLENGES
```python
[
    {
        "title": "📊 ビジネス企画力チャレンジ",
        "scenarios": ["シナリオ1", "シナリオ2", ...]
    },
    ...
]
```

#### PERFORMANCE_PATTERNS
```python
{
    "📊 ビジネス企画力チャレンジ": {
        "excellent": [{"action": "行動説明", "points": 3}, ...],
        "good": [{"action": "行動説明", "points": 2}, ...],
        "average": [{"action": "行動説明", "points": 1}, ...],
        "poor": [{"action": "行動説明", "points": -1}, ...]
    },
    ...
}
```

### 主要メソッド

#### run_career_rounds()
6ラウンドのバトル実行
1. チャレンジ発表
2. 個人パフォーマンス計算
3. 表示メンバー選出
4. チーム結果表示
5. ラウンド結果判定

#### calculate_individual_performance()
個人パフォーマンス計算
1. パフォーマンスレベル抽選（重み付き）
2. レベル内でランダムアクション選択
3. ボーナス計算・得点確定

#### select_display_members()
表示メンバー選出ロジック
1. チーム人数チェック（≤10人なら全員表示）
2. 未表示メンバー優先選出
3. 不足分を既表示メンバーから補完

#### announce_mvp()
MVP表彰
1. 全プレイヤーの累計得点集計
2. 最高得点者MVP選出
3. TOP5ランキング表示

## 権限・設定

### 実行権限
- Discord管理者権限
- 特定ロールID: `1236487195741913119`, `1236433752851349656`

### 設定ファイル
```python
# config/config.py
ADMIN_ID = "管理者ID"
```

## エラーハンドリング

### 一般的なエラー
- **権限不足**: 実行権限なしの場合
- **重複実行**: 既にランブル進行中の場合
- **参加者不足**: 最低人数未満での自動開始
- **タイムアウト**: UIコンポーネントのタイムアウト（300秒）

### 技術的エラー
- **AttributeError**: `channel.client`の不正アクセス対策済み
- **ゲーム状態管理**: `active_games`での重複防止
- **非同期処理**: 適切な`await`・`asyncio.sleep`配置

## パフォーマンス考慮

### メッセージ制限
- 大人数参加時の表示制限（10人/チーム）
- 適切な間隔での送信（2-3秒）
- エンベッド形式での見やすい表示

### メモリ管理
- ゲーム終了時の`active_games`クリーンアップ
- 表示履歴の適切な管理

## 拡張性

### 新チャレンジ追加
1. `rumble_data.py`の`CAREER_CHALLENGES`に追加
2. `PERFORMANCE_PATTERNS`に対応パターン追加

### 設定変更
- ラウンド数: `career_challenges`配列の要素数を変更
- 重み付け: `calculate_individual_performance()`内の確率調整
- 表示人数制限: `select_display_members()`の定数変更

### UI拡張
- 新ボタン追加は`RumbleView`クラスに`@discord.ui.button`デコレータで実装
- 管理者機能は`AdminRumbleView`クラスに追加

## テスト項目

### 基本機能
- [ ] ランブル開始・参加・退出
- [ ] チーム振り分け
- [ ] 6ラウンド実行
- [ ] 勝敗判定
- [ ] MVP表彰

### エッジケース
- [ ] 1人チーム vs 多人数チーム
- [ ] 100人規模での動作
- [ ] 同時複数サーバーでの実行
- [ ] 途中離脱・再参加

### パフォーマンス
- [ ] メッセージ送信量の確認
- [ ] レスポンス時間測定
- [ ] メモリ使用量監視

---

**更新履歴**
- 2025-06-14: 初版作成
- 人数制限・表示システム・重み付け調整を反映