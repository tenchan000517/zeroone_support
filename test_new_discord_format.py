#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しいDiscord埋め込みフォーマットのテスト
シンプルで読みやすい形式の確認
"""

import asyncio
from utils.enhanced_trends_manager import EnhancedTrendsManager

async def test_new_discord_format():
    """新しいDiscord埋め込みフォーマットのテスト"""
    print("🎮 新しいDiscord埋め込みフォーマット テスト")
    print("=" * 70)
    
    async with EnhancedTrendsManager() as manager:
        # トレンドデータ取得
        trends = await manager.get_enhanced_trends(max_trends=100)
        print(f"📊 取得データ数: {len(trends)}件")
        
        # 新しいDiscord埋め込み形式生成
        discord_data = manager.format_trends_for_discord(trends)
        
        # 埋め込みメッセージの詳細表示
        print("\n🎯 【Discord埋め込みメッセージプレビュー】")
        print("┌" + "─" * 68 + "┐")
        print(f"│ {discord_data.get('title', 'タイトルなし'):^66} │")
        print("└" + "─" * 68 + "┘")
        print()
        
        # 説明文（メインコンテンツ）を表示
        description = discord_data.get('description', '')
        print("📝 【説明文（メインコンテンツ）】")
        print("─" * 50)
        print(description)
        print()
        
        # フッター情報
        footer = discord_data.get('footer', {})
        if footer:
            print("👣 【フッター】")
            print("─" * 20)
            print(f"  {footer.get('text', '')}")
            print()
        
        # 埋め込みの制限チェック
        print("🔍 【Discord制限チェック】")
        print("─" * 30)
        
        title_len = len(discord_data.get('title', ''))
        desc_len = len(discord_data.get('description', ''))
        
        print(f"📋 タイトル: {title_len}/256文字 {'✅' if title_len <= 256 else '❌'}")
        print(f"📝 説明: {desc_len}/4096文字 {'✅' if desc_len <= 4096 else '❌'}")
        print(f"🎨 色: #{discord_data.get('color', 0):06x}")
        
        print()
        
        # カテゴリ別統計
        print("📊 【カテゴリ別統計】")
        print("─" * 25)
        categories_in_desc = []
        lines = description.split('\n')
        for line in lines:
            if line.startswith('📂 **') and line.endswith('**'):
                category = line.replace('📂 **', '').replace('**', '')
                categories_in_desc.append(category)
        
        print(f"✅ 表示カテゴリ数: {len(categories_in_desc)}個")
        for i, category in enumerate(categories_in_desc, 1):
            print(f"  {i}. {category}")
        
        # メンション情報
        print("\n💬 【メンション設定】")
        print("─" * 20)
        print("📅 配信日: 毎週水曜日 7:00")
        print("🔔 メンション: <@&1386267058307600525> (trends - ビジネストレンド速報)")
        print("📨 実際の送信内容:")
        print(f"    <@&1386267058307600525> [埋め込みメッセージ]")
        
        # 実際の表示イメージ
        print("\n" + "=" * 70)
        print("🎯 【実際のDiscord表示イメージ】")
        print("=" * 70)
        print()
        print("💬 **#トレンド配信チャンネル**")
        print("─" * 40)
        print("🤖 **ZERO to ONE Bot** - 今日 午前7:00")
        print()
        print("<@&1386267058307600525>")  # メンション表示
        print()
        
        # 埋め込みメッセージの表示
        print("┌─────────────────────────────────────────┐")
        print(f"│ {discord_data.get('title', ''):^39} │")
        print("├─────────────────────────────────────────┤")
        
        # 説明文を40文字ずつに分割して表示
        desc_lines = []
        current_line = ""
        words = description.split(' ')
        
        for word in words:
            if len(current_line + word) <= 39:
                current_line += word + " "
            else:
                if current_line:
                    desc_lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            desc_lines.append(current_line.strip())
        
        # 最初の10行のみ表示（長すぎる場合）
        display_lines = desc_lines[:10]
        if len(desc_lines) > 10:
            display_lines.append("...")
        
        for line in display_lines:
            print(f"│ {line:<39} │")
        
        print("├─────────────────────────────────────────┤")
        if footer:
            print(f"│ {footer.get('text', ''):<39} │")
        print("└─────────────────────────────────────────┘")
        
        print("\n" + "=" * 70)
        print("✅ 新しいフォーマットのテスト完了！")
        print("🎉 水曜日配信の準備が整いました")
        
        # 改善点の確認
        if len(categories_in_desc) >= 7:
            print("✅ 7カテゴリ表示: 成功")
        else:
            print(f"❌ 7カテゴリ表示: 失敗 ({len(categories_in_desc)}/7)")
        
        if desc_len <= 4096:
            print("✅ 文字数制限: クリア")
        else:
            print("❌ 文字数制限: 超過")
        
        return len(categories_in_desc) >= 7 and desc_len <= 4096

if __name__ == "__main__":
    result = asyncio.run(test_new_discord_format())
    exit(0 if result else 1)