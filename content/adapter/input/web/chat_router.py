from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field

from config.settings import OpenAISettings

MODEL_NAME = "gpt-4o"


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None


chat_router = APIRouter(tags=["chat"])


@chat_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    text/event-stream(SSE) 형태로 토큰을 순차 전송합니다.
    """
    settings = OpenAISettings()
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.api_key)
    model = MODEL_NAME  # 모델 변경 시 여기만 수정

    def event_generator():
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                stream=True,
            )
            for chunk in stream:
                delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
                if delta:
                    yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            # 오류를 SSE error 이벤트로 전달
            yield f"event: error\ndata: {str(exc)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
