# -*- coding:utf-8 -*-
import aiohttp
import xml.etree.ElementTree as ET
import datetime
from typing import List, Dict, Optional
import asyncio
import re

class TrendsManager:
    def __init__(self):
        self.daily_trends_url = "https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP"
        self.realtime_trends_url = "https://trends.google.co.jp/trends/trendingsearches/realtime/rss?geo=JP"
        
        # ビジネス関連キーワード（フィルタリング用）
        self.business_keywords = [
            "経済", "ビジネス", "企業", "株式", "投資", "市場", "経営", "売上", "利益",
            "M&A", "IPO", "決算", "業績", "AI", "DX", "IT", "テクノロジー", "イノベーション",
            "スタートアップ", "起業", "副業", "転職", "キャリア", "働き方", "リモートワーク",
            "マーケティング", "ブランド", "EC", "eコマース", "デジタル", "データ分析",
            "仮想通貨", "ブロックチェーン", "NFT", "メタバース", "サステナビリティ",
            "ESG", "SDGs", "グリーン", "カーボン"
        ]
    
    async def get_business_trends(self, max_trends: int = 5) -> List[Dict]:
        """ビジネス関連のトレンドを取得"""
        all_trends = []
        
        # デイリートレンドとリアルタイムトレンドの両方を取得
        daily_trends = await self._fetch_trends(self.daily_trends_url, "daily")
        realtime_trends = await self._fetch_trends(self.realtime_trends_url, "realtime")
        
        all_trends.extend(daily_trends)
        all_trends.extend(realtime_trends)
        
        # ビジネス関連のトレンドをフィルタリング
        business_trends = self._filter_business_trends(all_trends)
        
        # フォールバック：ビジネストレンドが少ない場合は一般的なトレンドも含める
        if len(business_trends) < 3:
            business_trends.extend(all_trends[:max_trends - len(business_trends)])
        
        # 重複除去
        unique_trends = self._remove_duplicates(business_trends)
        
        # フォールバック：データが取得できない場合
        if not unique_trends:
            unique_trends = self._get_fallback_trends()
        
        return unique_trends[:max_trends]
    
    async def _fetch_trends(self, url: str, trend_type: str) -> List[Dict]:
        """指定されたURLからトレンドを取得"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept-Language': 'ja,en;q=0.9'
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_rss(content, trend_type)
                    else:
                        print(f"Failed to fetch {trend_type} trends: {response.status}")
                        return []
        except Exception as e:
            print(f"Error fetching {trend_type} trends: {e}")
            return []
    
    def _parse_rss(self, rss_content: str, trend_type: str) -> List[Dict]:
        """RSS XMLを解析してトレンド情報を抽出"""
        trends = []
        
        try:
            root = ET.fromstring(rss_content)
            
            # RSS名前空間の処理
            items = root.findall('.//item')
            
            for item in items:
                title = item.find('title')
                description = item.find('description')
                pub_date = item.find('pubDate')
                link = item.find('link')
                
                if title is not None:
                    trend_title = title.text or ""
                    
                    # 説明文からより詳細な情報を抽出
                    trend_description = ""
                    if description is not None and description.text:
                        # HTMLタグを除去
                        clean_desc = re.sub(r'<[^>]+>', '', description.text)
                        trend_description = clean_desc.strip()
                    
                    # 日時情報
                    trend_date = ""
                    if pub_date is not None and pub_date.text:
                        trend_date = pub_date.text
                    
                    # リンク情報
                    trend_link = ""
                    if link is not None and link.text:
                        trend_link = link.text
                    
                    trends.append({
                        'title': trend_title,
                        'description': trend_description,
                        'date': trend_date,
                        'link': trend_link,
                        'type': trend_type,
                        'category': self._categorize_trend(trend_title + " " + trend_description)
                    })
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
        except Exception as e:
            print(f"Error parsing RSS: {e}")
        
        return trends
    
    def _filter_business_trends(self, trends: List[Dict]) -> List[Dict]:
        """ビジネス関連のトレンドをフィルタリング"""
        business_trends = []
        
        for trend in trends:
            text = (trend['title'] + " " + trend['description']).lower()
            
            # ビジネスキーワードが含まれているかチェック
            if any(keyword in text for keyword in self.business_keywords):
                business_trends.append(trend)
        
        return business_trends
    
    def _categorize_trend(self, text: str) -> str:
        """トレンドをカテゴリ分けする"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["ai", "人工知能", "機械学習", "dx", "デジタル"]):
            return "🤖 AI・テクノロジー"
        elif any(word in text_lower for word in ["投資", "株式", "市場", "経済", "金融"]):
            return "💰 経済・投資"
        elif any(word in text_lower for word in ["働き方", "転職", "キャリア", "リモート"]):
            return "💼 働き方・キャリア"
        elif any(word in text_lower for word in ["企業", "経営", "ビジネス", "売上", "決算"]):
            return "🏢 企業・経営"
        elif any(word in text_lower for word in ["esg", "サステナ", "環境", "グリーン"]):
            return "🌱 サステナビリティ"
        else:
            return "📊 一般トレンド"
    
    def _remove_duplicates(self, trends: List[Dict]) -> List[Dict]:
        """重複するトレンドを除去"""
        seen_titles = set()
        unique_trends = []
        
        for trend in trends:
            title_lower = trend['title'].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_trends.append(trend)
        
        return unique_trends
    
    def _get_fallback_trends(self) -> List[Dict]:
        """API利用不可時のフォールバックトレンド"""
        today = datetime.datetime.now()
        
        fallback_trends = [
            {
                'title': 'AI技術の企業導入が加速',
                'description': '生成AIツールを活用した業務効率化が多くの企業で導入されています',
                'date': today.strftime('%a, %d %b %Y %H:%M:%S +0900'),
                'link': 'https://trends.google.co.jp',
                'type': 'fallback',
                'category': '🤖 AI・テクノロジー'
            },
            {
                'title': 'リモートワーク関連サービスの需要増',
                'description': 'ハイブリッドワークの定着により、関連ツールやサービスへの注目が高まっています',
                'date': today.strftime('%a, %d %b %Y %H:%M:%S +0900'),
                'link': 'https://trends.google.co.jp',
                'type': 'fallback',
                'category': '💼 働き方・キャリア'
            },
            {
                'title': 'サステナビリティ投資に注目',
                'description': 'ESG投資への関心が高まり、企業の環境配慮が投資判断の重要要素になっています',
                'date': today.strftime('%a, %d %b %Y %H:%M:%S +0900'),
                'link': 'https://trends.google.co.jp',
                'type': 'fallback',
                'category': '🌱 サステナビリティ'
            }
        ]
        
        return fallback_trends
    
    def format_trends_for_embed(self, trends: List[Dict]) -> Dict:
        """トレンド情報をEmbed用にフォーマット"""
        if not trends:
            return {
                "title": "📊 ビジネストレンド速報",
                "description": "**GoogleTrends**から最新のビジネストレンドをお届けします！",
                "fields": [
                    {
                        "name": "📈 今日のトレンド",
                        "value": "現在トレンド情報を取得できませんでした。\n後ほど再度お試しください。",
                        "inline": False
                    }
                ],
                "color": 0x9C27B0
            }
        
        # トレンド情報を整形（Discord 1024文字制限対応）
        trend_list = []
        total_length = 0
        max_field_length = 900
        
        for i, trend in enumerate(trends[:3], 1):  # 最大3件表示
            try:
                title = trend['title']
                if len(title) > 30:
                    title = title[:27] + "..."
                
                description = trend.get('description', '')
                if description and len(description) > 50:
                    description = description[:47] + "..."
                
                category = trend.get('category', '📊 一般トレンド')
                
                trend_info = f"**{category}**\n🔥 {title}"
                
                if description:
                    trend_info += f"\n💭 {description}"
                
                if trend.get('link') and 'google' in trend['link']:
                    trend_info += f"\n🔗 [詳細を見る]({trend['link']})"
                
                # 文字数チェック
                if total_length + len(trend_info) + 2 > max_field_length:
                    break
                
                trend_list.append(trend_info)
                total_length += len(trend_info) + 2
                
            except Exception as e:
                print(f"Error formatting trend: {e}")
                continue
        
        return {
            "title": "📊 ビジネストレンド速報",
            "description": "**GoogleTrends**から厳選した最新ビジネストレンドをお届け！\n市場の動きをリアルタイムでキャッチ✨",
            "fields": [
                {
                    "name": "🔥 注目のトレンド",
                    "value": "\n\n".join(trend_list) if trend_list else "トレンド情報の取得に失敗しました",
                    "inline": False
                },
                {
                    "name": "💡 トレンド活用のヒント",
                    "value": "• 市場の変化をいち早くキャッチ\n• 顧客ニーズの変動を把握\n• 新しいビジネス機会を発見\n• 競合他社の動向を監視",
                    "inline": False
                }
            ],
            "color": 0x9C27B0,
            "footer": {
                "text": "📈 データソース: Google Trends Japan | トレンドを先取りして競争優位を築こう"
            }
        }