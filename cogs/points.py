# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
from utils.point_manager import PointManager
from config.config import ADMIN_ID

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.point_manager = PointManager()
    
    @commands.command(name='ポイント確認')
    async def check_points(self, ctx):
        """自分のポイントを確認"""
        points = self.point_manager.get_points(str(ctx.author.id))
        settings = self.point_manager.get_server_settings(str(ctx.guild.id))
        await ctx.send(f"{ctx.author.mention} 現在の{settings.point_name}: **{points}**")
    
    @commands.command(name='デイリーボーナス')
    async def daily_bonus(self, ctx):
        """デイリーボーナスを受け取る"""
        success, message = self.point_manager.claim_daily_bonus(
            str(ctx.author.id), 
            str(ctx.guild.id)
        )
        await ctx.send(f"{ctx.author.mention} {message}")
    
    @commands.command(name='ランキング')
    async def leaderboard(self, ctx):
        """ポイントランキングを表示"""
        leaderboard = self.point_manager.get_leaderboard(10)
        settings = self.point_manager.get_server_settings(str(ctx.guild.id))
        
        if not leaderboard:
            await ctx.send("まだランキングデータがありません")
            return
        
        embed = discord.Embed(
            title=f"{settings.point_name}ランキング TOP10",
            color=discord.Color.gold()
        )
        
        for i, (user_id, points) in enumerate(leaderboard, 1):
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"Unknown ({user_id})"
            embed.add_field(
                name=f"{i}位",
                value=f"{name}: {points}{settings.point_name}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ポイント付与')
    async def add_points_admin(self, ctx, member: discord.Member, amount: int, *, reason: str = "管理者による付与"):
        """管理者がポイントを付与"""
        if str(ctx.author.id) != ADMIN_ID:
            await ctx.send("このコマンドは管理者のみ使用できます")
            return
        
        if amount <= 0:
            await ctx.send("付与するポイントは1以上にしてください")
            return
        
        success = self.point_manager.add_points(str(member.id), amount, reason)
        settings = self.point_manager.get_server_settings(str(ctx.guild.id))
        
        if success:
            await ctx.send(f"{member.mention} に {amount}{settings.point_name} を付与しました（理由: {reason}）")
        else:
            await ctx.send("ポイントの付与に失敗しました")
    
    @commands.command(name='ポイント削除')
    async def remove_points_admin(self, ctx, member: discord.Member, amount: int, *, reason: str = "管理者による削除"):
        """管理者がポイントを削除"""
        if str(ctx.author.id) != ADMIN_ID:
            await ctx.send("このコマンドは管理者のみ使用できます")
            return
        
        if amount <= 0:
            await ctx.send("削除するポイントは1以上にしてください")
            return
        
        success = self.point_manager.remove_points(str(member.id), amount, reason)
        settings = self.point_manager.get_server_settings(str(ctx.guild.id))
        
        if success:
            await ctx.send(f"{member.mention} から {amount}{settings.point_name} を削除しました（理由: {reason}）")
        else:
            await ctx.send("ポイントが不足しているか、エラーが発生しました")
    
    @commands.command(name='ポイント設定')
    async def set_points_admin(self, ctx, member: discord.Member, amount: int):
        """管理者がポイントを直接設定"""
        if str(ctx.author.id) != ADMIN_ID:
            await ctx.send("このコマンドは管理者のみ使用できます")
            return
        
        if amount < 0:
            await ctx.send("ポイントは0以上にしてください")
            return
        
        success = self.point_manager.set_points(str(member.id), amount)
        settings = self.point_manager.get_server_settings(str(ctx.guild.id))
        
        if success:
            await ctx.send(f"{member.mention} の{settings.point_name}を {amount} に設定しました")
        else:
            await ctx.send("ポイントの設定に失敗しました")

async def setup(bot):
    await bot.add_cog(Points(bot))