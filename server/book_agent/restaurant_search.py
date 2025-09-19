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
from .translation_service import translate_korean_query

# 포괄적 한국어-영어 번역 딕셔너리
KOREAN_FOOD_TRANSLATION = {
    # 국가/지역 음식 (다양한 표현 포함)
    '중국|중식|짜장|짬뽕|탕수육|마파두부|궁보|딤섬': 'chinese',
    '일본|일식|스시|사시미|라멘|우동|소바|돈까스|규동|사케': 'japanese sushi ramen',
    '이탈리아|양식|파스타|피자|리조또|스파게티': 'italian pasta pizza',
    '태국|태식|팟타이|똠양꿍|그린커리|팬센': 'thai',
    '인도|인도식|커리|난|탄두리|바스마티': 'indian curry',
    '베트남|월남|쌀국수|분짜|반미': 'vietnamese pho',
    '멕시코|멕시칸|타코|부리또|케사디야|나초': 'mexican taco burrito',
    '한국|한식|김치|불고기|갈비|비빔밥|냉면|삼겹살': 'korean bbq',
    '프랑스|프렌치|에스카르고|크로아상': 'french',
    '스페인|스패니시|파에야|타파스': 'spanish',

    # 음식 유형
    '피자': 'pizza italian',
    '햄버거|버거': 'burger hamburger',
    '치킨|닭|프라이드': 'chicken fried',
    '스테이크|소고기': 'steak beef steakhouse',
    '바베큐|바비큐|BBQ|구이': 'barbecue bbq grilled',
    '해산물|생선|새우|랍스터|조개|회|횟집': 'seafood fish',
    '샐러드|야채': 'salad vegetarian',

    # 식당 유형
    '카페|커피|에스프레소|라떼|아메리카노': 'cafe coffee',
    '술집|바|맥주|와인|칵테일|호프': 'bar pub beer wine cocktail',
    '패스트푸드|패패': 'fast food',
    '뷔페|부페|올유캔잇': 'buffet all you can eat',

    # 식사 시간
    '아침|모닝|브런치': 'breakfast brunch morning',
    '점심|런치': 'lunch',
    '저녁|디너|만찬': 'dinner evening',
    '야식|새벽|밤': 'late night',

    # 접미사 (식당 유형)
    '집$': 'restaurant house',  # 중식집, 일식집
    '점$': 'restaurant',        # 중국점, 일본점
    '관$': 'restaurant',        # 중국관, 일본관
    '가$': 'restaurant house',  # 한정식가, 갈비가

    # 특징/분위기
    '가족|아이|어린이|키즈': 'family kids children friendly',
    '데이트|로맨틱|커플': 'romantic date couple',
    '조용|정적|차분': 'quiet peaceful',
    '분위기|무드|감성': 'atmosphere ambiance mood',
    '저렴|싸|가성비|가격': 'cheap affordable budget',
    '고급|비싼|프리미엄|럭셔리': 'expensive premium upscale fine dining',

    # 액션/의도
    '추천|소개': 'recommend',
    '맛있는|맛좋은|맛집': 'delicious tasty good popular',
    '좋은|괜찮은': 'good',
    '최고|베스트': 'best excellent',
    '먹고싶어|먹을|드시고': 'eat food',
    '가고싶어|가서|갈만한': 'go visit',
    '알려줘|찾아줘|검색': 'find search tell',
}

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

# Legacy translation function - now handled by translation_service.py
# Keeping KOREAN_FOOD_TRANSLATION as backup for pattern matching

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
            # 한국어 쿼리 번역으로 검색 품질 향상
            enhanced_query = translate_korean_query(query)

            # Generate query embedding
            query_embedding = self.model.encode([enhanced_query], convert_to_numpy=True)[0]

            # Search in Qdrant using correct API
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit * 2,  # Get more results for filtering
            )

            # Apply filters manually if needed
            filtered_results = search_results
            if filters:
                filtered_results = self._apply_manual_filters(search_results, filters)

            # Format and return results
            results = []
            for result in filtered_results[:limit]:
                restaurant_data = result.payload.copy()
                restaurant_data['similarity_score'] = result.score
                results.append(restaurant_data)

            return results

        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"Search error: {e}")  # Also print to console
            print(f"Query was: {query}")
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

        # Search without filters to avoid API issues
        return self.search_restaurants(preferences, filters=None, limit=limit)

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