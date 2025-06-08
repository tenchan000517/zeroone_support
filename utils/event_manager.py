# -*- coding:utf-8 -*-
import aiohttp
import datetime
from typing import List, Dict, Optional
from config.config import DOORKEEPER_API_TOKEN
from bs4 import BeautifulSoup
import re

class EventManager:
    def __init__(self):
        self.api_token = DOORKEEPER_API_TOKEN
        self.base_url = "https://api.doorkeeper.jp"
        
        # キャリア・ビジネス関連キーワード
        self.career_keywords = [
            "キャリア", "転職", "就職", "採用", "人事", "HR",
            "ビジネス", "起業", "スタートアップ", "経営", "マネジメント",
            "マーケティング", "営業", "セールス", "プロジェクト管理",
            "リーダーシップ", "スキルアップ", "研修", "セミナー",
            "IT", "プログラミング", "エンジニア", "デザイン", "UX",
            "データ分析", "AI", "DX", "デジタル", "Web",
            "ネットワーキング", "勉強会", "交流", "コミュニティ"
        ]
        
        # 都道府県マッピング
        self.prefecture_map = {
            "愛知": "愛知県", "愛知県": "愛知県",
            "東京": "東京都", "東京都": "東京都",
            "大阪": "大阪府", "大阪府": "大阪府",
            "神奈川": "神奈川県", "神奈川県": "神奈川県",
            "埼玉": "埼玉県", "埼玉県": "埼玉県",
            "千葉": "千葉県", "千葉県": "千葉県",
            "兵庫": "兵庫県", "兵庫県": "兵庫県",
            "京都": "京都府", "京都府": "京都府",
            "福岡": "福岡県", "福岡県": "福岡県",
            "北海道": "北海道", "札幌": "北海道"
        }
    
    async def get_career_events(self, regions: List[str] = None, days_ahead: int = 7) -> List[Dict]:
        """キャリア系イベントを取得（Doorkeeper + Peatix）"""
        if regions is None:
            regions = ["愛知県"]
        
        all_events = []
        
        # 1. Doorkeeper APIからイベント取得
        if self.api_token:
            for region in regions:
                prefecture = self.prefecture_map.get(region, region)
                
                # 複数のキーワードで検索して重複除去
                events_by_keyword = []
                for keyword in self.career_keywords[:3]:  # レート制限対策で上位3キーワード
                    events = await self._search_events(
                        prefecture=prefecture,
                        keyword=keyword,
                        days_ahead=days_ahead
                    )
                    events_by_keyword.extend(events)
                    
                    # レート制限対策：1秒待機
                    await asyncio.sleep(1)
                
                # 重複除去（event_idベース）
                unique_events = {}
                for event in events_by_keyword:
                    event_id = event.get('id', event.get('title', ''))
                    unique_events[event_id] = event
                
                all_events.extend(unique_events.values())
        
        # 2. Peatixからイベント取得を試行（現在はスキップ - CloudFront制限のため）
        # Peatixはアンチスクレイピング対策が強化されているため、
        # 将来的にAPIが提供された場合に対応予定
        # try:
        #     peatix_events = await self._fetch_peatix_events(regions, days_ahead)
        #     all_events.extend(peatix_events)
        # except Exception as e:
        #     print(f"Peatix fetch error: {e}")
        
        # 3. イベントがない場合はフォールバック
        if not all_events:
            all_events = self._get_fallback_events(regions)
        
        # 日付順にソート
        all_events.sort(key=lambda x: x.get('starts_at', ''))
        
        # 最大10件に制限
        return all_events[:10]
    
    async def _search_events(self, prefecture: str, keyword: str, days_ahead: int) -> List[Dict]:
        """Doorkeeper APIでイベント検索"""
        today = datetime.datetime.now().date()
        until_date = today + datetime.timedelta(days=days_ahead)
        
        # APIパラメータを簡素化（500エラー対策）
        params = {
            'q': keyword,
            'since': today.isoformat(),
            'sort': 'starts_at',
            'locale': 'ja'
        }
        
        # 地域フィルタリングは行わず、キーワード検索のみ実施
        # オンラインイベントも含めて幅広く取得し、後でフィルタリング
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'User-Agent': 'DJEyes-Bot/1.0',
            'Accept': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # まずAPIの基本接続をテスト
                test_url = f"{self.base_url}/events"
                print(f"Testing Doorkeeper API: {test_url}")
                print(f"Headers: {headers}")
                print(f"Params: {params}")
                
                async with session.get(
                    test_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    print(f"Response status: {response.status}")
                    response_text = await response.text()
                    print(f"Response text: {response_text[:500]}...")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list):
                                events = [item.get('event', item) for item in data if item]
                                print(f"Found {len(events)} events before filtering")
                                
                                # 地域フィルタリング: オンライン or 指定地域のイベント
                                filtered_events = self._filter_events_by_region(events, prefecture)
                                print(f"After region filtering: {len(filtered_events)} events")
                                return filtered_events
                            else:
                                print("Unexpected response format")
                                return []
                        except Exception as json_error:
                            print(f"JSON parsing error: {json_error}")
                            return []
                    elif response.status == 401:
                        print("API Token invalid or expired")
                        return []
                    elif response.status == 403:
                        print("API access forbidden")
                        return []
                    elif response.status == 500:
                        print("Server error - using fallback data")
                        return []
                    else:
                        print(f"Doorkeeper API error: {response.status} - {response_text}")
                        return []
        except aiohttp.ClientTimeout:
            print("API request timeout")
            return []
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []
    
    def _filter_events_by_region(self, events: List[Dict], target_prefecture: str) -> List[Dict]:
        """イベントを地域でフィルタリング（オンライン優遇）"""
        filtered = []
        
        for event in events:
            # オンラインイベントの判定キーワード
            online_keywords = ['オンライン', 'リモート', 'バーチャル', 'ウェビナー', 'Web', 'Zoom']
            
            # イベント情報から判定（None対策）
            title = (event.get('title') or '').lower()
            venue = (event.get('venue_name') or '').lower()
            address = (event.get('address') or '').lower()
            description = (event.get('description') or '').lower()
            
            # オンラインイベントの場合は地域関係なく含める
            if any(keyword.lower() in title or keyword.lower() in venue or keyword.lower() in description 
                   for keyword in online_keywords):
                filtered.append(event)
                continue
            
            # オフラインイベントの場合は地域チェック
            if target_prefecture:
                prefecture_short = target_prefecture.replace('県', '').replace('都', '').replace('府', '')
                if (prefecture_short in address or 
                    prefecture_short in venue or 
                    target_prefecture in address or 
                    target_prefecture in venue):
                    filtered.append(event)
                    continue
            
            # 地域情報が不明な場合も含める（情報不足対策）
            if not address and not venue:
                filtered.append(event)
        
        return filtered
    
    async def _fetch_peatix_events(self, regions: List[str], days_ahead: int) -> List[Dict]:
        """Peatixからイベント情報をスクレイピング"""
        events = []
        
        for region in regions:
            # 地域キーワード設定
            prefecture_short = region.replace('県', '').replace('都', '').replace('府', '')
            
            # Peatixの検索URLを構築（キャリア関連カテゴリ）
            # URLエンコードも追加
            from urllib.parse import quote
            search_urls = [
                f"https://peatix.com/search?q={quote(prefecture_short + ' キャリア')}&country=JP&l.text={quote(prefecture_short)}&l.ll=",
                f"https://peatix.com/search?q={quote(prefecture_short + ' ビジネス')}&country=JP&l.text={quote(prefecture_short)}&l.ll=",
                f"https://peatix.com/search?q={quote('オンライン キャリア')}&country=JP&l.ll="  # オンラインイベントも含む
            ]
            
            for url in search_urls[:2]:  # 負荷軽減のため2つまで
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            url,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                'Accept-Language': 'ja,en;q=0.9',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                html = await response.text()
                                parsed_events = self._parse_peatix_html(html, region)
                                events.extend(parsed_events[:3])  # 各検索から最大3件
                            else:
                                print(f"Peatix HTTP error: {response.status}")
                                
                except Exception as e:
                    print(f"Error fetching from Peatix: {e}")
                
                # レート制限対策
                await asyncio.sleep(2)
        
        return events
    
    def _parse_peatix_html(self, html: str, region: str) -> List[Dict]:
        """PeatixのHTMLをパースしてイベント情報を抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # デバッグ: HTML内容を確認
        print(f"Peatix HTML length: {len(html)}")
        
        # より汎用的なセレクタでイベントを探す
        # 1. article要素
        event_cards = soup.find_all('article')
        
        # 2. それでも見つからない場合は、href="/event/"を含むリンクを探す
        if not event_cards:
            all_links = soup.find_all('a', href=lambda x: x and '/event/' in x)
            # リンクの親要素をイベントカードとして扱う
            event_cards = []
            for link in all_links:
                parent = link.find_parent(['div', 'li', 'article'])
                if parent and parent not in event_cards:
                    event_cards.append(parent)
        
        print(f"Found {len(event_cards)} potential event cards")
        
        for card in event_cards[:5]:  # 最大5件
            try:
                # タイトル取得（複数の方法を試す）
                title = None
                # h2, h3タグ
                title_elem = card.find(['h2', 'h3'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                # それでもない場合は、event URLを含むリンクのテキスト
                if not title:
                    link_elem = card.find('a', href=lambda x: x and '/event/' in x)
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                
                if not title or len(title) < 3:  # タイトルが短すぎる場合はスキップ
                    continue
                
                # URL取得
                url_elem = card.find('a', href=lambda x: x and '/event/' in x)
                event_url = None
                if url_elem and url_elem.get('href'):
                    href = url_elem['href']
                    event_url = f"https://peatix.com{href}" if href.startswith('/') else href
                
                # 日時取得（様々なパターンを試す）
                date_text = ''
                for date_selector in ['time', '.date', '.schedule', '.event-date']:
                    date_elem = card.select_one(date_selector)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        break
                
                # 場所取得
                venue_text = None
                for venue_selector in ['.venue', '.location', '.place', '.event-venue']:
                    venue_elem = card.select_one(venue_selector)
                    if venue_elem:
                        venue_text = venue_elem.get_text(strip=True)
                        break
                
                # オンライン判定（タイトルと会場両方をチェック）
                full_text = f"{title} {venue_text or ''}"
                is_online = any(word in full_text for word in ['オンライン', 'リモート', 'ウェビナー', 'Zoom', 'Online'])
                
                # 日時パース（簡易的）
                today = datetime.datetime.now()
                starts_at = today.isoformat()  # デフォルト値
                
                if date_text:
                    # "12月25日" のような形式を想定
                    match = re.search(r'(\d+)月(\d+)日', date_text)
                    if match:
                        month = int(match.group(1))
                        day = int(match.group(2))
                        year = today.year
                        # 過去の日付なら来年と判定
                        if month < today.month or (month == today.month and day < today.day):
                            year += 1
                        starts_at = datetime.datetime(year, month, day).isoformat()
                
                event = {
                    'id': f'peatix_{hash(title)}',
                    'title': title,
                    'starts_at': starts_at,
                    'venue_name': venue_text or ('オンライン' if is_online else '会場未定'),
                    'address': region if not is_online else '',
                    'public_url': event_url or 'https://peatix.com',
                    'description': f'Peatixイベント: {title}'
                }
                
                events.append(event)
                
            except Exception as e:
                print(f"Error parsing Peatix event: {e}")
                continue
        
        return events
    
    def _get_fallback_events(self, regions: List[str]) -> List[Dict]:
        """API利用不可時のフォールバックイベント"""
        today = datetime.datetime.now()
        
        fallback_events = [
            {
                "title": "キャリアアップセミナー - 転職成功の秘訣",
                "starts_at": (today + datetime.timedelta(days=1)).isoformat(),
                "venue_name": "名古屋市中小企業振興会館",
                "address": f"{regions[0]}名古屋市千種区",
                "public_url": "https://example.com/career-seminar",
                "description": "転職を成功させるためのポイントを専門家が解説します。"
            },
            {
                "title": "スタートアップピッチイベント",
                "starts_at": (today + datetime.timedelta(days=3)).isoformat(),
                "venue_name": "テックハブ",
                "address": f"{regions[0]}名古屋市中区",
                "public_url": "https://example.com/startup-pitch",
                "description": "新進気鋭のスタートアップによるピッチイベント。"
            },
            {
                "title": "プログラミング勉強会 - Python入門",
                "starts_at": (today + datetime.timedelta(days=5)).isoformat(),
                "venue_name": "コワーキングスペース",
                "address": f"{regions[0]}名古屋市東区",
                "public_url": "https://example.com/python-study",
                "description": "Python初心者向けのハンズオン勉強会です。"
            },
            {
                "title": "ビジネスネットワーキング交流会",
                "starts_at": (today + datetime.timedelta(days=6)).isoformat(),
                "venue_name": "名古屋国際会議場",
                "address": f"{regions[0]}名古屋市熱田区",
                "public_url": "https://example.com/networking",
                "description": "異業種交流によるビジネスチャンス創出イベント。"
            }
        ]
        
        return fallback_events
    
    def format_events_for_embed(self, events: List[Dict], regions: List[str]) -> Dict:
        """イベント情報をEmbed用にフォーマット"""
        if not events:
            return {
                "title": "🎪 今週の地域イベント情報",
                "description": f"**対象地域:** {', '.join(regions)}",
                "fields": [
                    {
                        "name": "📅 今週のイベント",
                        "value": "今週は該当するキャリア・ビジネス系イベントが見つかりませんでした。\n来週の情報をお楽しみに！",
                        "inline": False
                    }
                ],
                "color": 0x9B59B6
            }
        
        # イベント情報を整形（Discord 1024文字制限対応）
        event_list = []
        total_length = 0
        max_field_length = 900  # 1024文字制限に余裕を持たせる
        
        for i, event in enumerate(events[:3], 1):  # 最大3件表示
            try:
                # 日時をパース
                starts_at = datetime.datetime.fromisoformat(
                    event['starts_at'].replace('Z', '+00:00')
                )
                date_str = starts_at.strftime("%m/%d(%a) %H:%M")
                
                # タイトルを短縮（20文字制限）
                title = event['title']
                if len(title) > 20:
                    title = title[:17] + "..."
                
                # オンラインイベント判定
                online_keywords = ['オンライン', 'リモート', 'バーチャル', 'ウェビナー', 'Web', 'Zoom']
                title_text = (event.get('title') or '').lower()
                venue_text = (event.get('venue_name') or '').lower()
                description_text = (event.get('description') or '').lower()
                
                is_online = any(keyword.lower() in title_text or keyword.lower() in venue_text or keyword.lower() in description_text 
                               for keyword in online_keywords)
                
                # 場所情報
                if is_online:
                    venue_display = "オンライン"
                else:
                    venue = event.get('venue_name', '会場未定')
                    if venue and venue != '会場未定':
                        if len(venue) > 15:
                            venue_display = venue[:12] + "..."
                        else:
                            venue_display = venue
                    else:
                        venue_display = "会場未定"
                
                event_info = f"**{title}**\n📅 {date_str}\n📍 {venue_display}"
                
                if event.get('public_url'):
                    event_info += f"\n🔗 [詳細]({event['public_url']})"
                
                # 文字数チェック
                if total_length + len(event_info) + 2 > max_field_length:
                    break
                
                event_list.append(event_info)
                total_length += len(event_info) + 2
                
            except Exception as e:
                print(f"Error formatting event: {e}")
                continue
        
        return {
            "title": "🎪 今週の地域イベント情報",
            "description": f"**対象地域:** {', '.join(regions)}\n\nキャリア・ビジネス系イベントをお届けします！",
            "fields": [
                {
                    "name": "📅 注目イベント",
                    "value": "\n\n".join(event_list) if event_list else "イベント情報の取得に失敗しました",
                    "inline": False
                },
                {
                    "name": "💡 参加のメリット",
                    "value": "• 新しいスキルや知識の習得\n• 業界の最新動向を把握\n• 貴重な人脈づくりの機会\n• キャリアアップのヒント獲得",
                    "inline": False
                }
            ],
            "color": 0x9B59B6
        }

# 非同期処理用のimport追加
import asyncio
from urllib.parse import quote