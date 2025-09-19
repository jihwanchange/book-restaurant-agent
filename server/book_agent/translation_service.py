#!/usr/bin/env python3
"""
Translation service for Korean to English using HuggingFace transformers.
Provides translation functionality without external API dependencies.
"""

import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)

class TranslationService:
    """Korean to English translation service using local models."""

    def __init__(self):
        """Initialize translation service."""
        self.translator = None
        self._initialize_translator()

    def _initialize_translator(self):
        """Initialize the translation model."""
        try:
            from transformers import pipeline
            import torch

            # Use CPU to avoid GPU compatibility issues
            device = "cpu"

            # Try to load a lightweight translation model
            # Using Helsinki-NLP models which are known to be reliable
            model_name = "Helsinki-NLP/opus-mt-ko-en"

            logger.info(f"Loading translation model: {model_name}")
            self.translator = pipeline(
                "translation",
                model=model_name,
                device=device,
                torch_dtype=torch.float32
            )
            logger.info("Translation model loaded successfully")

        except Exception as e:
            logger.warning(f"Could not load translation model: {e}")
            logger.info("Falling back to pattern-based translation")
            self.translator = None

    def translate_korean_to_english(self, korean_text: str) -> str:
        """
        Translate Korean text to English.
        Falls back to pattern matching if model translation fails.
        """
        if not korean_text or not korean_text.strip():
            return korean_text

        # First try model-based translation
        if self.translator:
            try:
                result = self.translator(korean_text, max_length=128)
                if result and len(result) > 0:
                    translated = result[0]['translation_text']
                    logger.info(f"Translated '{korean_text}' -> '{translated}'")
                    return translated
            except Exception as e:
                logger.warning(f"Translation model failed: {e}")

        # Fallback to enhanced pattern matching
        return self._pattern_based_translation(korean_text)

    def _pattern_based_translation(self, text: str) -> str:
        """Enhanced pattern-based translation as fallback."""

        # Enhanced Korean food translation patterns
        KOREAN_FOOD_PATTERNS = {
            # 국가/지역 음식
            r'중국|중식|짜장|짬뽕|탕수육|마파두부|궁보|딤섬|중식집|중국집|중국관': 'chinese food restaurant',
            r'일본|일식|스시|사시미|라멘|우동|소바|돈까스|규동|사케|일식집|일본집': 'japanese sushi ramen restaurant',
            r'이탈리아|양식|파스타|피자|리조또|스파게티|이탈리아식|양식집': 'italian pasta pizza restaurant',
            r'태국|태식|팟타이|똠양꿍|그린커리|팬센|태국식': 'thai food restaurant',
            r'인도|인도식|커리|난|탄두리|바스마티': 'indian curry restaurant',
            r'베트남|월남|쌀국수|분짜|반미': 'vietnamese pho restaurant',
            r'멕시코|멕시칸|타코|부리또|케사디야|나초': 'mexican taco burrito restaurant',
            r'한국|한식|김치|불고기|갈비|비빔밥|냉면|삼겹살|한식집': 'korean bbq restaurant',
            r'프랑스|프렌치|에스카르고|크로아상': 'french restaurant',
            r'스페인|스패니시|파에야|타파스': 'spanish restaurant',

            # 음식 유형
            r'피자|피자집': 'pizza restaurant',
            r'햄버거|버거|버거집': 'burger hamburger restaurant',
            r'치킨|닭|프라이드|치킨집': 'chicken fried restaurant',
            r'스테이크|소고기|스테이크하우스': 'steak beef steakhouse',
            r'바베큐|바비큐|BBQ|구이': 'barbecue bbq grilled restaurant',
            r'해산물|생선|새우|랍스터|조개|회|횟집': 'seafood fish restaurant',
            r'샐러드|야채|채식': 'salad vegetarian restaurant',

            # 식당 유형
            r'카페|커피|에스프레소|라떼|아메리카노|커피숍': 'cafe coffee shop',
            r'술집|바|맥주|와인|칵테일|호프|주점': 'bar pub beer wine cocktail',
            r'패스트푸드|패패|패스트': 'fast food restaurant',
            r'뷔페|부페|올유캔잇': 'buffet all you can eat restaurant',

            # 식사 시간
            r'아침|모닝|브런치': 'breakfast brunch morning restaurant',
            r'점심|런치': 'lunch restaurant',
            r'저녁|디너|만찬': 'dinner evening restaurant',
            r'야식|새벽|밤': 'late night restaurant',

            # 의도/액션
            r'추천해|추천해줘|알려줘|찾아줘|검색해|추천받고싶어': 'recommend find search',
            r'맛있는|맛좋은|맛집': 'delicious tasty good popular restaurant',
            r'좋은|괜찮은': 'good restaurant',
            r'최고|베스트': 'best excellent restaurant',
            r'먹고싶어|먹을|드시고': 'eat food restaurant',
            r'가고싶어|가서|갈만한': 'go visit restaurant',

            # 특징/분위기
            r'가족|아이|어린이|키즈': 'family kids children friendly restaurant',
            r'데이트|로맨틱|커플': 'romantic date couple restaurant',
            r'조용|정적|차분': 'quiet peaceful restaurant',
            r'분위기|무드|감성': 'atmosphere ambiance mood restaurant',
            r'저렴|싸|가성비|가격': 'cheap affordable budget restaurant',
            r'고급|비싼|프리미엄|럭셔리': 'expensive premium upscale fine dining restaurant',
        }

        translated_parts = []
        remaining_text = text

        # Apply pattern matching
        for korean_pattern, english_translation in KOREAN_FOOD_PATTERNS.items():
            if re.search(korean_pattern, text, re.IGNORECASE):
                translated_parts.append(english_translation)
                # Remove matched parts to avoid overlap
                remaining_text = re.sub(korean_pattern, '', remaining_text, flags=re.IGNORECASE)

        # Combine original and translated parts
        if translated_parts:
            # Remove duplicates and combine
            unique_translations = list(set(' '.join(translated_parts).split()))
            enhanced_query = f"{text} {' '.join(unique_translations)}"
            logger.info(f"Pattern translated '{text}' -> '{enhanced_query}'")
            return enhanced_query

        return text

    def is_korean_text(self, text: str) -> bool:
        """Check if text contains Korean characters."""
        korean_pattern = re.compile(r'[가-힣]+')
        return bool(korean_pattern.search(text))

# Global translation service instance
_translation_service = None

def get_translation_service() -> TranslationService:
    """Get or create the global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

def translate_korean_query(query: str) -> str:
    """
    Enhanced translation function that combines model-based and pattern-based approaches.
    """
    service = get_translation_service()

    # Only translate if text contains Korean
    if service.is_korean_text(query):
        return service.translate_korean_to_english(query)

    return query