# -*- coding:utf-8 -*-
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from config.config import ADMIN_ID, RSS_CONFIG

class RSSMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rss_url = RSS_CONFIG["url"]
        self.check_interval = RSS_CONFIG["check_interval"]
        self.data_dir = RSS_CONFIG["data_dir"]
        self.last_check_file = RSS_CONFIG["last_check_file"]
        self.target_channel_id = RSS_CONFIG["target_channel_id"]
        self.mention_role_id = RSS_CONFIG["mention_role_id"]
        self.known_articles = set()
        
        # データディレクトリ作成
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 既知記事を読み込み
        self.load_known_articles()
        
    async def cog_load(self):
        """Cogが読み込まれた時に実行"""
        if self.bot.is_ready():
            self.start_rss_monitor()
    
    def start_rss_monitor(self):
        """RSS監視タスクを開始"""
        if not self.rss_monitor_task.is_running():
            self.rss_monitor_task.start()
    
    def cog_unload(self):
        """Cogがアンロードされる時にタスクを停止"""
        self.rss_monitor_task.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """ボット起動時にRSS監視を開始"""
        await asyncio.sleep(10)  # ボット完全起動を待つ
        self.start_rss_monitor()
        print("RSS Monitor started")
    
    def load_known_articles(self):
        """既知記事リストを読み込み"""
        if os.path.exists(self.last_check_file):
            try:
                with open(self.last_check_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.known_articles = set(data.get('known_articles', []))
                    print(f"Loaded {len(self.known_articles)} known articles")
            except Exception as e:
                print(f"Error loading known articles: {e}")
                self.known_articles = set()
        else:
            self.known_articles = set()
    
    def save_known_articles(self):
        """既知記事リストを保存"""
        try:
            data = {
                'known_articles': list(self.known_articles),
                'last_check': datetime.now(timezone.utc).isoformat()
            }
            with open(self.last_check_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving known articles: {e}")
    
    @tasks.loop(seconds=600)  # 10分間隔
    async def rss_monitor_task(self):
        """RSS監視メインタスク"""
        try:
            new_articles = await self.check_rss_feed()
            
            if new_articles:
                print(f"Found {len(new_articles)} new articles")
                
                for article in new_articles:
                    # 指定チャンネルに通知を送信
                    await self.send_new_article_notification(article)
                    await asyncio.sleep(1)  # レート制限対策
                
                # 既知記事リストを更新
                for article in new_articles:
                    self.known_articles.add(article['guid'])
                
                self.save_known_articles()
            
        except Exception as e:
            print(f"RSS monitoring error: {e}")
    
    async def check_rss_feed(self):
        """RSSフィードをチェックして新記事を検出"""
        try:
            print(f"Fetching RSS from: {self.rss_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url, timeout=30) as response:
                    if response.status == 200:
                        rss_content = await response.text()
                        print(f"RSS fetch successful, content length: {len(rss_content)}")
                        return self.parse_rss_content(rss_content)
                    else:
                        print(f"RSS fetch failed: Status {response.status} for URL: {self.rss_url}")
                        return []
        except asyncio.TimeoutError:
            print("RSS fetch timeout")
            return []
        except Exception as e:
            print(f"RSS fetch error: {e}")
            return []
    
    def parse_rss_content(self, rss_content):
        """RSS XMLを解析して新記事を抽出"""
        try:
            root = ET.fromstring(rss_content)
            new_articles = []
            
            # RSS 2.0形式のitemを検索
            for item in root.findall('.//item'):
                guid_elem = item.find('guid')
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                category_elem = item.find('category')
                
                if guid_elem is not None and guid_elem.text:
                    guid = guid_elem.text.strip()
                    
                    # 新記事かチェック
                    if guid not in self.known_articles:
                        article = {
                            'guid': guid,
                            'title': title_elem.text.strip() if title_elem is not None and title_elem.text else "タイトル不明",
                            'link': link_elem.text.strip() if link_elem is not None and link_elem.text else guid,
                            'description': self.clean_html(description_elem.text) if description_elem is not None and description_elem.text else "説明なし",
                            'pub_date': pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else "",
                            'category': category_elem.text.strip() if category_elem is not None and category_elem.text else "未分類"
                        }
                        new_articles.append(article)
            
            return new_articles
            
        except ET.ParseError as e:
            print(f"RSS XML parse error: {e}")
            return []
        except Exception as e:
            print(f"RSS content parse error: {e}")
            return []
    
    def clean_html(self, text):
        """HTMLタグを除去してテキストをクリーンアップ"""
        if not text:
            return ""
        
        # 簡単なHTMLタグ除去
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        clean_text = clean_text.replace('&quot;', '"').replace('&apos;', "'")
        
        # 改行とスペースを正規化
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # 150文字に制限
        if len(clean_text) > 150:
            clean_text = clean_text[:147] + "..."
        
        return clean_text
    
    async def send_new_article_notification(self, article):
        """新記事通知をDiscordに送信"""
        try:
            # 設定で指定されたチャンネルを取得
            target_channel = self.bot.get_channel(int(self.target_channel_id))
            
            if not target_channel:
                print(f"Target channel not found: {self.target_channel_id}")
                return
            
            if not target_channel.permissions_for(target_channel.guild.me).send_messages:
                print(f"No permission to send message in channel: {target_channel.name}")
                return
            
            # Embedを作成
            embed = discord.Embed(
                title="🆕 新しいブログ記事が公開されました！",
                description=f"**{article['title']}**",
                color=0x0099ff,
                url=article['link']
            )
            
            embed.add_field(
                name="🏷️ カテゴリ", 
                value=article['category'], 
                inline=True
            )
            
            if article['pub_date']:
                embed.add_field(
                    name="📅 公開日", 
                    value=self.format_pub_date(article['pub_date']), 
                    inline=True
                )
            
            embed.add_field(
                name="💡 概要", 
                value=article['description'], 
                inline=False
            )
            
            embed.add_field(
                name="🔗 記事を読む",
                value=f"[こちらからアクセス]({article['link']})",
                inline=False
            )
            
            embed.set_footer(text="FIND to DO Blog | プログラミング学習支援サイト")
            
            # ロールメンションを作成
            role_mention = f"<@&{self.mention_role_id}>"
            
            # 送信
            await target_channel.send(content=role_mention, embed=embed)
            print(f"Article notification sent to #{target_channel.name} with role mention")
            
        except discord.Forbidden:
            print(f"No permission to send message in channel: {target_channel.name}")
        except Exception as e:
            print(f"Error sending notification to channel: {e}")
    
    def format_pub_date(self, pub_date_str):
        """公開日をフォーマット"""
        try:
            # RFC 2822 形式をパース
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date_str)
            
            # JST変換
            jst = timezone(timedelta(hours=9))
            dt_jst = dt.astimezone(jst)
            
            return dt_jst.strftime("%Y年%m月%d日 %H:%M")
        except Exception:
            return pub_date_str
    
    async def get_all_rss_articles(self):
        """テスト用：全RSS記事を取得（既知チェックなし）"""
        try:
            print(f"[TEST] Fetching RSS from: {self.rss_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url, timeout=30) as response:
                    if response.status == 200:
                        rss_content = await response.text()
                        print(f"[TEST] RSS fetch successful, content length: {len(rss_content)}")
                        return self.parse_all_rss_content(rss_content)
                    else:
                        print(f"[TEST] RSS fetch failed: Status {response.status} for URL: {self.rss_url}")
                        # 404の場合、URLが正しいか確認を促す
                        if response.status == 404:
                            print(f"[TEST] RSS not found. Please check if the RSS is deployed at: {self.rss_url}")
                        return []
        except asyncio.TimeoutError:
            print("RSS fetch timeout")
            return []
        except Exception as e:
            print(f"RSS fetch error: {e}")
            return []
    
    def parse_all_rss_content(self, rss_content):
        """テスト用：全RSS記事を解析（既知チェックなし）"""
        try:
            root = ET.fromstring(rss_content)
            all_articles = []
            
            # RSS 2.0形式のitemを検索
            for item in root.findall('.//item'):
                guid_elem = item.find('guid')
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                category_elem = item.find('category')
                
                if guid_elem is not None and guid_elem.text:
                    article = {
                        'guid': guid_elem.text.strip(),
                        'title': title_elem.text.strip() if title_elem is not None and title_elem.text else "タイトル不明",
                        'link': link_elem.text.strip() if link_elem is not None and link_elem.text else guid_elem.text.strip(),
                        'description': self.clean_html(description_elem.text) if description_elem is not None and description_elem.text else "説明なし",
                        'pub_date': pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else "",
                        'category': category_elem.text.strip() if category_elem is not None and category_elem.text else "未分類"
                    }
                    all_articles.append(article)
            
            return all_articles
            
        except ET.ParseError as e:
            print(f"RSS XML parse error: {e}")
            return []
        except Exception as e:
            print(f"RSS content parse error: {e}")
            return []
    
    # テスト用コマンド
    @discord.app_commands.command(name='rss_test', description='RSS監視機能のテスト（管理者専用）')
    @discord.app_commands.default_permissions(administrator=True)
    async def test_rss_monitor(self, interaction: discord.Interaction):
        """RSS監視機能のテスト"""
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # テスト用に全記事を取得（既知記事チェックをスキップ）
            all_articles = await self.get_all_rss_articles()
            
            if all_articles:
                # 最新記事1件をテスト送信
                test_article = all_articles[0]
                await self.send_new_article_notification(test_article)
                
                await interaction.followup.send(
                    f"✅ テスト完了\n"
                    f"📄 RSS内の記事数: {len(all_articles)}件\n"
                    f"🆕 最新記事: {test_article['title']}\n"
                    f"📅 公開日: {test_article['pub_date']}\n"
                    f"💡 注: テストなので既知記事でも送信します",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ RSS取得失敗または記事が見つかりません",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ テスト中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
    
    @discord.app_commands.command(name='rss_status', description='RSS監視状況の確認（管理者専用）')
    @discord.app_commands.default_permissions(administrator=True)
    async def rss_status(self, interaction: discord.Interaction):
        """RSS監視状況を表示"""
        
        embed = discord.Embed(
            title="📊 RSS監視状況",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🌐 監視URL",
            value=self.rss_url,
            inline=False
        )
        
        embed.add_field(
            name="📢 投稿先チャンネル",
            value=f"<#{self.target_channel_id}>",
            inline=False
        )
        
        embed.add_field(
            name="🏷️ メンションロール",
            value=f"<@&{self.mention_role_id}>",
            inline=False
        )
        
        embed.add_field(
            name="⏰ チェック間隔",
            value=f"{self.check_interval // 60}分",
            inline=True
        )
        
        embed.add_field(
            name="📚 既知記事数",
            value=f"{len(self.known_articles)}件",
            inline=True
        )
        
        embed.add_field(
            name="🔄 監視状態",
            value="実行中" if self.rss_monitor_task.is_running() else "停止中",
            inline=True
        )
        
        # 最終チェック時刻
        if os.path.exists(self.last_check_file):
            try:
                with open(self.last_check_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_check = data.get('last_check', 'なし')
                    embed.add_field(
                        name="🕐 最終チェック",
                        value=last_check,
                        inline=False
                    )
            except:
                embed.add_field(
                    name="🕐 最終チェック",
                    value="不明",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RSSMonitorCog(bot))