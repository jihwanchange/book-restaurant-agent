from typing_extensions import override
from typing import Callable, Any, AsyncGenerator, Optional
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event
from google.genai.types import ModelContent

import json
from .restaurant_search import search_restaurants_by_query, format_restaurant_response

def _handle_greetings_flow(user_message: str) -> list:
    """Handle greetings and initial user interaction."""
    # Handle empty messages
    if not user_message or user_message.strip() == "":
        return [{"type": "Message", "text": "안녕하세요! 레스토랑 추천이나 예약을 도와드릴 수 있습니다. 무엇을 도와드릴까요?"}]

    # Greeting keywords in multiple languages
    greeting_keywords = [
        "안녕", "안녕하세요", "안녕하십니까", "처음", "시작", "헬로",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "시작해", "시작할게", "도움말", "help"
    ]

    user_lower = user_message.lower().strip()

    # Check for greetings
    if any(keyword in user_lower for keyword in greeting_keywords):
        return [{"type": "Message", "text": "안녕하세요! 저는 레스토랑 추천과 예약을 도와드리는 AI 어시스턴트입니다. 🍽️\n\n다음과 같은 도움을 드릴 수 있습니다:\n• 음식 종류나 분위기에 따른 레스토랑 추천\n• 레스토랑 예약 관리\n\n어떤 종류의 음식이나 레스토랑을 찾고 계신가요?"}]

    # If not a greeting, try other flows
    return _handle_restaurant_recommendation_flow(user_message)

def _handle_restaurant_recommendation_flow(user_message: str) -> list:
    """Handle restaurant search and recommendation requests."""
    search_keywords = ["추천해", "추천해줘", "알려줘", "찾아줘", "검색해", "추천받고싶어", "먹고싶어", "recommend", "find", "search"]
    food_keywords = ["식당", "레스토랑", "맛집", "음식", "요리", "카페", "술집", "바", "restaurant", "food", "cafe", "bar"]
    cuisine_keywords = ["이탈리아", "중국", "한국", "일본", "태국", "피자", "커피", "치킨", "italian", "chinese", "korean", "japanese", "thai", "pizza", "coffee", "chicken"]

    user_lower = user_message.lower()

    has_search_intent = any(keyword in user_lower for keyword in search_keywords)
    has_food_context = any(keyword in user_lower for keyword in food_keywords) or \
                      any(keyword in user_lower for keyword in cuisine_keywords)

    if has_search_intent or (has_food_context and len(user_message) > 3):
        # Use vector search to find restaurants
        restaurants = search_restaurants_by_query(user_message, limit=3)
        return format_restaurant_response(restaurants)

    # If not a recommendation request, try reservation flow
    return _handle_restaurant_reservation_flow(user_message)

def _handle_restaurant_reservation_flow(user_message: str) -> list:
    """Handle restaurant reservation requests."""
    reservation_keywords = ["예약", "예약해", "예약해줘", "booking", "reserve", "reservation"]

    user_lower = user_message.lower()

    # Check for reservation keywords
    if any(keyword in user_lower for keyword in reservation_keywords):
        return [{"type": "Message", "text": "레스토랑 예약을 도와드리겠습니다! 다음 정보를 알려주세요:\n\n• 원하시는 레스토랑 이름\n• 예약 날짜와 시간\n• 인원수\n\n예: '홍콩반점 내일 저녁 7시 4명 예약해줘'"}]

    # Handle specific restaurant mentions for reservation
    if "홍콩반점" in user_message:
        return [
            {"type": "Reservation State", "title": "홍콩반점", "id": "222", "status": "생성"},
            {"type": "Message", "text": "홍콩반점 예약을 도와드리겠습니다. 예약 날짜와 시간, 그리고 인원수를 알려주세요."}
        ]
    elif "모레" in user_message:
        return [
            {"type": "Reservation State", "title": "홍콩반점", "id": "222", "status": "생성", "datetime": "2025-09-09 12:30", "persons": 4},
            {"type": "Message", "text": "9월 9일 오후 12시 30분, 4명, 홍콩반점 예약을 진행할까요?"}
        ]
    elif user_message == "예약해줘.":
        return [
            {"type": "Reservation State", "title": "홍콩반점", "id": "222", "status": "확정", "datetime": "2025-09-09 19:00", "persons": 4},
            {"type": "Message", "text": "9월 9일 오후 7시, 4명, 홍콩반점 예약이 완료되었습니다."}
        ]

    # Default response for unclear requests
    return [{"type": "Message", "text": "무엇을 도와드릴까요? 다음과 같은 요청을 해보세요:\n\n🔍 **레스토랑 추천**: '이탈리아 음식 추천해줘', '카페 알려줘'\n📅 **예약 관리**: '홍콩반점 예약해줘', '내일 저녁 예약'\n\n구체적으로 말씀해 주시면 더 정확한 도움을 드릴 수 있습니다."}]

class SimpleAgent(BaseAgent):
    "Agent that wraps a user-provided function and executes it as part of the agent workflow."
    func: Callable[..., Any]
    input_key: Optional[str] = None

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        inputs = {self.input_key: ctx.user_content.parts[0].text} if self.input_key else {}
        output = await self._maybe_await(self.func(**inputs))

        yield Event(author=self.name, invocation_id=ctx.invocation_id,
                    content=ModelContent(json.dumps(output, ensure_ascii=False)))

    async def _maybe_await(self, value):
        if callable(getattr(value, "__await__", None)):
            return await value
        return value

def _handle_user_message(user_message: str) -> str:
    try:
        return _handle_greetings_flow(user_message)
    except Exception as e:
        # Fallback to simple response if any error occurs
        print(f"Error in agent: {e}")
        return [{"type": "Message", "text": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."}]

root_agent = SimpleAgent(name="book_agent",
                         func=_handle_user_message,
                         input_key="user_message")
