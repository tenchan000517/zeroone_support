# -*- coding:utf-8 -*-
import discord
from discord.ext import commands, tasks
import datetime
import asyncio
from config.config import ADMIN_ID

class ChannelIntroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_intro_date = {}  # ギルドごとの最後の送信日を記録

    def generate_channel_description(self, channel: discord.TextChannel) -> str:
        """チャンネルの説明を動的に生成"""
        
        # topicがある場合はそれを使用
        if channel.topic:
            return channel.topic
        
        # チャンネル名から汎用的な説明を生成
        channel_name = channel.name.lower()
        
        if '一般' in channel_name or 'general' in channel_name:
            return "メンバー同士の雑談や、一般的な話題を楽しむチャンネルです。どなたでも気軽に参加できます！"
        elif '雑談' in channel_name or 'chat' in channel_name or 'talk' in channel_name:
            return "自由に雑談を楽しむチャンネルです。日常の出来事や趣味の話など、気軽にお話しましょう！"
        elif '質問' in channel_name or 'question' in channel_name or 'help' in channel_name:
            return "分からないことがあれば気軽に質問してください。メンバー同士で助け合いましょう！"
        elif 'お知らせ' in channel_name or 'news' in channel_name or 'announce' in channel_name:
            return "重要なお知らせや最新情報をお届けするチャンネルです。定期的にチェックしてください！"
        elif 'イベント' in channel_name or 'event' in channel_name:
            return "イベントの告知や参加者募集を行うチャンネルです。楽しいイベントにぜひご参加ください！"
        elif 'ボット' in channel_name or 'bot' in channel_name:
            return "ボットとの交流や機能テストを行うチャンネルです。様々なコマンドを試してみてください！"
        elif 'ビジネス' in channel_name or 'business' in channel_name:
            return "ビジネスに関する情報交換や相談を行うチャンネルです。起業や副業の話題も歓迎です！"
        elif 'プログラミング' in channel_name or 'programming' in channel_name or 'code' in channel_name:
            return "プログラミングに関する質問や技術的な議論を行うチャンネルです。コード共有も歓迎！"
        elif '音楽' in channel_name or 'music' in channel_name:
            return "音楽に関する話題や楽曲紹介を行うチャンネルです。好きなアーティストや楽曲をシェアしましょう！"
        elif 'ゲーム' in channel_name or 'game' in channel_name or 'gaming' in channel_name:
            return "ゲームに関する話題や一緒にプレイする仲間を募集するチャンネルです。楽しくゲームしましょう！"
        elif '作品' in channel_name or 'showcase' in channel_name or 'portfolio' in channel_name:
            return "創作物や作品を共有するチャンネルです。イラスト、写真、音楽など様々な作品をお待ちしています！"
        elif '学習' in channel_name or 'study' in channel_name or 'learning' in channel_name:
            return "学習に関する情報交換や勉強会の告知を行うチャンネルです。一緒に成長しましょう！"
        elif '新人' in channel_name or 'welcome' in channel_name or 'newcomer' in channel_name:
            return "新しく参加されたメンバーを歓迎するチャンネルです。自己紹介や挨拶をお気軽にどうぞ！"
        elif '開発' in channel_name or 'dev' in channel_name or 'development' in channel_name:
            return "開発に関する議論やプロジェクトの相談を行うチャンネルです。技術的な交流を深めましょう！"
        elif 'ニュース' in channel_name or 'news' in channel_name:
            return "最新のニュースや話題の情報を共有するチャンネルです。世の中の動向をチェックしましょう！"
        else:
            return f"「{channel.name}」に関連する話題を扱うチャンネルです。メンバー同士で活発な交流を楽しみましょう！"

    def check_role_panel_in_channel(self, channel: discord.TextChannel) -> tuple[bool, list]:
        """チャンネルにロールパネルメッセージがあるかチェック"""
        async def search_role_panels():
            role_panels = []
            try:
                async for message in channel.history(limit=200):
                    # ロールパネルの特徴を持つメッセージを探す
                    if (message.author == self.bot.user and 
                        message.embeds and 
                        any('ロール' in embed.title for embed in message.embeds if embed.title) and
                        message.components):  # ボタンがある
                        
                        # ボタンからロール情報を抽出
                        roles = []
                        for component in message.components:
                            if hasattr(component, 'children'):
                                for child in component.children:
                                    if hasattr(child, 'custom_id') and child.custom_id and child.custom_id.startswith('role_'):
                                        role_id = child.custom_id.replace('role_', '')
                                        role = channel.guild.get_role(int(role_id))
                                        if role:
                                            roles.append(role.name)
                        
                        if roles:
                            role_panels.append({
                                'message_id': message.id,
                                'roles': roles,
                                'created_at': message.created_at
                            })
                
                return len(role_panels) > 0, role_panels
            except:
                return False, []
        
        # 非同期関数を実行
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(search_role_panels())

    @discord.app_commands.command(name='channel_intro', description='サーバー内全チャンネル紹介を表示')
    @discord.app_commands.describe(
        role='表示対象となるロール（省略時は実行者のロールで判定）',
        format='出力形式（message または markdown）'
    )
    async def channel_intro(self, interaction: discord.Interaction, 
                           role: discord.Role = None, 
                           format: str = "message"):
        """サーバー内全チャンネル紹介を表示"""
        
        # 対象ロールを決定
        target_role = role or interaction.user.top_role
        
        # そのロールが見ることができるチャンネルを取得
        accessible_channels = []
        for channel in interaction.guild.text_channels:
            # チャンネルの表示権限をチェック
            permissions = channel.permissions_for_role(target_role)
            if permissions.view_channel:
                accessible_channels.append(channel)
        
        if not accessible_channels:
            await interaction.response.send_message("アクセス可能なチャンネルが見つかりませんでした。", ephemeral=True)
            return
        
        # カテゴリ別にグループ化
        categorized_channels = {}
        for channel in accessible_channels:
            category_name = channel.category.name if channel.category else "その他"
            if category_name not in categorized_channels:
                categorized_channels[category_name] = []
            categorized_channels[category_name].append(channel)
        
        # ロールパネルの場所を先に確認
        role_panel_channels = []
        for channel in accessible_channels:
            has_panel, panels = self.check_role_panel_in_channel(channel)
            if has_panel:
                role_panel_channels.append((channel, panels))
        
        if format.lower() == "markdown":
            # Markdown形式で全チャンネル紹介を生成
            intro_text = f"# 📋 {interaction.guild.name} チャンネル紹介\n\n"
            intro_text += f"**{target_role.name}** ロールでアクセス可能なチャンネル一覧です。\n\n"
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"## 📂 {category_name}\n\n"
                
                for channel in channels:
                    description = self.generate_channel_description(channel)
                    has_role_panel, role_panels = self.check_role_panel_in_channel(channel)
                    
                    intro_text += f"### #{channel.name}\n"
                    intro_text += f"{description}\n"
                    
                    if has_role_panel:
                        intro_text += f"🔔 **ここで通知ロールを取得できます**\n"
                    
                    intro_text += "\n"
                
                intro_text += "---\n\n"
            
            # ロールパネルの場所を案内
            if role_panel_channels:
                intro_text += "## 🔔 通知ロール取得について\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"**#{ch.name}** で通知ロール（{', '.join(set(all_roles))}）を取得できます\n"
                intro_text += "通知ロールを取得すると、重要なお知らせを見逃すことがありません！\n\n"
            
            intro_text += "## 🌟 コミュニティガイド\n"
            intro_text += "• 💬 挨拶から始めて、気軽に会話に参加してください\n" 
            intro_text += "• 📝 各チャンネルのルールを守って楽しく利用しましょう\n"
            intro_text += "• ❓ 分からないことがあれば質問チャンネルで気軽に聞いてください\n\n"
            intro_text += f"**ZERO to ONE** 🚀 みんなで作る素敵なコミュニティ"
            
        else:
            # 通常メッセージ形式で全チャンネル紹介を生成
            intro_text = f"**📋 {interaction.guild.name} チャンネル紹介**\n\n"
            intro_text += f"**{target_role.name}** ロールでアクセス可能なチャンネル一覧です。\n\n"
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"**📂 {category_name}**\n"
                
                for channel in channels:
                    description = self.generate_channel_description(channel)
                    has_role_panel, role_panels = self.check_role_panel_in_channel(channel)
                    
                    intro_text += f"• **#{channel.name}**: {description}"
                    
                    if has_role_panel:
                        intro_text += f" 🔔(通知ロール取得可能)"
                    
                    intro_text += "\n"
                
                intro_text += "\n"
            
            # ロールパネルの場所を案内
            if role_panel_channels:
                intro_text += "**🔔 通知ロール取得について**\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"#{ch.name} で通知ロール（{', '.join(set(all_roles))}）を取得できます\n"
                intro_text += "通知ロールを取得すると、重要なお知らせを見逃すことがありません！\n\n"
            
            intro_text += "**🌟 コミュニティガイド**\n"
            intro_text += "💬 挨拶から始めて、気軽に会話に参加してください\n"
            intro_text += "📝 各チャンネルのルールを守って楽しく利用しましょう\n\n"
            intro_text += "**ZERO to ONE** 🚀 みんなで作る素敵なコミュニティ"
        
        # 長すぎる場合は分割送信
        if len(intro_text) > 2000:
            await interaction.response.send_message("チャンネル紹介が長いため、複数回に分けて送信します。", ephemeral=True)
            
            # 2000文字ずつに分割
            chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk, ephemeral=True)
                else:
                    await interaction.followup.send(chunk, ephemeral=True)
        else:
            await interaction.response.send_message(intro_text, ephemeral=True)

    @discord.app_commands.command(name='channel_intro_config', description='チャンネル紹介の定期送信設定')
    @discord.app_commands.describe(
        action='設定アクション',
        channel='送信先チャンネル',
        enabled='有効/無効',
        hour='送信時刻（時）',
        minute='送信時刻（分）',
        interval_days='送信間隔（日数）'
    )
    async def channel_intro_config(self, interaction: discord.Interaction, 
                                  action: str,
                                  channel: discord.TextChannel = None,
                                  enabled: bool = None,
                                  hour: int = None,
                                  minute: int = None,
                                  interval_days: int = None):
        """チャンネル紹介の定期送信設定"""
        
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        # 設定はファイルベースで簡易実装
        guild_id = str(interaction.guild.id)
        
        if action.lower() == "show":
            # 現在の設定を表示
            embed = discord.Embed(
                title="🔧 チャンネル紹介 定期送信設定",
                description="現在の設定状況を表示します",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📝 機能説明",
                value="• サーバー全体のチャンネル紹介を定期送信\n• 通知ロール取得場所を分かりやすく案内\n• 新規メンバーへの案内効果が期待できます",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ 設定方法",
                value="`/channel_intro_config action:setup` で設定開始",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        elif action.lower() == "setup":
            embed = discord.Embed(
                title="✅ チャンネル紹介機能セットアップ完了",
                description="チャンネル紹介機能が利用可能になりました！",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🔧 利用可能なコマンド",
                value="• `/channel_intro` - サーバー全体のチャンネル紹介を表示\n• `/channel_intro format:markdown` - Markdown形式で表示\n• `/channel_intro role:@ロール名` - 指定ロールでの表示",
                inline=False
            )
            
            embed.add_field(
                name="✨ 機能特徴",
                value="• チャンネルのtopicがあれば自動使用\n• topicがなければチャンネル名から説明生成\n• 通知ロール取得場所を分かりやすく案内\n• カテゴリ別に整理して表示",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        else:
            await interaction.response.send_message(
                "利用可能なアクション: `show`（設定表示）, `setup`（セットアップ）",
                ephemeral=True
            )

    # 定期送信機能
    @tasks.loop(hours=24)
    async def daily_channel_intro(self):
        """定期的なチャンネル紹介送信"""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            
            # 設定ファイルから定期送信設定を読み込み（簡易実装）
            # 実際の運用では、設定管理システムと連携
            
            # 各チャンネルをチェック
            for channel in guild.text_channels:
                # ロールパネルがあるチャンネルを優先的に紹介
                has_role_panel, role_panels = self.check_role_panel_in_channel(channel)
                
                if has_role_panel:
                    # 最後の送信から一定期間経過していればチャンネル紹介を送信
                    last_sent = self.last_intro_date.get(f"{guild_id}_{channel.id}")
                    now = datetime.datetime.now()
                    
                    if not last_sent or (now - last_sent).days >= 7:  # 7日間隔
                        await self.send_periodic_intro(channel, has_role_panel, role_panels)
                        self.last_intro_date[f"{guild_id}_{channel.id}"] = now

    async def send_periodic_intro(self, channel: discord.TextChannel, has_role_panel: bool, role_panels: list):
        """定期的なチャンネル紹介の送信（サーバー全体の紹介）"""
        try:
            # サーバー全体のチャンネル紹介を生成
            guild = channel.guild
            intro_text = f"**📋 {guild.name} チャンネル紹介**\n\n"
            
            # カテゴリ別にチャンネルをグループ化
            categorized_channels = {}
            for ch in guild.text_channels:
                # @everyoneが見えるチャンネルのみ対象
                permissions = ch.permissions_for(guild.default_role)
                if permissions.view_channel:
                    category_name = ch.category.name if ch.category else "その他"
                    if category_name not in categorized_channels:
                        categorized_channels[category_name] = []
                    categorized_channels[category_name].append(ch)
            
            # ロールパネルの場所を先に確認
            role_panel_channels = []
            for ch in guild.text_channels:
                has_panel, panels = self.check_role_panel_in_channel(ch)
                if has_panel:
                    role_panel_channels.append((ch, panels))
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"**📂 {category_name}**\n"
                
                for ch in channels:
                    description = self.generate_channel_description(ch)
                    has_panel, panels = self.check_role_panel_in_channel(ch)
                    
                    intro_text += f"• **#{ch.name}**: {description}"
                    
                    if has_panel:
                        intro_text += f" 🔔(通知ロール取得可能)"
                    
                    intro_text += "\n"
                
                intro_text += "\n"
            
            # ロールパネルの場所を案内
            if role_panel_channels:
                intro_text += "**🔔 通知ロール取得について**\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"#{ch.name} で通知ロール（{', '.join(set(all_roles))}）を取得できます\n"
                intro_text += "通知ロールを取得すると、重要なお知らせを見逃すことがありません！\n\n"
            
            intro_text += "**🌟 コミュニティガイド**\n"
            intro_text += "💬 挨拶から始めて、気軽に会話に参加してください\n"
            intro_text += "📝 各チャンネルのルールを守って楽しく利用しましょう\n\n"
            intro_text += "**ZERO to ONE** 🚀 みんなで作る素敵なコミュニティ"
            
            # 長すぎる場合は分割送信
            if len(intro_text) > 2000:
                chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
                for chunk in chunks:
                    await channel.send(chunk)
            else:
                await channel.send(intro_text)
            
        except discord.Forbidden:
            # 送信権限がない場合はスキップ
            pass
        except Exception as e:
            print(f"Error sending periodic intro to {channel.name}: {e}")

    async def cog_load(self):
        """Cogロード時にタスクを開始"""
        if not self.daily_channel_intro.is_running():
            self.daily_channel_intro.start()

    def cog_unload(self):
        """Cogアンロード時にタスクを停止"""
        self.daily_channel_intro.cancel()

async def setup(bot):
    await bot.add_cog(ChannelIntroCog(bot))