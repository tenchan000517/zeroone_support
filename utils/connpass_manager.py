# -*- coding:utf-8 -*-
import aiohttp
import datetime
from typing import List, Dict, Optional
from config.config import CONNPASS_API_KEY
import asyncio

class ConnpassManager:
    def __init__(self):
        self.api_key = CONNPASS_API_KEY
        self.base_url = "https://connpass.com/api/v1/event/"
        
        # オンライン講座関連キーワード
        self.online_course_keywords = [
            "オンライン", "リモート", "ウェビナー", "Web講座", "オンライン講座",
            "配信", "ライブ", "バーチャル", "デジタル", "在宅",
            "プログラミング", "IT", "DX", "AI", "データ分析",
            "ビジネス", "マーケティング", "起業", "スタートアップ",
            "キャリア", "スキルアップ", "学習", "研修", "セミナー"
        ]
        
        # 都道府県マッピング
        self.prefecture_map = {
            "愛知": "愛知県", "愛知県": "愛知県",
            "東京": "東京都", "東京都": "東京都",
            "大阪": "大阪府", "大阪府": "大阪府",
            "神奈川": "神奈川県", "神奈川県": "神奈川県",
        }
    
    async def get_online_courses(self, regions: List[str] = None, days_ahead: int = 7) -> List[Dict]:
        """オンライン講座イベントを取得"""
        if regions is None:
            regions = ["愛知県"]
        
        all_events = []
        
        # 複数のキーワードで検索
        for keyword in self.online_course_keywords[:5]:  # 上位5キーワード
            events = await self._search_events(
                keyword=keyword,
                days_ahead=days_ahead
            )
            all_events.extend(events)
            
            # レート制限対策：1秒待機
            await asyncio.sleep(1)
        
        # 重複除去（event_idベース）
        unique_events = {}
        for event in all_events:
            event_id = event.get('event_id', event.get('title', ''))
            unique_events[event_id] = event
        
        filtered_events = list(unique_events.values())
        
        # オンライン講座のみフィルタリング
        online_events = self._filter_online_events(filtered_events)
        
        # イベントがない場合はフォールバック
        if not online_events:
            online_events = self._get_fallback_courses()
        
        # 日付順にソート
        online_events.sort(key=lambda x: x.get('started_at', ''))
        
        # 最大8件に制限
        return online_events[:8]
    
    async def _search_events(self, keyword: str, days_ahead: int) -> List[Dict]:
        """Connpass APIでイベント検索"""
        today = datetime.datetime.now()
        
        # 今月と来月を対象
        current_month = today.strftime("%Y%m")
        next_month = (today.replace(day=1) + datetime.timedelta(days=32)).strftime("%Y%m")
        
        params = {
            'keyword': keyword,
            'ym': f"{current_month},{next_month}",
            'count': 20,
            'order': 2,  # 更新日時順
            'format': 'json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    print(f"Connpass API status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            events = data.get('events', [])
                            print(f"Found {len(events)} events for keyword: {keyword}")
                            return events
                        except Exception as json_error:
                            print(f"JSON parsing error: {json_error}")
                            return []
                    else:
                        print(f"Connpass API error: {response.status}")
                        return []
        except Exception as e:
            print(f"Error fetching events from Connpass: {e}")
            return []
    
    def _filter_online_events(self, events: List[Dict]) -> List[Dict]:
        """オンライン講座のみフィルタリング"""
        online_events = []
        
        online_keywords = [
            'オンライン', 'リモート', 'ウェビナー', 'Web', 'バーチャル',
            '配信', 'ライブ', 'Zoom', 'Google Meet', 'Teams'
        ]
        
        for event in events:
            title = (event.get('title') or '').lower()
            catch_copy = (event.get('catch') or '').lower()
            description = (event.get('description') or '').lower()
            address = (event.get('address') or '').lower()
            place = (event.get('place') or '').lower()
            
            # オンライン講座の判定
            full_text = f"{title} {catch_copy} {description} {address} {place}"
            is_online = any(keyword.lower() in full_text for keyword in online_keywords)
            
            # 地域が設定されていない（オンライン）場合も対象
            if not address and not place:
                is_online = True
            
            if is_online:
                online_events.append(event)
        
        return online_events
    
    def _get_fallback_courses(self) -> List[Dict]:
        """API利用不可時のフォールバックコース"""
        today = datetime.datetime.now()
        
        fallback_courses = [
            {
                "event_id": "fallback_1",
                "title": "Python初心者向けオンライン講座",
                "started_at": (today + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "プログラミング初心者でも安心のPython入門コース",
                "event_url": "https://connpass.com/event/example1/",
                "place": "オンライン開催",
                "address": "",
                "description": "Python基礎からWebアプリ開発まで学べる実践的なオンライン講座です。"
            },
            {
                "event_id": "fallback_2", 
                "title": "Web制作スキルアップウェビナー",
                "started_at": (today + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "現役エンジニアが教えるWeb制作のコツ",
                "event_url": "https://connpass.com/event/example2/",
                "place": "オンライン配信",
                "address": "",
                "description": "HTML/CSS/JavaScriptを使った実践的なWeb制作技術を学習できます。"
            },
            {
                "event_id": "fallback_3",
                "title": "データ分析入門オンラインセミナー", 
                "started_at": (today + datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "ExcelからPythonまで、データ分析の基礎を学ぼう",
                "event_url": "https://connpass.com/event/example3/",
                "place": "リモート開催",
                "address": "",
                "description": "ビジネスに活かせるデータ分析スキルをオンラインで身につけられます。"
            }
        ]
        
        return fallback_courses
    
    def format_courses_for_embed(self, courses: List[Dict]) -> Dict:
        """オンライン講座情報をEmbed用にフォーマット"""
        if not courses:
            return {
                "title": "💻 今週のオンライン講座情報",
                "description": "connpassから最新のオンライン講座をお届けします！",
                "fields": [
                    {
                        "name": "📚 今週の講座",
                        "value": "今週は該当するオンライン講座が見つかりませんでした。\n来週の情報をお楽しみに！",
                        "inline": False
                    }
                ],
                "color": 0x3498DB
            }
        
        # 講座情報を整形（Discord 1024文字制限対応）
        course_list = []
        total_length = 0
        max_field_length = 900
        
        for i, course in enumerate(courses[:4], 1):  # 最大4件表示
            try:
                # 日時をパース
                started_at_str = course.get('started_at', '')
                if started_at_str:
                    # connpassの日時形式をパース
                    started_at = datetime.datetime.fromisoformat(
                        started_at_str.replace('+09:00', '')
                    )
                    date_str = started_at.strftime("%m/%d(%a) %H:%M")
                else:
                    date_str = "日時未定"
                
                # タイトルを短縮（25文字制限）
                title = course.get('title', 'タイトル未定')
                if len(title) > 25:
                    title = title[:22] + "..."
                
                # キャッチコピー
                catch = course.get('catch', '')
                if catch and len(catch) > 30:
                    catch = catch[:27] + "..."
                
                course_info = f"**{title}**\n📅 {date_str}"
                
                if catch:
                    course_info += f"\n💡 {catch}"
                
                # 場所情報
                place = course.get('place', 'オンライン')
                if place and place != 'オンライン':
                    if len(place) > 15:
                        place = place[:12] + "..."
                    course_info += f"\n📍 {place}"
                else:
                    course_info += f"\n📍 オンライン開催"
                
                if course.get('event_url'):
                    course_info += f"\n🔗 [詳細・申込]({course['event_url']})"
                
                # 文字数チェック
                if total_length + len(course_info) + 2 > max_field_length:
                    break
                
                course_list.append(course_info)
                total_length += len(course_info) + 2
                
            except Exception as e:
                print(f"Error formatting course: {e}")
                continue
        
        return {
            "title": "💻 今週のオンライン講座情報",
            "description": "**connpass**から厳選したオンライン講座をお届けします！\n新しいスキルを身につけるチャンス✨",
            "fields": [
                {
                    "name": "📚 注目の講座",
                    "value": "\n\n".join(course_list) if course_list else "講座情報の取得に失敗しました",
                    "inline": False
                },
                {
                    "name": "🎯 オンライン学習のメリット",
                    "value": "• 自宅から気軽に参加可能\n• 移動時間ゼロで効率的\n• 録画視聴で復習も安心\n• 全国の講師から学べる",
                    "inline": False
                }
            ],
            "color": 0x3498DB,
            "footer": {
                "text": "💡 気になる講座があれば早めの申込みがおすすめです！"
            }
        }