#!/usr/bin/env python3
"""
Enhanced restaurant search and recommendation service using Qdrant vector database.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import re

logger = logging.getLogger(__name__)

@dataclass
class SearchFilters:
    """Search filters for restaurant recommendations."""
    location: Optional[str] = None
    categories: Optional[List[str]] = None
    min_stars: Optional[float] = None
    good_for_kids: Optional[bool] = None
    dogs_allowed: Optional[bool] = None
    price_range: Optional[str] = None  # "low", "medium", "high"

class RestaurantSearchService:
    """Restaurant search service using vector similarity and filters."""

    def __init__(self,
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the search service."""

        # Connect to Qdrant
        try:
            self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
            logger.info(f"Connected to Qdrant at {qdrant_host}:{qdrant_port}")
        except Exception as e:
            logger.warning(f"Cannot connect to Qdrant server: {e}")
            self.client = QdrantClient(":memory:")

        # Initialize embedding model
        import torch
        device = "cpu"  # Force CPU to avoid GPU issues
        self.model = SentenceTransformer(model_name, device=device)
        self.collection_name = "restaurants"

    def search_restaurants(self,
                          query: str,
                          filters: Optional[SearchFilters] = None,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """Search restaurants using semantic similarity and filters."""

        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

            # Search in Qdrant (simplified without filters for now)
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit * 2,  # Get more results for filtering
                # Remove score_threshold to get all results
            )

            # Apply filters manually if needed
            filtered_results = search_results
            if filters:
                filtered_results = self._apply_manual_filters(search_results, filters)

            # Format and return results
            results = []
            for result in filtered_results[:limit]:
                restaurant_data = result.payload
                restaurant_data['similarity_score'] = result.score
                results.append(restaurant_data)

            return results

        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []

    def _apply_manual_filters(self, results, filters: SearchFilters):
        """Apply filters manually to search results."""
        filtered = []
        for result in results:
            payload = result.payload

            # Apply location filter
            if filters.location and filters.location not in payload.get('city', ''):
                continue

            # Apply rating filter
            if filters.min_stars and payload.get('stars', 0) < filters.min_stars:
                continue

            # Apply category filter
            if filters.categories:
                restaurant_categories = payload.get('categories', [])
                if not any(cat in restaurant_categories for cat in filters.categories):
                    continue

            # Apply other filters
            if filters.good_for_kids is not None and payload.get('good_for_kids') != filters.good_for_kids:
                continue

            if filters.dogs_allowed is not None and payload.get('dogs_allowed') != filters.dogs_allowed:
                continue

            filtered.append(result)

        return filtered

    def _build_qdrant_filter(self, filters: SearchFilters) -> Dict:
        """Build Qdrant filter from SearchFilters."""
        conditions = []

        if filters.location:
            conditions.append({
                "key": "city",
                "match": {"value": filters.location}
            })

        if filters.min_stars:
            conditions.append({
                "key": "stars",
                "range": {"gte": filters.min_stars}
            })

        if filters.good_for_kids is not None:
            conditions.append({
                "key": "good_for_kids",
                "match": {"value": filters.good_for_kids}
            })

        if filters.dogs_allowed is not None:
            conditions.append({
                "key": "dogs_allowed",
                "match": {"value": filters.dogs_allowed}
            })

        if filters.categories:
            # Match any of the specified categories
            category_conditions = []
            for category in filters.categories:
                category_conditions.append({
                    "key": "categories",
                    "match": {"any": [category]}
                })
            if category_conditions:
                conditions.append({
                    "should": category_conditions
                })

        if not conditions:
            return None

        return {"must": conditions} if len(conditions) > 1 else conditions[0]

    def get_recommendations_by_preferences(self,
                                         preferences: str,
                                         location: str = "Santa Barbara",
                                         limit: int = 3) -> List[Dict[str, Any]]:
        """Get restaurant recommendations based on user preferences."""

        # Parse preferences for filters
        filters = self._parse_preferences(preferences, location)

        # Search with semantic similarity
        return self.search_restaurants(preferences, filters, limit)

    def _parse_preferences(self, preferences: str, location: str) -> SearchFilters:
        """Parse user preferences to extract filters."""
        filters = SearchFilters(location=location)

        # Extract categories from preferences
        category_keywords = {
            'italian': ['Italian'],
            'pizza': ['Pizza', 'Italian'],
            'chinese': ['Chinese'],
            'thai': ['Thai'],
            'mexican': ['Mexican'],
            'coffee': ['Coffee & Tea'],
            'breakfast': ['Breakfast & Brunch'],
            'lunch': ['Sandwiches', 'American (Traditional)'],
            'dinner': ['American (New)', 'Italian'],
            'bar': ['Bars', 'Wine Bars'],
            'fast food': ['Fast Food'],
            'seafood': ['Seafood']
        }

        preferences_lower = preferences.lower()
        for keyword, categories in category_keywords.items():
            if keyword in preferences_lower:
                filters.categories = categories
                break

        # Extract rating preference
        if '4 star' in preferences_lower or 'high rating' in preferences_lower:
            filters.min_stars = 4.0
        elif '3 star' in preferences_lower or 'good rating' in preferences_lower:
            filters.min_stars = 3.0

        # Extract family preferences
        if 'family' in preferences_lower or 'kids' in preferences_lower:
            filters.good_for_kids = True

        # Extract pet preferences
        if 'dog' in preferences_lower or 'pet' in preferences_lower:
            filters.dogs_allowed = True

        return filters

# Global service instance
_search_service = None

def get_search_service() -> RestaurantSearchService:
    """Get or create the global search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = RestaurantSearchService()
    return _search_service

def search_restaurants_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Simple function to search restaurants by query."""
    service = get_search_service()
    return service.get_recommendations_by_preferences(query, limit=limit)

def format_restaurant_response(restaurants: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Format restaurant results for the agent response."""
    if not restaurants:
        return [{"type": "Message", "text": "죄송합니다. 조건에 맞는 레스토랑을 찾을 수 없습니다."}]

    response = []

    # Add introduction message
    response.append({
        "type": "Message",
        "text": f"추천 레스토랑 {len(restaurants)}곳을 찾았습니다:"
    })

    # Add restaurant options
    for restaurant in restaurants:
        categories = ', '.join(restaurant.get('categories', []))
        stars = restaurant.get('stars', 0)
        review_count = restaurant.get('review_count', 0)
        address = restaurant.get('address', '')
        city = restaurant.get('city', '')

        description = f"{categories} · ⭐{stars} ({review_count}개 리뷰)"
        if address and city:
            description += f" · {address}, {city}"

        response.append({
            "type": "Restaurant Option",
            "title": restaurant.get('name', ''),
            "id": restaurant.get('restaurant_id', ''),
            "description": description
        })

    return response