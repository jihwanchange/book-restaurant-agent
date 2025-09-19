from typing_extensions import override
from typing import Callable, Any, AsyncGenerator, Optional
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event
from google.genai.types import ModelContent

import json
from .restaurant_search import search_restaurants_by_query, format_restaurant_response

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
        # Handle empty or greeting messages first
        if not user_message or user_message.strip() == "":
            return [{"type":"Message", "text":"안녕하세요! 레스토랑 추천이나 예약을 도와드릴 수 있습니다. 무엇을 도와드릴까요?"}]

        # Handle greetings and simple queries
        greeting_keywords = ["안녕", "hello", "hi", "안녕하세요", "처음", "시작"]
        if any(keyword in user_message.lower() for keyword in greeting_keywords):
            return [{"type":"Message", "text":"안녕하세요! 레스토랑 추천이나 예약을 도와드릴 수 있습니다. 어떤 종류의 음식이나 레스토랑을 찾고 계신가요?"}]

        # Check for specific restaurant search/recommendation requests
        search_keywords = ["추천해", "추천해줘", "알려줘", "찾아줘", "검색해", "추천받고싶어", "먹고싶어"]
        food_keywords = ["식당", "레스토랑", "맛집", "음식", "요리", "카페", "술집", "바"]

        has_search_intent = any(keyword in user_message for keyword in search_keywords)
        has_food_context = any(keyword in user_message for keyword in food_keywords) or \
                          any(keyword in user_message for keyword in ["이탈리아", "중국", "한국", "일본", "태국", "피자", "커피", "치킨"])

        if has_search_intent or (has_food_context and len(user_message) > 3):
            # Use vector search to find restaurants
            restaurants = search_restaurants_by_query(user_message, limit=3)
            return format_restaurant_response(restaurants)

        # Handle specific restaurant reservations (keep existing logic)
        elif "홍콩반점" in user_message:
            return [  {"type":"Reservation State", "title":"홍콩반점", "id":"222", "status":"생성"}, {"type":"Message", "text":"홍콩반점 예약을 도와드리겠습니다. 예약 날짜와 시간, 그리고 인원수를 알려주세요."} ]
        elif "모레" in user_message:
            return [  {"type":"Reservation State", "title":"홍콩반점", "id":"222", "status":"생성", "datetime":"2025-09-09 12:30", "persons": 4},  {"type":"Message", "text":"9월 9일 오후 12시 30분, 4명, 홍콩반점 예약을 진행할까요?"} ]
        elif user_message == "예약해줘.":
            return [  {"type":"Reservation State", "title":"홍콩반점", "id":"222", "status":"확정", "datetime":"2025-09-09 19:00", "persons": 4}, {"type":"Message", "text":"9월 9일 오후 7시, 4명, 홍콩반점 예약이 완료되었습니다."} ]

        # Default response for unclear requests
        return [{"type":"Message", "text":"레스토랑 추천이나 예약을 도와드릴 수 있습니다. 예를 들어 '이탈리아 음식 추천해줘' 또는 '카페 알려줘'라고 말씀해 주세요."}]

    except Exception as e:
        # Fallback to simple response if vector search fails
        print(f"Error in restaurant search: {e}")
        return [{"type":"Message", "text":"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."}]

root_agent = SimpleAgent(name="book_agent",
                         func=_handle_user_message,
                         input_key="user_message")
