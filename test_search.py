#!/usr/bin/env python3
"""Test restaurant search functionality directly."""

import sys
sys.path.append('server')

from book_agent.restaurant_search import search_restaurants_by_query, format_restaurant_response

def test_search():
    print("Testing restaurant search...")

    # Test queries
    queries = [
        "피자 추천해줘",
        "이탈리아 음식",
        "Italian restaurant",
        "pizza"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        try:
            restaurants = search_restaurants_by_query(query, limit=3)
            print(f"Found {len(restaurants)} restaurants")

            for i, restaurant in enumerate(restaurants, 1):
                print(f"  {i}. {restaurant.get('name', 'Unknown')} (score: {restaurant.get('similarity_score', 0):.3f})")
                print(f"     Categories: {', '.join(restaurant.get('categories', []))}")

            # Test response formatting
            response = format_restaurant_response(restaurants)
            print(f"Formatted response: {len(response)} items")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_search()