from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from content.application.usecase.stopword_usecase import StopwordUseCase
from content.infrastructure.repository.stopword_repository_impl import StopwordRepositoryImpl

filter_router = APIRouter(tags=["filter"])


# ---- 의존성 주입용 팩토리 ----
def get_stopword_usecase() -> StopwordUseCase:
    # 실제 환경에 맞게 repository 초기화
    repo = StopwordRepositoryImpl()
    usecase = StopwordUseCase(stopword_repository=repo, lang="ko")
    return usecase


# ---- Pydantic 모델 ----
class FilterRequest(BaseModel):
    text: str


class FilterResponse(BaseModel):
    original: str
    filtered: str
    has_profanity: bool


@filter_router.post("", response_model=FilterResponse)
async def filter_text(
    request: Request,
    payload: FilterRequest,
    usecase: StopwordUseCase = Depends(get_stopword_usecase),
):
    """
    욕설/불용어를 '**' 로 치환하는 엔드포인트.
    """
    cleaned_data = request.state.cleaned_body or payload.dict()
    
    text_to_filter = cleaned_data.get("text") or payload.text
    #filtered = usecase.filter_stopwords(payload.text)
    filtered = usecase.filter_stopwords(text_to_filter)
    has_profanity = payload.text != filtered

    return FilterResponse(
        original=payload.text,
        filtered=filtered,
        has_profanity=has_profanity,
    )