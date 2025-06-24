#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Trends Manager カテゴリ分類デバッグ
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.enhanced_trends_manager import EnhancedTrendsManager

async def debug_categories():
    """カテゴリ分類の詳細デバッグ"""
    print("🔍 カテゴリ分類デバッグ開始")
    print("=" * 60)
    
    async with EnhancedTrendsManager() as manager:
        # トレンド取得
        trends = await manager.get_enhanced_trends(max_trends=20)
        
        print(f"📊 取得記事数: {len(trends)}件")
        print("\n📋 記事別カテゴリ判定詳細:")
        
        for i, trend in enumerate(trends[:10]):  # 最初の10件を詳細分析
            title = trend.get('title', '')
            description = trend.get('description', '')
            category = trend.get('category', '')
            confidence = trend.get('category_confidence', 0)
            
            print(f"\n【{i+1}】{title}")
            print(f"  🏷️ 判定カテゴリ: {category} (信頼度: {confidence})")
            print(f"  📝 説明文: {description[:50]}...")
            
            # 各カテゴリでのマッチ数をチェック
            combined_text = f"{title.lower()} {description.lower()}"
            print(f"  🔍 カテゴリ別マッチ数:")
            
            for cat, keywords in manager.category_keywords.items():
                matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)
                if matches > 0:
                    matched_keywords = [kw for kw in keywords if kw.lower() in combined_text]
                    print(f"    {cat}: {matches}件 -> {matched_keywords[:3]}")
        
        # カテゴリ統計
        print(f"\n📊 全体カテゴリ統計:")
        category_stats = {}
        for trend in trends:
            cat = trend.get('category', '不明')
            if cat not in category_stats:
                category_stats[cat] = []
            category_stats[cat].append(trend)
        
        for cat, items in category_stats.items():
            print(f"  {cat}: {len(items)}件")
            for item in items[:2]:  # 各カテゴリの代表例
                print(f"    - {item.get('title', 'N/A')[:40]}...")

if __name__ == "__main__":
    asyncio.run(debug_categories())