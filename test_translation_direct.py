#!/usr/bin/env python3
"""Test the translation service directly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

# Test the translation service directly
try:
    # Import only the translation module to avoid dependency issues
    sys.path.append(os.path.join(os.path.dirname(__file__), 'server', 'book_agent'))
    from translation_service import translate_korean_query

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

except ImportError as e:
    print(f"Import error: {e}")
    print("Trying to test pattern matching directly...")

    # Fallback - test the pattern matching logic directly
    import re

    KOREAN_FOOD_PATTERNS = {
        r'중국|중식|짜장|짬뽕|탕수육|마파두부|궁보|딤섬|중식집|중국집|중국관': 'chinese food restaurant',
        r'일본|일식|스시|사시미|라멘|우동|소바|돈까스|규동|사케|일식집|일본집': 'japanese sushi ramen restaurant',
        r'이탈리아|양식|파스타|피자|리조또|스파게티|이탈리아식|양식집': 'italian pasta pizza restaurant',
        r'피자|피자집': 'pizza restaurant',
    }

    def simple_translate(text):
        translated_parts = []
        for korean_pattern, english_translation in KOREAN_FOOD_PATTERNS.items():
            if re.search(korean_pattern, text, re.IGNORECASE):
                translated_parts.append(english_translation)

        if translated_parts:
            unique_translations = list(set(' '.join(translated_parts).split()))
            return f"{text} {' '.join(unique_translations)}"
        return text

    test_queries = ["중식집 추천해줘", "피자 추천해줘", "이탈리아 음식"]
    for query in test_queries:
        print(f"'{query}' -> '{simple_translate(query)}'")