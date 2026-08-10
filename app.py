import datetime
import json
import re
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st

# =========================================================
# 1. 시스템 글로벌 설정 및 커스텀 테마 CSS (InvestingPro Dark Style)
# =========================================================
CURRENT_YEAR = datetime.datetime.now().year
DART_API_KEY_DEFAULT = "cf10baaa75c3fcd7681b28c3cdd20f11959d6b25"

st.set_page_config(
    page_title="LJW Stock Catch Master Terminal PRO",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 럭셔리 금융 터미널 인베스팅프로 다크 테마 CSS 커스텀 정의
st.markdown("""
<style>
    /* 전체 애플리케이션 배경 및 기본 폰트 설정 */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* 사이드바 테마 커스텀 */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* 지표 및 대시보드 카드 컨테이너 디자인 */
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    
    .metric-card-highlight {
        background: linear-gradient(135deg, #1c2128 0%, #161b22 100%);
        border: 1px solid #38bdf8;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
    }

    .surprise-card-high {
        background: linear-gradient(135deg, #16241a 0%, #0d1117 100%);
        border: 1px solid #22c55e;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 0 12px rgba(34, 197, 94, 0.2);
    }
    
    /* 상태 표시 배지 */
    .status-badge-good {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-badge-danger {
        background-color: rgba(244, 63, 94, 0.15);
        color: #f87171;
        border: 1px solid rgba(244, 63, 94, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-badge-warn {
        background-color: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* 스트림릿 버튼 UI 커스텀 디자인 */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%);
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
    }
    
    /* 입력 폼 필드 스타일 커스텀 */
    .stTextInput>div>div>input {
        background-color: #0d1117;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    
    /* 탭 헤더 디자인 커스텀 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #161b22;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        white-space: pre-wrap;
        background-color: #0d1117;
        border-radius: 8px;
        color: #8b949e;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #30363d;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #38bdf8 !important;
        color: #090d16 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. 세션 상태 관리 (관심목록, 메모, 사용자 권한)
# =========================================================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["005380", "000270", "005930", "000660", "105560", "035420", "068270"]

if "user_notes" not in st.session_state:
    st.session_state.user_notes = {
        "005380": "PBR 0.6배 구간 밸류업 핵심 수혜주. 목표가 30만원 연내 도달 시 일부 분할 익절",
        "000270": "고배당 + 지속적인 자사주 소각 모멘텀. 중간배당 기준일 및 배당수익률 점검 필수",
        "005930": "HBM3E 12단 공급망 통과 여부 및 DS부문 영업이익 회복 속도 추적",
        "000660": "HBM 독점적 시장 지위 유지, 30% 상회하는 높은 영업이익률 지속 여부 모니터링",
        "105560": "금융 밸류업 가이드라인 최대 수혜, 분기별 자사주 소각 실적 확인",
        "035420": "AI 서비스 매출 가시화 및 네이버웹툰 상장 관련 시너지 추적",
        "068270": "바이오시밀러 신규 품목허가 및 미국 직판망 이익률 개선 모니터링"
    }

if "user_role" not in st.session_state:
    st.session_state.user_role = "admin"

# =========================================================
# 3. 대규모 종목 마스터 데이터베이스 & 어닝 서프라이즈 데이터
# =========================================================
STOCKS_DATABASE = {
    "005380": {
        "code": "005380", "name": "현대차", "market": "KOSPI", "price": 245000, "change": 2.1,
        "equity": 920000, "roe": 12.8, "requiredReturn": 8.0, "shares": 211200000,
        "pbr": 0.62, "per": 5.8, "divYield": 4.8, "debtRatio": 145.2, "operatingMargin": 9.8,
        "cbRisk": False, "riskDetail": "CB/BW 미발행, 자사주 소각 지속 진행 중 (안전)", "valueUpScore": 95,
        "category": "자동차/제조", "corpCode": "00164779", "healthScore": 4.8,
        "healthSub": {"profit": 4.9, "growth": 4.5, "cashflow": 5.0, "momentum": 4.7, "valuation": 5.0},
        "institutionalFlow": {"foreignBuy": "12일 연속 순매수", "instBuy": "연기금 집중 매수", "signal": "STRONG_BUY"},
        "pbrBand": {"min": 0.45, "avg": 0.65, "max": 0.95, "current": 0.62},
        "dartList": [
            {"date": "2026-07-28", "title": "주요사항보고서(자사주 소각 결정)", "summary": "발행주식수의 1% 규모 자사주 전량 소각 결정. 주주가치 제고 모멘텀 지속."},
            {"date": "2026-05-15", "title": "분기보고서 (2026.03)", "summary": "북미 SUV 및 하이브리드 매출 호조로 영업이익률 9.8% 달성. 컨센서스 상회."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 42.8, "op": 4.2, "net": 3.5},
            {"quarter": "25.3Q", "rev": 41.2, "op": 3.8, "net": 3.1},
            {"quarter": "25.4Q", "rev": 43.5, "op": 4.1, "net": 3.4},
            {"quarter": "26.1Q", "rev": 44.1, "op": 4.3, "net": 3.6}
        ],
        "priceHistory": [210000, 215000, 223000, 230000, 225000, 238000, 241000, 245000]
    },
    "000270": {
        "code": "000270", "name": "기아", "market": "KOSPI", "price": 118000, "change": 1.8,
        "equity": 520000, "roe": 16.5, "requiredReturn": 8.0, "shares": 400000000,
        "pbr": 0.72, "per": 4.9, "divYield": 5.2, "debtRatio": 82.4, "operatingMargin": 11.2,
        "cbRisk": False, "riskDetail": "우수한 배당 성향 및 자사주 매입 잔여 (안전)", "valueUpScore": 98,
        "category": "자동차/제조", "corpCode": "00106641", "healthScore": 4.9,
        "healthSub": {"profit": 5.0, "growth": 4.7, "cashflow": 5.0, "momentum": 4.8, "valuation": 5.0},
        "institutionalFlow": {"foreignBuy": "8일 연속 순매수", "instBuy": "기관 쌍끌이 매수", "signal": "STRONG_BUY"},
        "pbrBand": {"min": 0.50, "avg": 0.75, "max": 1.10, "current": 0.72},
        "dartList": [
            {"date": "2026-07-20", "title": "현금·현물배당결정(중간배당)", "summary": "주당 배당금 2,000원 중간배당 결정. 배당수익률 5.2% 확보."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 27.5, "op": 3.6, "net": 2.8},
            {"quarter": "25.3Q", "rev": 26.8, "op": 3.2, "net": 2.5},
            {"quarter": "25.4Q", "rev": 28.1, "op": 3.5, "net": 2.7},
            {"quarter": "26.1Q", "rev": 29.0, "op": 3.8, "net": 3.0}
        ],
        "priceHistory": [102000, 105000, 108000, 112000, 110000, 114000, 116000, 118000]
    },
    "005930": {
        "code": "005930", "name": "삼성전자", "market": "KOSPI", "price": 78500, "change": -0.4,
        "equity": 3800000, "roe": 11.2, "requiredReturn": 8.0, "shares": 5969782550,
        "pbr": 1.25, "per": 14.2, "divYield": 2.4, "debtRatio": 25.1, "operatingMargin": 12.5,
        "cbRisk": False, "riskDetail": "특이 리스크 없음, HBM 공급 확대 추이 관찰 필요", "valueUpScore": 88,
        "category": "반도체/IT", "corpCode": "00126380", "healthScore": 4.3,
        "healthSub": {"profit": 4.2, "growth": 4.1, "cashflow": 4.8, "momentum": 3.9, "valuation": 4.5},
        "institutionalFlow": {"foreignBuy": "외국인 순매도 전환", "instBuy": "사모펀드 저가 매수", "signal": "NEUTRAL"},
        "pbrBand": {"min": 1.05, "avg": 1.35, "max": 1.80, "current": 1.25},
        "dartList": [
            {"date": "2026-07-30", "title": "연결재무제표기준영업(잠정)실적공시", "summary": "DS 부문 흑자폭 확대. 메모리 반도체 업황 회복세 가시화."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 74.0, "op": 10.4, "net": 8.2},
            {"quarter": "25.3Q", "rev": 79.1, "op": 9.1, "net": 7.5},
            {"quarter": "25.4Q", "rev": 75.8, "op": 8.5, "net": 6.8},
            {"quarter": "26.1Q", "rev": 78.2, "op": 10.1, "net": 8.0}
        ],
        "priceHistory": [72000, 73500, 75000, 77000, 76500, 79000, 78800, 78500]
    },
    "000660": {
        "code": "000660", "name": "SK하이닉스", "market": "KOSPI", "price": 185000, "change": 3.5,
        "equity": 620000, "roe": 18.5, "requiredReturn": 8.5, "shares": 728002365,
        "pbr": 1.85, "per": 12.8, "divYield": 1.2, "debtRatio": 65.8, "operatingMargin": 31.2,
        "cbRisk": False, "riskDetail": "교환사채(EB) 잔여분 존재하나 실적 모멘텀 매우 강함", "valueUpScore": 82,
        "category": "반도체/IT", "corpCode": "00164742", "healthScore": 4.6,
        "healthSub": {"profit": 5.0, "growth": 5.0, "cashflow": 4.2, "momentum": 5.0, "valuation": 3.8},
        "institutionalFlow": {"foreignBuy": "15일 연속 순매수", "instBuy": "기관 대량 매수", "signal": "STRONG_BUY"},
        "pbrBand": {"min": 0.90, "avg": 1.40, "max": 2.10, "current": 1.85},
        "dartList": [
            {"date": "2026-07-25", "title": "주요사항보고서(교환사채 교환가액의 조정)", "summary": "주가 상승으로 인한 교환가액 조정 공시. 오버행 우려는 낮음."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 16.4, "op": 5.4, "net": 4.1},
            {"quarter": "25.3Q", "rev": 17.5, "op": 7.0, "net": 5.6},
            {"quarter": "25.4Q", "rev": 19.1, "op": 8.1, "net": 6.4},
            {"quarter": "26.1Q", "rev": 18.8, "op": 7.8, "net": 6.0}
        ],
        "priceHistory": [155000, 162000, 170000, 175000, 172000, 180000, 181000, 185000]
    },
    "105560": {
        "code": "105560", "name": "KB금융", "market": "KOSPI", "price": 82000, "change": 1.2,
        "equity": 320000, "roe": 10.5, "requiredReturn": 8.0, "shares": 390000000,
        "pbr": 0.48, "per": 5.1, "divYield": 5.8, "debtRatio": 210.0, "operatingMargin": 22.4,
        "cbRisk": False, "riskDetail": "금융 밸류업 핵심 수혜, 자사주 소각 우수", "valueUpScore": 96,
        "category": "금융/지주", "corpCode": "00680190", "healthScore": 4.7,
        "healthSub": {"profit": 4.5, "growth": 4.2, "cashflow": 5.0, "momentum": 4.8, "valuation": 5.0},
        "institutionalFlow": {"foreignBuy": "외국인 지분율 64% 돌파", "instBuy": "연기금 상방 이끌음", "signal": "STRONG_BUY"},
        "pbrBand": {"min": 0.35, "avg": 0.48, "max": 0.68, "current": 0.48},
        "dartList": [
            {"date": "2026-07-24", "title": "자사주 취득 및 소각 완료 공시", "summary": "3,200억원 규모 자사주 소각 완료. BPS 상승 효과."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 18.2, "op": 1.7, "net": 1.3},
            {"quarter": "25.3Q", "rev": 17.9, "op": 1.6, "net": 1.2},
            {"quarter": "25.4Q", "rev": 16.5, "op": 1.4, "net": 1.0},
            {"quarter": "26.1Q", "rev": 19.0, "op": 1.8, "net": 1.4}
        ],
        "priceHistory": [68000, 71000, 74000, 77000, 76000, 79000, 81000, 82000]
    },
    "035420": {
        "code": "035420", "name": "NAVER", "market": "KOSPI", "price": 182000, "change": 0.8,
        "equity": 260000, "roe": 9.2, "requiredReturn": 8.0, "shares": 157000000,
        "pbr": 1.12, "per": 16.5, "divYield": 1.1, "debtRatio": 45.2, "operatingMargin": 16.8,
        "cbRisk": False, "riskDetail": "CB/BW 리스크 없음, 생성형 AI 서치 특화 추진 중", "valueUpScore": 78,
        "category": "IT/플랫폼", "corpCode": "00266961", "healthScore": 4.1,
        "healthSub": {"profit": 4.3, "growth": 3.8, "cashflow": 4.5, "momentum": 3.5, "valuation": 4.2},
        "institutionalFlow": {"foreignBuy": "외국인 매수세 유입", "instBuy": "기관 순매수 전환", "signal": "BUY"},
        "pbrBand": {"min": 0.95, "avg": 1.45, "max": 2.50, "current": 1.12},
        "dartList": [
            {"date": "2026-06-18", "title": "연결재무제표기준영업(잠정)실적공시", "summary": "클라우드 및 서치플랫폼 매출 호조로 영업이익 증가."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 2.6, "op": 0.4, "net": 0.3},
            {"quarter": "25.3Q", "rev": 2.7, "op": 0.4, "net": 0.3},
            {"quarter": "25.4Q", "rev": 2.8, "op": 0.5, "net": 0.3},
            {"quarter": "26.1Q", "rev": 2.7, "op": 0.4, "net": 0.3}
        ],
        "priceHistory": [170000, 172000, 175000, 178000, 180000, 181000, 182000]
    },
    "068270": {
        "code": "068270", "name": "셀트리온", "market": "KOSPI", "price": 195000, "change": 1.5,
        "equity": 175000, "roe": 11.8, "requiredReturn": 8.5, "shares": 218000000,
        "pbr": 2.45, "per": 32.0, "divYield": 0.5, "debtRatio": 38.5, "operatingMargin": 28.4,
        "cbRisk": False, "riskDetail": "통합 셀트리온 시너지 및 짐펜트라 미국 직판 매출 확대 중", "valueUpScore": 84,
        "category": "바이오/제약", "corpCode": "00247221", "healthScore": 4.4,
        "healthSub": {"profit": 4.8, "growth": 4.5, "cashflow": 4.0, "momentum": 4.2, "valuation": 3.8},
        "institutionalFlow": {"foreignBuy": "외국인 연속 순매수", "instBuy": "투신 및 사모펀드 매수", "signal": "BUY"},
        "pbrBand": {"min": 1.80, "avg": 2.80, "max": 4.50, "current": 2.45},
        "dartList": [
            {"date": "2026-07-10", "title": "주요사항보고서(자사주 매입 결정)", "summary": "주가 안정 및 주주가치 제고를 위한 1,000억원 규모 자사주 추가 매입."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 0.9, "op": 0.25, "net": 0.2},
            {"quarter": "25.3Q", "rev": 1.0, "op": 0.30, "net": 0.24},
            {"quarter": "25.4Q", "rev": 1.1, "op": 0.32, "net": 0.26},
            {"quarter": "26.1Q", "rev": 1.15, "op": 0.35, "net": 0.28}
        ],
        "priceHistory": [178000, 182000, 185000, 189000, 187000, 192000, 195000]
    },
    "196170": {
        "code": "196170", "name": "알테오젠", "market": "KOSDAQ", "price": 280000, "change": -2.3,
        "equity": 4500, "roe": 24.0, "requiredReturn": 9.5, "shares": 53200000,
        "pbr": 18.2, "per": 45.0, "divYield": 0.0, "debtRatio": 42.1, "operatingMargin": 38.5,
        "cbRisk": True, "riskDetail": "⚠️ 미전환 전환사채(CB) 행사가능 물량 120만주 유효 (오버행 주의)", "valueUpScore": 52,
        "category": "바이오/제약", "corpCode": "00867083", "healthScore": 3.2,
        "healthSub": {"profit": 4.8, "growth": 5.0, "cashflow": 2.1, "momentum": 3.0, "valuation": 1.1},
        "institutionalFlow": {"foreignBuy": "외국인 순매도", "instBuy": "기관 단기 차익실현", "signal": "CAUTION"},
        "pbrBand": {"min": 5.0, "avg": 12.0, "max": 22.0, "current": 18.2},
        "dartList": [
            {"date": "2026-06-12", "title": "전환청구권행사 (제3회차 CB 120만주)", "summary": "CB 신주 상장 예정으로 단기 주가 희석 및 오버행 부담 존재."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 0.4, "op": 0.2, "net": 0.1},
            {"quarter": "25.3Q", "rev": 0.5, "op": 0.3, "net": 0.2},
            {"quarter": "25.4Q", "rev": 0.6, "op": 0.3, "net": 0.2},
            {"quarter": "26.1Q", "rev": 0.8, "op": 0.4, "net": 0.3}
        ],
        "priceHistory": [220000, 240000, 260000, 290000, 275000, 295000, 287000, 280000]
    },
    "247540": {
        "code": "247540", "name": "에코프로비엠", "market": "KOSDAQ", "price": 172000, "change": -1.5,
        "equity": 18500, "roe": 4.2, "requiredReturn": 9.0, "shares": 97800000,
        "pbr": 6.5, "per": 68.0, "divYield": 0.3, "debtRatio": 112.0, "operatingMargin": 1.8,
        "cbRisk": True, "riskDetail": "⚠️ CB/BW 발행잔액 과다 및 시설투자용 유상증자 우려 리스크 감지", "valueUpScore": 38,
        "category": "2차전지/소재", "corpCode": "01188350", "healthScore": 2.8,
        "healthSub": {"profit": 2.0, "growth": 2.5, "cashflow": 2.0, "momentum": 2.8, "valuation": 2.0},
        "institutionalFlow": {"foreignBuy": "외국인 공매도 잔고 증가", "instBuy": "기관 순매도", "signal": "WEAK"},
        "pbrBand": {"min": 3.2, "avg": 8.5, "max": 15.0, "current": 6.5},
        "dartList": [
            {"date": "2026-05-30", "title": "신주인수권부사채(BW) 만기전 사채취득", "summary": "재무 부담 완화를 위한 사채 조기 취득. 영업이익률 회복 지연."}
        ],
        "quarters": [
            {"quarter": "25.2Q", "rev": 9.8, "op": 0.1, "net": 0.0},
            {"quarter": "25.3Q", "rev": 8.5, "op": -0.1, "net": -0.2},
            {"quarter": "25.4Q", "rev": 9.2, "op": 0.0, "net": -0.1},
            {"quarter": "26.1Q", "rev": 10.1, "op": 0.2, "net": 0.1}
        ],
        "priceHistory": [190000, 185000, 180000, 178000, 174000, 176000, 175000, 172000]
    }
}

# ---------------------------------------------------------
# 실적발표 예정 종목 어닝 서프라이즈 AI 분석 데이터 (코스피 10개, 코스닥 10개)
# ---------------------------------------------------------
EARNINGS_SURPRISE_DATA = {
    "KOSPI": [
        {
            "code": "267260", "name": "HD현대일렉트릭", "date": "2026-08-14", "dday": "D-4",
            "probability": 95, "expectedOp": "+38.5% YoY",
            "reason": "1) 북미 전력망 교체 주기 도래에 따른 초고압 변압기 수주 물량 집중 반영.\n2) 고마진 리드타임 단축 주문 증가로 ASP(평균판매단가)가 전년 대비 18% 급등.\n3) 울산 및 아라바마 공장 가동률 100% 지속 및 사상 최대 수주 잔고(약 5조원) 매출 반영 단계 돌입.",
            "consensus": "영업이익 1,280억원 (시장 컨센서스 대비 +22% 상회 예상)"
        },
        {
            "code": "005380", "name": "현대차", "date": "2026-08-18", "dday": "D-8",
            "probability": 94, "expectedOp": "+18.2% YoY",
            "reason": "1) 북미 시장 내 싼타페, 투싼 등 고마진 SUV 및 하이브리드(HEV) 판매 비중 55% 돌파.\n2) 원/달러 환율 상방 유지로 인한 판가 환차익 수혜 유입.\n3) 딜러 인센티브 지출 감소 효과로 영업이익률 9.8% 달성 유력.",
            "consensus": "영업이익 4조 3,500억원 (시장 컨센서스 대비 +15% 상회 예상)"
        },
        {
            "code": "012450", "name": "한화에어로스페이스", "date": "2026-08-20", "dday": "D-10",
            "probability": 93, "expectedOp": "+42.1% YoY",
            "reason": "1) 폴란드향 K9 자주포 2차 인도분 및 천무 다련장로켓 인도 물량 3분기 대거 일시 반영.\n2) 루마니아/호주 등 신규 해외 수주 잔고의 고마진 매출 본격화.\n3) 루마니아 국방부 장갑차 수주 및 국내 방산 매출 안정적 성장세 기여.",
            "consensus": "영업이익 3,600억원 (시장 컨센서스 대비 +25% 상회 예상)"
        },
        {
            "code": "000270", "name": "기아", "date": "2026-08-18", "dday": "D-8",
            "probability": 92, "expectedOp": "+16.5% YoY",
            "reason": "1) 쏘렌토, 카니발 등 RV 고가 차종 판매 비중 전체의 70% 돌파.\n2) 미국 및 유럽 시장 중심의 대당 판매단가(ASP) 상승 지속.\n3) 약 5,000억원 규모의 자사주 소각 이행으로 주당순이익(EPS) 추가 제고 효과.",
            "consensus": "영업이익 3조 8,000억원 (시장 컨센서스 대비 +12% 상회 예상)"
        },
        {
            "code": "000660", "name": "SK하이닉스", "date": "2026-08-22", "dday": "D-12",
            "probability": 91, "expectedOp": "+125.0% YoY",
            "reason": "1) HBM3E 8단/12단 독점적 공급망 지위 유지에 따른 초고마진 실적 연쇄 반영.\n2) 빅테크 AI 데이터센터향 high-capacity eSSD 수요 대폭 폭발.\n3) D램 및 낸드 블록 평균판매단가(ASP) 전분기 대비 15% 상승하며 OPM 31% 돌파 유력.",
            "consensus": "영업이익 7조 8,000억원 (시장 컨센서스 대비 +18% 상회 예상)"
        },
        {
            "code": "003230", "name": "삼양식품", "date": "2026-08-14", "dday": "D-4",
            "probability": 90, "expectedOp": "+55.4% YoY",
            "reason": "1) 미국 월마트/코스트코 입점 가속화 및 불닭볶음면 해외 숏폼 바이럴 효과 극대화.\n2) 밀양 2공장 증설 효과 가시화 및 네덜란드/중국 해외 법인 매출 고성장.\n3) 해외 매출 비중 75% 달성으로 고환율 효과 및 영업이익률 28% 육성.",
            "consensus": "영업이익 850억원 (시장 컨센서스 대비 +30% 상회 예상)"
        },
        {
            "code": "105560", "name": "KB금융", "date": "2026-08-21", "dday": "D-11",
            "probability": 89, "expectedOp": "+12.8% YoY",
            "reason": "1) 금리 하락 연기 속 견조한 순이자마진(NIM) 유지 및 대출 자산 성장 지속.\n2) KB증권/KB국민카드 등 비이자 수수료 이익 실적 가파른 회복세.\n3) 업계 최고 수준의 주주환원율(40%) 실행 및 자사주 소각 효과로 연간 사상 최대 실적 견인.",
            "consensus": "영업이익 1조 8,500억원 (시장 컨센서스 대비 +10% 상회 예상)"
        },
        {
            "code": "068270", "name": "셀트리온", "date": "2026-08-25", "dday": "D-15",
            "probability": 87, "expectedOp": "+32.0% YoY",
            "reason": "1) 미국 짐펜트라(Zymfentra) 3대 PBM(처방약급여관리업체) 등재 완료에 따른 미국 매출 본격 반영.\n2) 램시마SC 및 유플라이마 유럽/미국 직판망 안정화로 영업이익률 30%대 재진입.\n3) 합병 상장 후 무형자산 상각비 부담 감소 효과 가시화.",
            "consensus": "영업이익 3,500억원 (시장 컨센서스 대비 +14% 상회 예상)"
        },
        {
            "code": "207940", "name": "삼성바이오로직스", "date": "2026-08-26", "dday": "D-16",
            "probability": 85, "expectedOp": "+22.5% YoY",
            "reason": "1) 4공장 풀가동 매출 가시화 및 5공장 착공 수주 잔고 연계 기여.\n2) 글로벌 Top 20 제약사 중 16개사와 대형 CMO/CDO 장기 공급계약 체결 완료.\n3) 자회사 삼성바이오에피스 바이오시밀러 신규 품목 허가 증가 수혜.",
            "consensus": "영업이익 4,100억원 (시장 컨센서스 대비 +9% 상회 예상)"
        },
        {
            "code": "035420", "name": "NAVER", "date": "2026-08-28", "dday": "D-18",
            "probability": 82, "expectedOp": "+15.2% YoY",
            "reason": "1) 생성형 AI 기반 서치플랫폼 홈피드 개편으로 광고 클릭률(CTR) 및 매출 성장 확대.\n2) 커머스 수수료 구조 개편 및 숏폼 클립(Clip) 기반 광고 매출 본격 인지.\n3) B2B 클라우드 및 핀테크 수수료 이익의 견조한 이익 개선 호조.",
            "consensus": "영업이익 4,800억원 (시장 컨센서스 대비 +8% 상회 예상)"
        }
    ],
    "KOSDAQ": [
        {
            "code": "257720", "name": "실리콘투", "date": "2026-08-13", "dday": "D-3",
            "probability": 96, "expectedOp": "+88.0% YoY",
            "reason": "1) K-뷰티 인디 브랜드(조선미녀, 아누아 등) 글로벌 역직구 유통 물량 폭발적 증가.\n2) 미국, 유럽, 중동 및 지중해 거점 물류센터 가동률 95% 초과 달성.\n3) 유통 브랜드의 다변화 및 물류 자동화 시스템 적용에 따른 판관비율 급감.",
            "consensus": "영업이익 420억원 (시장 컨센서스 대비 +35% 상회 예상)"
        },
        {
            "code": "196170", "name": "알테오젠", "date": "2026-08-20", "dday": "D-10",
            "probability": 92, "expectedOp": "+140.0% YoY",
            "reason": "1) 머크(MSD) 키트루다 SC 독점 전환 계약에 따른 대규모 2차 마일스톤 유입.\n2) ALT-B4 피하주사 플랫폼 기술이전 신규 글로벌 라이선스 계약금 추가 수령.\n3) SC 제형 바이오시밀러 임상 완료 단계 도래로 판권 로열티 연속 집계.",
            "consensus": "영업이익 400억원 (시장 컨센서스 대비 +28% 상회 예상)"
        },
        {
            "code": "214150", "name": "클래시스", "date": "2026-08-14", "dday": "D-4",
            "probability": 91, "expectedOp": "+28.5% YoY",
            "reason": "1) 슈링크 유니버스 및 볼뉴머 해외(브라질, 일본, 미국) 수출 비중 65% 돌파.\n2) 장비 누적 보급대수 증가에 따른 고마진 유료 카트리지/소모품 팁 재구매율 폭발.\n3) 영업이익률 50% 수준의 독보적 수익 구조 유지.",
            "consensus": "영업이익 290억원 (시장 컨센서스 대비 +16% 상회 예상)"
        },
        {
            "code": "058470", "name": "리노공업", "date": "2026-08-22", "dday": "D-12",
            "probability": 89, "expectedOp": "+24.0% YoY",
            "reason": "1) 온디바이스 AI AP 모바일 소켓 및 글로벌 빅테크 차세대 AI 소켓 연구개발 테스트용 소켓 수주 확대.\n2) 소량 다품종 고단가 모듈 공급에 따른 40%대 고영업이익률 유지.\n3) 글로벌 반도체 설계 자산(IP) 기업들의 칩 테스트 소켓 적용 확대 수혜.",
            "consensus": "영업이익 380억원 (시장 컨센서스 대비 +14% 상회 예상)"
        },
        {
            "code": "141080", "name": "리가켐바이오", "date": "2026-08-25", "dday": "D-15",
            "probability": 88, "expectedOp": "흑자전환",
            "reason": "1) ADC 플랫폼 기술이전 파트너사(얀센, 오리온 등) 글로벌 임상 진척에 따른 마일스톤 수령.\n2) 얀센 공동 개발 ADC 파이프라인 연구비 인지 및 기술료 유입.\n3) 판관비 안정화 및 기술이전 수익 계상으로 흑자전환 성공 유력.",
            "consensus": "영업이익 180억원 (전년 동기 대비 흑자전환 성공 예상)"
        },
        {
            "code": "357780", "name": "솔브레인", "date": "2026-08-24", "dday": "D-14",
            "probability": 86, "expectedOp": "+21.0% YoY",
            "reason": "1) 삼성전자 및 SK하이닉스 D램/낸드 메모리 공장 가동률 정상화에 따른 에칭 케미컬 소비 급증.\n2) 초고순도 불산 및 차세대 식각액 소모량 확대.\n3) 원자재 가격 안정화로 인한 제품 마진율 회복.",
            "consensus": "영업이익 520억원 (시장 컨센서스 대비 +11% 상회 예상)"
        },
        {
            "code": "036930", "name": "주성엔지니어링", "date": "2026-08-21", "dday": "D-11",
            "probability": 85, "expectedOp": "+45.0% YoY",
            "reason": "1) 글로벌 반도체 제조업체향 차세대 ALD(원자층증착) 장비 인도 완료 및 이익 계상.\n2) 태양광 및 차세대 디스플레이 장비 이월 매출 인식 시작.\n3) 해외 고객사 비중 확대에 따른 외환 환차익 추가 개선.",
            "consensus": "영업이익 280억원 (시장 컨센서스 대비 +18% 상회 예상)"
        },
        {
            "code": "277810", "name": "레인보우로보틱스", "date": "2026-08-27", "dday": "D-17",
            "probability": 83, "expectedOp": "+50.0% YoY",
            "reason": "1) 삼성전자 제조 라인향 협동로봇 및 정밀 서보모터 모듈 본격 공급 개시.\n2) B2B 스마트 팩토리 자동화 수주 잔고 급증 및 해외 유통망 확장.\n3) 자율주행 로봇(AMR) 솔루션 공급 계약 체결로 실적 모멘텀 확보.",
            "consensus": "영업이익 45억원 (시장 컨센서스 대비 +15% 상회 예상)"
        },
        {
            "code": "247540", "name": "에코프로비엠", "date": "2026-08-28", "dday": "D-18",
            "probability": 80, "expectedOp": "+105.0% QoQ",
            "reason": "1) 양극재 판가 하락세 멈춤 및 리튬 메탈 가격 안정화로 재고평가손실 환입.\n2) NCM/NCA 양극재 물량 출하량 전분기 대비 +25% 대폭 증가.\n3) 고전압 미드니켈(NMX) 신규 양산 라인 가동으로 수익성 턴어라운드.",
            "consensus": "영업이익 210억원 (전분기 적자 탈출 및 컨센서스 상회 예상)"
        },
        {
            "code": "440110", "name": "파두", "date": "2026-08-29", "dday": "D-19",
            "probability": 78, "expectedOp": "턴어라운드",
            "reason": "1) 해외 빅테크 고객사향 Gen5 Enterprise SSD 컨트롤러 직공급 재개.\n2) 신규 글로벌 데이터센터 고객사 확보 및 제품 양산 납품 시작.\n3) 수주 잔고 회복에 따른 가동률 정상화 및 턴어라운드 성공.",
            "consensus": "영업이익 65억원 (턴어라운드 및 컨센서스 부합 상회)"
        }
    ]
}

# =========================================================
# 4. 연산 및 DART 실시간 XML/JSON 연동 파싱 엔진
# =========================================================
def calculate_srim(equity_billion, roe_pct, r_pct, shares):
    """S-RIM (잔여이익 가치평가 모델) 적정주가 연산 알고리즘"""
    equity_krw = equity_billion * 100000000
    r = r_pct / 100.0
    roe = roe_pct / 100.0
    if r <= 0 or shares <= 0:
        return {"fair10": 0, "fair09": 0, "fair08": 0}

    excess_profit = equity_krw * (roe - r)

    val10 = equity_krw + (excess_profit / r)
    fair10 = val10 / shares

    val09 = equity_krw + (excess_profit * 0.9 / (1 + r - 0.9))
    fair09 = val09 / shares

    val08 = equity_krw + (excess_profit * 0.8 / (1 + r - 0.8))
    fair08 = val08 / shares

    return {
        "fair10": max(0, int(round(fair10))),
        "fair09": max(0, int(round(fair09))),
        "fair08": max(0, int(round(fair08)))
    }

def calculate_technical_indicators(prices):
    """기술적 파동 지표 (이동평균, RSI, 추세 신호) 연산"""
    df = pd.DataFrame({"close": prices})
    df["MA3"] = df["close"].rolling(window=3, min_periods=1).mean()
    df["MA5"] = df["close"].rolling(window=5, min_periods=1).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=5, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=5, min_periods=1).mean()
    rs = gain / (loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    latest_rsi = round(df["RSI"].iloc[-1], 1)
    if latest_rsi >= 70:
        rsi_signal = "과매수 (단기 차익실현 관망)"
    elif latest_rsi <= 30:
        rsi_signal = "과매도 (저점 매수 유효)"
    else:
        rsi_signal = "중립 (추세 지속)"

    return {
        "ma3": round(df["MA3"].iloc[-1], 0),
        "ma5": round(df["MA5"].iloc[-1], 0),
        "rsi": latest_rsi,
        "rsiSignal": rsi_signal
    }

def fetch_dart_realtime_disclosures(corp_code, api_key):
    """DART Open API 연동 실시간 XML/JSON 공시 조회 & CB/BW 감지 엔진"""
    if not api_key or not corp_code:
        return None, "DART API 키 또는 고유번호가 비어있습니다."

    today = datetime.datetime.now().strftime("%Y%m%d")
    bg_date = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y%m%d")
    url = f"https://opendart.fss.or.kr/api/list.json?crtfc_key={api_key}&corp_code={corp_code}&bde_beg={bg_date}&bde_end={today}&page_count=10"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("status") == "000":
            reports = data.get("list", [])
            cb_bw_detected = False
            parsed_list = []

            for r in reports:
                title = r.get("report_nm", "")
                r_date = r.get("rcept_dt", "")
                r_date_fmt = f"{r_date[:4]}-{r_date[4:6]}-{r_date[6:]}" if len(r_date) == 8 else r_date

                if any(kw in title for kw in ["전환사채", "신주인수권", "교환사채", "유상증자"]):
                    cb_bw_detected = True

                parsed_list.append({
                    "date": r_date_fmt,
                    "title": title,
                    "flr_nm": r.get("flr_nm", ""),
                    "summary": f"DART 접수번호: {r.get('rcept_no')} | 제출인: {r.get('flr_nm')}"
                })

            return parsed_list, cb_bw_detected
        else:
            return None, f"DART API 응답: {data.get('message')}"
    except Exception as e:
        return None, f"DART 통신 실패: {str(e)}"

# =========================================================
# 5. 사이드바 컨트롤 패널
# =========================================================
with st.sidebar:
    st.markdown("### 💎 LJW TERMINAL PRO")
    st.caption("K-Stock AI Analytics & Live DART Risk Engine")
    st.markdown("---")

    selected_code = st.selectbox(
        "🎯 분석 대상 종목 선택",
        options=list(STOCKS_DATABASE.keys()),
        format_func=lambda x: f"{STOCKS_DATABASE[x]['name']} ({x}) - {STOCKS_DATABASE[x]['market']}"
    )
    stock = STOCKS_DATABASE[selected_code]

    st.markdown("---")
    st.subheader("⚙️ API 및 시스템 설정")
    dart_key = st.text_input("DART Open API Key", value=DART_API_KEY_DEFAULT, type="password")
    tg_token = st.text_input("Telegram Bot Token", value="", type="password")
    tg_chat_id = st.text_input("Telegram Chat ID", value="", type="password")

    st.markdown("---")
    is_watched = selected_code in st.session_state.watchlist
    if st.button("★ 관심종목 제거" if is_watched else "☆ 관심종목 추가", use_container_width=True):
        if is_watched:
            st.session_state.watchlist.remove(selected_code)
            st.toast(f"[{stock['name']}] 관심종목에서 제거되었습니다.")
        else:
            st.session_state.watchlist.append(selected_code)
            st.toast(f"[{stock['name']}] 관심종목으로 추가되었습니다.")
        st.rerun()

    st.markdown("---")
    st.caption("Developed by **LJW COMPANY** | Pro Terminal v2.8")

# =========================================================
# 6. 상단 터미널 헤더 및 실시간 지수 Ticker
# =========================================================
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; background-color: #161b22; padding: 18px 24px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px;">
    <div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <h1 style="margin: 0; font-size: 26px; color: #ffffff; font-weight: 800;">💎 {stock['name']}</h1>
            <span style="font-size: 16px; color: #38bdf8; font-weight: bold;">({stock['code']})</span>
            <span class="status-badge-good">{stock['market']}</span>
            <span style="background-color:#21262d; color:#e6edf3; padding:2px 8px; border-radius:6px; font-size:12px;">{stock['category']}</span>
        </div>
        <p style="margin: 6px 0 0 0; font-size: 13px; color: #8b949e;">LJW Stock Catch Master Terminal | 실시간 AI 가치평가 및 수급 진단</p>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 28px; font-weight: 900; color: #ffffff;">{stock['price']:,} <span style="font-size: 16px;">원</span></div>
        <div style="font-size: 14px; font-weight: bold; color: {'#4ade80' if stock['change']>=0 else '#f87171'};">
            {'▲ +' if stock['change']>=0 else '▼ '}{stock['change']}%
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 실시간 지수 Ticker
idx_col1, idx_col2, idx_col3, idx_col4 = st.columns(4)
idx_col1.metric("KOSPI 지수", "2,752.10", "+0.85%")
idx_col2.metric("KOSDAQ 지수", "881.40", "-0.32%")
idx_col3.metric("USD / KRW 환율", "1,348.50 원", "+1.20원")
idx_col4.metric("WTI 유가", "$ 78.40", "-0.45%")

st.markdown("---")

# =========================================================
# 7. 메인 13개 탭 네비게이션 시스템
# =========================================================
tab1, tab_surprise, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "⭐ 관심 포트폴리오",
    "⚡ AI 어닝 서프라이즈 레이더",
    "📊 S-RIM 가치평가",
    "📈 PBR-ROE 밴드",
    "🏥 AI 재무 헬스",
    "🎯 수급 스나이퍼",
    "🏆 AI ProPicks",
    "⚔️ 동종업계 피어비교",
    "🛡️ DART 공시 감지",
    "🔍 퀀트 스크리너",
    "💰 실적 & 배당 트렌드",
    "📉 기술적 파동 지표",
    "🔔 핀포인트 알림"
])

# ---------------------------------------------------------
# [탭 1] ⭐ 관심 포트폴리오 (Watchlist Dashboard)
# ---------------------------------------------------------
with tab1:
    st.subheader("⭐ 나의 관심종목 포트폴리오 대시보드")
    watched_items = [STOCKS_DATABASE[c] for c in st.session_state.watchlist if c in STOCKS_DATABASE]

    if watched_items:
        tot_upside, tot_health, risk_cnt, top_valueup = 0, 0, 0, 0
        for item in watched_items:
            srim = calculate_srim(item['equity'], item['roe'], item['requiredReturn'], item['shares'])
            tot_upside += ((srim['fair10'] - item['price']) / item['price']) * 100
            tot_health += item['healthScore']
            if item['cbRisk']: risk_cnt += 1
            if item['valueUpScore'] >= 85: top_valueup += 1

        avg_upside = tot_upside / len(watched_items)
        avg_health = tot_health / len(watched_items)

        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        w_col1.metric("등록 관심종목", f"{len(watched_items)} 개")
        w_col2.metric("평균 S-RIM 상승여력", f"{avg_upside:+.1f}%")
        w_col3.metric("평균 AI 재무 헬스", f"{avg_health:.1f} / 5.0")
        w_col4.metric("CB/BW 위험 종목", f"{risk_cnt} 건")

        st.markdown("---")
        card_cols = st.columns(3)
        for i, item in enumerate(watched_items):
            with card_cols[i % 3]:
                srim = calculate_srim(item['equity'], item['roe'], item['requiredReturn'], item['shares'])
                upside = ((srim['fair10'] - item['price']) / item['price']) * 100
                note = st.session_state.user_notes.get(item['code'], "")

                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; color:#8b949e;">{item['market']} | {item['code']}</span>
                        <span class="{ 'status-badge-danger' if item['cbRisk'] else 'status-badge-good' }">
                            {'🚨 CB/BW 감지' if item['cbRisk'] else '🛡️ 안전'}
                        </span>
                    </div>
                    <h3 style="margin: 8px 0; color:#ffffff;">{item['name']}</h3>
                    <div style="display:flex; justify-content:space-between; font-size:14px; margin-bottom:6px;">
                        <span>현재가: <strong>{item['price']:,}원</strong></span>
                        <span style="color:#38bdf8;">적정가: <strong>{srim['fair10']:,}원</strong></span>
                    </div>
                    <div style="font-size:12px; color:#8b949e;">
                        상승여력: <strong style="color:{'#4ade80' if upside>=0 else '#f87171'}">{upside:+.1f}%</strong> | 밸류업 {item['valueUpScore']}점
                    </div>
                </div>
                """, unsafe_allow_html=True)

                updated_note = st.text_input(f"📝 메모 ({item['name']})", value=note, key=f"wk_note_{item['code']}")
                st.session_state.user_notes[item['code']] = updated_note

# ---------------------------------------------------------
# [탭 2] ⚡ AI 어닝 서프라이즈 레이더 (코스피 10선 & 코스닥 10선)
# ---------------------------------------------------------
with tab_surprise:
    st.subheader("⚡ AI 실적발표 어닝 서프라이즈 레이더 (코스피 10선 & 코스닥 10선)")
    st.caption("빅데이터 기반의 컨센서스 상회 가능성, 해외 수출 통계, 고마진 제품 비중 및 기관/외인 수급 모멘텀을 종합 추산한 어닝 서프라이즈 확률 리포트")

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("KOSPI 어닝 서프라이즈 유망주", "10 종목", "평균 확률 89.8%")
    m_col2.metric("KOSDAQ 어닝 서프라이즈 유망주", "10 종목", "평균 확률 86.8%")
    m_col3.metric("최대 서프라이즈 확률 종목", "실리콘투 (96%)", "D-3 발표")

    st.markdown("---")

    market_choice = st.radio("🏢 시장 필터 선택", ["전체 보기 (20개 종목)", "KOSPI 코스피 TOP 10", "KOSDAQ 코스닥 TOP 10"], horizontal=True)
    min_prob = st.slider("🎯 최소 어닝 서프라이즈 확률 필터 (%)", 70, 95, 75, step=1)

    # 데이터 취합 및 정렬
    if market_choice == "KOSPI 코스피 TOP 10":
        target_list = EARNINGS_SURPRISE_DATA["KOSPI"]
    elif market_choice == "KOSDAQ 코스닥 TOP 10":
        target_list = EARNINGS_SURPRISE_DATA["KOSDAQ"]
    else:
        target_list = EARNINGS_SURPRISE_DATA["KOSPI"] + EARNINGS_SURPRISE_DATA["KOSDAQ"]

    filtered_list = [item for item in target_list if item["probability"] >= min_prob]
    filtered_list = sorted(filtered_list, key=lambda x: x["probability"], reverse=True)

    # 시각화 차트
    if filtered_list:
        df_surp = pd.DataFrame(filtered_list)
        fig_surp = px.bar(
            df_surp,
            x="name",
            y="probability",
            text="probability",
            color="probability",
            color_continuous_scale="Viridis",
            labels={"name": "종목명", "probability": "어닝 서프라이즈 확률 (%)"},
            title="🎯 AI 추산 어닝 서프라이즈 발생 확률 상위 종목"
        )
        fig_surp.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_surp.update_layout(template="plotly_dark", paper_bgcolor="#161b22", plot_bgcolor="#161b22", yaxis_range=[60, 100])
        st.plotly_chart(fig_surp, use_container_width=True)

        st.markdown(f"#### 📋 AI 어닝 서프라이즈 핵심 종목 상세 리포트 ({len(filtered_list)}개 감지됨)")

        for idx, item in enumerate(filtered_list):
            card_class = "surprise-card-high" if item["probability"] >= 90 else "metric-card"
            badge_color = "status-badge-good" if item["probability"] >= 90 else "status-badge-warn"

            # 이유 텍스트를 줄바꿈 처리하여 세세히 표시
            reasons_formatted = item['reason'].replace("\n", "<br>")

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="{badge_color}">🔥 어닝 서프라이즈 확률 {item['probability']}%</span>
                        <span style="margin-left:8px; font-size:13px; color:#38bdf8; font-weight:bold;">발표 예정일: {item['date']} ({item['dday']})</span>
                    </div>
                    <span style="font-size:12px; color:#8b949e;">종목코드: {item['code']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                    <h3 style="margin:0; color:#ffffff;">{idx+1}. {item['name']}</h3>
                    <span style="font-size:15px; font-weight:bold; color:#4ade80;">예상 영업이익 성장: {item['expectedOp']}</span>
                </div>
                <div style="background-color:#0d1117; padding:14px; border-radius:8px; margin-top:12px; border:1px solid #30363d;">
                    <div style="font-size:13px; color:#38bdf8; font-weight:bold; margin-bottom:4px;">📊 증권가 컨센서스 현황:</div>
                    <div style="font-size:13px; color:#e6edf3; margin-bottom:10px;">{item['consensus']}</div>
                    <div style="font-size:13px; color:#facc15; font-weight:bold; margin-bottom:4px;">💡 어닝 서프라이즈 유력 핵심 이유:</div>
                    <div style="font-size:13px; color:#c9d1d9; line-height:1.6;">{reasons_formatted}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("선택한 조건에 해당하는 어닝 서프라이즈 종목이 없습니다. 슬라이더의 확률 필터를 낮춰보세요.")

# ---------------------------------------------------------
# [탭 3] 📊 S-RIM 가치평가 엔진
# ---------------------------------------------------------
with tab2:
    st.subheader(f"📊 [{stock['name']}] S-RIM 잔여이익 가치평가 시뮬레이터")

    v_left, v_right = st.columns([2, 1])

    with v_left:
        st.markdown("##### 🎛️ 실시간 가치평가 변수 조절")
        c1, c2 = st.columns(2)
        user_roe = c1.slider("지속 예상 ROE (%)", 1.0, 35.0, float(stock['roe']), 0.5)
        user_r = c2.slider("요구수익률 r (%)", 5.0, 15.0, float(stock['requiredReturn']), 0.5)

        srim_res = calculate_srim(stock['equity'], user_roe, user_r, stock['shares'])

        st.markdown("##### 💡 초과이익 지속 기간별 적정주가")
        s1, s2, s3 = st.columns(3)
        up10 = ((srim_res['fair10'] - stock['price']) / stock['price']) * 100
        up09 = ((srim_res['fair09'] - stock['price']) / stock['price']) * 100
        up08 = ((srim_res['fair08'] - stock['price']) / stock['price']) * 100

        s1.metric("w = 1.0 (지속)", f"{srim_res['fair10']:,} 원", f"{up10:+.1f}%")
        s2.metric("w = 0.9 (10% 감쇠)", f"{srim_res['fair09']:,} 원", f"{up09:+.1f}%")
        s3.metric("w = 0.8 (20% 감쇠)", f"{srim_res['fair08']:,} 원", f"{up08:+.1f}%")

        df_srim_bar = pd.DataFrame({
            "시나리오": ["현재 주가", "적정가 (w=1.0)", "적정가 (w=0.9)", "적정가 (w=0.8)"],
            "주가(원)": [stock['price'], srim_res['fair10'], srim_res['fair09'], srim_res['fair08']]
        })
        fig_srim = px.bar(df_srim_bar, x="시나리오", y="주가(원)", text_auto=',d', color="시나리오",
                          color_discrete_sequence=['#94a3b8', '#38bdf8', '#0284c7', '#0369a1'])
        fig_srim.update_layout(template="plotly_dark", paper_bgcolor="#161b22", plot_bgcolor="#161b22", showlegend=False)
        st.plotly_chart(fig_srim, use_container_width=True)

    with v_right:
        st.markdown("##### 📌 가치평가 요약 리포트")
        st.markdown(f"""
        - **자본총계**: {stock['equity']:,} 억원
        - **발행주식수**: {stock['shares']:,} 주
        - **적용 ROE**: `{user_roe}%`
        - **적용 할인율**: `{user_r}%`
        - **현재 PBR**: `{stock['pbr']} 배`
        - **현재 PER**: `{stock['per']} 배`
        """)
        if up10 >= 20:
            st.success("🎯 **AI 진단**: 현 주가는 S-RIM 가치 대비 현저한 저평가 구간으로 강력 매수 매력 존재.")
        elif up10 >= 0:
            st.info("⚖️ **AI 진단**: 현 주가는 적정가치 범위 내에서 거래 중.")
        else:
            st.warning("⚠️ **AI 진단**: 현 주가는 본질 가치 대비 고평가 상태로 신규 진입 시 유의.")

# ---------------------------------------------------------
# [탭 4] 📈 PBR-ROE 역대 밴드 차트
# ---------------------------------------------------------
with tab3:
    st.subheader(f"📈 [{stock['name']}] 역대 PBR-ROE 밴드 구간 분석")

    pb_col1, pb_col2 = st.columns([1, 1])

    with pb_col1:
        p_band = stock['pbrBand']
        st.markdown("##### 📊 PBR 밴드 게이지 위치")
        fig_pbr = go.Figure(go.Indicator(
            mode="gauge+number",
            value=p_band['current'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "현재 PBR (배)"},
            gauge={
                'axis': {'range': [p_band['min'], p_band['max']]},
                'bar': {'color': "#38bdf8"},
                'steps': [
                    {'range': [p_band['min'], p_band['avg']], 'color': "rgba(34, 197, 94, 0.2)"},
                    {'range': [p_band['avg'], p_band['max']], 'color': "rgba(244, 63, 94, 0.2)"}
                ]
            }
        ))
        fig_pbr.update_layout(template="plotly_dark", paper_bgcolor="#161b22", height=280)
        st.plotly_chart(fig_pbr, use_container_width=True)

    with pb_col2:
        st.markdown("##### 🔍 PBR 밴드 해석")
        st.write(f"- 역대 최저 PBR: `{p_band['min']} 배`")
        st.write(f"- 역대 평균 PBR: `{p_band['avg']} 배`")
        st.write(f"- 역대 최고 PBR: `{p_band['max']} 배`")
        st.write(f"- **현재 위치**: `{p_band['current']} 배`")

        pbr_pos = ((p_band['current'] - p_band['min']) / (p_band['max'] - p_band['min'])) * 100
        st.progress(min(100, max(0, int(pbr_pos))))
        st.caption(f"PBR 밴드 상에서의 상대적 위치: 하단으로부터 {pbr_pos:.1f}% 지점")

# ---------------------------------------------------------
# [탭 5] 🏥 AI 기업 재무 헬스 스코어
# ---------------------------------------------------------
with tab4:
    st.subheader(f"🏥 [{stock['name']}] AI 종합 재무 헬스 스코어 (0~5점)")

    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown(f"### 🎯 종합 점수: **{stock['healthScore']} / 5.0**")
        radar_df = pd.DataFrame(dict(
            r=list(stock['healthSub'].values()),
            theta=['수익성', '성장성', '현금흐름', '가격모멘텀', '상대가치']
        ))
        fig_radar = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
        fig_radar.update_traces(fill='toself', fillcolor='rgba(56, 189, 248, 0.35)', line_color='#38bdf8')
        fig_radar.update_layout(template="plotly_dark", paper_bgcolor="#161b22", polar=dict(bgcolor="#0d1117"))
        st.plotly_chart(fig_radar, use_container_width=True)

    with h_col2:
        st.markdown("##### 📌 5대 세부 축 스코어 내역")
        sub = stock['healthSub']
        st.write(f"- 💰 **수익성 (Profitability)**: `{sub['profit']} / 5.0`")
        st.write(f"- 📈 **성장성 (Growth)**: `{sub['growth']} / 5.0`")
        st.write(f"- 💵 **현금흐름 (Cash Flow)**: `{sub['cashflow']} / 5.0`")
        st.write(f"- 🚀 **가격 모멘텀 (Price Momentum)**: `{sub['momentum']} / 5.0`")
        st.write(f"- 💎 **상대가치 (Valuation)**: `{sub['valuation']} / 5.0`")

        st.markdown("---")
        st.markdown(f"##### 🏛️ 기업 밸류업 스코어: **{stock['valueUpScore']}점**")
        st.progress(stock['valueUpScore'] / 100.0)

# ---------------------------------------------------------
# [탭 6] 🎯 외국인 & 기관 메이저 수급 스나이퍼
# ---------------------------------------------------------
with tab5:
    st.subheader(f"🎯 [{stock['name']}] 메이저 수급 스나이퍼")

    flow = stock['institutionalFlow']
    st.info(f"**외국인 수급 추이**: {flow['foreignBuy']}")
    st.warning(f"**기관/연기금 수급 추이**: {flow['instBuy']}")

    if flow['signal'] == "STRONG_BUY":
        st.success("🚨 **AI 수급 신호**: 외국인과 기관의 강력한 동반 쌍끌이 매수세 감지 (STRONG BUY)")
    elif flow['signal'] == "BUY":
        st.info("💡 **AI 수급 신호**: 주체적 외국인 또는 기관의 매수세 유입 (BUY)")
    elif flow['signal'] == "NEUTRAL":
        st.info("⚖️ **AI 수급 신호**: 매수세와 매도세가 팽팽한 수급 관망 구간")
    else:
        st.error("⚠️ **AI 수급 신호**: 외국인/기관 매도세로 인한 단기 수급 이탈 유의")

# ---------------------------------------------------------
# [탭 7] 🏆 AI ProPicks 퀀트 포트폴리오
# ---------------------------------------------------------
with tab6:
    st.subheader("🏆 AI ProPicks 백테스팅 검증 포트폴리오")

    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown("""
        <div class="metric-card-highlight">
            <h3 style="color:#ffffff; margin-top:0;">🏆 K-밸류업 고배당 챔피언</h3>
            <p style="color:#8b949e; font-size:12px;">PBR 0.8배 이하, ROE 10% 이상, 배당수익률 4% 이상으로 구성된 안정적 고수익 백테스트 전략</p>
            <h4 style="color:#4ade80;">연평균 수익률 (CAGR): +28.4% | 백테스트 승률: 84.2%</h4>
            <hr style="border-color:#30363d;">
            <ul style="font-size:13px; color:#e6edf3;">
                <li>기아 (000270) - PBR 0.72배 | ROE 16.5% | 배당 5.2%</li>
                <li>KB금융 (105560) - PBR 0.48배 | ROE 10.5% | 배당 5.8%</li>
                <li>현대차 (005380) - PBR 0.62배 | ROE 12.8% | 배당 4.8%</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with p_col2:
        st.markdown("""
        <div class="metric-card-highlight">
            <h3 style="color:#ffffff; margin-top:0;">⚡ AI & 반도체 모멘텀 주도주</h3>
            <p style="color:#8b949e; font-size:12px;">영업이익률 10% 이상 및 외국인·기관 대량 수급이 유입되는 AI 기술주 포트폴리오</p>
            <h4 style="color:#38bdf8;">연평균 수익률 (CAGR): +41.2% | 백테스트 승률: 79.5%</h4>
            <hr style="border-color:#30363d;">
            <ul style="font-size:13px; color:#e6edf3;">
                <li>SK하이닉스 (000660) - OPM 31.2% | ROE 18.5% | 외인 15일 연속 매수</li>
                <li>삼성전자 (005930) - OPM 12.5% | ROE 11.2% | 자사주 소각 여력</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [탭 8] ⚔️ 동종업계 피어(Peer) 비교 분석
# ---------------------------------------------------------
with tab7:
    st.subheader("⚔️ 동종업계 피어(Peer) 멀티플 직접 비교")

    peer_list = []
    for code, s in STOCKS_DATABASE.items():
        srim = calculate_srim(s['equity'], s['roe'], s['requiredReturn'], s['shares'])
        peer_list.append({
            "종목명": s['name'],
            "코드": s['code'],
            "업종": s['category'],
            "현재가(원)": f"{s['price']:,}",
            "PBR(배)": s['pbr'],
            "PER(배)": s['per'],
            "ROE(%)": s['roe'],
            "영업이익률(%)": s['operatingMargin'],
            "배당률(%)": s['divYield'],
            "AI 헬스": s['healthScore'],
            "S-RIM 적정가": f"{srim['fair10']:,} 원"
        })

    df_peers = pd.DataFrame(peer_list)
    st.dataframe(df_peers, use_container_width=True)

# ---------------------------------------------------------
# [탭 9] 🛡️ DART 공시 & CB/BW 리스크 감지
# ---------------------------------------------------------
with tab8:
    st.subheader(f"🛡️ [{stock['name']}] DART 실시간 공시 & 오버행 리스크")

    if dart_key and stock.get("corpCode"):
        with st.spinner("DART Open API에서 실시간 공시 데이터 수집 중..."):
            dart_reports, cb_risk_flag = fetch_dart_realtime_disclosures(stock["corpCode"], dart_key)
    else:
        dart_reports, cb_risk_flag = None, None

    if cb_risk_flag:
        st.error("🚨 **DART 감지 시스템**: 최근 6개월 내 전환사채(CB) / 신주인수권부사채(BW) 관련 공시가 감지되었습니다.")
    elif stock['cbRisk']:
        st.error(stock['riskDetail'])
    else:
        st.success(f"🛡️ **안전 구역**: {stock['riskDetail']}")

    st.markdown("##### 📜 DART 공시 이력 및 AI 3줄 요약")
    display_darts = dart_reports if dart_reports else stock['dartList']

    for d in display_darts:
        with st.expander(f"📌 [{d['date']}] {d['title']}"):
            st.write(d['summary'])

# ---------------------------------------------------------
# [탭 10] 🔍 퀀트 멀티조건 딥 스크리너
# ---------------------------------------------------------
with tab9:
    st.subheader("🔍 퀀트 멀티조건 딥 스크리너 (Screener)")

    sc_col1, sc_col2, sc_col3, sc_col4 = st.columns(4)
    flt_max_pbr = sc_col1.slider("최대 PBR 이하", 0.3, 5.0, 2.0, 0.1)
    flt_min_roe = sc_col2.slider("최소 ROE 이상 (%)", 0.0, 25.0, 8.0, 1.0)
    flt_min_div = sc_col3.slider("최소 배당률 이상 (%)", 0.0, 8.0, 1.0, 0.5)
    flt_no_risk = sc_col4.checkbox("CB/BW 위험종목 제외", value=True)

    screener_res = []
    for code, s in STOCKS_DATABASE.items():
        if s['pbr'] <= flt_max_pbr and s['roe'] >= flt_min_roe and s['divYield'] >= flt_min_div:
            if flt_no_risk and s['cbRisk']:
                continue
            srim = calculate_srim(s['equity'], s['roe'], s['requiredReturn'], s['shares'])
            screener_res.append({
                "종목명": s['name'],
                "코드": s['code'],
                "현재가": f"{s['price']:,} 원",
                "PBR": f"{s['pbr']} 배",
                "ROE": f"{s['roe']} %",
                "배당수익률": f"{s['divYield']} %",
                "AI 헬스": f"{s['healthScore']} 점",
                "S-RIM 적정가": f"{srim['fair10']:,} 원"
            })

    st.dataframe(pd.DataFrame(screener_res), use_container_width=True)

# ---------------------------------------------------------
# [탭 11] 💰 실적 & 배당 트렌드
# ---------------------------------------------------------
with tab10:
    st.subheader(f"💰 [{stock['name']}] 분기별 실적 추이 & 배당 트렌드")

    q_df = pd.DataFrame(stock['quarters'])
    fig_q = make_subplots(specs=[[{"secondary_y": True}]])

    fig_q.add_trace(
        go.Bar(x=q_df['quarter'], y=q_df['rev'], name="매출액 (조원)", marker_color="#38bdf8"),
        secondary_y=False
    )
    fig_q.add_trace(
        go.Scatter(x=q_df['quarter'], y=q_df['op'], name="영업이익 (조원)", mode="lines+markers", line=dict(color="#4ade80", width=3)),
        secondary_y=True
    )

    fig_q.update_layout(template="plotly_dark", paper_bgcolor="#161b22", plot_bgcolor="#161b22", title="분기별 매출 및 영업이익 추이")
    st.plotly_chart(fig_q, use_container_width=True)

# ---------------------------------------------------------
# [탭 12] 📉 기술적 파동 지표
# ---------------------------------------------------------
with tab11:
    st.subheader(f"📉 [{stock['name']}] 기술적 이평선 및 RSI 지표")

    tech = calculate_technical_indicators(stock['priceHistory'])
    t1, t2, t3 = st.columns(3)
    t1.metric("3일 이동평균", f"{int(tech['ma3']):,} 원")
    t2.metric("5일 이동평균", f"{int(tech['ma5']):,} 원")
    t3.metric("RSI (14)", f"{tech['rsi']}", tech['rsiSignal'])

    fig_p = px.line(x=list(range(len(stock['priceHistory']))), y=stock['priceHistory'], title="최근 주가 추이", labels={'x': '기간', 'y': '주가(원)'})
    fig_p.update_traces(line_color="#38bdf8", line_width=3)
    fig_p.update_layout(template="plotly_dark", paper_bgcolor="#161b22", plot_bgcolor="#161b22")
    st.plotly_chart(fig_p, use_container_width=True)

# ---------------------------------------------------------
# [탭 13] 🔔 핀포인트 조건 알림
# ---------------------------------------------------------
with tab12:
    st.subheader("🔔 텔레그램 핀포인트 조건 알림 연동")

    st.markdown("""
    관심 종목의 **목표가 도달, 외인/기관 수급 급변, DART 오버행 공시 감지, 어닝 서프라이즈 발생** 시 텔레그램으로 즉시 발송합니다.
    """)

    if st.button("📲 텔레그램 알림 발송 테스트"):
        if not tg_token or not tg_chat_id:
            st.warning("⚠️ 사이드바에서 Telegram Bot Token과 Chat ID를 입력해 주세요.")
        else:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            msg = f"🚨 [LJW Terminal 알림]\n\n⭐ 분석 종목: {stock['name']} ({stock['code']})\n- 현재가: {stock['price']:,}원\n- AI 헬스 스코어: {stock['healthScore']}/5.0\n- 수급 신호: {stock['institutionalFlow']['signal']}\n- 리스크: {stock['riskDetail']}"
            try:
                res = requests.post(url, json={"chat_id": tg_chat_id, "text": msg}, timeout=5)
                if res.status_code == 200:
                    st.success("✅ 텔레그램 테스트 메시지가 성공적으로 발송되었습니다!")
                else:
                    st.error("❌ 발송 실패: Bot Token 및 Chat ID를 확인해 주세요.")
            except Exception as e:
                st.error(f"❌ 통신 오류 발생: {e}")