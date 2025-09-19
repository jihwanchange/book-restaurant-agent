#!/usr/bin/env python3
"""
Generate comprehensive descriptions for restaurants to enable similarity search.
Combines name, categories, ambiences, location, and reviews into searchable text.
"""

import json
import os
from typing import Dict, List, Any

def generate_restaurant_description(restaurant: Dict[str, Any]) -> str:
    """Generate a comprehensive description for a restaurant."""

    # Basic info
    name = restaurant.get('name', '')
    categories = ', '.join(restaurant.get('categories', []))

    # Location info
    location_parts = []
    if restaurant.get('city'):
        location_parts.append(restaurant['city'])
    if restaurant.get('state'):
        location_parts.append(restaurant['state'])
    location = ', '.join(location_parts)

    # Ambiences and attributes
    ambiences = ', '.join(restaurant.get('ambiences', []))
    good_for_meals = ', '.join(restaurant.get('good_for_meals', []))

    # Features
    features = []
    if restaurant.get('good_for_kids'):
        features.append('family-friendly')
    if restaurant.get('dogs_allowed'):
        features.append('pet-friendly')
    if restaurant.get('wifi'):
        features.append('wifi available')
    if restaurant.get('happy_hour'):
        features.append('happy hour')

    # Reviews summary
    tips = restaurant.get('tips', [])[:5]  # Take first 5 tips
    tips_text = ' '.join(tips) if tips else ''

    # Star rating and review count
    stars = restaurant.get('stars', 0)
    review_count = restaurant.get('review_count', 0)

    # Construct description
    description_parts = [
        f"{name} is a {categories} restaurant",
        f"located in {location}" if location else "",
        f"with {ambiences} atmosphere" if ambiences else "",
        f"good for {good_for_meals}" if good_for_meals else "",
        f"featuring {', '.join(features)}" if features else "",
        f"rated {stars} stars with {review_count} reviews",
        tips_text[:200] if tips_text else ""  # Limit tips to 200 chars
    ]

    # Filter out empty parts and join
    description = '. '.join([part for part in description_parts if part.strip()])

    return description

def process_restaurants_json(input_file: str, output_file: str):
    """Process restaurants JSON and generate descriptions."""

    with open(input_file, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)

    print(f"Processing {len(restaurants)} restaurants...")

    # Generate descriptions
    for restaurant in restaurants:
        description = generate_restaurant_description(restaurant)
        restaurant['description'] = description

        # Also create a shorter search text for embedding
        search_text = f"{restaurant.get('name', '')} {', '.join(restaurant.get('categories', []))} {', '.join(restaurant.get('ambiences', []))}"
        restaurant['search_text'] = search_text

    # Save enhanced data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

    print(f"Enhanced restaurants data saved to {output_file}")

    # Print sample description
    if restaurants:
        print("\nSample description:")
        print(f"Name: {restaurants[0]['name']}")
        print(f"Description: {restaurants[0]['description'][:200]}...")

if __name__ == "__main__":
    input_file = "yelp/restaurants.json"
    output_file = "yelp/restaurants_enhanced.json"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        exit(1)

    process_restaurants_json(input_file, output_file)