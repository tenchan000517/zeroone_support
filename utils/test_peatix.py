#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peatixスクレイピングのテストスクリプト
実際のPeatix HTMLの構造を確認するためのツール
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def test_peatix_search():
    # テスト用URL
    url = f"https://peatix.com/search?q={quote('愛知 ビジネス')}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ja,en;q=0.9',
    }
    
    print(f"Fetching: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 様々なセレクタを試す
            selectors = [
                ('article', None),
                ('div', {'class': 'event'}),
                ('div', {'class': 'search-result'}),
                ('a', {'href': lambda x: x and '/event/' in x}),
                ('div', {'role': 'article'}),
                ('li', {'class': lambda x: x and 'event' in str(x)}),
            ]
            
            for tag, attrs in selectors:
                if attrs:
                    elements = soup.find_all(tag, attrs)
                else:
                    elements = soup.find_all(tag)
                print(f"\n{tag} {attrs}: Found {len(elements)} elements")
                
                if elements:
                    # 最初の要素の構造を表示
                    first = elements[0]
                    print(f"First element classes: {first.get('class', [])}")
                    print(f"HTML preview: {str(first)[:200]}...")
                    
                    # タイトルらしきものを探す
                    for title_tag in ['h1', 'h2', 'h3', 'h4', 'a']:
                        title_elem = first.find(title_tag)
                        if title_elem:
                            text = title_elem.get_text(strip=True)
                            if len(text) > 5:  # 意味のあるテキスト
                                print(f"Potential title ({title_tag}): {text[:50]}")
                                break
            
            # JavaScript rendered content check
            scripts = soup.find_all('script')
            print(f"\nFound {len(scripts)} script tags")
            for script in scripts[:3]:
                if script.string and 'event' in script.string.lower():
                    print("Found event-related JavaScript")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_peatix_search()