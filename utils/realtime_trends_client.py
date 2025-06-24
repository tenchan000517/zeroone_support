# -*- coding:utf-8 -*-
"""
Realtime Trends Client
Node.js版の高品質トレンド取得システムをPythonに移植

オリジナル: find-to-do-site/src/lib/realtime-trends.ts
移植者: Claude Code

機能:
- Zenn API: 技術記事（いいね数順、トレンド、最新）
- Hacker News: 海外技術情報
- GitHub Trending: 人気リポジトリ  
- Google News RSS: 日本語技術ニュース
- 各分野専門記事取得
- 自動カテゴリ分類
- 重複除去システム
"""

import aiohttp
import asyncio
import json
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
from urllib.parse import quote

@dataclass
class TrendItem:
    """トレンドアイテムの統一データ構造"""
    id: str
    title: str
    url: str
    score: int = 0
    likes: int = 0
    comments: int = 0
    source: str = ""
    published_at: str = ""
    topics: List[str] = None
    category: str = ""
    description: str = ""
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []

class RealtimeTrendsClient:
    """リアルタイムトレンド取得クライアント"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.seen_urls: Set[str] = set()
        
        # カテゴリ別キーワード辞書（Node.js版から移植）
        self.category_keywords = {
            'プログラミング': [
                'programming', 'code', 'coding', 'algorithm', 'data structure', 
                'clean code', 'refactoring', 'software engineering', 'design pattern',
                'プログラミング', 'アルゴリズム', 'データ構造', 'ソフトウェア工学',
                'python', 'rust', 'go', 'java', 'c++', 'c#', 'kotlin', 'swift',
                'ruby', 'php', 'scala', 'dart',
                'node.js', 'express', 'fastify', 'nest.js', 'spring', 'django',
                'flask', 'laravel', 'rails'
            ],
            'ウェブ開発': [
                'javascript', 'typescript', 'es6', 'es2024', 'vanilla js',
                'frontend', 'web development', 'html', 'css', 'sass', 'tailwind', 'bootstrap',
                'フロントエンド', 'ウェブ開発', 'フロントエンド開発', 'ウェブサイト制作',
                'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'gatsby',
                'react native', 'vue3', 'react hooks', 'vue composition',
                'css grid', 'flexbox', 'css modules', 'styled components',
                'responsive', 'mobile-first', 'レスポンシブ', 'レスポンシブデザイン',
                'pwa', 'spa', 'ssr', 'ssg', 'jamstack',
                'web components', 'web assembly', 'service worker', 'websocket'
            ],
            '生成AI': [
                'AI', '人工知能', '機械学習', 'ディープラーニング', 'ニューラルネットワーク',
                'artificial intelligence', 'machine learning', 'deep learning',
                'neural network', 'transformer', 'gpt', 'llm', 'claude', 'chatgpt',
                'openai', 'anthropic', 'gemini', 'bard', 'copilot',
                '生成AI', 'generative ai', 'prompt engineering', 'fine-tuning',
                'rag', 'retrieval augmented generation', 'llama', 'mistral'
            ],
            'データサイエンス・AI開発': [
                'データサイエンス', 'データ分析', 'python', 'pandas', '統計', '可視化', '予測',
                'data science', 'data analysis', 'statistics', 'visualization',
                'big data', 'ビッグデータ', 'データマイニング', 'analytics',
                'jupyter', 'notebook', 'matplotlib', 'seaborn', 'plotly',
                'tensorflow', 'pytorch', 'scikit-learn', 'numpy', 'scipy'
            ],
            'キャリア': [
                'キャリア', '転職', 'スキル', '年収', '面接', '履歴書', '成長',
                'career', 'job change', 'skill', 'salary', 'interview', 'resume',
                'フリーランス', 'リモートワーク', '副業', 'エンジニア転職',
                'スキルアップ', 'キャリアアップ', '働き方', 'ワークライフバランス'
            ],
            'ビジネス': [
                'ビジネス', '戦略', 'マーケティング', '売上', '成長', 'ROI', 'KPI',
                'business', 'strategy', 'marketing', 'sales', 'growth',
                'スタートアップ', 'DX', 'デジタル変革', 'イノベーション',
                '経営', '事業', '起業', 'IPO', 'M&A', '投資'
            ],
            '勉強・自己啓発': [
                '学習', '勉強', 'スキルアップ', '成長', '習慣', '効率', '継続',
                'learning', 'study', 'skill up', 'growth', 'habit', 'efficiency',
                '読書', 'オンライン学習', 'MOOC', 'Udemy', 'Coursera'
            ]
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; TrendBot/1.0)',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_trends(self) -> List[TrendItem]:
        """すべてのソースからトレンドを取得（Node.js版のgetAllTrends相当）"""
        print("🌐 統合トレンド取得開始")
        all_trends = []
        
        try:
            # 並行取得でパフォーマンス向上
            tasks = [
                self.get_zenn_trending(),
                self.get_hacker_news_trending(),
                self.get_web_dev_trends(),
                self.get_business_trends(),
                self.get_programming_trends(),
                self.get_data_science_trends(),
                self.get_ai_tech_trends()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_trends.extend(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ 一部取得エラー: {result}")
            
            # 重複除去
            unique_trends = self._remove_duplicates(all_trends)
            
            print(f"📊 統合トレンド取得完了: {len(unique_trends)}件（重複除去前: {len(all_trends)}件）")
            return unique_trends
            
        except Exception as e:
            print(f"❌ 統合取得エラー: {e}")
            return []
    
    async def get_zenn_trending(self) -> List[TrendItem]:
        """Zenn API - 最優秀ソース（80件取得、高品質記事20%）"""
        results = []
        
        try:
            endpoints = [
                'https://zenn.dev/api/articles?order=liked_count&count=100',
                'https://zenn.dev/api/articles?order=trending&count=50',
                'https://zenn.dev/api/articles?order=latest&count=30'
            ]
            
            for endpoint in endpoints:
                try:
                    print(f"📚 Zenn API取得中: {endpoint}")
                    
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('articles'):
                                for article in data['articles']:
                                    # 品質フィルタを緩和: いいね20+またはいいね10+ AND コメント3+
                                    liked_count = article.get('liked_count', 0)
                                    comments_count = article.get('comments_count', 0)
                                    
                                    is_high_quality = (liked_count > 20 or 
                                                     (liked_count > 10 and comments_count > 3))
                                    
                                    if is_high_quality:
                                        trend_item = TrendItem(
                                            id=f"zenn-{article.get('id')}",
                                            title=article.get('title', ''),
                                            url=f"https://zenn.dev{article.get('path', '')}",
                                            likes=liked_count,
                                            comments=comments_count,
                                            source='Zenn API',
                                            published_at=article.get('published_at', ''),
                                            topics=[t.get('name', '') for t in article.get('topics', [])]
                                        )
                                        results.append(trend_item)
                    
                    # レート制限対策: 500ms待機
                    await asyncio.sleep(0.5)
                    
                except Exception as endpoint_error:
                    print(f"❌ Zenn API エンドポイントエラー: {endpoint} - {endpoint_error}")
            
            print(f"✅ Zenn API取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ Zenn API取得エラー: {error}")
            return []
    
    async def get_hacker_news_trending(self) -> List[TrendItem]:
        """Hacker News API - 高品質（30件取得、海外技術情報）"""
        results = []
        
        try:
            print("🌍 Hacker News API取得開始")
            
            # Step 1: トップストーリーIDを取得
            top_stories_url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
            async with self.session.get(top_stories_url) as response:
                if response.status != 200:
                    raise Exception(f"Top stories取得失敗: {response.status}")
                
                top_stories = await response.json()
                if not isinstance(top_stories, list):
                    raise Exception('Invalid top stories format')
            
            # Step 2: 上位30件の個別記事を取得
            for story_id in top_stories[:30]:
                try:
                    item_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                    async with self.session.get(item_url) as item_response:
                        if item_response.status == 200:
                            item = await item_response.json()
                            
                            # 品質フィルタ: スコア50+、タイトルあり、URLあり
                            if (item.get('type') == 'story' and 
                                item.get('score', 0) > 50 and
                                item.get('title') and 
                                item.get('url')):
                                
                                trend_item = TrendItem(
                                    id=f"hn-{story_id}",
                                    title=item.get('title', ''),
                                    url=item.get('url', ''),
                                    score=item.get('score', 0),
                                    comments=item.get('descendants', 0),
                                    source='Hacker News',
                                    published_at=datetime.fromtimestamp(
                                        item.get('time', 0)
                                    ).isoformat() + 'Z'
                                )
                                results.append(trend_item)
                    
                    # API制限対策
                    await asyncio.sleep(0.1)
                    
                except Exception as item_error:
                    print(f"⚠️ HN item取得エラー: {story_id} - {item_error}")
                    continue
            
            print(f"✅ Hacker News取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ Hacker News取得エラー: {error}")
            return []
    
    async def get_web_dev_trends(self) -> List[TrendItem]:
        """ウェブ開発記事取得開始"""
        print("🌐 ウェブ開発記事取得開始")
        results = []
        
        try:
            # Zenn記事フィルタリング
            zenn_web_trends = await self._get_zenn_filtered_articles('web development')
            results.extend(zenn_web_trends)
            
            # Google News検索
            web_keywords = ['React 開発', 'Vue.js フロントエンド', 'JavaScript フレームワーク', 
                           'ウェブ開発 最新', 'CSS フレームワーク']
            
            for keyword in web_keywords:
                google_trends = await self._get_google_news_by_keyword(keyword, 'ウェブ開発')
                results.extend(google_trends)
                await asyncio.sleep(1)  # レート制限
            
            print(f"✅ ウェブ開発記事取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ ウェブ開発記事取得エラー: {error}")
            return []
    
    async def get_business_trends(self) -> List[TrendItem]:
        """ビジネス記事専門取得"""
        print("💼 ビジネス記事専門取得開始")
        results = []
        
        try:
            business_keywords = [
                'DX推進', 'デジタル変革', 'ビジネス戦略', 'マーケティング戦略',
                '働き方改革', 'スタートアップ', '事業成長', 'イノベーション'
            ]
            
            for keyword in business_keywords:
                print(f"💼 ビジネス記事検索中: {keyword}")
                google_trends = await self._get_google_news_by_keyword(keyword, 'ビジネス')
                results.extend(google_trends)
                await asyncio.sleep(1)
            
            print(f"✅ ビジネス記事取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ ビジネス記事取得エラー: {error}")
            return []
    
    async def get_programming_trends(self) -> List[TrendItem]:
        """プログラミング記事専門取得"""
        print("💻 プログラミング記事専門取得開始")
        results = []
        
        try:
            programming_keywords = [
                'Python プログラミング', 'Java 開発', 'Go言語', 'Rust プログラミング',
                'アルゴリズム 実装', 'データ構造', '設計パターン', 'クリーンコード'
            ]
            
            for keyword in programming_keywords:
                print(f"💻 プログラミング記事検索中: {keyword}")
                google_trends = await self._get_google_news_by_keyword(keyword, 'プログラミング')
                results.extend(google_trends)
                await asyncio.sleep(1)
            
            print(f"✅ プログラミング記事取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ プログラミング記事取得エラー: {error}")
            return []
    
    async def get_data_science_trends(self) -> List[TrendItem]:
        """データサイエンス・AI開発記事専門取得"""
        print("📊 データサイエンス・AI開発記事専門取得開始")
        results = []
        
        try:
            ds_keywords = [
                'データサイエンス', '機械学習 実装', 'Python データ分析', 'pandas 活用',
                '統計分析', 'ビッグデータ', 'データ可視化', 'MLOps'
            ]
            
            for keyword in ds_keywords:
                print(f"📊 データサイエンス記事検索中: {keyword}")
                google_trends = await self._get_google_news_by_keyword(keyword, 'データサイエンス')
                results.extend(google_trends)
                await asyncio.sleep(1)
            
            print(f"✅ データサイエンス記事取得完了: {len(results)}件")
            return results
            
        except Exception as error:
            print(f"❌ データサイエンス記事取得エラー: {error}")
            return []
    
    async def get_ai_tech_trends(self) -> List[TrendItem]:
        """生成AI専門情報取得"""
        print("🤖 生成AI専門情報取得開始")
        results = []
        
        try:
            ai_keywords = ['claude code', 'chatgpt', 'gemini', 'anthropic', 'openai']
            
            for keyword in ai_keywords:
                google_trends = await self._get_google_news_by_keyword(keyword, '生成AI')
                results.extend(google_trends)
                await asyncio.sleep(1)
            
            print(f"✅ 生成AI専門情報: {len(results)}件取得")
            return results
            
        except Exception as error:
            print(f"❌ 生成AI取得エラー: {error}")
            return []
    
    async def _get_zenn_filtered_articles(self, filter_keyword: str) -> List[TrendItem]:
        """Zennから特定キーワードでフィルタリング"""
        results = []
        
        try:
            endpoint = 'https://zenn.dev/api/articles?order=liked_count&count=100'
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('articles'):
                        for article in data['articles']:
                            title = article.get('title', '').lower()
                            if any(kw in title for kw in ['react', 'vue', 'javascript', 'web', 'frontend']):
                                if article.get('liked_count', 0) > 10:
                                    trend_item = TrendItem(
                                        id=f"zenn-web-{article.get('id')}",
                                        title=article.get('title', ''),
                                        url=f"https://zenn.dev{article.get('path', '')}",
                                        likes=article.get('liked_count', 0),
                                        comments=article.get('comments_count', 0),
                                        source='Zenn API',
                                        published_at=article.get('published_at', ''),
                                        topics=[t.get('name', '') for t in article.get('topics', [])]
                                    )
                                    results.append(trend_item)
            
            print(f"📚 Zenn記事フィルタリング: {len(results)}件の{filter_keyword}記事を抽出")
            
        except Exception as error:
            print(f"❌ Zennフィルタリングエラー: {error}")
        
        return results
    
    async def _get_google_news_by_keyword(self, keyword: str, category: str) -> List[TrendItem]:
        """Google News RSS検索"""
        results = []
        
        try:
            print(f"🔍 Google News検索中: {keyword}")
            rss_url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ja&gl=JP&ceid=JP:ja"
            
            async with self.session.get(rss_url) as response:
                if response.status == 200:
                    rss_text = await response.text()
                    items = self._parse_rss_feed(rss_text)
                    
                    for i, item in enumerate(items[:5]):  # 各キーワードから5件まで
                        trend_item = TrendItem(
                            id=f"google-{category.lower()}-{hash(keyword + str(i))}",
                            title=item.get('title', ''),
                            url=item.get('link', ''),
                            source=f'Google News ({category})',
                            published_at=item.get('pubDate', ''),
                            topics=[keyword],
                            description=self._clean_description(item.get('title', ''))
                        )
                        results.append(trend_item)
        
        except Exception as error:
            print(f"❌ Google News検索エラー ({keyword}): {error}")
        
        return results
    
    def _parse_rss_feed(self, rss_text: str) -> List[Dict]:
        """RSS XMLパース"""
        items = []
        
        try:
            root = ET.fromstring(rss_text)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                
                if title_elem is not None:
                    items.append({
                        'title': title_elem.text or '',
                        'link': link_elem.text if link_elem is not None else '',
                        'pubDate': pub_date_elem.text if pub_date_elem is not None else ''
                    })
        
        except ET.ParseError as e:
            print(f"❌ RSS解析エラー: {e}")
        
        return items
    
    def _clean_description(self, text: str) -> str:
        """説明文をクリーニング"""
        # サイト名部分を除去
        clean_text = re.sub(r'\s*-\s*[^-]*$', '', text)
        
        # 長すぎる場合は切り詰め
        if len(clean_text) > 100:
            clean_text = clean_text[:97] + "..."
        
        return clean_text
    
    def _remove_duplicates(self, trends: List[TrendItem]) -> List[TrendItem]:
        """重複除去（URL、タイトル類似度ベース）"""
        unique_trends = []
        seen_urls = set()
        seen_titles = set()
        
        for trend in trends:
            # URL重複チェック
            if trend.url and trend.url in seen_urls:
                continue
            
            # タイトル類似度チェック（簡易版）
            title_lower = trend.title.lower()
            title_words = set(title_lower.split())
            
            is_similar = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # 単語の一致率が80%以上なら類似とみなす
                if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.8:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_trends.append(trend)
                if trend.url:
                    seen_urls.add(trend.url)
                seen_titles.add(title_lower)
        
        return unique_trends
    
    def categorize_trends(self, trends: List[TrendItem]) -> Dict[str, List[TrendItem]]:
        """トレンドをカテゴリ別に分類"""
        categorized = {category: [] for category in self.category_keywords.keys()}
        categorized['週間総合'] = []
        
        for trend in trends:
            title_text = trend.title.lower()
            description_text = trend.description.lower()
            combined_text = f"{title_text} {description_text}"
            
            # カテゴリ判定
            best_category = '週間総合'
            max_matches = 0
            
            for category, keywords in self.category_keywords.items():
                matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)
                if matches > max_matches:
                    max_matches = matches
                    best_category = category
            
            trend.category = best_category
            categorized[best_category].append(trend)
        
        return categorized

# 使用例とテスト
async def demo_realtime_trends():
    """デモ実行"""
    async with RealtimeTrendsClient() as client:
        print("🚀 リアルタイムトレンドシステム開始")
        
        # 全トレンド取得
        all_trends = await client.get_all_trends()
        
        print(f"\n📊 取得結果: {len(all_trends)}件")
        
        # カテゴリ別分類
        categorized = client.categorize_trends(all_trends)
        
        print("\n📂 カテゴリ別統計:")
        for category, items in categorized.items():
            if items:
                print(f"  {category}: {len(items)}件")
        
        # サンプル表示
        print("\n🔥 トレンドサンプル:")
        for i, trend in enumerate(all_trends[:5], 1):
            print(f"{i}. [{trend.source}] {trend.title}")
            print(f"   カテゴリ: {trend.category}")
            print(f"   スコア: {trend.score}, いいね: {trend.likes}")
            print(f"   URL: {trend.url[:50]}...")
            print()

if __name__ == "__main__":
    asyncio.run(demo_realtime_trends())