"""
날짜 및 숫자 포맷 정규화 유틸리티

다양한 형식의 날짜와 숫자를 통일된 포맷으로 변환합니다.
- 날짜: 2025-01-01, 2025.1.1, 1월 1일, Jan 1 2025 등 → ISO 형식
- 숫자: 쉼표, 원 단위, 천원 단위, % 등 → float
"""
import re
from datetime import datetime, date
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class DateNormalizer:
    """다양한 날짜 포맷을 통일된 형식으로 변환"""
    
    # 한국어 월 매핑
    KR_MONTHS = {
        '1월': 1, '2월': 2, '3월': 3, '4월': 4,
        '5월': 5, '6월': 6, '7월': 7, '8월': 8,
        '9월': 9, '10월': 10, '11월': 11, '12월': 12,
    }
    
    # 영어 월 매핑
    EN_MONTHS = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'june': 6, 'july': 7, 'august': 8, 'september': 9,
        'october': 10, 'november': 11, 'december': 12,
    }
    
    # 파싱 패턴 (우선순위 순)
    PATTERNS = [
        # YYYY-MM-DD or YYYY/MM/DD
        (r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', 'ymd_dash'),
        # YYYY.MM.DD or YYYY.M.D
        (r'^(\d{4})\.(\d{1,2})\.(\d{1,2})\.?$', 'ymd_dot'),
        # DD-MM-YYYY or DD/MM/YYYY (유럽식, 일이 먼저)
        # 주의: MM-DD-YYYY와 구분하기 어렵기 때문에 기본값은 YMD 우선
        # MM/DD/YYYY
        (r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', 'mdy_dash'),
        # YYYYMMDD
        (r'^(\d{4})(\d{2})(\d{2})$', 'ymd_compact'),
        # 한국어: YYYY년 MM월 DD일
        (r'^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일?$', 'ymd_korean'),
        # 한국어: MM월 DD일 (올해 기준)
        (r'^(\d{1,2})월\s*(\d{1,2})일?$', 'md_korean'),
        # 영어: Jan 1, 2025 or January 1, 2025
        (r'^([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})$', 'en_mdy'),
        # 영어: 1 Jan 2025
        (r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', 'en_dmy'),
        # YY-MM-DD (2자리 연도)
        (r'^(\d{2})[-/.](\d{1,2})[-/.](\d{1,2})$', 'short_ymd'),
    ]
    
    def __init__(self, output_format: str = '%Y-%m-%d', default_year: Optional[int] = None):
        """
        Args:
            output_format: 출력 날짜 포맷 (strftime 형식)
            default_year: 연도가 없는 날짜에 사용할 기본 연도
        """
        self.output_format = output_format
        self.default_year = default_year or datetime.now().year
        self._compiled_patterns = [(re.compile(p), name) for p, name in self.PATTERNS]
    
    def normalize(self, value: Union[str, datetime, date, None]) -> Optional[str]:
        """
        다양한 형식의 날짜를 통일된 문자열로 변환
        
        Args:
            value: 날짜 값 (문자열, datetime, date 등)
            
        Returns:
            정규화된 날짜 문자열 또는 None
        """
        if value is None:
            return None
        
        # 이미 datetime/date 객체인 경우
        if isinstance(value, datetime):
            return value.strftime(self.output_format)
        if isinstance(value, date):
            return value.strftime(self.output_format)
        
        # 문자열 정리
        value = str(value).strip()
        if not value:
            return None
        
        for pattern, parser_name in self._compiled_patterns:
            match = pattern.match(value)
            if match:
                try:
                    parsed = self._parse_match(match, parser_name)
                    if parsed:
                        return parsed.strftime(self.output_format)
                except (ValueError, TypeError) as e:
                    logger.debug(f"날짜 파싱 실패 ({parser_name}): {value} - {e}")
                    continue
        
        # strptime 폴백으로 추가 포맷 시도
        fallback_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y.%m.%d %H:%M:%S',
            '%d.%m.%Y',
            '%m.%d.%Y',
        ]
        for fmt in fallback_formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime(self.output_format)
            except ValueError:
                continue
        
        logger.debug(f"날짜 파싱 불가: {value}")
        return None
    
    def _parse_match(self, match, parser_name: str) -> Optional[date]:
        """매치된 패턴에 따라 날짜 파싱"""
        groups = match.groups()
        
        if parser_name == 'ymd_dash' or parser_name == 'ymd_dot':
            return date(int(groups[0]), int(groups[1]), int(groups[2]))
        
        elif parser_name == 'mdy_dash':
            m, d, y = int(groups[0]), int(groups[1]), int(groups[2])
            # MM/DD/YYYY 기본 해석 (미국식)
            if m > 12:
                # 첫 번째가 12보다 크면 DD/MM/YYYY로 해석
                return date(y, d, m)
            return date(y, m, d)
        
        elif parser_name == 'ymd_compact':
            return date(int(groups[0]), int(groups[1]), int(groups[2]))
        
        elif parser_name == 'ymd_korean':
            return date(int(groups[0]), int(groups[1]), int(groups[2]))
        
        elif parser_name == 'md_korean':
            return date(self.default_year, int(groups[0]), int(groups[1]))
        
        elif parser_name == 'en_mdy':
            month_str = groups[0].lower()
            month = self.EN_MONTHS.get(month_str)
            if month:
                return date(int(groups[2]), month, int(groups[1]))
        
        elif parser_name == 'en_dmy':
            month_str = groups[1].lower()
            month = self.EN_MONTHS.get(month_str)
            if month:
                return date(int(groups[2]), month, int(groups[0]))
        
        elif parser_name == 'short_ymd':
            year = int(groups[0])
            year = year + 2000 if year < 100 else year
            return date(year, int(groups[1]), int(groups[2]))
        
        return None


class NumberNormalizer:
    """다양한 숫자 포맷을 통일된 형식으로 변환
    
    지원하는 포맷:
    - 쉼표 구분: 1,000,000
    - 원 단위: 1,000원, 1000원
    - 천원 단위: 1,000천원 → 1,000,000
    - 백만원 단위: 100백만원 → 100,000,000
    - 억원 단위: 1억원 → 100,000,000
    - 퍼센트: 10%, 10.5%
    - 달러: $1,000, USD 1,000
    - 괄호 음수: (1,000) → -1000
    - 공백 포함: 1 000 000
    """
    
    # 한국어 단위 매핑 (곱수)
    KR_UNITS = {
        '원': 1,
        '천원': 1_000,
        '천': 1_000,
        '만원': 10_000,
        '만': 10_000,
        '십만원': 100_000,
        '십만': 100_000,
        '백만원': 1_000_000,
        '백만': 1_000_000,
        '천만원': 10_000_000,
        '천만': 10_000_000,
        '억원': 100_000_000,
        '억': 100_000_000,
        '조원': 1_000_000_000_000,
        '조': 1_000_000_000_000,
    }
    
    # 단위 정렬 (긴 것부터 매칭)
    KR_UNIT_PATTERN = '|'.join(
        sorted(KR_UNITS.keys(), key=len, reverse=True)
    )
    
    def __init__(self, 
                 default_unit: str = '원',
                 strip_currency: bool = True,
                 strip_percent: bool = False):
        """
        Args:
            default_unit: 단위가 명시되지 않은 경우 기본 단위 (곱수 적용 안함)
            strip_currency: 통화 기호 제거 여부
            strip_percent: % 기호 제거하고 소수로 변환할지 여부 (True면 10% → 0.1)
        """
        self.default_unit = default_unit
        self.strip_currency = strip_currency
        self.strip_percent = strip_percent
    
    def normalize(self, value: Union[str, int, float, None]) -> Optional[float]:
        """
        다양한 형식의 숫자를 float로 변환
        
        Args:
            value: 숫자 값
            
        Returns:
            정규화된 float 값 또는 None
        """
        if value is None:
            return None
        
        # 이미 숫자인 경우
        if isinstance(value, (int, float)):
            return float(value)
        
        # 문자열 정리
        value = str(value).strip()
        if not value or value == '-' or value == 'N/A' or value == 'n/a':
            return None
        
        # 음수 처리: 괄호 표기 (1,000) → -1000
        is_negative = False
        if value.startswith('(') and value.endswith(')'):
            is_negative = True
            value = value[1:-1].strip()
        elif value.startswith('-') or value.startswith('△') or value.startswith('▲'):
            is_negative = True
            value = value[1:].strip()
        
        # 퍼센트 처리
        is_percent = False
        if value.endswith('%'):
            is_percent = True
            value = value[:-1].strip()
        
        # 통화 기호 제거
        value = re.sub(r'^[¥$€£₩]\s*', '', value)
        value = re.sub(r'^(USD|KRW|JPY|EUR|GBP)\s*', '', value, flags=re.IGNORECASE)
        
        # 한국어 단위 처리
        multiplier = 1
        unit_match = re.search(rf'({self.KR_UNIT_PATTERN})$', value)
        if unit_match:
            unit = unit_match.group(1)
            multiplier = self.KR_UNITS.get(unit, 1)
            value = value[:unit_match.start()].strip()
        
        # 공백 제거 (유럽식 천 단위 구분)
        value = value.replace(' ', '')
        
        # 쉼표 제거
        value = value.replace(',', '')
        
        # 전각 숫자 → 반각
        value = value.translate(str.maketrans('０１２３４５６７８９．', '0123456789.'))
        
        try:
            result = float(value) * multiplier
            
            if is_negative:
                result = -result
            
            if is_percent and self.strip_percent:
                result = result / 100.0
            
            return result
        except (ValueError, TypeError):
            logger.debug(f"숫자 파싱 불가: {value}")
            return None
    
    def format_output(self, value: Optional[float], 
                      decimal_places: int = 0,
                      use_comma: bool = True) -> str:
        """정규화된 숫자를 포맷된 문자열로 출력"""
        if value is None:
            return ''
        
        if decimal_places == 0:
            formatted = f"{int(round(value)):,}" if use_comma else str(int(round(value)))
        else:
            formatted = f"{value:,.{decimal_places}f}" if use_comma else f"{value:.{decimal_places}f}"
        
        return formatted
