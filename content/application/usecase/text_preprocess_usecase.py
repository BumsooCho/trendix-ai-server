from typing import Optional

from content.application.port.text_preprocess_in_port import TextPreprocessInPort
from content.application.port.text_preprocess_out_port import TextPreprocessOutPort
from content.domain.text_preprocessor import TextPreprocessor


class TextPreprocessUseCase(TextPreprocessInPort):
    """
    댓글/설명 텍스트를 전처리하고,
    필요 시 AI 분석 파이프라인으로 전달하는 유즈케이스.
    """

    def __init__(
        self,
        text_preprocessor: TextPreprocessor,
        out_port: Optional[TextPreprocessOutPort] = None,
    ):
        self.text_preprocessor = text_preprocessor
        self.out_port = out_port

    def clean_comment(self, raw_comment: str) -> str:
        return self.text_preprocessor.preprocess(raw_comment)

    def clean_description(self, raw_desc: str) -> str:
        return self.text_preprocessor.preprocess(raw_desc)

    def clean_generic(self, text: str) -> str:
        """
        특별한 구분 없이 일반 텍스트 정제.
        """
        return self.text_preprocessor.preprocess(text)
    


    def preprocess_comment(self, raw_comment: str) -> str:
        cleaned = self.text_preprocessor.preprocess(raw_comment)

        # AI 분석 파이프라인 연계가 필요하면 out_port 사용
        if self.out_port:
            self.out_port.send_to_ai_pipeline(
                cleaned_text=cleaned,
                meta={"type": "comment"}
            )

        return cleaned

    def preprocess_description(self, raw_description: str) -> str:
        cleaned = self.text_preprocessor.preprocess(raw_description)

        if self.out_port:
            self.out_port.send_to_ai_pipeline(
                cleaned_text=cleaned,
                meta={"type": "description"}
            )

        return cleaned
