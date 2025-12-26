import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field
import asyncio

from config.settings import OpenAISettings

MODEL_NAME = "gpt-4o"


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    conversationId: str | None = None  # ⭐ 추가


chat_router = APIRouter(tags=["chat"])


@chat_router.post("/chat/stream")
async def chat_stream(request_body: ChatRequest, request: Request):  # ⭐ Request 추가
    """
    text/event-stream(SSE) 형태로 토큰을 순차 전송합니다.
    클라이언트 연결 종료 시 스트림을 중단합니다.
    """
    settings = OpenAISettings()
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.api_key)
    model = MODEL_NAME

    async def event_generator():
        try:
            if request_body.conversationId:
                yield f"data: {json.dumps({'conversationId': request_body.conversationId})}\n\n"

            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": m.role, "content": m.content} for m in request_body.messages],
                stream=True,
            )

            for chunk in stream:
                if await request.is_disconnected():
                    break

                delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
                if delta:
                    # ⭐ 이전 소스처럼 JSON으로 감싸서 보냅니다.
                    # content 안의 줄바꿈(\n)이 문자열로 안전하게 인코딩됩니다.
                    data = f"data: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"
                    yield data

                await asyncio.sleep(0)

            yield "data: [DONE]\n\n"

        except Exception as exc:
            print(f"Stream error: {exc}")
            yield f"event: error\ndata: {str(exc)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )