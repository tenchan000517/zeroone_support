"""
即座に適用すべき修正
チャンネル権限チェックの緩和
"""

# 修正1: on_message のチャンネル権限チェックを緩和
ON_MESSAGE_FIX = '''
@commands.Cog.listener()
async def on_message(self, message):
    """メッセージ送信時にカウント（修正版）"""
    # BOTメッセージは除外
    if message.author.bot:
        return
    
    # ギルドチェック
    if not message.guild:
        return
    
    try:
        print(f"🔍 [METRICS] メッセージ受信: {message.author.name} in {message.channel.name}")
        
        # チャンネルIDとユーザーIDを文字列で管理
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # 運営ロールかどうかチェック
        staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role and (staff_role in message.author.roles)
        print(f"🔍 [METRICS] is_staff: {is_staff}")
        
        # メッセージカウント（権限チェックを一時的に削除）
        if is_staff:
            if channel_id not in self.staff_message_counts:
                self.staff_message_counts[channel_id] = {}
            if user_id not in self.staff_message_counts[channel_id]:
                self.staff_message_counts[channel_id][user_id] = 0
            self.staff_message_counts[channel_id][user_id] += 1
            print(f"📊 [METRICS] 運営メッセージカウント +1: {message.author.name}")
        else:
            if channel_id not in self.message_counts:
                self.message_counts[channel_id] = {}
            if user_id not in self.message_counts[channel_id]:
                self.message_counts[channel_id][user_id] = 0
            self.message_counts[channel_id][user_id] += 1
            print(f"📊 [METRICS] ユーザーメッセージカウント +1: {message.author.name}")
        
        # 現在のカウント状況を表示
        total_user = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
        
        print(f"📊 [METRICS] 現在の合計 - ユーザー: {total_user}件, 運営: {total_staff}件")
        
    except Exception as e:
        print(f"❌ [METRICS] on_message処理エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
'''

# または、権限チェックを残しつつ条件を緩和する版
ON_MESSAGE_FIX_V2 = '''
@commands.Cog.listener()
async def on_message(self, message):
    """メッセージ送信時にカウント（権限チェック改善版）"""
    # BOTメッセージは除外
    if message.author.bot:
        return
    
    # ギルドチェック
    if not message.guild:
        return
    
    try:
        print(f"🔍 [METRICS] メッセージ受信: {message.author.name} in {message.channel.name}")
        
        # プライベートチャンネルの判定を改善
        # カテゴリーチャンネルやスレッドも考慮
        is_private = False
        
        # NSFWチャンネルまたは明らかなプライベートチャンネルのみ除外
        if hasattr(message.channel, 'is_nsfw') and message.channel.is_nsfw():
            is_private = True
            print(f"❌ [METRICS] NSFWチャンネルのため除外")
        
        # プライベートスレッドも除外
        if hasattr(message.channel, 'type') and message.channel.type == discord.ChannelType.private_thread:
            is_private = True
            print(f"❌ [METRICS] プライベートスレッドのため除外")
        
        if is_private:
            return
        
        # チャンネルIDとユーザーIDを文字列で管理
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # 運営ロールかどうかチェック
        staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role and (staff_role in message.author.roles)
        
        # メッセージカウント
        if is_staff:
            if channel_id not in self.staff_message_counts:
                self.staff_message_counts[channel_id] = {}
            if user_id not in self.staff_message_counts[channel_id]:
                self.staff_message_counts[channel_id][user_id] = 0
            self.staff_message_counts[channel_id][user_id] += 1
            print(f"📊 [METRICS] 運営メッセージカウント +1: {message.author.name}")
        else:
            if channel_id not in self.message_counts:
                self.message_counts[channel_id] = {}
            if user_id not in self.message_counts[channel_id]:
                self.message_counts[channel_id][user_id] = 0
            self.message_counts[channel_id][user_id] += 1
            print(f"📊 [METRICS] ユーザーメッセージカウント +1: {message.author.name}")
        
        # 現在のカウント状況を表示
        total_user = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
        
        print(f"📊 [METRICS] 現在の合計 - ユーザー: {total_user}件, 運営: {total_staff}件")
        
    except Exception as e:
        print(f"❌ [METRICS] on_message処理エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
'''

print("選択してください：")
print("1. 権限チェックを完全に削除（すべてのチャンネルをカウント）")
print("2. 権限チェックを緩和（NSFWとプライベートスレッドのみ除外）")
print("\n推奨: オプション1（まずは動作確認を優先）")