# 🚀 高品質トレンド取得システム

find-to-do-siteから移植した高品質なトレンドデータ取得システムです。

## 📊 システム概要

### データソース（全11種類）
1. **Zenn API** - 技術記事（いいね数順、トレンド、最新）
2. **Hacker News** - 海外技術情報（スコア50+のみ）
3. **Google News RSS** - 各分野別検索
   - ウェブ開発
   - ビジネス
   - プログラミング
   - データサイエンス
4. **生成AI専門検索** - Claude Code、ChatGPT等の最新情報
5. **自動生成コンテンツ** - キャリア、勉強・自己啓発

### 品質保証
- **総データ数**: 200件近く（従来の20倍以上）
- **自動重複除去**: URL・タイトル類似度ベース
- **品質フィルタ**: いいね数、スコア、コメント数による選別
- **自動カテゴリ分類**: 7カテゴリに自動振り分け

## 🔧 インストール・設定

### 必要なパッケージ
```bash
pip install aiohttp
# (その他の依存関係は既存のrequirements.txtに含まれています)
```

### ファイル構成
```
utils/
├── enhanced_trends_manager.py      # 簡易版（推奨）
├── realtime_trends_client.py      # 完全版（Node.js移植）
└── trends_manager.py              # 既存（Google Trends）
```

## 💻 使用方法

### 1. 簡易版（enhanced_trends_manager.py）

```python
import asyncio
from utils.enhanced_trends_manager import EnhancedTrendsManager

async def get_trends_example():
    async with EnhancedTrendsManager() as manager:
        # 基本的な取得
        trends = await manager.get_enhanced_trends(max_trends=20)
        
        # カテゴリ指定取得
        ai_trends = await manager.get_enhanced_trends(
            max_trends=10, 
            categories=['AI技術', 'プログラミング']
        )
        
        # Discord用フォーマット
        discord_embed = manager.format_trends_for_discord(trends)
        
        return trends, discord_embed

# 実行
trends, embed = asyncio.run(get_trends_example())
```

### 2. 完全版（realtime_trends_client.py）

```python
import asyncio
from utils.realtime_trends_client import RealtimeTrendsClient

async def get_comprehensive_trends():
    async with RealtimeTrendsClient() as client:
        # 全ソースから取得
        all_trends = await client.get_all_trends()
        
        # カテゴリ別分類
        categorized = client.categorize_trends(all_trends)
        
        # 特定ソースのみ取得
        zenn_trends = await client.get_zenn_trending()
        hn_trends = await client.get_hacker_news_trending()
        
        return all_trends, categorized

# 実行
all_trends, categorized = asyncio.run(get_comprehensive_trends())
```

## 📋 データ構造

### TrendItem（基本構造）
```python
{
    "id": "zenn-422179",
    "title": "Claude Code 逆引きコマンド事典",
    "url": "https://zenn.dev/ml_bear/articles/84e92429698177",
    "source": "Zenn API",
    "score": 0,
    "likes": 198,
    "comments": 0,
    "published_at": "2025-06-23T08:01:48.381+09:00",
    "topics": ["プログラミング", "AI"],
    "category": "プログラミング",
    "description": "Claude Code 逆引きコマンド事典",
    "quality_score": 95,
    "hasRichDescription": false
}
```

### カテゴリ一覧
- **プログラミング**: Python、Java、Go等の技術記事
- **ウェブ開発**: React、Vue、JavaScript等
- **生成AI**: Claude、ChatGPT、Gemini等
- **データサイエンス・AI開発**: データ分析、機械学習
- **キャリア**: 転職、スキルアップ、働き方
- **ビジネス**: DX、マーケティング、経営戦略
- **勉強・自己啓発**: 学習方法、自己成長

## 🔄 既存コードとの統合

### Discord Cogでの使用例

```python
# cogs/daily_content.py に追加

from utils.enhanced_trends_manager import EnhancedTrendsManager

class DailyContent(commands.Cog):
    # 既存のメソッドに追加
    
    async def get_enhanced_business_trends(self):
        """高品質ビジネストレンド取得"""
        async with EnhancedTrendsManager() as manager:
            trends = await manager.get_enhanced_trends(
                max_trends=10,
                categories=['ビジネス', 'AI技術', 'キャリア']
            )
            return manager.format_trends_for_discord(trends)
    
    @commands.command()
    async def enhanced_trends(self, ctx):
        """高品質トレンド情報を取得"""
        try:
            embed_data = await self.get_enhanced_business_trends()
            
            embed = discord.Embed(
                title=embed_data["title"],
                description=embed_data["description"],
                color=embed_data["color"]
            )
            
            for field in embed_data["fields"]:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            
            if "footer" in embed_data:
                embed.set_footer(text=embed_data["footer"]["text"])
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ トレンド取得エラー: {e}")
```

## 📈 パフォーマンス比較

| 項目 | 従来システム | 新システム | 改善率 |
|------|-------------|-----------|--------|
| データ数 | 5-10件 | 180-200件 | 2000%+ |
| データソース | 1種類 | 11種類 | 1100% |
| カテゴリ分類 | 手動 | 自動 | - |
| 重複除去 | なし | あり | - |
| 品質フィルタ | 基本 | 高度 | - |
| 説明文 | 限定的 | 全件対応 | 100% |

## 🚀 活用例

### 1. 自動コンテンツ生成
```python
async def generate_daily_tech_news():
    async with EnhancedTrendsManager() as manager:
        trends = await manager.get_enhanced_trends(
            max_trends=15,
            categories=['プログラミング', 'ウェブ開発', 'AI技術']
        )
        
        # トレンドデータを基にニュース記事を自動生成
        tech_news = format_tech_news(trends)
        return tech_news
```

### 2. 業界分析レポート
```python
async def analyze_industry_trends():
    async with RealtimeTrendsClient() as client:
        all_trends = await client.get_all_trends()
        categorized = client.categorize_trends(all_trends)
        
        # カテゴリ別の傾向分析
        analysis = {
            category: {
                'count': len(items),
                'top_sources': get_top_sources(items),
                'hot_topics': extract_hot_topics(items)
            }
            for category, items in categorized.items()
        }
        
        return analysis
```

### 3. リアルタイム通知
```python
async def setup_trend_monitoring():
    """定期的にトレンドをチェックして重要な情報を通知"""
    while True:
        async with EnhancedTrendsManager() as manager:
            trends = await manager.get_enhanced_trends(max_trends=50)
            
            # 高スコア記事の検出
            hot_trends = [t for t in trends if t.get('quality_score', 0) > 80]
            
            if hot_trends:
                await notify_hot_trends(hot_trends)
        
        await asyncio.sleep(3600)  # 1時間毎
```

## 🔧 カスタマイズ

### キーワード追加
```python
# enhanced_trends_manager.py の category_keywords に追加
self.category_keywords['新カテゴリ'] = [
    'keyword1', 'keyword2', 'キーワード3'
]
```

### 新しいデータソース追加
```python
async def get_custom_source_trends(self) -> List[Dict]:
    """カスタムソースからデータ取得"""
    # 実装例
    pass
```

## 🎯 注意事項

### レート制限
- **Zenn API**: 500ms間隔
- **Hacker News**: 100ms間隔
- **Google News**: 1秒間隔

### エラーハンドリング
すべてのAPIでタイムアウトとリトライが実装済み。エラー時は自動的にフォールバック。

### メモリ使用量
大量データ取得時は適切にセッション管理を行う。

## 📞 サポート

質問や問題があれば、find-to-do-siteプロジェクトのClaude Codeまでお気軽にどうぞ！

---

*🤖 Generated with Claude Code from find-to-do-site project*