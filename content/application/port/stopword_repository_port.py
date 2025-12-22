from abc import ABC, abstractmethod
from typing import Set


class StopwordRepositoryPort(ABC):
    """
    불용어를 DB 등에서 읽어오는 포트 (추상 리포지토리).
    """

    @abstractmethod
    def get_stopwords(self, lang: str = "ko") -> Set[str]:
        """
        활성(enabled) 상태인 불용어를 모두 반환.
        """
        raise NotImplementedError