FROM python:3.13-slim

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /
RUN chmod +x /wait-for-it.sh

# 컨테이너 작업 디렉토리
WORKDIR /app

# requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 복사 (모든 도메인 포함)
COPY . .

# PYTHONPATH 지정 (루트 전체)
ENV PYTHONPATH=/app

EXPOSE 33333

# CMD를 wait-for-it로 감싸서 DB와 Redis 준비 후 실행
CMD ["/wait-for-it.sh", "mysql:3306", "--", "/wait-for-it.sh", "redis:6379", "--", "python", "-m", "app.main"]
