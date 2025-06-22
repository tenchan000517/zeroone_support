# 🔗 Discord RSS連携 実装ドキュメント

## 📋 概要

FIND to DO サイトのブログ記事生成時に、zeroone_support Discord Botが自動でDiscordチャンネルに通知を投稿する機能の実装仕様書。

## 🎯 実装完了状況

### ✅ find-to-do-site側（完了済み）

#### 1. RSS生成ライブラリ
**ファイル**: `src/lib/rss.ts`
- `generateRSSFeed()`: RSS 2.0フォーマット生成
- `addNewArticleToRSS()`: 新記事をRSSに追加
- `generateRSSItemsFromExistingBlogs()`: 既存記事からRSSアイテム生成

#### 2. ブログ生成プロセスとの統合
**ファイル**: `src/scripts/generate-blog.ts`
- ブログ記事保存後に自動でRSS更新
- `/public/rss.xml` の自動生成・更新

#### 3. RSS出力先
**URL**: `https://find-to-do.com/rss.xml`
**ローカル**: `http://localhost:3000/rss.xml`

## 🤖 zeroone_support側実装要件

### 📝 新規作成ファイル
`cogs/rss_monitor.py`

### 🔧 実装機能

#### 1. RSS監視機能
```python
# 監視設定
RSS_URL = "https://find-to-do.com/rss.xml"
CHECK_INTERVAL = 600  # 10分間隔
```

#### 2. 新記事検出ロジック
- RSS XMLをパースして最新記事を取得
- 前回チェック時からの新しい`<item>`を検出
- 記事の`<guid>`をキーとして重複チェック

#### 3. Discord投稿フォーマット
```python
# 投稿内容例
embed = discord.Embed(
    title="🆕 新しいブログ記事が公開されました！",
    description=f"**{article_title}**",
    color=0x0099ff,
    url=article_url
)
embed.add_field(name="🏷️ カテゴリ", value=category, inline=True)
embed.add_field(name="📅 公開日", value=pub_date, inline=True)
embed.add_field(name="💡 概要", value=description, inline=False)
embed.set_footer(text="FIND to DO Blog")
```

## 📊 RSSフィード構造

### XML形式
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>FIND to DO - 学生向けプログラミング支援ブログ</title>
    <link>https://find-to-do.com</link>
    <description>プログラミング初心者の学生・インターン向けの技術情報やキャリアガイドを配信</description>
    <lastBuildDate>[UTC時刻]</lastBuildDate>
    
    <item>
      <title><![CDATA[記事タイトル]]></title>
      <link>https://find-to-do.com/news-blog/[category]/[slug]</link>
      <description><![CDATA[記事の要約]]></description>
      <pubDate>[RFC 2822形式の日時]</pubDate>
      <guid isPermaLink="true">https://find-to-do.com/news-blog/[category]/[slug]</guid>
      <category><![CDATA[カテゴリ名]]></category>
    </item>
  </channel>
</rss>
```

### データ項目説明

| 項目 | 説明 | 例 |
|------|------|-----|
| `<title>` | 記事タイトル | "学生向けプログラミングインターンシップの探し方" |
| `<link>` | 記事URL | "https://find-to-do.com/news-blog/intern/student-guide" |
| `<description>` | 記事要約（150文字程度） | "プログラミング初心者の学生がインターン..." |
| `<pubDate>` | 公開日時（UTC） | "Sat, 22 Jun 2025 01:00:00 GMT" |
| `<guid>` | 一意識別子（記事URL） | "https://find-to-do.com/news-blog/intern/student-guide" |
| `<category>` | カテゴリ名 | "インターン", "技術", "キャリア" |

## 🔄 動作フロー

### 1. ブログ記事生成時
```
ブログ生成 → 記事保存 → RSS更新 → /public/rss.xml 生成
```

### 2. Discord通知時
```
RSS監視 → 新記事検出 → Discord Embed生成 → チャンネル投稿
```

## ⚙️ 設定項目

### zeroone_support設定ファイル
```python
# config/config.py に追加
RSS_CONFIG = {
    "enabled": True,
    "url": "https://find-to-do.com/rss.xml",
    "check_interval": 600,  # 秒（10分間隔）
    "channel_id": 123456789012345678,  # 投稿先チャンネルID
    "last_check_file": "data/rss_last_check.json"
}
```

## 🧪 テスト手順

### 1. RSS生成テスト
```bash
# find-to-do-site
npm run generate
curl https://find-to-do.com/rss.xml
```

### 2. Discord Bot テスト
```python
# zeroone_support
# RSS監視機能の単体テスト
!rss_test
```

### 3. 統合テスト
1. find-to-do-siteでブログ記事生成
2. RSS更新確認
3. Discord Botの新記事検出・投稿確認

## 📋 実装チェックリスト

### find-to-do-site（✅ 完了）
- [x] `src/lib/rss.ts` 作成
- [x] `src/scripts/generate-blog.ts` 統合
- [x] RSS自動生成機能
- [x] 記事メタデータ抽出

### zeroone_support（⏳ 実装待ち）
- [ ] `cogs/rss_monitor.py` 作成
- [ ] RSS XMLパース機能
- [ ] 新記事検出ロジック
- [ ] Discord Embed投稿機能
- [ ] 設定ファイル追加
- [ ] スケジューラー統合

## 🚨 注意事項

### エラーハンドリング
- RSS取得失敗時の処理
- XMLパースエラー時の処理
- Discord API制限時の処理

### パフォーマンス
- RSS取得の非同期処理
- 大量記事時のメモリ使用量
- Discord API Rate Limit対応

### セキュリティ
- RSS URL検証
- XSS対策（Embed内容のサニタイズ）
- 不正なXMLへの対処

---

**作成日**: 2025年6月22日  
**担当**: Claude Code  
**次回担当者**: zeroone_support開発チーム  

## 🚀 実装開始用プロンプト

```
zeroone_support Discord Botに RSS監視機能を追加してください。

RSS URL: https://find-to-do.com/rss.xml
新記事検出時にDiscordチャンネルに自動投稿する機能を実装。

詳細仕様: /mnt/c/find-to-do-site/DISCORD_RSS_INTEGRATION.md
参考: 既存の cogs/daily_content.py のパターンに従って実装
```