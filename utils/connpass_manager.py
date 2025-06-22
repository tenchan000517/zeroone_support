# -*- coding:utf-8 -*-
import aiohttp
import datetime
from typing import List, Dict, Optional
from config.config import CONNPASS_API_KEY
import asyncio

class ConnpassManager:
    def __init__(self):
        self.api_key = CONNPASS_API_KEY
        self.base_url = "https://connpass.com/api/v2/events/"
        
        # 幅広いキーワードで検索
        self.search_keywords = [
            "プログラミング", "IT", "DX", "AI", "データ分析",
            "ビジネス", "マーケティング", "起業", "スタートアップ",
            "キャリア", "スキルアップ", "学習", "研修", "セミナー",
            "勉強会", "ハンズオン", "ワークショップ", "LT", "もくもく会"
        ]
        
        # 初心者・学習向けフィルタリングキーワード（キャリア関連を追加）
        self.filter_keywords = [
            "初心者", "学ぶ", "スキル", "入門", "AI", "アプリ", "Web",
            "ハンズオン", "プログラミング", "Claude code", "データドリブン",
            "セキュリティ", "勉強会", "エンジニア", "キャリア", "就活", "転職", "就職"
        ]
        
        # オンライン開催のplace値パターン
        self.online_place_patterns = [
            "オンライン", "リモート", "Google Meet", "Zoom",
            "YouTube", "gather", "twitch", "Teams", "オンライン開催",
            "オンライン配信", "リモート開催", "バーチャル", "ウェビナー"
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
        for keyword in self.search_keywords[:10]:  # 上位10キーワード
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
            event_id = event.get('id') or event.get('event_id') or event.get('title') or ''
            unique_events[event_id] = event
        
        filtered_events = list(unique_events.values())
        
        # オンラインイベントのフィルタリング
        online_events = self._filter_online_events(filtered_events)
        
        # 初心者・学習向けキーワードでフィルタリング
        filtered_online_events = self._filter_by_keywords(online_events)
        
        # イベントがない場合はフォールバック
        if not filtered_online_events:
            filtered_online_events = self._get_fallback_courses()
        
        # 今日から1週間以内のイベントのみフィルタリング
        today = datetime.datetime.now()
        one_week_later = today + datetime.timedelta(days=7)
        
        # 日付範囲でフィルタリング
        date_filtered_events = []
        parse_errors = 0
        no_date_count = 0
        
        print(f"DEBUG: Filtering {len(filtered_online_events)} events by date range: {today.strftime('%Y-%m-%d')} to {one_week_later.strftime('%Y-%m-%d')}")
        
        for event in filtered_online_events:
            started_at_str = event.get('started_at', '')
            if started_at_str:
                try:
                    # connpassの日時形式をパース
                    event_date = datetime.datetime.fromisoformat(
                        started_at_str.replace('+09:00', '')
                    )
                    # 今日から1週間以内かチェック
                    if today <= event_date <= one_week_later:
                        date_filtered_events.append(event)
                        print(f"DEBUG: Added event '{event.get('title', 'No title')[:50]}...' on {event_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"DEBUG: Skipped event '{event.get('title', 'No title')[:50]}...' on {event_date.strftime('%Y-%m-%d')} (outside date range)")
                except ValueError as e:
                    # 日付パースエラーの場合はスキップ
                    parse_errors += 1
                    print(f"DEBUG: Date parse error for '{started_at_str}': {e}")
                    continue
            else:
                # 日付情報がない場合もスキップ
                no_date_count += 1
                continue
        
        print(f"DEBUG: Date filtering results - kept: {len(date_filtered_events)}, parse errors: {parse_errors}, no date: {no_date_count}")
        
        print(f"Date-filtered to {len(date_filtered_events)} events within 1 week from today")
        
        # まずマッチ度でソート（降順）してトップ10を選択
        date_filtered_events.sort(key=lambda x: -x.get('_match_score', 0))
        top_10_events = date_filtered_events[:10]
        
        # 選ばれた上位10件を日付順にソート
        top_10_events.sort(key=lambda x: x.get('started_at', ''))
        
        return top_10_events
    
    async def _search_events(self, keyword: str, days_ahead: int) -> List[Dict]:
        """Connpass APIでイベント検索"""
        today = datetime.datetime.now()
        end_date = today + datetime.timedelta(days=days_ahead)
        
        # 日付範囲を指定（YYYYMMDD形式）
        ymd_start = today.strftime("%Y%m%d")
        ymd_end = end_date.strftime("%Y%m%d")
        
        params = {
            'keyword': keyword,
            'ym': today.strftime("%Y%m"),  # 今月のイベントを検索
            'count': 100,  # 多めに取得
            'order': 2,  # 開催日時順
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers={'X-API-Key': self.api_key},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    print(f"Connpass API status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            events = data.get('events', [])
                            print(f"Found {len(events)} events for keyword: {keyword}")
                            
                            # デバッグ: 最初の3件のイベント詳細を出力
                            for i, event in enumerate(events[:3]):
                                print(f"\n=== Event {i+1} for '{keyword}' ===")
                                print(f"Title: {event.get('title', 'N/A')}")
                                print(f"Address: {event.get('address', 'N/A')}")
                                print(f"Place: {event.get('place', 'N/A')}")
                                print(f"Group: {event.get('group', {}).get('title', 'N/A')}")
                                print(f"Event Type: {event.get('event_type', 'N/A')}")
                                print(f"URL: {event.get('url', 'N/A')}")
                            
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
        """オンラインイベントのみフィルタリング"""
        online_events = []
        
        for event in events:
            address = event.get('address') or ''
            place = event.get('place') or ''
            title = (event.get('title') or '').lower()
            
            # placeフィールドでオンライン判定
            is_online = False
            for pattern in self.online_place_patterns:
                if pattern in place or pattern in address:
                    is_online = True
                    break
            
            # 小文字変換してより厳密にチェック
            place_lower = place.lower()
            address_lower = address.lower()
            
            if not is_online:
                online_keywords = ['zoom', 'discord', 'meet', 'teams', 'slack', 'online', 'remote']
                for keyword in online_keywords:
                    if keyword in place_lower or keyword in address_lower or keyword in title:
                        is_online = True
                        break
            
            # addressとplaceが両方空または「-」の場合もオンラインとみなす
            if not is_online and (not address.strip() or address.strip() == '-') and (not place.strip() or place.strip() == '-'):
                is_online = True
            
            if is_online:
                online_events.append(event)
        
        print(f"Filtered to {len(online_events)} online events from {len(events)} total events")
        return online_events
    
    def _filter_by_keywords(self, events: List[Dict]) -> List[Dict]:
        """初心者・学習向けキーワードでフィルタリング"""
        filtered_events = []
        
        # 高重みキーワード（学生・キャリア関連）
        high_weight_keywords = ["学生", "キャリア", "インターン", "ガクチカ", "就活", "就職"]
        
        for event in events:
            title = (event.get('title') or '').lower()
            catch = (event.get('catch') or '').lower()
            description = (event.get('description') or '').lower()
            
            # イベント情報全体のテキスト
            event_text = f"{title} {catch} {description}"
            
            # キーワードマッチング（重み付き）
            match_score = 0
            matched_keywords = []
            for keyword in self.filter_keywords:
                if keyword.lower() in event_text:
                    # 高重みキーワードは1.5倍のスコア
                    if keyword in high_weight_keywords:
                        match_score += 1.5
                    else:
                        match_score += 1.0
                    matched_keywords.append(keyword)
            
            # 1つ以上のキーワードがマッチした場合に選択
            if match_score > 0:
                # マッチスコアをイベント情報に追加
                event['_match_score'] = match_score
                event['_matched_keywords'] = matched_keywords
                filtered_events.append(event)
                print(f"✓ Matched event: {event.get('title', 'N/A')} (score: {match_score:.1f})")
        
        print(f"Keyword-filtered to {len(filtered_events)} events from {len(events)} online events")
        return filtered_events
    
    def _get_fallback_courses(self) -> List[Dict]:
        """API利用不可時のフォールバックコース"""
        today = datetime.datetime.now()
        
        fallback_courses = [
            {
                "event_id": "fallback_1",
                "title": "Python初心者向けオンライン講座",
                "started_at": (today + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "プログラミング初心者でも安心のPython入門コース",
                "url": "https://connpass.com/event/example1/",
                "place": "オンライン開催",
                "address": "",
                "description": "<p>Python基礎からWebアプリ開発まで学べる実践的なオンライン講座です。</p><p>プログラミング未経験者でも安心の丁寧な指導で、実際のプロジェクトを通して学習できます。</p>",
                "_match_score": 5,
                "_matched_keywords": ["初心者", "スキル", "Web", "プログラミング", "エンジニア"]
            },
            {
                "event_id": "fallback_2", 
                "title": "Web制作スキルアップウェビナー",
                "started_at": (today + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "現役エンジニアが教えるWeb制作のコツ",
                "url": "https://connpass.com/event/example2/",
                "place": "オンライン配信",
                "address": "",
                "description": "<p>HTML/CSS/JavaScriptを使った実践的なWeb制作技術を学習できます。</p><p>レスポンシブデザインやモダンな開発手法も含めて幅広くカバーします。</p>",
                "_match_score": 4,
                "_matched_keywords": ["スキル", "Web", "プログラミング", "エンジニア"]
            },
            {
                "event_id": "fallback_3",
                "title": "データ分析入門オンラインセミナー", 
                "started_at": (today + datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "catch": "ExcelからPythonまで、データ分析の基礎を学ぼう",
                "url": "https://connpass.com/event/example3/",
                "place": "リモート開催",
                "address": "",
                "description": "<p>ビジネスに活かせるデータ分析スキルをオンラインで身につけられます。</p><p>ExcelからPython、統計解析まで段階的に学習し、実務で使える技術を習得できます。</p>",
                "_match_score": 6,
                "_matched_keywords": ["学ぶ", "スキル", "入門", "AI", "プログラミング", "エンジニア"]
            }
        ]
        
        return fallback_courses
    
    def format_courses_for_embed(self, courses: List[Dict]) -> List[Dict]:
        """オンライン講座情報をEmbed用にフォーマット"""
        if not courses:
            return [{
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
            }]
        
        # フォールバックデータかチェック
        is_fallback = any(course.get('event_id', '').startswith('fallback_') for course in courses)
        
        if is_fallback:
            return [{
                "title": "💻 今週のオンライン講座情報",
                "description": "⚠️ **現在、条件に合うイベントが見つかりませんでした**\n\n以下は参考として、よくあるオンライン講座のタイプをご紹介します：",
                "fields": [
                    {
                        "name": "🎯 人気のオンライン講座カテゴリ",
                        "value": "• **Python/プログラミング入門**\n• **Web制作・デザイン**\n• **データ分析・AI活用**\n• **キャリアアップ・転職支援**",
                        "inline": False
                    },
                    {
                        "name": "💡 イベントを探すコツ",
                        "value": "• [connpass](https://connpass.com/)で直接検索\n• 「オンライン」「初心者」などのキーワードで絞り込み\n• 興味のある技術分野で検索してみましょう！",
                        "inline": False
                    }
                ],
                "color": 0xFFA500,  # オレンジ色（注意喚起）
                "footer": {
                    "text": "💪 来週こそ素敵なイベントが見つかりますように！"
                }
            }]
        
        # 上位5件と下位5件に分割して2つのembedを作成
        print(f"DEBUG: format_courses_for_embed received {len(courses)} courses")
        
        def create_course_info(course):
            """個別のコース情報を作成"""
            try:
                # 日時をパース
                started_at_str = course.get('started_at', '')
                if started_at_str:
                    started_at = datetime.datetime.fromisoformat(
                        started_at_str.replace('+09:00', '')
                    )
                    date_str = started_at.strftime("%m/%d(%a) %H:%M")
                else:
                    date_str = "日時未定"
                
                # タイトルを短縮（35文字制限）
                title = course.get('title') or 'タイトル未定'
                if len(title) > 35:
                    title = title[:32] + "..."
                
                course_info = f"**{title}**\n📅 {date_str}"
                
                # キャッチコピーまたはdescriptionから要約を追加
                catch = (course.get('catch') or '').strip()
                description = (course.get('description') or '').strip()
                
                summary_text = ""
                if catch:
                    summary_text = catch
                elif description:
                    # HTMLタグを除去して最初の文を抽出
                    import re
                    clean_desc = re.sub(r'<[^>]+>', '', description)
                    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                    if clean_desc:
                        sentences = clean_desc.split('。')
                        first_sentence = sentences[0] if sentences else ""
                        if len(first_sentence) > 60:
                            summary_text = first_sentence[:57] + "..."
                        else:
                            summary_text = first_sentence + '。' if first_sentence else ""
                
                if summary_text:
                    if len(summary_text) > 60:
                        summary_text = summary_text[:57] + "..."
                    course_info += f"\n💡 {summary_text}"
                
                # 場所情報（簡略化）
                place = course.get('place') or 'オンライン'
                if place and place != 'オンライン':
                    if len(place) > 12:
                        place = place[:9] + "..."
                    course_info += f"\n📍 {place}"
                else:
                    course_info += f"\n📍 オンライン"
                
                # URL
                url = course.get('url') or course.get('event_url')
                if url:
                    course_info += f"\n🔗 [詳細・申込]({url})"
                
                return course_info
                
            except Exception as e:
                print(f"Error formatting course: {e}")
                return None
        
        # 上位5件用のembed
        first_courses = courses[:5]
        first_course_list = []
        for course in first_courses:
            course_info = create_course_info(course)
            if course_info:
                first_course_list.append(course_info)
        
        first_embed = {
            "title": "💻 今週のオンライン講座情報 (1/2)",
            "description": "**connpass**から厳選したオンライン講座をお届けします！\n新しいスキルを身につけるチャンス✨",
            "fields": [
                {
                    "name": "📚 注目の講座",
                    "value": "\n\n".join(first_course_list) if first_course_list else "講座情報の取得に失敗しました",
                    "inline": False
                }
            ],
            "color": 0x3498DB,
            "footer": {
                "text": "💡 気になる講座があれば早めの申込みがおすすめです！"
            }
        }
        
        # 下位5件用のembed（6件以上ある場合のみ）
        embeds = [first_embed]
        
        if len(courses) > 5:
            second_courses = courses[5:10]
            second_course_list = []
            for course in second_courses:
                course_info = create_course_info(course)
                if course_info:
                    second_course_list.append(course_info)
            
            if second_course_list:
                second_embed = {
                    "title": "💻 今週のオンライン講座情報 (2/2)",
                    "description": "続いて、こちらの講座もチェックしてみてください！",
                    "fields": [
                        {
                            "name": "📚 注目の講座",
                            "value": "\n\n".join(second_course_list),
                            "inline": False
                        },
                        {
                            "name": "🎯 オンライン学習のメリット",
                            "value": "• 自宅から気軽に参加可能\n• 移動時間ゼロで効率的\n• 録画視聴で復習も安心\n• 全国の講師から学べる",
                            "inline": False
                        }
                    ],
                    "color": 0x3498DB
                }
                embeds.append(second_embed)
        else:
            # 5件以下の場合は1つ目のembedにメリット情報を追加
            first_embed["fields"].append({
                "name": "🎯 オンライン学習のメリット",
                "value": "• 自宅から気軽に参加可能\n• 移動時間ゼロで効率的\n• 録画視聴で復習も安心\n• 全国の講師から学べる",
                "inline": False
            })
        
        return embeds
    
    async def get_weekly_courses(self):
        """今週のオンラインコースを取得"""
        try:
            # 既存のget_online_coursesメソッドを使用
            all_events = await self.get_online_courses(regions=[], days_ahead=7)
            return all_events
        except Exception as e:
            print(f"Error getting weekly courses: {e}")
            return []
    
    async def get_events_embed(self):
        """connpassから今週のイベント情報を取得してEmbed形式で返す"""
        try:
            courses = await self.get_weekly_courses()
            embeds = self.format_courses_for_embed(courses)
            return embeds
            
        except Exception as e:
            print(f"Error creating connpass embed: {e}")
            # エラー時のフォールバック
            return [{
                "title": "💻 今週のオンライン講座情報",
                "description": "申し訳ございません。現在、講座情報の取得に問題が発生しています。",
                "fields": [
                    {
                        "name": "🔄 再試行のお願い",
                        "value": "しばらく時間をおいてから再度お試しください。\nまたは[connpass](https://connpass.com/)で直接検索してみてください。",
                        "inline": False
                    }
                ],
                "color": 0xFF6B6B  # 赤色（エラー）
            }]