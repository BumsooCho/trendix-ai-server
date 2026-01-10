-- Performance Indexes for Surge Video Query Optimization
-- 
-- These indexes significantly improve the performance of fetch_surge_videos()
-- Apply them to your database for optimal query performance

-- 1. Composite index for video_metrics_snapshot: 급등 영상 조회 성능 향상
-- DISTINCT ON과 snapshot_date 기준 정렬에 최적화
CREATE INDEX IF NOT EXISTS idx_vms_video_platform_date 
ON video_metrics_snapshot (video_id, platform, snapshot_date DESC);

-- 2. Video 테이블 published_at/crawled_at 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_video_published_crawled_platform 
ON video (
    COALESCE(published_at::date, crawled_at::date), 
    platform
) WHERE COALESCE(published_at::date, crawled_at::date) IS NOT NULL;

-- 3. video_metrics_snapshot의 snapshot_date 범위 조회 최적화
CREATE INDEX IF NOT EXISTS idx_vms_snapshot_date 
ON video_metrics_snapshot (snapshot_date);

-- 4. video_score upsert 성능 향상 (이미 PK로 존재하지만 명시)
-- video_score 테이블의 PRIMARY KEY가 video_id라고 가정
-- CREATE INDEX IF NOT EXISTS idx_video_score_video_id ON video_score (video_id);

-- 5. video_sentiment 조인 최적화
CREATE INDEX IF NOT EXISTS idx_video_sentiment_video_id 
ON video_sentiment (video_id);

-- 6. channel 조인 최적화
CREATE INDEX IF NOT EXISTS idx_channel_channel_id 
ON channel (channel_id);

-- 7. video 테이블의 platform 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_video_platform 
ON video (platform);

-- 통계 정보 갱신 (PostgreSQL)
ANALYZE video;
ANALYZE video_metrics_snapshot;
ANALYZE video_score;
ANALYZE video_sentiment;
ANALYZE channel;

-- 쿼리 플랜 확인 (테스트용)
/*
EXPLAIN ANALYZE
WITH target_videos AS (
    SELECT video_id, platform
    FROM video v
    WHERE COALESCE(v.published_at::date, v.crawled_at::date) 
          BETWEEN CURRENT_DATE - INTERVAL '3 days' AND CURRENT_DATE
      AND platform = 'youtube'
)
SELECT COUNT(*) FROM target_videos;
*/
