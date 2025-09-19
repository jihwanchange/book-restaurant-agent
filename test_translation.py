#!/usr/bin/env python3
"""Test the new translation service."""

import sys
sys.path.append('server')

from book_agent.translation_service import translate_korean_query

def test_translation():
    print("Testing new translation service...")

    # Test queries that previously failed
    test_queries = [
        "중식집 추천해줘",
        "피자 추천해줘",
        "이탈리아 음식",
        "일식집 알려줘",
        "태국 음식점",
        "Korean BBQ",  # English should be left unchanged
        "스테이크 맛집",
        "카페 찾아줘",
        "브런치 카페"
    ]

    for query in test_queries:
        print(f"\nOriginal: '{query}'")
        try:
            translated = translate_korean_query(query)
            print(f"Translated: '{translated}'")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_translation()