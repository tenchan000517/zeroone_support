#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Embed表示シミュレーションテスト
実際の埋め込みメッセージの内容と文字数制限を確認
"""

import asyncio
import sys
sys.path.append('/mnt/c/zeroone_support')

from utils.enhanced_trends_manager import EnhancedTrendsManager

def simulate_discord_embed(embed_data):
    """Discord Embedメッセージをテキストでシミュレーション"""
    print("=" * 60)
    print("🎮 DISCORD EMBED シミュレーション")
    print("=" * 60)
    
    # タイトル表示
    print(f"📋 タイトル: {embed_data['title']}")
    print(f"📝 説明: {embed_data['description']}")
    print(f"🎨 色: #{embed_data['color']:06x}")
    print()
    
    # フィールド表示（実際のDiscord表示に近い形式）
    print("📂 フィールド一覧:")
    print("-" * 50)
    
    total_chars = 0
    for i, field in enumerate(embed_data['fields'], 1):
        field_name = field['name']
        field_value = field['value']
        
        print(f"\n【フィールド {i}】")
        print(f"🏷️ 名前: {field_name}")
        print(f"📏 文字数: {len(field_value)}文字")
        
        # 文字数制限チェック
        if len(field_value) > 1024:
            print("⚠️ 警告: 1024文字制限を超過!")
            print(f"📝 内容（最初の500文字）:\n{field_value[:500]}...")
        else:
            print("✅ 文字数制限内")
            print(f"📝 内容:\n{field_value}")
        
        total_chars += len(field_value)
        print(f"📊 累積文字数: {total_chars}文字")
    
    # フッター表示
    if 'footer' in embed_data:
        print(f"\n👣 フッター: {embed_data['footer']['text']}")
    
    # 全体統計
    print("\n" + "=" * 50)
    print("📊 Discord Embed統計情報")
    print("=" * 50)
    print(f"📋 タイトル文字数: {len(embed_data['title'])}文字")
    print(f"📝 説明文字数: {len(embed_data['description'])}文字")
    print(f"📂 フィールド数: {len(embed_data['fields'])}個")
    print(f"📏 全フィールド合計文字数: {total_chars}文字")
    
    # 制限チェック
    print("\n🔍 Discord制限チェック:")
    print(f"  タイトル (256文字制限): {'✅' if len(embed_data['title']) <= 256 else '❌'}")
    print(f"  説明 (4096文字制限): {'✅' if len(embed_data['description']) <= 4096 else '❌'}")
    print(f"  フィールド数 (25個制限): {'✅' if len(embed_data['fields']) <= 25 else '❌'}")
    
    field_limit_ok = all(len(field['value']) <= 1024 for field in embed_data['fields'])
    print(f"  各フィールド (1024文字制限): {'✅' if field_limit_ok else '❌'}")

async def test_enhanced_trends_discord_display():
    """新システムの実際のDiscord表示をテストする"""
    print("🚀 Enhanced Trends Manager Discord表示テスト開始")
    print("=" * 60)
    
    async with EnhancedTrendsManager() as manager:
        # 実際のトレンドデータ取得
        print("📈 トレンドデータ取得中...")
        all_trends = await manager.get_enhanced_trends(max_trends=200)
        print(f"✅ {len(all_trends)}件のトレンドデータを取得")
        
        # カテゴリ別に分類・ソート（weekly_content.pyと同じロジック）
        print("\n📂 カテゴリ別分類開始...")
        categorized = {}
        for trend in all_trends:
            category = trend.get('category', '一般')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(trend)
        
        print(f"📊 検出カテゴリ: {list(categorized.keys())}")
        
        # 各カテゴリ上位1-2件抽出
        top_trends = {}
        for category, trends in categorized.items():
            sorted_trends = sorted(trends, key=lambda x: x.get('quality_score', 0), reverse=True)
            top_trends[category] = sorted_trends[:2]  # 上位2件
            print(f"  🏷️ {category}: {len(trends)}件 → 上位{len(sorted_trends[:2])}件抽出")
        
        # Discord用フォーマット生成
        final_trends = [trend for trends in top_trends.values() for trend in trends]
        print(f"\n🎯 最終選択: {len(final_trends)}件")
        
        embed_data = manager.format_trends_for_discord(final_trends)
        print("✅ Discord Embed形式生成完了")
        
        # シミュレーション実行
        print("\n" + "🎮" * 20)
        simulate_discord_embed(embed_data)
        
        return embed_data

async def test_field_splitting():
    """フィールド分割テスト（1024文字制限対応）"""
    print("\n🔧 フィールド分割テスト")
    print("=" * 40)
    
    # 長いコンテンツの例
    long_content = """🔥 **非常に長いタイトルの記事例: プログラミング初心者から上級者まで学べる完全ガイド集**
📰 Zenn | 品質: 100/100 | ❤️ 500

🔥 **もう一つの長い記事: データサイエンスと機械学習を活用したビジネス課題解決の実践的アプローチ**
📰 Hacker News | 品質: 95/100 | ❤️ 300

🔥 **三番目の記事: ウェブ開発における最新のフレームワーク比較と選択指針**
📰 Google News | 品質: 90/100 | ❤️ 200""" * 5  # 5倍に拡張
    
    print(f"📏 テストコンテンツ文字数: {len(long_content)}文字")
    
    # 1024文字で分割
    if len(long_content) > 1024:
        print("⚠️ 1024文字を超過 - 分割が必要")
        
        # 分割ロジック
        chunks = []
        current_chunk = ""
        lines = long_content.split('\n')
        
        for line in lines:
            test_chunk = current_chunk + ("\n" if current_chunk else "") + line
            if len(test_chunk) <= 1024:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"📦 {len(chunks)}個のチャンクに分割:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  チャンク{i}: {len(chunk)}文字")
            print(f"    プレビュー: {chunk[:100]}...")
    else:
        print("✅ 1024文字以内 - 分割不要")

if __name__ == "__main__":
    print("🎮 Discord Embed表示シミュレーションテスト")
    print("=" * 60)
    
    # メインテスト実行
    asyncio.run(test_enhanced_trends_discord_display())
    
    # フィールド分割テスト実行
    asyncio.run(test_field_splitting())
    
    print("\n🎉 テスト完了!")