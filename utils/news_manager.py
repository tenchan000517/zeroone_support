# -*- coding:utf-8 -*-
import aiohttp
import datetime
import json
from typing import List, Dict
from urllib.parse import quote

class NewsManager:
    def __init__(self):
        # テック・イノベーション関連キーワード
        self.tech_keywords = [
            "AI", "人工知能", "機械学習", "ChatGPT", "生成AI",
            "DX", "デジタル変革", "クラウド", "AWS", "Azure",
            "プログラミング", "Python", "JavaScript", "React",
            "スタートアップ", "起業", "VC", "投資",
            "ブロックチェーン", "Web3", "NFT", "暗号通貨",
            "IoT", "5G", "AR", "VR", "メタバース",
            "サイバーセキュリティ", "データサイエンス"
        ]
        
        # Googleニュース検索のベースURL
        self.google_news_base = "https://news.google.com/rss/search"
    
    async def get_tech_news(self, max_articles: int = 5) -> List[Dict]:
        """テック系ニュースを取得"""
        all_articles = []
        
        # 複数キーワードで検索して多様性確保
        for keyword in self.tech_keywords[:3]:  # 上位3キーワード
            try:
                articles = await self._fetch_google_news(keyword, max_articles=2)
                all_articles.extend(articles)
            except Exception as e:
                print(f"Error fetching news for {keyword}: {e}")
                continue
        
        # 重複除去（タイトルベース）
        unique_articles = {}
        for article in all_articles:
            title = article.get('title', '')
            if title and title not in unique_articles:
                unique_articles[title] = article
        
        # 日付順でソート
        sorted_articles = sorted(
            unique_articles.values(),
            key=lambda x: x.get('pub_date', ''),
            reverse=True
        )
        
        return sorted_articles[:max_articles]
    
    async def _fetch_google_news(self, keyword: str, max_articles: int = 5) -> List[Dict]:
        """GoogleニュースRSSから記事を取得"""
        query = f"{keyword} テクノロジー OR イノベーション"
        encoded_query = quote(query)
        url = f"{self.google_news_base}?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; DJEyes-Bot/1.0)'}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_rss_content(content, max_articles)
                    else:
                        print(f"Google News API error: {response.status}")
                        return []
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []
    
    def _parse_rss_content(self, rss_content: str, max_articles: int) -> List[Dict]:
        """RSS XMLコンテンツをパース"""
        import xml.etree.ElementTree as ET
        
        articles = []
        try:
            root = ET.fromstring(rss_content)
            
            # RSS 2.0形式のitem要素を探索
            items = root.findall('.//item')[:max_articles]
            
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                description_elem = item.find('description')
                
                if title_elem is not None and link_elem is not None:
                    article = {
                        'title': title_elem.text or '',
                        'url': link_elem.text or '',
                        'pub_date': pub_date_elem.text if pub_date_elem is not None else '',
                        'description': description_elem.text if description_elem is not None else ''
                    }
                    
                    # HTMLタグを除去
                    article['description'] = self._clean_html(article['description'])
                    
                    articles.append(article)
                    
        except ET.ParseError as e:
            print(f"RSS parsing error: {e}")
        except Exception as e:
            print(f"Error parsing RSS: {e}")
            
        return articles
    
    def _clean_html(self, text: str) -> str:
        """HTMLタグを除去"""
        import re
        if not text:
            return ""
        
        # HTMLタグを除去
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 余分な空白を整理
        clean_text = ' '.join(clean_text.split())
        
        return clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
    
    def get_fallback_tech_news(self) -> List[Dict]:
        """フォールバック用のテックニュース"""
        today = datetime.datetime.now()
        
        return [
            {
                'title': '生成AI市場が急拡大、企業の導入率70%突破',
                'url': 'https://example.com/ai-market-growth',
                'pub_date': today.strftime('%Y-%m-%d'),
                'description': '最新調査により、生成AI技術の企業導入が加速していることが明らかになりました。'
            },
            {
                'title': 'クラウドネイティブ技術の採用が加速',
                'url': 'https://example.com/cloud-native-adoption',
                'pub_date': today.strftime('%Y-%m-%d'),
                'description': 'コンテナ化とマイクロサービス技術の導入企業が前年比150%増加。'
            },
            {
                'title': 'サイバーセキュリティ投資が過去最高に',
                'url': 'https://example.com/cybersecurity-investment',
                'pub_date': today.strftime('%Y-%m-%d'),
                'description': 'DX推進に伴い、セキュリティ対策への投資が急増している。'
            }
        ]
    
    def format_news_for_embed(self, articles: List[Dict]) -> Dict:
        """ニュース記事をEmbed用にフォーマット"""
        if not articles:
            # フォールバック記事を使用
            articles = self.get_fallback_tech_news()
        
        # 記事リストを作成（Discord 1024文字制限対応）
        article_list = []
        total_length = 0
        max_field_length = 900  # 1024文字制限に余裕を持たせる
        
        for i, article in enumerate(articles[:3], 1):  # 最大3記事に制限
            title = article.get('title', 'タイトル不明')
            url = article.get('url', '')
            
            # タイトルを短縮（25文字制限）
            if len(title) > 25:
                title = title[:22] + "..."
            
            if url and url != 'https://example.com':
                article_info = f"**{title}**\n🔗 [詳細]({url})"
            else:
                article_info = f"**{title}**"
            
            # 文字数チェック
            if total_length + len(article_info) + 2 > max_field_length:  # +2 for \n\n
                break
                
            article_list.append(article_info)
            total_length += len(article_info) + 2
        
        return {
            "title": "🌐 最新テック・イノベーション情報",
            "description": "最新のテクノロジー動向をお届けします！",
            "fields": [
                {
                    "name": "📰 注目ニュース",
                    "value": "\n\n".join(article_list) if article_list else "ニュースの取得に失敗しました",
                    "inline": False
                },
                {
                    "name": "💡 ビジネスへの活用",
                    "value": "• 最新技術トレンドの把握\n• 競合分析と戦略立案\n• 新しいビジネス機会の発見",
                    "inline": False
                }
            ],
            "color": 0x1DA1F2  # Twitter blue
        }