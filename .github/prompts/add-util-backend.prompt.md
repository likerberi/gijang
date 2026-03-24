---
description: "플러그인/전략 패턴 유틸리티 백엔드 추가. OCR처럼 ABC 추상 클래스 + 팩토리 + 설정 기반 백엔드 선택 구조를 생성."
agent: "agent"
---

documents/utils/ocr.py 패턴을 참조하여 새 유틸리티 백엔드를 생성해줘.

## 요구사항
- ABC 기반 `Base{Name}Backend` 추상 클래스 (extract/is_available 메서드)
- 구현체 클래스들 (각각 선택 의존성)
- `get_{name}_backend(name=None)` 팩토리 함수 (폴백 체인)
- `{action}_{name}(input, **kwargs)` 한 줄 호출 헬퍼 함수
- `{Name}Result` 결과 클래스 (`to_dict()` 메서드)
- config/settings.py에 `{NAME}_BACKEND`, `{NAME}_LANG` 등 설정 추가
- requirements.txt에 선택 의존성 추가 (주석 처리)

## 참조할 기존 패턴 (documents/utils/ocr.py)
```python
class BaseOCRBackend(ABC):
    @abstractmethod
    def extract(self, image_path, lang='kor+eng'):
        pass
    @abstractmethod
    def is_available(self):
        pass

_FALLBACK_ORDER = ['tesseract', 'easyocr', 'paddleocr']

def get_ocr_backend(name=None):
    """팩토리: 설정 또는 이름으로 백엔드 선택, 불가능하면 폴백"""
    ...

def extract_text(image_path, lang=None, backend=None):
    """한 줄 호출 헬퍼"""
    ...
```

## 파일 위치
- `documents/utils/{name}.py` 에 생성
- 싱글턴 패턴: 무거운 모델 로딩은 클래스 변수로 캐싱

## 규칙
- 모든 백엔드가 미설치여도 에러 없이 graceful하게 처리
- `is_available()` 체크 후 사용 가능한 백엔드 자동 선택
- import는 try/except로 감싸서 선택 의존성 처리
