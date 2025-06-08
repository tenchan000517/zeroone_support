# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
import asyncio
import datetime
from config.config import ADMIN_ID

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def categorize_channels(self, guild: discord.Guild) -> dict:
        """チャンネルを自動分類"""
        categories = {
            "general": [],
            "introduction": [],
            "role": [],
            "announcement": [],
            "chat": [],
            "other": []
        }
        
        # テキストチャンネルのみを対象
        text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
        
        for channel in text_channels:
            name_lower = channel.name.lower()
            
            # 一般・メイン
            if any(word in name_lower for word in ['general', '一般', 'メイン', 'main', 'lobby', 'ロビー']):
                categories["general"].append(channel)
            # 自己紹介
            elif any(word in name_lower for word in ['自己紹介', 'introduction', 'intro', '紹介', 'profile']):
                categories["introduction"].append(channel)
            # ロール取得
            elif any(word in name_lower for word in ['role', 'ロール', '役職', '通知']):
                categories["role"].append(channel)
            # アナウンス・お知らせ
            elif any(word in name_lower for word in ['announce', 'アナウンス', 'お知らせ', 'news', 'ニュース', '重要']):
                categories["announcement"].append(channel)
            # 雑談
            elif any(word in name_lower for word in ['chat', '雑談', 'talk', 'random', 'ランダム', '話']):
                categories["chat"].append(channel)
            else:
                categories["other"].append(channel)
        
        return categories
    
    def create_welcome_embed(self, member: discord.Member, guild: discord.Guild) -> discord.Embed:
        """ZERO to ONE専用ウェルカムメッセージのEmbedを作成"""
        # Embed作成
        embed = discord.Embed(
            title=f"🚀 Welcome to ZERO to ONE！",
            description=f"{member.mention}さん、ようこそ！\n\n"
                       f"**夢を現実に変える場所へ**\n"
                       f"ここは起業家・クリエイター・イノベーターが集まるコミュニティです。\n\n"
                       f"あなたのアイデアが、次の大きな一歩になるかもしれません。\n"
                       f"共に学び、成長し、新しい価値を創造しましょう！",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        # ユーザーのアバターを設定
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # フィールド追加
        embed.add_field(
            name="🎯 はじめに",
            value="• 自己紹介チャンネルで自分を紹介しよう\n"
                  "• 興味のあるトピックに参加しよう\n"
                  "• 質問や相談は気軽にどうぞ！",
            inline=False
        )
        
        embed.add_field(
            name="🤖 DJアイズで遊ぼう！",
            value="• `/help` - 全機能の使い方\n"
                  "• `今日の運勢` - 占い\n"
                  "• `おみくじ` - ビジネス運チェック\n"
                  "• `@DJアイズ` - AIに質問！",
            inline=True
        )
        
        embed.add_field(
            name="📰 毎日配信",
            value="• 月-金: ビジネスTips\n"
                  "• 土: イベント情報\n"
                  "• 日: 成功マインド\n"
                  "毎朝7時に有益情報！",
            inline=True
        )
        
        # チャンネルを分類
        categories = self.categorize_channels(guild)
        
        # 🏠 はじめに
        start_channels = []
        if categories["introduction"]:
            start_channels.extend([f"{ch.mention}" for ch in categories["introduction"][:2]])
        if categories["role"]:
            start_channels.extend([f"{ch.mention}" for ch in categories["role"][:2]])
        
        if start_channels:
            embed.add_field(
                name="🏠 まずはこちらから",
                value="\n".join([
                    f"📝 **自己紹介・ロール取得**",
                    *start_channels[:4],  # 最大4個
                    "ここで自己紹介とロール設定をお願いします！"
                ]),
                inline=False
            )
        
        # 📢 重要なお知らせ
        important_channels = []
        if categories["announcement"]:
            important_channels.extend([f"{ch.mention}" for ch in categories["announcement"][:3]])
        
        if important_channels:
            embed.add_field(
                name="📢 重要なお知らせ",
                value="\n".join([
                    f"🔔 **最新情報をチェック**",
                    *important_channels,
                    "サーバーの最新情報やルールをご確認ください"
                ]),
                inline=False
            )
        
        # 💬 交流エリア
        social_channels = []
        if categories["general"]:
            social_channels.extend([f"{ch.mention}" for ch in categories["general"][:2]])
        if categories["chat"]:
            social_channels.extend([f"{ch.mention}" for ch in categories["chat"][:3]])
        
        if social_channels:
            embed.add_field(
                name="💬 交流エリア",
                value="\n".join([
                    f"🗣️ **気軽にお話しください**",
                    *social_channels[:5],  # 最大5個
                    "メンバー同士で楽しく交流しましょう！"
                ]),
                inline=False
            )
        
        # 📚 その他のチャンネル
        other_important = [ch for ch in categories["other"] if ch.position < 10][:3]  # 上位のチャンネル
        if other_important:
            embed.add_field(
                name="📚 その他のチャンネル",
                value="\n".join([
                    f"🔍 **その他のコンテンツ**",
                    *[f"{ch.mention}" for ch in other_important],
                    "専門的な話題や特別なコンテンツはこちら"
                ]),
                inline=False
            )
        
        embed.set_footer(
            text=f"Let's make it happen! 🌟 | メンバー数: {guild.member_count}人",
            icon_url=guild.icon.url if guild.icon else None
        )
        
        return embed
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """メンバーが参加した時の自動ウェルカムメッセージ"""
        guild = member.guild
        
        # Mee6などの他ボットより後に送信されるよう遅延
        await asyncio.sleep(3)
        
        # システムチャンネルまたは一般チャンネルを取得
        welcome_channel = None
        
        # 1. システムチャンネル
        if guild.system_channel:
            welcome_channel = guild.system_channel
        else:
            # 2. general系チャンネル
            categories = self.categorize_channels(guild)
            if categories["general"]:
                welcome_channel = categories["general"][0]
            # 3. 最初のテキストチャンネル
            else:
                text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                if text_channels:
                    welcome_channel = text_channels[0]
        
        if welcome_channel:
            try:
                embed = self.create_welcome_embed(member, guild)
                await welcome_channel.send(f"{member.mention}", embed=embed)
                print(f"Welcome message sent for {member.display_name} in {guild.name}")
            except discord.Forbidden:
                print(f"No permission to send welcome message in {welcome_channel.name}")
            except Exception as e:
                print(f"Error sending welcome message: {e}")
    
    @discord.app_commands.command(name='welcome_test', description='ウェルカムメッセージのテスト表示')
    async def test_welcome(self, interaction: discord.Interaction):
        """ウェルカムメッセージのテスト（管理者専用）"""
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        # テスト用のEmbedを作成
        embed = self.create_welcome_embed(interaction.user, interaction.guild)
        
        # 管理者にのみ表示
        await interaction.response.send_message(
            "📋 **ウェルカムメッセージのプレビュー**\n"
            "実際のメッセージは以下のようになります：",
            embed=embed,
            ephemeral=True
        )
        
        # チャンネル分類の詳細情報も表示
        categories = self.categorize_channels(interaction.guild)
        detail_info = []
        
        for category, channels in categories.items():
            if channels:
                channel_list = ", ".join([ch.name for ch in channels[:3]])
                if len(channels) > 3:
                    channel_list += f" など({len(channels)}個)"
                detail_info.append(f"**{category}**: {channel_list}")
        
        if detail_info:
            detail_embed = discord.Embed(
                title="🔍 チャンネル分類詳細",
                description="\n".join(detail_info),
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=detail_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))