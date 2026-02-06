# app/core/chnl_constants.py
"""
로그 채널(chnl) 코드와 표시명 매핑.
API 응답 chlTypeCd 값에 대한 구분을 일관되게 사용하기 위한 상수.
"""

# chnl 코드 -> 한글 표시명 (MA0: 모바일앱, MW0: 모바일웹, HOM: 홈페이지)
CHNL_LABELS = {
    "MA0": "모바일앱",
    "MW0": "모바일웹",
    "HOM": "홈페이지",
}


def get_chnl_label(code: str) -> str:
    """
    채널 코드를 표시용 라벨로 변환.
    :param code: chlTypeCd 값 (MA0, MW0, HOM 등)
    :return: 한글 표시명. 매핑 없으면 코드 그대로 반환
    """
    if not code:
        return "-"
    return CHNL_LABELS.get(str(code).strip().upper(), code)
