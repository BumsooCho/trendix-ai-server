import re
from typing import Set
from content.application.port.stopword_repository_port import StopwordRepositoryPort


class TextPreprocessor:
    """
    댓글/설명 텍스트에서
    - 특수문자 정리
    - 불용어 제거 (DB에서 로드)
    """

    #def __init__(self, stopwords: List[str] | None = None):
        # # 기본 불용어 목록 (예시)
        # default_stopwords = {
        #     "그리고", "그러나", "하지만", "또한", "근데",
        #     "정말", "진짜", "그냥", "이거", "저거",
        #     "뭐지", "뭐야", "아니", "그", "것", "수",
        # }
        # self.stopwords = set(stopwords or default_stopwords)

    def __init__(self, stopword_repository: StopwordRepositoryPort, lang: str = "ko"):
        self.stopword_repository = stopword_repository
        self.lang = lang
        self.stopwords: Set[str] = set()
        self._load_stopwords()
        # 특수문자/이모지 등 제거용 정규식 (예시)
        # 한글/영문/숫자/공백만 남기고 나머지는 공백으로 치환
        self._allowed_pattern = re.compile(r"[^0-9a-zA-Z가-힣\s]+")

        # 다중 공백 제거 패턴
        self._multi_space_pattern = re.compile(r"\s+")

    def _load_stopwords(self):
        self.stopwords = self.stopword_repository.get_stopwords(self.lang)

    def reload_stopwords(self):
        """
        운영 중에 불용어가 변경되었을 때 재로드할 수 있는 메서드.
        """
        self._load_stopwords()
        
    def normalize_text(self, text: str) -> str:
        """
        특수문자 제거 + 공백 정리
        """
        if not text:
            return ""

        # 특수문자/이모지 제거
        text = self._allowed_pattern.sub(" ", text)

        # 대소문자 통일 (필요시)
        text = text.lower()

        # 다중 공백을 하나로
        text = self._multi_space_pattern.sub(" ", text).strip()

        return text

    def remove_stopwords(self, text: str) -> str:
        """
        불용어 제거 (단어 단위)
        """
        if not text:
            return ""

        tokens = text.split()
        filtered_tokens = [t for t in tokens if t not in self.stopwords]
        return " ".join(filtered_tokens)

    def preprocess(self, text: str) -> str:
        """
        전체 전처리 pipeline:
        1) normalize_text
        2) remove_stopwords
        """
        normalized = self.normalize_text(text)
        return self.remove_stopwords(normalized)
