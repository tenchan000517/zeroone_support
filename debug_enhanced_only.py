#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')
import asyncio

async def test_enhanced_trends():
    """EnhancedTrendsManagerの単体テスト"""
    try:
        print("=== EnhancedTrendsManager Debug Test ===")
        
        from utils.enhanced_trends_manager import EnhancedTrendsManager
        print("✓ Import successful")
        
        async with EnhancedTrendsManager() as manager:
            print("✓ Manager initialized")
            
            # データ取得テスト
            print("\n--- データ取得テスト ---")
            trends = await manager.get_enhanced_trends(max_trends=10)
            print(f"取得件数: {len(trends)}")
            
            if trends:
                print(f"\n最初のトレンド:")
                first = trends[0]
                print(f"  Title: {first.get('title', 'N/A')}")
                print(f"  Category: {first.get('category', 'N/A')}")
                print(f"  Source: {first.get('source', 'N/A')}")
                print(f"  Quality Score: {first.get('quality_score', 'N/A')}")
                
                # Discord用フォーマットテスト
                print("\n--- Discord フォーマットテスト ---")
                embed_data = manager.format_trends_for_discord(trends[:5])
                print(f"Embed Title: {embed_data.get('title', 'N/A')}")
                print(f"Fields存在: {'fields' in embed_data}")
                print(f"Fields数: {len(embed_data.get('fields', []))}")
                print(f"Description長: {len(embed_data.get('description', ''))}")
                
                if embed_data.get('description'):
                    desc = embed_data['description']
                    print(f"Description preview: {desc[:200]}...")
                
            else:
                print("⚠️ データが取得できませんでした")
                
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_trends())