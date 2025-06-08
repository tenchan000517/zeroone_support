# -*- coding:utf-8 -*-
import discord
from discord.ext import commands

class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.app_commands.command(name='help', description='DJアイズの使い方を表示')
    async def help_command(self, interaction: discord.Interaction):
        """一般ユーザー向けヘルプコマンド"""
        
        embed = discord.Embed(
            title="🤖 DJアイズ 使い方ガイド",
            description="ZERO to ONEサポートBotの全機能",
            color=discord.Color.green()
        )
        
        # 基本コマンド
        embed.add_field(
            name="💬 基本機能",
            value=(
                "**メンション or DJアイズ**で話しかけてね！\n"
                "`@DJアイズ 天気` - 天気予報\n"
                "`@DJアイズ って何？` - Wikipedia検索\n"
                "`@DJアイズ 慰めて` - 励ましの言葉\n"
                "`@DJアイズ なろう [キーワード]` - 小説検索"
            ),
            inline=False
        )
        
        # 運勢・占い
        embed.add_field(
            name="🔮 占い・運勢",
            value=(
                "`今日の運勢` - ZERO to ONE星座占い（1日1回）\n"
                "`おみくじ` - スタートアップおみくじ\n"
                "`犯罪係数` - サイコパス診断"
            ),
            inline=False
        )
        
        # ゲーム・娯楽
        embed.add_field(
            name="🎮 ゲーム機能",
            value=(
                "`/rumble` - ランブル（バトルロイヤル）開始\n"
                "`@DJアイズ グー/チョキ/パー` - じゃんけん\n"
                "`@DJアイズ マインスイーパ` - マインスイーパー\n"
                "`@DJアイズ 1d6` - ダイスロール"
            ),
            inline=False
        )
        
        # ポイントシステム
        embed.add_field(
            name="💰 ポイントシステム",
            value=(
                "`/point check` - ポイント確認\n"
                "`/point daily` - デイリーボーナス（100pt）\n"
                "`/point ranking` - ランキング表示\n"
                "`/role_panel create` - ロール購入パネル作成（管理者）"
            ),
            inline=False
        )
        
        # 素数判定
        embed.add_field(
            name="🔢 特殊機能",
            value=(
                "`@DJアイズ 17は素数` - 素数判定\n"
                "`@DJアイズ お掃除` - #暴風域 のみ使用可"
            ),
            inline=False
        )
        
        # 定期配信
        embed.add_field(
            name="📰 毎日の定期配信",
            value=(
                "月: 💎 起業家格言\n"
                "火: 📊 ビジネストレンド\n"
                "水: 🛠️ スキルアップTips\n"
                "木: 🌐 テックニュース（リアルタイム）\n"
                "金: 🎯 今日のチャレンジ\n"
                "土: 🎪 地域イベント情報\n"
                "日: 🚀 成功マインドセット"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 AI機能：メンションして質問すると、AIが回答します！")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpSystem(bot))