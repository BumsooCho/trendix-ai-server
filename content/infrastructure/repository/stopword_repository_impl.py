from typing import Set
import psycopg2
from psycopg2.extras import RealDictCursor

from config.database.session import SessionLocal
from content.application.port.stopword_repository_port import StopwordRepositoryPort
from content.infrastructure.orm.models import (
    StopwordORM
)

class StopwordRepositoryImpl(StopwordRepositoryPort):
    def __init__(self):
        self.db = SessionLocal()

    def get_stopwords(self, lang: str = "ko") -> Set[str]:
        try:
            query = (
                self.db.query(StopwordORM.word)
                .filter(
                    StopwordORM.lang == lang,
                    StopwordORM.enabled == True
                )
            )
            rows = query.all()
            return {row.word for row in rows}
        finally:
            self.db.close()
        