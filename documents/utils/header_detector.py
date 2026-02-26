"""
엑셀 파일의 실제 헤더 행 자동 탐지

다양한 엑셀 파일에서 실제 데이터가 시작되는 행을 찾아냅니다.
- 빈 행 건너뛰기
- 제목/회사명 등 비데이터 행 무시
- 실제 컬럼 헤더 행 탐지
"""
import re
from typing import Optional, Tuple, List, Any
import logging

logger = logging.getLogger(__name__)


class HeaderDetector:
    """엑셀 파일에서 헤더 행을 자동 탐지"""
    
    # 헤더가 아닌 행의 특징 (제목, 부제 등)
    NON_HEADER_PATTERNS = [
        r'^\d{4}년',           # 연도 시작 (2024년 매출현황)
        r'^제?\d+기',          # 기수 (제1기, 2기)
        r'작성[일자]',          # 작성일
        r'기간\s*:',           # 기간:
        r'단위\s*:',           # 단위:
        r'^\(단위',            # (단위:
        r'^[가-힣]+\s*(주식)?회사',  # 회사명
        r'^(주)\s',            # (주) 회사명
        r'^\s*$',              # 빈 행
    ]
    
    def __init__(self, min_columns: int = 2, max_scan_rows: int = 20):
        """
        Args:
            min_columns: 헤더로 인정할 최소 컬럼 수
            max_scan_rows: 스캔할 최대 행 수
        """
        self.min_columns = min_columns
        self.max_scan_rows = max_scan_rows
        self._non_header_compiled = [
            re.compile(p) for p in self.NON_HEADER_PATTERNS
        ]
    
    def detect(self, rows: List[List[Any]]) -> Tuple[int, List[str]]:
        """
        헤더 행 인덱스와 헤더 목록을 반환
        
        Args:
            rows: 2D 리스트 (엑셀에서 읽은 전체 행)
            
        Returns:
            (header_row_index, headers) 튜플
        """
        if not rows:
            return 0, []
        
        scan_limit = min(len(rows), self.max_scan_rows)
        
        best_header_idx = 0
        best_score = -1
        best_headers = []
        
        for idx in range(scan_limit):
            row = rows[idx]
            
            if not row:
                continue
            
            # None이 아닌 셀 수
            non_empty = [cell for cell in row if cell is not None and str(cell).strip()]
            
            if len(non_empty) < self.min_columns:
                continue
            
            # 헤더 특성 점수 계산
            score = self._score_header_row(row, idx, rows)
            
            if score > best_score:
                best_score = score
                best_header_idx = idx
                best_headers = [
                    str(cell).strip() if cell is not None else f'column_{i}'
                    for i, cell in enumerate(row)
                ]
        
        logger.info(f"헤더 행 탐지: index={best_header_idx}, headers={best_headers}")
        return best_header_idx, best_headers
    
    def _score_header_row(self, row: List[Any], row_idx: int, all_rows: List[List[Any]]) -> float:
        """헤더 행 가능성 점수를 계산"""
        score = 0.0
        non_empty_cells = [cell for cell in row if cell is not None and str(cell).strip()]
        
        if not non_empty_cells:
            return -1
        
        # 1. 문자열이 대부분인 행 → 헤더 가능성 높음
        str_count = sum(1 for cell in non_empty_cells if isinstance(cell, str))
        str_ratio = str_count / len(non_empty_cells) if non_empty_cells else 0
        score += str_ratio * 30
        
        # 2. 비헤더 패턴에 해당하면 감점
        first_cell = str(row[0]).strip() if row[0] else ''
        for pattern in self._non_header_compiled:
            if pattern.search(first_cell):
                score -= 50
                break
        
        # 3. None이 아닌 셀이 많을수록 가산
        fill_ratio = len(non_empty_cells) / len(row) if row else 0
        score += fill_ratio * 20
        
        # 4. 다음 행에 숫자 데이터가 있으면 가산 (현재 행이 헤더일 가능성)
        if row_idx + 1 < len(all_rows):
            next_row = all_rows[row_idx + 1]
            if next_row:
                next_non_empty = [c for c in next_row if c is not None]
                next_num_count = sum(
                    1 for c in next_non_empty 
                    if isinstance(c, (int, float)) or (
                        isinstance(c, str) and re.match(r'^[\d,.-]+$', c.strip())
                    )
                )
                if next_non_empty:
                    num_ratio = next_num_count / len(next_non_empty)
                    score += num_ratio * 20
        
        # 5. 셀 값이 짧은 문자열이면 가산 (헤더는 보통 짧음)
        avg_len = sum(len(str(c)) for c in non_empty_cells) / len(non_empty_cells)
        if avg_len < 20:
            score += 10
        elif avg_len > 50:
            score -= 10
        
        # 6. 중복된 값이 없으면 가산 (헤더는 보통 고유)
        unique_ratio = len(set(str(c) for c in non_empty_cells)) / len(non_empty_cells)
        score += unique_ratio * 10
        
        return score
    
    def extract_data_with_header(self, rows: List[List[Any]]) -> Tuple[List[str], List[List[Any]], dict]:
        """
        헤더를 탐지하고 데이터를 분리하여 반환
        
        Returns:
            (headers, data_rows, meta_info)
        """
        header_idx, headers = self.detect(rows)
        
        data_rows = rows[header_idx + 1:]
        
        # 헤더 위의 행은 메타 정보로 수집
        meta_rows = rows[:header_idx]
        meta_info = {
            'header_row_index': header_idx,
            'meta_rows': [
                [str(cell) if cell is not None else '' for cell in row]
                for row in meta_rows
            ],
            'total_data_rows': len(data_rows),
        }
        
        return headers, data_rows, meta_info
