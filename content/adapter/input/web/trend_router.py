from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from content.application.usecase.trend_query_usecase import TrendQueryUseCase
from content.infrastructure.repository.content_repository_impl import ContentRepositoryImpl

trend_router = APIRouter(tags=["trends"])

# 트렌드 탭 전용 조회용 유즈케이스/리포지토리 싱글턴
repository = ContentRepositoryImpl()
usecase = TrendQueryUseCase(repository)


@trend_router.get("/categories/hot")
async def get_hot_categories(
    limit: int = Query(default=20, ge=1, le=100),
    platform: str | None = Query(default=None, description="플랫폼 필터 (예: youtube)"),
):
    """
    카테고리별 최신 집계(랭킹 순) 리스트를 조회한다.
    """
    result = usecase.get_hot_categories(platform=platform, limit=limit)
    if not result:
        raise HTTPException(status_code=404, detail="집계된 카테고리 트렌드가 없습니다.")
    # datetime/date 등이 JSON 직렬화 오류를 내지 않도록 변환
    return JSONResponse(jsonable_encoder({"items": result}))


@trend_router.get("/categories/{category}/recommendations")
async def get_category_recommendations(
    category: str,
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=14, ge=1, le=90, description="최근 N일 내 수집본만 대상으로 추천"),
    platform: str | None = Query(default=None, description="플랫폼 필터 (예: youtube)"),
):
    """
    카테고리 내 추천 콘텐츠(점수/신선도 기반)를 조회한다.
    """
    items = usecase.get_recommended_contents(category, limit=limit, days=days, platform=platform)
    if not items:
        raise HTTPException(status_code=404, detail="추천 가능한 콘텐츠가 없습니다.")
    # datetime/date 등이 JSON 직렬화 오류를 내지 않도록 변환
    return JSONResponse(jsonable_encoder({"category": category, "items": items}))


@trend_router.get("/categories")
async def list_categories(limit: int = Query(default=100, ge=1, le=500)):
    """
    관심사 등록용 카테고리 목록을 조회한다.
    """
    categories = usecase.get_categories(limit=limit)
    if not categories:
        raise HTTPException(status_code=404, detail="등록된 카테고리가 없습니다.")
    return JSONResponse(jsonable_encoder({"categories": categories}))


@trend_router.get("/videos/surge")
async def get_surge_videos(
    limit: int = Query(default=30, ge=1, le=100),
    days: int = Query(default=3, ge=1, le=30, description="최근 N일 내 업로드/수집된 영상만 대상"),
    velocity_days: int = Query(
        default=1,
        ge=1,
        le=7,
        description="단기 증가량/증가율 비교 기준 일수 (예: 1일 전과 비교)",
    ),
    platform: str | None = Query(default=None, description="플랫폼 필터 (예: youtube)"),
):
    """
    급등(스파이크) 영상 랭킹 리스트를 조회한다.

    - delta_views_window / growth_rate_window: 최근 velocity_days일 기준 단기 증가량/증가율
    - surge_score: 간단한 급등 점수(현재는 growth_rate 기반, 추후 조합식으로 확장 가능)
    """
    items = usecase.get_surge_videos(
        platform=platform, limit=limit, days=days, velocity_days=velocity_days
    )
    if not items:
        raise HTTPException(status_code=404, detail="급등 영상이 없습니다.")
    return JSONResponse(jsonable_encoder({"items": items}))