from __future__ import annotations

from typing import Iterable, List, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


class YouTubeAnalyticsClient:
    """
    YouTube Analytics API v2 래퍼 예시.

    - https://developers.google.com/youtube/analytics
    - 필수 OAuth2 scope 예시:
      - https://www.googleapis.com/auth/yt-analytics.readonly
      - 또는 https://www.googleapis.com/auth/youtube.readonly

    이 클라이언트는 **액세스 토큰을 외부에서 주입**받는 것을 가정합니다.
    (예: 소셜 로그인/백오피스에서 발급받은 구글 OAuth2 토큰 등)
    """

    def __init__(self, access_token: str):
        """
        :param access_token: YouTube Analytics를 호출할 수 있는 Google OAuth2 액세스 토큰
        """
        creds = Credentials(token=access_token)
        # youtubeAnalytics v2 서비스 생성
        self.service = build(
            "youtubeAnalytics",
            "v2",
            credentials=creds,
            cache_discovery=False,
        )

    def query_channel_basic_metrics(
        self,
        channel_id: str,
        start_date: str,
        end_date: str,
        metrics: str = "views,likes,comments,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
        dimensions: str = "day",
    ) -> Dict[str, Any]:
        """
        채널 단위 기본 지표 조회 예시.

        :param channel_id: "UC..." 형태의 채널 ID
        :param start_date: "YYYY-MM-DD"
        :param end_date: "YYYY-MM-DD"
        :param metrics: 조회할 메트릭 목록 (쉼표 구분)
        :param dimensions: 기본은 일 단위 집계("day")
        :return: Analytics API raw response + rows를 dict 리스트로 파싱한 구조
        """
        try:
            response = (
                self.service.reports()
                .query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date,
                    endDate=end_date,
                    metrics=metrics,
                    dimensions=dimensions,
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"YouTube Analytics channel query failed: {exc}") from exc

        return self._parse_report_response(response)

    def query_videos_basic_metrics(
        self,
        channel_id: str,
        video_ids: Iterable[str],
        start_date: str,
        end_date: str,
        metrics: str = "views,likes,comments,estimatedMinutesWatched,averageViewDuration",
    ) -> Dict[str, Any]:
        """
        여러 영상에 대한 기본 지표 조회 예시.

        - dimensions: "video"
        - filters: "video==ID1,ID2,..."
        """
        video_list: List[str] = list(video_ids)
        if not video_list:
            return {"columnHeaders": [], "rows": []}

        filters_value = "video==" + ",".join(video_list)

        try:
            response = (
                self.service.reports()
                .query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date,
                    endDate=end_date,
                    metrics=metrics,
                    dimensions="video",
                    filters=filters_value,
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"YouTube Analytics video query failed: {exc}") from exc

        return self._parse_report_response(response)

    @staticmethod
    def _parse_report_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analytics API의 표 형태 응답(columnHeaders + rows)을
        다루기 편한 dict 리스트로 변환해 주는 유틸.
        """
        headers = [h.get("name") for h in response.get("columnHeaders", [])]
        rows = response.get("rows", []) or []

        parsed_rows: List[Dict[str, Any]] = []
        for row in rows:
            parsed_rows.append({header: value for header, value in zip(headers, row)})

        return {
            "raw": response,
            "columns": headers,
            "rows": parsed_rows,
        }


