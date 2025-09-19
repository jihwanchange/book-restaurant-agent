#!/usr/bin/env python3
"""
Enhanced restaurant description generator with smart review filtering.
Focuses on quality over quantity for better vector search results.
"""

import json
import re
from typing import Dict, List, Any
from collections import Counter

def filter_high_quality_reviews(reviews: List[Dict], limit: int = 3) -> List[str]:
    """Filter and select high-quality reviews for embedding."""

    if not reviews:
        return []

    # 1. Filter by star rating (4-5 stars for positive features)
    high_rated = [r for r in reviews if r.get('stars', 0) >= 4]

    # 2. Filter by review length (meaningful reviews, not too short/long)
    meaningful_reviews = []
    for review in high_rated:
        text = review.get('review', '')
        word_count = len(text.split())
        if 10 <= word_count <= 50:  # Sweet spot for meaningful content
            meaningful_reviews.append(review)

    # 3. Filter out generic/spam reviews
    quality_reviews = []
    spam_keywords = ['great place', 'highly recommend', 'will be back', 'love this place']

    for review in meaningful_reviews:
        text = review.get('review', '').lower()
        # Skip if too generic
        if not any(spam in text for spam in spam_keywords):
            quality_reviews.append(review)

    # 4. Prefer reviews that mention specific food/features
    feature_keywords = [
        'pizza', 'pasta', 'sauce', 'taste', 'flavor', 'fresh', 'spicy', 'sweet',
        'atmosphere', 'service', 'staff', 'ambiance', 'quiet', 'romantic',
        'family', 'kids', 'parking', 'location', 'price', 'value'
    ]

    scored_reviews = []
    for review in quality_reviews:
        text = review.get('review', '').lower()
        score = sum(1 for keyword in feature_keywords if keyword in text)
        scored_reviews.append((score, review))

    # Sort by feature score and take top reviews
    scored_reviews.sort(key=lambda x: x[0], reverse=True)

    return [review['review'] for score, review in scored_reviews[:limit]]

def filter_useful_tips(tips: List[str], limit: int = 5) -> List[str]:
    """Filter tips to get most informative ones."""

    if not tips:
        return []

    # Filter by length (avoid too short tips)
    meaningful_tips = [tip for tip in tips if len(tip.split()) >= 3]

    # Prefer tips with specific food mentions
    food_keywords = ['pizza', 'coffee', 'burger', 'salad', 'soup', 'dessert', 'drink']
    food_tips = [tip for tip in meaningful_tips
                 if any(food in tip.lower() for food in food_keywords)]

    # Combine food tips with general tips
    if food_tips:
        result = food_tips[:3]  # Prioritize food-specific tips
        remaining = [tip for tip in meaningful_tips if tip not in result]
        result.extend(remaining[:limit-len(result)])
        return result[:limit]

    return meaningful_tips[:limit]

def extract_sentiment_keywords(reviews: List[Dict]) -> List[str]:
    """Extract key sentiment and feature words from reviews."""

    positive_words = []
    negative_words = []

    # Positive sentiment keywords
    pos_keywords = ['delicious', 'amazing', 'excellent', 'perfect', 'fresh', 'tasty', 'flavorful', 'crispy']
    neg_keywords = ['terrible', 'awful', 'bland', 'overpriced', 'slow', 'rude', 'cold', 'dry']

    for review in reviews:
        text = review.get('review', '').lower()
        stars = review.get('stars', 0)

        if stars >= 4:  # Positive reviews
            positive_words.extend([word for word in pos_keywords if word in text])
        elif stars <= 2:  # Negative reviews (use sparingly)
            negative_words.extend([word for word in neg_keywords if word in text])

    # Count frequency and return most common
    pos_counter = Counter(positive_words)
    most_common_positive = [word for word, count in pos_counter.most_common(3)]

    return most_common_positive

def generate_enhanced_description(restaurant: Dict[str, Any]) -> Dict[str, str]:
    """Generate enhanced description with smart review filtering."""

    # Basic info
    name = restaurant.get('name', '')
    categories = ', '.join(restaurant.get('categories', []))

    # Location
    city = restaurant.get('city', '')
    state = restaurant.get('state', '')
    location = f"{city}, {state}" if city and state else city or state

    # Smart review filtering
    reviews = restaurant.get('reviews', [])
    tips = restaurant.get('tips', [])

    high_quality_reviews = filter_high_quality_reviews(reviews, limit=2)
    useful_tips = filter_useful_tips(tips, limit=3)
    sentiment_keywords = extract_sentiment_keywords(reviews)

    # Combine filtered content
    review_text = ' '.join(high_quality_reviews) if high_quality_reviews else ''
    tips_text = ' '.join(useful_tips) if useful_tips else ''
    sentiment_text = ' '.join(sentiment_keywords) if sentiment_keywords else ''

    # Features
    features = []
    if restaurant.get('good_for_kids'):
        features.append('family-friendly')
    if restaurant.get('dogs_allowed'):
        features.append('pet-friendly')
    if restaurant.get('wifi'):
        features.append('wifi available')

    # Ambience
    ambiences = ', '.join(restaurant.get('ambiences', []))

    # Rating info
    stars = restaurant.get('stars', 0)
    review_count = restaurant.get('review_count', 0)

    # Construct enhanced description
    description_parts = []

    if name:
        description_parts.append(f"{name} is a {categories} restaurant")
    if location:
        description_parts.append(f"located in {location}")
    if stars and review_count:
        description_parts.append(f"with {stars} stars from {review_count} reviews")
    if features:
        description_parts.append(f"featuring {', '.join(features)}")
    if ambiences:
        description_parts.append(f"with {ambiences} ambiance")
    if sentiment_text:
        description_parts.append(f"known for being {sentiment_text}")

    description = '. '.join(description_parts) + '.'

    # Create search-optimized text
    search_parts = [name, categories, location]
    if review_text:
        search_parts.append(review_text)
    if tips_text:
        search_parts.append(tips_text)
    if sentiment_text:
        search_parts.append(sentiment_text)

    search_text = ' '.join(search_parts)

    return {
        'description': description,
        'search_text': search_text
    }

def main():
    """Process restaurants and add enhanced descriptions."""

    # Load original data
    with open('yelp/restaurants.json', 'r', encoding='utf-8') as f:
        restaurants = json.load(f)

    print(f"Processing {len(restaurants)} restaurants with enhanced filtering...")

    # Add enhanced descriptions
    for i, restaurant in enumerate(restaurants):
        enhanced = generate_enhanced_description(restaurant)
        restaurant['description'] = enhanced['description']
        restaurant['search_text'] = enhanced['search_text']

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} restaurants...")

    # Save enhanced version
    with open('yelp/restaurants_smart_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

    print("✅ Created restaurants_smart_enhanced.json with intelligent review filtering")

    # Show sample
    sample = restaurants[0]
    print(f"\n📝 Sample enhanced description for '{sample['name']}':")
    print(f"Description: {sample['description'][:200]}...")
    print(f"Search text: {sample['search_text'][:200]}...")

if __name__ == "__main__":
    main()