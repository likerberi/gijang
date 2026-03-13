"""
OCR 백엔드 추상화 레이어

지원 엔진:
  - tesseract (기본): 가볍고 빠름, 시스템 바이너리 필요
  - easyocr: PyTorch 기반, 한국어 정확도 좋음
  - paddleocr: 최고 정확도, 레이아웃 인식 (세금계산서 등)

설정: config/settings.py → OCR_BACKEND = 'tesseract' | 'easyocr' | 'paddleocr'
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class OCRResult:
    """OCR 결과 — 프레임워크 독립 (Pydantic 호환 dict 제공)"""
    __slots__ = ('text', 'engine', 'lang', 'confidence', 'regions')

    def __init__(self, text: str, engine: str, lang: str = '',
                 confidence: float = 0.0, regions: Optional[list] = None):
        self.text = text
        self.engine = engine
        self.lang = lang
        self.confidence = confidence
        self.regions = regions or []

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'engine': self.engine,
            'lang': self.lang,
            'confidence': round(self.confidence, 3),
            'regions': self.regions,
        }


class BaseOCRBackend(ABC):
    """OCR 백엔드 인터페이스"""

    @abstractmethod
    def extract(self, image_path: str, lang: str = 'kor+eng') -> OCRResult:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class TesseractBackend(BaseOCRBackend):
    """pytesseract 백엔드 (기본)"""

    def is_available(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract(self, image_path: str, lang: str = 'kor+eng') -> OCRResult:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)

        # confidence 추출 (tsv 모드)
        try:
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data['conf'] if str(c).lstrip('-').isdigit() and int(c) > 0]
            avg_conf = sum(confs) / len(confs) / 100 if confs else 0.0
        except Exception:
            avg_conf = 0.0

        return OCRResult(
            text=text.strip(),
            engine='tesseract',
            lang=lang,
            confidence=avg_conf,
        )


class EasyOCRBackend(BaseOCRBackend):
    """EasyOCR 백엔드 — PyTorch 기반, 한국어 정확도 우수"""

    _reader = None  # 싱글턴 (모델 로딩 비용 절약)

    def is_available(self) -> bool:
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_reader(self, lang_list: list):
        import easyocr
        if self._reader is None:
            self._reader = easyocr.Reader(lang_list, gpu=False)
        return self._reader

    def extract(self, image_path: str, lang: str = 'kor+eng') -> OCRResult:
        lang_list = _parse_lang(lang)
        reader = self._get_reader(lang_list)
        results = reader.readtext(image_path)

        lines = []
        confs = []
        regions = []
        for bbox, text, conf in results:
            lines.append(text)
            confs.append(conf)
            regions.append({
                'text': text,
                'confidence': round(conf, 3),
                'bbox': [[int(p) for p in point] for point in bbox],
            })

        return OCRResult(
            text='\n'.join(lines),
            engine='easyocr',
            lang=lang,
            confidence=sum(confs) / len(confs) if confs else 0.0,
            regions=regions,
        )


class PaddleOCRBackend(BaseOCRBackend):
    """PaddleOCR 백엔드 — 최고 정확도, 레이아웃 인식"""

    _engine = None

    def is_available(self) -> bool:
        try:
            from paddleocr import PaddleOCR  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_engine(self, lang: str):
        from paddleocr import PaddleOCR
        if self._engine is None:
            # korean → 한국어 모델
            paddle_lang = 'korean' if 'kor' in lang else 'en'
            self._engine = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)
        return self._engine

    def extract(self, image_path: str, lang: str = 'kor+eng') -> OCRResult:
        engine = self._get_engine(lang)
        result = engine.ocr(image_path, cls=True)

        lines = []
        confs = []
        regions = []
        for page in (result or []):
            for item in (page or []):
                bbox, (text, conf) = item
                lines.append(text)
                confs.append(conf)
                regions.append({
                    'text': text,
                    'confidence': round(conf, 3),
                    'bbox': [[int(p) for p in point] for point in bbox],
                })

        return OCRResult(
            text='\n'.join(lines),
            engine='paddleocr',
            lang=lang,
            confidence=sum(confs) / len(confs) if confs else 0.0,
            regions=regions,
        )


# ─── 팩토리 & 유틸 ───

_BACKENDS = {
    'tesseract': TesseractBackend,
    'easyocr': EasyOCRBackend,
    'paddleocr': PaddleOCRBackend,
}

_FALLBACK_ORDER = ['tesseract', 'easyocr', 'paddleocr']


def get_ocr_backend(name: Optional[str] = None) -> Optional[BaseOCRBackend]:
    """OCR 백엔드 인스턴스 반환

    name이 None이면 settings.OCR_BACKEND를 참조하고,
    그것도 없으면 설치된 순서대로 폴백.
    """
    if name is None:
        try:
            from django.conf import settings
            name = getattr(settings, 'OCR_BACKEND', None)
        except Exception:
            pass

    if name and name in _BACKENDS:
        backend = _BACKENDS[name]()
        if backend.is_available():
            return backend
        logger.warning(f"OCR 백엔드 '{name}' 사용 불가 — 폴백 시도")

    # 폴백: 설치된 것 중 첫 번째
    for fallback_name in _FALLBACK_ORDER:
        backend = _BACKENDS[fallback_name]()
        if backend.is_available():
            logger.info(f"OCR 폴백: {fallback_name}")
            return backend

    logger.warning("사용 가능한 OCR 엔진이 없습니다")
    return None


def extract_text(image_path: str, lang: str = 'kor+eng',
                 backend: Optional[str] = None) -> OCRResult:
    """한 줄 호출용 헬퍼 — 백엔드 자동 선택"""
    ocr = get_ocr_backend(backend)
    if ocr is None:
        return OCRResult(text='', engine='none', lang=lang)
    return ocr.extract(image_path, lang=lang)


def _parse_lang(lang: str) -> list:
    """'kor+eng' → ['ko', 'en'] (easyocr 형식)"""
    mapping = {'kor': 'ko', 'eng': 'en', 'jpn': 'ja', 'chi_sim': 'ch_sim'}
    parts = lang.split('+')
    return [mapping.get(p, p) for p in parts]
