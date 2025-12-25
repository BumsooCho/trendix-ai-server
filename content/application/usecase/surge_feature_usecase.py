from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Iterable, List, Optional, Dict, Any


@dataclass
class ViewSample:
    """
    단일 시점의 조회수 측정값.

    - 예: 크롤러가 1분/5분마다 수집한 view_count 스냅샷
    """

    timestamp: datetime
    view_count: int


@dataclass
class SurgeFeatures:
    """
    급등(스파이크) 판정을 위한 피처 집합.

    - Δviews_t: 단기 조회수 변화량
    - growth_rate_t: 단기 증가율
    - acceleration: 증가율의 가속도
    - age_minutes / age_hours: 업로드 이후 경과 시간
    - baseline_ratio_*: 채널 평소 영상 대비 몇 배인지
    """

    # 단기 변화량 및 증가율
    delta_views_10m: Optional[float] = None
    delta_views_30m: Optional[float] = None
    delta_views_1h: Optional[float] = None
    delta_views_6h: Optional[float] = None

    growth_rate_10m: Optional[float] = None
    growth_rate_30m: Optional[float] = None
    growth_rate_1h: Optional[float] = None
    growth_rate_6h: Optional[float] = None

    # 증가 가속도 (예: 10분 증가율 - 30분 증가율)
    acceleration_10m_vs_30m: Optional[float] = None

    # 업로드 경과 시간
    age_minutes: Optional[float] = None
    age_hours: Optional[float] = None

    # 채널 베이스라인 대비 배수 (대형 채널 평소 영상 대비)
    baseline_velocity_10m_per_min: Optional[float] = None
    velocity_10m_per_min: Optional[float] = None
    ratio_velocity_10m_to_baseline: Optional[float] = None

    # (옵션) 동시성/군집 기반 트렌드 파도 지표용 슬롯
    co_movement_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _find_reference_view(
    samples: List[ViewSample], target_time: datetime
) -> Optional[int]:
    """
    target_time 이전(또는 같은 시점) 중 가장 최근 스냅샷의 view_count를 찾는다.
    """
    # samples는 시간순 정렬을 가정한다.
    ref: Optional[int] = None
    for s in samples:
        if s.timestamp <= target_time:
            ref = s.view_count
        else:
            break
    return ref


def compute_surge_features(
    samples: Iterable[ViewSample],
    published_at: Optional[datetime],
    *,
    # 분석 대상 윈도우 (분 단위)
    window_10m: int = 10,
    window_30m: int = 30,
    window_1h: int = 60,
    window_6h: int = 360,
    # 채널 베이스라인: 최근 N개 쇼츠의 "초기 10분" 평균 속도 (조회수/분)
    channel_baseline_velocities_10m: Optional[Iterable[float]] = None,
    # 동시성(트렌드 파도) 점수: 외부에서 계산한 값을 그대로 주입
    co_movement_score: Optional[float] = None,
) -> SurgeFeatures:
    """
    단일 영상에 대해 급등 판단을 위한 피처들을 계산한다.

    입력:
        - samples: (timestamp, view_count) 시계열. 시간 오름차순을 권장.
        - published_at: 영상 업로드 시각
        - window_*: 단기 변화 관측 윈도우 (분)
        - channel_baseline_velocities_10m:
            해당 채널의 최근 N개 쇼츠에서 측정한
            "업로드 후 10분 구간의 조회수 증가 속도(조회수/분)" 리스트.
            -> 대형 채널 평소 성과 대비 몇 배인지 산출에 사용.
        - co_movement_score:
            비슷한 키워드/해시태그/카테고리 군집 내에서
            동시에 오르는 정도를 외부 로직에서 계산해 주입.
    """
    history = sorted(list(samples), key=lambda s: s.timestamp)
    if not history:
        return SurgeFeatures()

    now_sample = history[-1]
    now = now_sample.timestamp
    views_now = now_sample.view_count

    def _delta_and_growth(window_minutes: int) -> tuple[Optional[float], Optional[float], Optional[float]]:
        target_time = now - timedelta(minutes=window_minutes)
        prev_views = _find_reference_view(history, target_time)
        if prev_views is None:
            return None, None, None

        delta = float(views_now - prev_views)
        base = float(prev_views if prev_views > 0 else 1)
        growth = delta / base

        elapsed_minutes = max((now - target_time).total_seconds() / 60.0, 1.0)
        velocity_per_min = delta / elapsed_minutes
        return delta, growth, velocity_per_min

    # 1) 단기 조회수 변화량 / 증가율 / 속도(조회수/분)
    delta_10m, growth_10m, velocity_10m = _delta_and_growth(window_10m)
    delta_30m, growth_30m, _ = _delta_and_growth(window_30m)
    delta_1h, growth_1h, _ = _delta_and_growth(window_1h)
    delta_6h, growth_6h, _ = _delta_and_growth(window_6h)

    # 2) 증가 가속도: 짧은 윈도우 증가율 - 더 긴 윈도우 증가율
    acceleration_10m_vs_30m: Optional[float] = None
    if growth_10m is not None and growth_30m is not None:
        acceleration_10m_vs_30m = growth_10m - growth_30m

    # 3) 업로드 경과 시간
    age_minutes: Optional[float] = None
    age_hours: Optional[float] = None
    if published_at is not None:
        age_minutes = max((now - published_at).total_seconds() / 60.0, 0.0)
        age_hours = age_minutes / 60.0

    # 4) 채널 베이스라인 대비 배수
    baseline_velocity_10m_per_min: Optional[float] = None
    ratio_velocity_10m_to_baseline: Optional[float] = None
    if channel_baseline_velocities_10m:
        velocities = [v for v in channel_baseline_velocities_10m if v is not None]
        if velocities:
            baseline_velocity_10m_per_min = float(mean(velocities))
            if velocity_10m is not None and baseline_velocity_10m_per_min > 0:
                ratio_velocity_10m_to_baseline = velocity_10m / baseline_velocity_10m_per_min

    return SurgeFeatures(
        delta_views_10m=delta_10m,
        delta_views_30m=delta_30m,
        delta_views_1h=delta_1h,
        delta_views_6h=delta_6h,
        growth_rate_10m=growth_10m,
        growth_rate_30m=growth_30m,
        growth_rate_1h=growth_1h,
        growth_rate_6h=growth_6h,
        acceleration_10m_vs_30m=acceleration_10m_vs_30m,
        age_minutes=age_minutes,
        age_hours=age_hours,
        baseline_velocity_10m_per_min=baseline_velocity_10m_per_min,
        velocity_10m_per_min=velocity_10m,
        ratio_velocity_10m_to_baseline=ratio_velocity_10m_to_baseline,
        co_movement_score=co_movement_score,
    )


