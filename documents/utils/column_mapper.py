"""
열 이름 매핑 유틸리티

서로 다른 파일의 제각각인 열 이름을 표준 열 이름으로 매핑합니다.
- 매출액 / 매출 금액 / sales → 매출액
- 유사 문자열 매칭 (fuzzy matching)
- 사용자 정의 매핑 테이블
"""
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class ColumnMapper:
    """열 이름 매핑 처리기"""
    
    # 기본 표준 열 이름 매핑 (키: 표준명, 값: 유사어 리스트)
    DEFAULT_MAPPINGS = {
        # 날짜 관련
        '날짜': ['date', '일자', '일시', '거래일', '거래일자', '작성일', '작성일자', '기준일', '기준일자', '사용일', '이용일', '승인일', '결제일', '거래일시'],
        '연도': ['year', '년도', '년', '사업연도'],
        '월': ['month', '월份'],
        
        # 은행/카드 거래 열 (입금/출금 — 매출/매입과 구분!)
        '입금액': ['입금', '입금금액', 'credit', 'deposit', '수입금액', '받은금액', '수입', '대변'],
        '출금액': ['출금', '출금금액', 'debit', 'withdrawal', '보낸금액', '사용금액', '결제금액', '이용금액', '지출', '지급', '차변'],
        '잔액': ['잔고', '누적잔액', 'balance', '계좌잔액'],
        '적요': ['내용', '거래내용', '상세', '거래처', '이용내역', '사용처', '가맹점', '거래적요'],
        
        # 재무제표 금액 관련
        '매출액': ['sales', 'revenue', '매출', '매출금액', '매출 금액', '총매출', '총매출액', 'total_sales'],
        '매입액': ['purchase', 'cost', '매입', '매입금액', '매입 금액', '총매입', '총매입액'],
        '영업이익': ['operating_profit', '영업 이익', '영업손익'],
        '순이익': ['net_profit', 'net_income', '당기순이익', '순손익', '당기 순이익'],
        '매출원가': ['cost_of_sales', 'cogs', '매출 원가', '원가'],
        '판관비': ['sga', '판매관리비', '판매비와관리비', '판매비와 관리비'],
        '금액': ['amount', 'amt', '총액', '합계금액', '합계 금액'],
        '단가': ['unit_price', 'price', '가격'],
        '수량': ['quantity', 'qty', '갯수', '개수'],
        
        # 거래처/업체
        '거래처': ['customer', 'client', '거래처명', '업체명', '업체', '고객', '고객명', '회사명', '회사'],
        '사업자번호': ['business_number', 'biz_no', '사업자등록번호', '사업자 등록번호'],
        '대표자': ['ceo', '대표', '대표자명', '대표이사'],
        
        # 상품/품목
        '품목': ['item', 'product', '품명', '상품', '상품명', '제품', '제품명', '품목명'],
        '규격': ['spec', 'specification', '스펙', '사양'],
        '비고': ['note', 'remark', 'remarks', '메모', '참고', '비 고'],
    }
    
    def __init__(self, 
                 custom_mappings: Optional[Dict[str, List[str]]] = None,
                 similarity_threshold: float = 0.7,
                 use_default: bool = True):
        """
        Args:
            custom_mappings: 사용자 정의 매핑 (키: 표준명, 값: 유사어 리스트)
            similarity_threshold: 유사도 임계값 (0~1, 높을수록 엄격)
            use_default: 기본 매핑 사용 여부
        """
        self.similarity_threshold = similarity_threshold
        self.mappings: Dict[str, List[str]] = {}
        
        if use_default:
            self.mappings.update(self.DEFAULT_MAPPINGS)
        
        if custom_mappings:
            for standard_name, aliases in custom_mappings.items():
                if standard_name in self.mappings:
                    self.mappings[standard_name].extend(aliases)
                else:
                    self.mappings[standard_name] = aliases
        
        # 역방향 인덱스 생성 (빠른 조회용)
        self._reverse_index: Dict[str, str] = {}
        for standard_name, aliases in self.mappings.items():
            self._reverse_index[standard_name.lower()] = standard_name
            for alias in aliases:
                self._reverse_index[alias.lower()] = standard_name
    
    def map_column(self, column_name: str) -> Tuple[str, float]:
        """
        열 이름을 표준 이름으로 매핑
        
        Args:
            column_name: 매핑할 열 이름
            
        Returns:
            (표준 열 이름, 신뢰도) 튜플. 매핑 실패 시 원래 이름과 0.0 반환
        """
        if not column_name:
            return column_name, 0.0
        
        cleaned = self._clean_name(column_name)
        
        # 1. 정확히 매칭
        if cleaned in self._reverse_index:
            return self._reverse_index[cleaned], 1.0
        
        # 2. 공백/특수문자 제거 후 매칭
        compressed = re.sub(r'[\s_\-./]', '', cleaned)
        for key, standard in self._reverse_index.items():
            if re.sub(r'[\s_\-./]', '', key) == compressed:
                return standard, 0.95
        
        # 3. 포함 관계 매칭
        for key, standard in self._reverse_index.items():
            if key in cleaned or cleaned in key:
                return standard, 0.8
        
        # 4. 유사 문자열 매칭 (fuzzy)
        best_match = None
        best_score = 0.0
        
        for key, standard in self._reverse_index.items():
            score = SequenceMatcher(None, cleaned, key).ratio()
            if score > best_score:
                best_score = score
                best_match = standard
        
        if best_match and best_score >= self.similarity_threshold:
            return best_match, best_score
        
        # 매핑 실패 → 원래 이름 유지
        return column_name, 0.0
    
    def map_headers(self, headers: List[str]) -> Dict[str, dict]:
        """
        전체 헤더 목록을 매핑
        
        Args:
            headers: 원본 헤더 리스트
            
        Returns:
            매핑 결과 딕셔너리
            {
                'original_name': {
                    'standard_name': '표준명',
                    'confidence': 0.95,
                    'mapped': True
                }
            }
        """
        result = {}
        for header in headers:
            standard_name, confidence = self.map_column(header)
            result[header] = {
                'standard_name': standard_name,
                'confidence': confidence,
                'mapped': confidence > 0.0,
            }
        return result
    
    def suggest_mappings(self, headers_list: List[List[str]]) -> Dict[str, dict]:
        """
        여러 파일의 헤더들을 분석하여 매핑 규칙을 제안
        
        Args:
            headers_list: 각 파일의 헤더 리스트들
            
        Returns:
            제안된 매핑 규칙
        """
        # 모든 파일의 헤더 수집
        all_headers = set()
        for headers in headers_list:
            for h in headers:
                all_headers.add(h)
        
        # 각 헤더에 대해 매핑 시도
        suggestions = {}
        mapped_groups: Dict[str, List[str]] = {}  # 표준명 → [원본명들]
        
        for header in all_headers:
            standard_name, confidence = self.map_column(header)
            suggestions[header] = {
                'standard_name': standard_name,
                'confidence': confidence,
                'mapped': confidence > 0.0,
            }
            
            if confidence > 0:
                if standard_name not in mapped_groups:
                    mapped_groups[standard_name] = []
                mapped_groups[standard_name].append(header)
        
        # 매핑되지 않은 헤더끼리 유사도 분석
        unmapped = [h for h in all_headers if suggestions[h]['confidence'] == 0]
        
        for i, h1 in enumerate(unmapped):
            for h2 in unmapped[i+1:]:
                score = SequenceMatcher(
                    None, 
                    self._clean_name(h1), 
                    self._clean_name(h2)
                ).ratio()
                if score >= self.similarity_threshold:
                    # 유사한 미매핑 헤더 → 그룹으로 제안
                    group_key = h1  # 첫 번째를 표준명으로 제안
                    if group_key not in mapped_groups:
                        mapped_groups[group_key] = [h1]
                    mapped_groups[group_key].append(h2)
        
        return {
            'individual': suggestions,
            'groups': mapped_groups,
        }
    
    def add_mapping(self, standard_name: str, aliases: List[str]):
        """매핑 규칙 추가"""
        if standard_name in self.mappings:
            self.mappings[standard_name].extend(aliases)
        else:
            self.mappings[standard_name] = aliases
        
        # 역방향 인덱스 업데이트
        self._reverse_index[standard_name.lower()] = standard_name
        for alias in aliases:
            self._reverse_index[alias.lower()] = standard_name
    
    def _clean_name(self, name: str) -> str:
        """열 이름 정리"""
        cleaned = str(name).strip().lower()
        # 앞뒤 공백, 줄바꿈 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
    
    def to_dict(self) -> Dict[str, List[str]]:
        """현재 매핑을 딕셔너리로 반환"""
        return dict(self.mappings)
    
    @classmethod
    def from_dict(cls, data: Dict[str, List[str]], **kwargs) -> 'ColumnMapper':
        """딕셔너리에서 ColumnMapper 생성"""
        return cls(custom_mappings=data, **kwargs)
