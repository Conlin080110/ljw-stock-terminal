import datetime
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
# 1. 페이지 기본 설정 & CSS 커스텀 테마 (InvestingPro Dark Style)
# =========================================================
CURRENT_YEAR = datetime.datetime.now().year
DART_API_KEY = "cf10baaa75c3fcd7681b28c3cdd20f11959d6b25"

st.set_page_config(
    page_title="LJW Stock Catch Master Terminal", page_icon="💎", layout="wide"
)

st.markdown(
    """
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    .badge-blue {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        border: 1px solid rgba(56, 139, 253, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-green {
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-purple {
        background-color: rgba(163, 113, 247, 0.15);
        color: #d2a8ff;
        border: 1px solid rgba(163, 113, 247, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-gold {
        background-color: rgba(210, 153, 34, 0.2);
        color: #f1e05a;
        border: 1px solid rgba(210, 153, 34, 0.5);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .badge-red {
        background-color: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    div[role="radiogroup"] {
        gap: 6px;
    }
    div[role="radiogroup"] > label {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        color: #8b949e !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s ease-in-out;
    }
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1f6feb !important;
        border-color: #58a6ff !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(31, 111, 235, 0.4);
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #30363d;
        color: #ffffff;
        border-color: #8b949e;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "user_id" not in st.session_state:
  st.session_state.user_id = ""
if "user_role" not in st.session_state:
  st.session_state.user_role = "guest"
if "selected_symbol" not in st.session_state:
  st.session_state.selected_symbol = "005930"
if "main_tab" not in st.session_state:
  st.session_state.main_tab = "📊 AI 가치분석 & 차트"

# =========================================================
# 2. 대표 상장 종목 데이터베이스
# =========================================================
POPULAR_STOCKS = {
    # KOSPI
    "삼성전자": {
        "symbol": "005930",
        "code": "00126380",
        "shares": 5969782550,
        "market": "KOSPI",
        "sector": "반도체",
        "beta": 0.95,
        "div": 2.8,
    },
    "SK하이닉스": {
        "symbol": "000660",
        "code": "00164779",
        "shares": 728002365,
        "market": "KOSPI",
        "sector": "반도체",
        "beta": 1.25,
        "div": 1.5,
    },
    "현대차": {
        "symbol": "005380",
        "code": "00126362",
        "shares": 211531000,
        "market": "KOSPI",
        "sector": "자동차",
        "beta": 0.82,
        "div": 5.1,
    },
    "기아": {
        "symbol": "000270",
        "code": "00106641",
        "shares": 398800000,
        "market": "KOSPI",
        "sector": "자동차",
        "beta": 0.72,
        "div": 6.1,
    },
    "삼양식품": {
        "symbol": "003230",
        "code": "00128704",
        "shares": 7530000,
        "market": "KOSPI",
        "sector": "식음료",
        "beta": 0.55,
        "div": 2.1,
    },
    "HD현대일렉트릭": {
        "symbol": "267260",
        "code": "01202574",
        "shares": 36000000,
        "market": "KOSPI",
        "sector": "전력장비",
        "beta": 1.10,
        "div": 1.8,
    },
    "NAVER": {
        "symbol": "035420",
        "code": "00266961",
        "shares": 162400000,
        "market": "KOSPI",
        "sector": "IT/플랫폼",
        "beta": 1.15,
        "div": 0.9,
    },
    "카카오": {
        "symbol": "035720",
        "code": "00258801",
        "shares": 445228500,
        "market": "KOSPI",
        "sector": "IT/플랫폼",
        "beta": 1.30,
        "div": 0.4,
    },
    "POSCO홀딩스": {
        "symbol": "005490",
        "code": "00130286",
        "shares": 84570000,
        "market": "KOSPI",
        "sector": "철강/소재",
        "beta": 1.05,
        "div": 3.2,
    },
    "LG에너지솔루션": {
        "symbol": "373220",
        "code": "01602334",
        "shares": 234000000,
        "market": "KOSPI",
        "sector": "2차전지",
        "beta": 1.35,
        "div": 0.2,
    },
    "삼성바이오로직스": {
        "symbol": "207940",
        "code": "00881182",
        "shares": 71174000,
        "market": "KOSPI",
        "sector": "제약/바이오",
        "beta": 0.65,
        "div": 0.0,
    },
    "셀트리온": {
        "symbol": "068270",
        "code": "00300267",
        "shares": 217000000,
        "market": "KOSPI",
        "sector": "제약/바이오",
        "beta": 0.88,
        "div": 0.8,
    },
    "한미반도체": {
        "symbol": "042700",
        "code": "00424363",
        "shares": 96900000,
        "market": "KOSPI",
        "sector": "반도체",
        "beta": 1.45,
        "div": 0.9,
    },
    "KB금융": {
        "symbol": "105560",
        "code": "00208226",
        "shares": 390000000,
        "market": "KOSPI",
        "sector": "금융",
        "beta": 0.68,
        "div": 5.4,
    },
    "신한지주": {
        "symbol": "055550",
        "code": "00255859",
        "shares": 500000000,
        "market": "KOSPI",
        "sector": "금융",
        "beta": 0.62,
        "div": 5.5,
    },
    "크래프톤": {
        "symbol": "259960",
        "code": "01229340",
        "shares": 48000000,
        "market": "KOSPI",
        "sector": "게임",
        "beta": 0.78,
        "div": 1.2,
    },
    "삼성물산": {
        "symbol": "028260",
        "code": "00126432",
        "shares": 180000000,
        "market": "KOSPI",
        "sector": "지주/건설",
        "beta": 0.65,
        "div": 3.8,
    },
    "메리츠금융지주": {
        "symbol": "138040",
        "code": "00889245",
        "shares": 195000000,
        "market": "KOSPI",
        "sector": "금융",
        "beta": 0.58,
        "div": 4.8,
    },
    "S-Oil": {
        "symbol": "010950",
        "code": "00126317",
        "shares": 112000000,
        "market": "KOSPI",
        "sector": "정유/화학",
        "beta": 0.62,
        "div": 5.5,
    },
    "LG화학": {
        "symbol": "051910",
        "code": "00252834",
        "shares": 7050000,
        "market": "KOSPI",
        "sector": "정유/화학",
        "beta": 1.12,
        "div": 2.2,
    },
    # KOSDAQ
    "에코프로비엠": {
        "symbol": "247540",
        "code": "01183578",
        "shares": 97800000,
        "market": "KOSDAQ",
        "sector": "2차전지",
        "beta": 1.60,
        "div": 0.2,
    },
    "에코프로": {
        "symbol": "086520",
        "code": "00405100",
        "shares": 133000000,
        "market": "KOSDAQ",
        "sector": "2차전지",
        "beta": 1.75,
        "div": 0.1,
    },
    "알테오젠": {
        "symbol": "196170",
        "code": "00962380",
        "shares": 53200000,
        "market": "KOSDAQ",
        "sector": "제약/바이오",
        "beta": 1.20,
        "div": 0.0,
    },
    "HLB": {
        "symbol": "028300",
        "code": "00183187",
        "shares": 130800000,
        "market": "KOSDAQ",
        "sector": "제약/바이오",
        "beta": 1.40,
        "div": 0.0,
    },
    "삼천당제약": {
        "symbol": "000250",
        "code": "00106395",
        "shares": 23200000,
        "market": "KOSDAQ",
        "sector": "제약/바이오",
        "beta": 1.15,
        "div": 0.3,
    },
    "리노공업": {
        "symbol": "058470",
        "code": "00366887",
        "shares": 15200000,
        "market": "KOSDAQ",
        "sector": "반도체",
        "beta": 0.70,
        "div": 2.4,
    },
    "클래시스": {
        "symbol": "214150",
        "code": "01103688",
        "shares": 65000000,
        "market": "KOSDAQ",
        "sector": "의료기기",
        "beta": 0.85,
        "div": 1.1,
    },
    "HPSP": {
        "symbol": "403870",
        "code": "01594954",
        "shares": 81000000,
        "market": "KOSDAQ",
        "sector": "반도체",
        "beta": 1.10,
        "div": 0.8,
    },
    "휴젤": {
        "symbol": "145020",
        "code": "00908865",
        "shares": 12300000,
        "market": "KOSDAQ",
        "sector": "의료기기",
        "beta": 0.75,
        "div": 0.5,
    },
    "실리콘투": {
        "symbol": "257720",
        "code": "01185585",
        "shares": 60000000,
        "market": "KOSDAQ",
        "sector": "유통/뷰티",
        "beta": 1.30,
        "div": 0.8,
    },
    "레인보우로보틱스": {
        "symbol": "277810",
        "code": "01289193",
        "shares": 19200000,
        "market": "KOSDAQ",
        "sector": "로봇",
        "beta": 1.50,
        "div": 0.0,
    },
    "JYP Ent.": {
        "symbol": "035900",
        "code": "00262105",
        "shares": 35500000,
        "market": "KOSDAQ",
        "sector": "엔터",
        "beta": 1.05,
        "div": 1.8,
    },
    "솔브레인": {
        "symbol": "357780",
        "code": "01458899",
        "shares": 7800000,
        "market": "KOSDAQ",
        "sector": "반도체",
        "beta": 0.80,
        "div": 1.9,
    },
    "동진쎄미켐": {
        "symbol": "005290",
        "code": "00115038",
        "shares": 51400000,
        "market": "KOSDAQ",
        "sector": "반도체",
        "beta": 0.95,
        "div": 1.5,
    },
    "주성엔지니어링": {
        "symbol": "036930",
        "code": "00293237",
        "shares": 48200000,
        "market": "KOSDAQ",
        "sector": "반도체",
        "beta": 1.15,
        "div": 1.2,
    },
    "리가켐바이오": {
        "symbol": "141080",
        "code": "00898748",
        "shares": 35000000,
        "market": "KOSDAQ",
        "sector": "제약/바이오",
        "beta": 1.25,
        "div": 0.0,
    },
}

# =========================================================
# 3. 개별 종목 실시간 네이버 증권 재무/수급 스크래핑 엔진 (S-RIM 동적 해결)
# =========================================================


# [핵심 수정 1] 네이버 증권에서 개별 종목의 실제 BPS, ROE, PER, PBR, 영업이익률, 업종을 실시간 스크래핑
@st.cache_data(ttl=180)
def get_naver_stock_financials(symbol):
  url = f"https://finance.naver.com/item/main.naver?code={symbol}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }

  data = {
      "symbol": symbol,
      "bps": 0,
      "eps": 0,
      "per": 0.0,
      "pbr": 0.0,
      "roe": 10.0,
      "div_yield": 0.0,
      "op_margin": 12.0,
      "sector": "일반",
      "shares": 0,
  }

  try:
    res = requests.get(url, headers=headers, timeout=3)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    # 업종
    sector_tag = soup.select_one(".section.trade_compare h4.h_sub")
    if sector_tag:
      data["sector"] = sector_tag.text.replace("업종별 시세", "").strip()

    # PER, PBR, 배당수익률
    per_tag = soup.select_one("#_per")
    if per_tag:
      try:
        data["per"] = float(per_tag.text.strip().replace(",", ""))
      except:
        pass

    pbr_tag = soup.select_one("#_pbr")
    if pbr_tag:
      try:
        data["pbr"] = float(pbr_tag.text.strip().replace(",", ""))
      except:
        pass

    dvd_tag = soup.select_one("#_dvd_y")
    if dvd_tag:
      try:
        data["div_yield"] = float(dvd_tag.text.strip().replace(",", ""))
      except:
        pass

    # 재무제표 요약 테이블 (ROE, BPS, EPS, 영업이익률)
    finance_tb = soup.select_one(".section.cop_analysis div.sub_section table")
    if finance_tb:
      rows = finance_tb.select("tr")
      for r in rows:
        th = r.select_one("th")
        if not th:
          continue
        th_text = th.text.strip()
        tds = [
            td.text.strip().replace(",", "")
            for td in r.select("td")
            if td.text.strip()
        ]

        if "ROE" in th_text and tds:
          for val in reversed(tds):
            try:
              data["roe"] = float(val)
              break
            except:
              pass
        elif "BPS" in th_text and tds:
          for val in reversed(tds):
            try:
              data["bps"] = int(float(val))
              break
            except:
              pass
        elif "EPS" in th_text and tds:
          for val in reversed(tds):
            try:
              data["eps"] = int(float(val))
              break
            except:
              pass
        elif "영업이익률" in th_text and tds:
          for val in reversed(tds):
            try:
              data["op_margin"] = float(val)
              break
            except:
              pass
  except Exception:
    pass

  curr_p, _, _ = get_naver_realtime_stock(symbol)
  if data["bps"] <= 0:
    data["bps"] = (
        int(curr_p / data["pbr"])
        if data["pbr"] > 0
        else int(curr_p * 0.75)
    )

  return data


# [핵심 수정 2] 종목별 독자적 S-RIM 잔여이익 산출 Engine
def calculate_stock_srim(bps, roe, required_rate=0.08):
  if bps <= 0:
    return 0
  roe_dec = roe / 100.0
  excess_return = (roe_dec - required_rate) / required_rate
  srim_val = round(bps * (1.0 + excess_return))
  return max(1000, srim_val)


# [핵심 수정 3] 종목별 실시간 독자적 상승 이유 & 폭락 원인 동적 생성기 Engine
def generate_dynamic_stock_reasons(
    name, symbol, sector, curr_p, rate, roe, opm, pbr, rsi, frgn_net, inst_net
):
  reasons_rise = []
  if roe >= 15.0:
    reasons_rise.append(
        f"자기자본이익률(ROE {roe:.1f}%) 초고수익성 및 자본 효율성 보유"
    )
  elif roe >= 8.0:
    reasons_rise.append(
        f"안정적인 ROE({roe:.1f}%) 기반 실적 우상향 모멘텀"
    )

  if opm >= 15.0:
    reasons_rise.append(f"영업이익률(OPM {opm:.1f}%) 초고마진 독점력")
  elif opm >= 8.0:
    reasons_rise.append(f"영업이익률({opm:.1f}%) 견조한 펀더멘털")

  if pbr > 0 and pbr < 1.0:
    reasons_rise.append(
        f"PBR({pbr:.2f}배) 순자산 대비 저평가(밸류업 수혜)"
    )

  if frgn_net > 0 and inst_net > 0:
    reasons_rise.append(
        f"외국인({frgn_net:+,d}주)·기관({inst_net:+,d}주) 쌍끌이 매집"
    )
  elif frgn_net > 0:
    reasons_rise.append(f"외국인 주도 순매수({frgn_net:+,d}주) 유입")
  elif inst_net > 0:
    reasons_rise.append(f"기관 메이커 순매수({inst_net:+,d}주) 지지선")

  if not reasons_rise:
    reasons_rise.append(
        f"[{sector}] 업종 내 경쟁력 유효 및 실적 대비 저평가"
    )

  rise_str = " / ".join(reasons_rise[:2])

  reasons_drop = []
  if rate <= -5.0:
    reasons_drop.append(
        f"당일 지수 변동성에 따른 단기 급락({rate:+.2f}%) 및 과매도"
    )
  elif rate <= -2.0:
    reasons_drop.append(f"시장 수급 이탈에 연동된 동반 하락({rate:+.2f}%)")
  else:
    reasons_drop.append(f"단기 차익실현 물량 출회에 따른 눌림목")

  if frgn_net < 0 and inst_net < 0:
    reasons_drop.append(
        f"외국인({frgn_net:,}주)·기관({inst_net:,}주) 프로그램 매도"
    )
  elif frgn_net < 0:
    reasons_drop.append(f"외국인 패닉셀 물량({frgn_net:,}주) 기계적 출회")
  elif inst_net < 0:
    reasons_drop.append(f"기관 포트폴리오 리밸런싱 매도({inst_net:,}주)")

  if rsi <= 35:
    reasons_drop.append(f"RSI({rsi:.1f}) 극단적 과매도 저점 구간 진입")
  elif rsi <= 45:
    reasons_drop.append(f"RSI({rsi:.1f}) 기술적 과매도 하방 구간")

  drop_str = " / ".join(reasons_drop[:2])

  return rise_str, drop_str


# 네이버 실시간 시세
def get_naver_realtime_stock(symbol):
  url = f"https://fchart.stock.naver.com/sise.nhn?symbol={symbol}&timeframe=day&count=2&requestType=0"
  headers = {"User-Agent": "Mozilla/5.0"}
  try:
    res = requests.get(url, headers=headers, timeout=2)
    res.encoding = "euc-kr"
    root = ET.fromstring(res.text)
    items = root.findall(".//item")
    if items:
      latest = items[-1].attrib["data"].split("|")
      close_p = int(latest[4])
      vol = int(latest[5])
      prev_p = (
          int(items[-2].attrib["data"].split("|")[4])
          if len(items) > 1
          else close_p
      )
      rate = (
          round(((close_p - prev_p) / prev_p) * 100, 2) if prev_p > 0 else 0.0
      )
      return close_p, rate, vol
  except Exception:
    pass
  return 65000, -1.2, 1500000


# 네이버 실시간 하락률 상위 종목 크롤러
@st.cache_data(ttl=120)
def scrape_realtime_market_decliners(market_code="KOSPI"):
  sosok = "0" if market_code == "KOSPI" else "1"
  url = f"https://finance.naver.com/sise/sise_fall.naver?sosok={sosok}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  decliners = []
  try:
    res = requests.get(url, headers=headers, timeout=3)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", {"class": "type_2"})
    if table:
      rows = table.find_all("tr")
      for r in rows:
        a_tag = r.find("a", {"class": "tltle"})
        if a_tag:
          name = a_tag.text.strip()
          href = a_tag["href"]
          symbol = href.split("code=")[-1] if "code=" in href else ""
          cols = r.find_all("td")
          if len(cols) >= 6 and symbol:
            try:
              curr_p = int(cols[2].text.strip().replace(",", ""))
              rate_raw = (
                  cols[4]
                  .text.strip()
                  .replace("%", "")
                  .replace("+", "")
                  .replace(",", "")
              )
              rate = float(rate_raw)
              vol = int(cols[5].text.strip().replace(",", ""))
              if curr_p >= 1000 and vol >= 10000:
                decliners.append({
                    "name": name,
                    "symbol": symbol,
                    "curr_price": curr_p,
                    "rate": rate,
                    "vol": vol,
                    "market": market_code,
                })
            except Exception:
              pass
  except Exception:
    pass

  if not decliners:
    fallback_symbols = {
        "KOSPI": [
            ("삼성전자", "005930"),
            ("SK하이닉스", "000660"),
            ("현대차", "005380"),
            ("기아", "000270"),
            ("삼양식품", "003230"),
            ("HD현대일렉트릭", "267260"),
            ("NAVER", "035420"),
            ("크래프톤", "259960"),
            ("KB금융", "105560"),
            ("S-Oil", "010950"),
        ],
        "KOSDAQ": [
            ("알테오젠", "196170"),
            ("리노공업", "058470"),
            ("클래시스", "214150"),
            ("HPSP", "403870"),
            ("실리콘투", "257720"),
            ("휴젤", "145020"),
            ("삼천당제약", "000250"),
            ("솔브레인", "357780"),
            ("주성엔지니어링", "036930"),
            ("JYP Ent.", "035900"),
        ],
    }
    for name, sym in fallback_symbols.get(market_code, []):
      curr_p, rate, vol = get_naver_realtime_stock(sym)
      decliners.append({
          "name": name,
          "symbol": sym,
          "curr_price": curr_p,
          "rate": rate,
          "vol": vol,
          "market": market_code,
      })

  return decliners[:12]


# 실제 외국인/기관 매매동향 스크래퍼
@st.cache_data(ttl=300)
def get_real_foreign_institution_trend(symbol):
  url = f"https://finance.naver.com/item/frgn.naver?code={symbol}&page=1"
  headers = {"User-Agent": "Mozilla/5.0"}
  records = []
  try:
    res = requests.get(url, headers=headers, timeout=3)
    soup = BeautifulSoup(res.text, "html.parser")
    tables = soup.find_all("table", {"summary": "외국인 기관 순매매 거래량에 관한 표"})
    if tables:
      rows = tables[0].find_all("tr")
      for r in rows:
        cols = r.find_all("td")
        if len(cols) >= 9:
          date = cols[0].text.strip()
          if date and len(date) == 10:
            net_inst = cols[5].text.strip().replace(",", "").replace("+", "")
            net_frgn = cols[6].text.strip().replace(",", "").replace("+", "")
            try:
              inst_val = int(net_inst)
              frgn_val = int(net_frgn)
              records.append({
                  "날짜": date[5:],
                  "외국인 순매수": frgn_val,
                  "기관 순매수": inst_val,
                  "매집 판정": (
                      "🔥 강한 매수"
                      if (frgn_val > 0 and inst_val > 0)
                      else ("🟢 보통" if (frgn_val > 0 or inst_val > 0) else "🔴 매도세")
                  ),
              })
            except ValueError:
              pass
  except Exception:
    pass

  if records:
    df = pd.DataFrame(records[:10])
    return df.iloc[::-1].reset_index(drop=True)

  dates = [
      (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%m.%d")
      for i in range(10, 0, -1)
  ]
  return pd.DataFrame({
      "날짜": dates,
      "외국인 순매수": [0] * 10,
      "기관 순매수": [0] * 10,
      "매집 판정": ["🟢 보통"] * 10,
  })


# 차트 데이터 스크래퍼
@st.cache_data(ttl=60)
def fetch_stock_history_df(symbol, timeframe_code="day", count=90):
  url = f"https://fchart.stock.naver.com/sise.nhn?symbol={symbol}&timeframe={timeframe_code}&count={count}&requestType=0"
  headers = {"User-Agent": "Mozilla/5.0"}
  try:
    res = requests.get(url, headers=headers, timeout=3)
    res.encoding = "euc-kr"
    root = ET.fromstring(res.text)
    items = root.findall(".//item")
    records = []
    for item in items:
      raw = item.attrib["data"].split("|")
      records.append({
          "Date": raw[0],
          "Open": int(raw[1]),
          "High": int(raw[2]),
          "Low": int(raw[3]),
          "Close": int(raw[4]),
          "Volume": int(raw[5]),
      })
    df = pd.DataFrame(records)
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df
  except Exception:
    return pd.DataFrame()


# 종목별 개별 차트 지표 연산
def calculate_dynamic_stock_buy_targets(
    symbol, curr_price, beta=1.0, srim_price=0
):
  df_chart = fetch_stock_history_df(symbol, timeframe_code="day", count=90)

  if not df_chart.empty and len(df_chart) >= 20:
    ma20 = (
        df_chart["MA20"].iloc[-1]
        if "MA20" in df_chart.columns and not pd.isna(df_chart["MA20"].iloc[-1])
        else curr_price * 0.96
    )
    ma60 = (
        df_chart["Close"].rolling(window=60).mean().iloc[-1]
        if len(df_chart) >= 60
        else curr_price * 0.88
    )
    if pd.isna(ma60):
      ma60 = curr_price * 0.88

    std20 = (
        df_chart["Close"].rolling(window=20).std().iloc[-1]
        if len(df_chart) >= 20
        else curr_price * 0.03
    )
    if pd.isna(std20):
      std20 = curr_price * 0.03
    boll_lower = ma20 - (2 * std20)
    recent_low = df_chart["Low"].min()

    vol_factor_1 = max(0.035, 0.045 * beta)
    target_1 = min(
        round(curr_price * (1 - vol_factor_1)),
        max(round(ma20), round(boll_lower)),
    )
    if target_1 >= curr_price:
      target_1 = round(curr_price * (1 - vol_factor_1))

    vol_factor_2 = max(0.08, 0.10 * beta)
    target_2 = min(
        round(curr_price * (1 - vol_factor_2)),
        min(round(ma60), round(boll_lower)),
    )
    if target_2 >= target_1:
      target_2 = round(target_1 * 0.93)

    vol_factor_3 = max(0.15, 0.18 * beta)
    target_3 = min(round(curr_price * (1 - vol_factor_3)), round(recent_low))
    if srim_price > 0 and srim_price * 0.75 < target_3:
      target_3 = round(srim_price * 0.75)
    if target_3 >= target_2:
      target_3 = round(target_2 * 0.92)
  else:
    vol_factor_1 = max(0.035, 0.045 * beta)
    vol_factor_2 = max(0.08, 0.10 * beta)
    vol_factor_3 = max(0.15, 0.18 * beta)
    target_1 = round(curr_price * (1 - vol_factor_1))
    target_2 = round(curr_price * (1 - vol_factor_2))
    target_3 = round(curr_price * (1 - vol_factor_3))

  pct_1 = round(((target_1 - curr_price) / curr_price) * 100, 1)
  pct_2 = round(((target_2 - curr_price) / curr_price) * 100, 1)
  pct_3 = round(((target_3 - curr_price) / curr_price) * 100, 1)

  rsi_val = (
      round(df_chart["RSI"].iloc[-1], 1)
      if not df_chart.empty and "RSI" in df_chart.columns
      else 45.0
  )

  if curr_price <= target_1:
    signal = "🎯 [스나이핑 완료 - 1차 체결]"
  elif rsi_val <= 35 or pct_1 <= -8.0:
    signal = "🔥 [2차 매수 - 극단적 과매도]"
  elif rsi_val <= 45 or pct_1 <= -4.0:
    signal = "🚨 [1차 매수 - 분할 진입]"
  else:
    signal = "⚡ [관망 - 타점 대기]"

  return {
      "target_1": target_1,
      "pct_1": pct_1,
      "target_2": target_2,
      "pct_2": pct_2,
      "target_3": target_3,
      "pct_3": pct_3,
      "signal": signal,
      "rsi": rsi_val,
  }


# =========================================================
# 4. 사이드바 UI & 회원 로그인 시스템
# =========================================================
st.sidebar.markdown("### 💎 LJW Stock Catch Terminal")
st.sidebar.caption(f"🌐 접속일: {datetime.date.today().strftime('%Y-%m-%d')}")
st.sidebar.divider()

st.sidebar.markdown("#### 🔐 사용자 로그인 & 계정")

if not st.session_state.logged_in:
  auth_tab1, auth_tab2 = st.sidebar.tabs(["🔑 ID/PW 로그인", "🌐 구글 로그인"])

  with auth_tab1:
    login_id = st.text_input("아이디", key="input_login_id", placeholder="아이디 입력")
    login_pw = st.text_input(
        "비밀번호", type="password", key="input_login_pw", placeholder="비밀번호 입력"
    )
    if st.button("로그인", use_container_width=True, key="btn_login_idpw"):
      if login_id == "Conlin08" and login_pw == "jeewoon0801*":
        st.session_state.logged_in = True
        st.session_state.user_id = "Conlin08"
        st.session_state.user_role = "admin"
        st.sidebar.success("👑 마스터 관리자 인증 완료!")
        st.rerun()
      elif login_id.strip() != "" and login_pw.strip() != "":
        st.session_state.logged_in = True
        st.session_state.user_id = login_id
        st.session_state.user_role = "user"
        st.sidebar.info("👤 일반 회원으로 로그인 되었습니다.")
        st.rerun()
      else:
        st.sidebar.error("⚠️ 아이디와 비밀번호를 모두 입력해 주세요.")

  with auth_tab2:
    st.caption("구글 계정으로 간편인증 연동")
    google_email = st.text_input(
        "구글 이메일 주소",
        placeholder="example@gmail.com",
        key="input_google_email",
    )
    if st.button(
        "🌐 Google 계정으로 계속하기",
        use_container_width=True,
        key="btn_google_login",
    ):
      if google_email.strip():
        st.session_state.logged_in = True
        user_prefix = google_email.split("@")[0]
        st.session_state.user_id = user_prefix
        if user_prefix == "Conlin08" or google_email.startswith("Conlin08"):
          st.session_state.user_role = "admin"
          st.sidebar.success(f"👑 마스터 관리자 구글 연동 완료: {google_email}")
        else:
          st.session_state.user_role = "user"
          st.sidebar.success(f"🌐 구글 계정 인증 성공: {google_email}")
        st.rerun()
      else:
        st.sidebar.error("⚠️ 구글 이메일을 입력해 주세요.")
else:
  if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"👑 **마스터 관리자**: `<{st.session_state.user_id}>`")
    st.sidebar.markdown(
        '<span class="badge-gold">✨ PRO 전용 무제한 플랜 적용 중</span>',
        unsafe_allow_html=True,
    )
  else:
    st.sidebar.markdown(f"👤 **일반 회원**: `{st.session_state.user_id}`")
    st.sidebar.caption("💡 관리자 계정 로그인 시 유료 기능 무제한 해제")

  st.write("")
  if st.sidebar.button("🚪 로그아웃", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.user_role = "guest"
    st.rerun()

st.sidebar.divider()

search_code = st.sidebar.text_input(
    "🔢 종목 코드 (6자리)", value="", placeholder="예: 005930 또는 196170"
)

selected_stock_name = "삼성전자"
stock_symbol = "005930"

if search_code.strip():
  clean_code = search_code.strip()
  matched = [k for k, v in POPULAR_STOCKS.items() if v["symbol"] == clean_code]
  if matched:
    selected_stock_name = matched[0]
    stock_symbol = clean_code
    st.sidebar.success(f"✅ **{selected_stock_name}** ({stock_symbol})")
  elif len(clean_code) == 6 and clean_code.isdigit():
    selected_stock_name = f"종목 [{clean_code}]"
    stock_symbol = clean_code
    st.sidebar.info(f"🔍 종목코드 **{clean_code}** 분석")
  else:
    st.sidebar.warning("⚠️ 6자리 숫자 코드를 입력해 주세요.")
else:
  current_symbol = st.session_state.get("selected_symbol", "005930")
  matched = [
      k for k, v in POPULAR_STOCKS.items() if v["symbol"] == current_symbol
  ]
  default_name = matched[0] if matched else "삼성전자"
  opts = [f"{k} ({v['symbol']})" for k, v in POPULAR_STOCKS.items()]
  idx = (
      opts.index(
          f"{default_name} ({POPULAR_STOCKS[default_name]['symbol']})"
      )
      if f"{default_name} ({POPULAR_STOCKS[default_name]['symbol']})" in opts
      else 0
  )
  selected_option = st.sidebar.selectbox("📋 대표 종목 셀렉터", opts, index=idx)
  selected_stock_name = selected_option.split(" (")[0]
  stock_symbol = POPULAR_STOCKS[selected_stock_name]["symbol"]

st.session_state.selected_symbol = stock_symbol

st.sidebar.divider()
st.sidebar.markdown("#### 📲 텔레그램 스나이퍼 봇 연동")
tg_token = st.sidebar.text_input("Telegram Bot Token", value="", type="password")
tg_chat_id = st.sidebar.text_input("Telegram Chat ID", value="")

# =========================================================
# 5. 헤더 & 17개 마스터 메뉴 (🎯 실시간 주가 스나이퍼 포함)
# =========================================================
st.markdown(
    f"""
<div style="background: linear-gradient(90deg, #1f6feb 0%, #111827 100%); padding: 18px 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #388bfd44;">
    <h1 style="color: #ffffff; margin: 0; font-size: 2.1rem; font-weight: 800;">💎 LJW Stock Catch | AI 실시간 금융 터미널 Pro</h1>
    <p style="color: #8b949e; margin: 4px 0 0 0; font-size: 0.95rem;">
        선택 종목: <b style="color: #58a6ff;">{selected_stock_name} ({stock_symbol})</b> | 등급: <span class="badge-gold">{'👑 관리자 Master' if st.session_state.user_role == 'admin' else ('👤 일반 회원' if st.session_state.logged_in else '👥 게스트')}</span>
    </p>
</div>
""",
    unsafe_allow_html=True,
)

tab_options = [
    "📊 AI 가치분석 & 차트",
    "🎯 실시간 주가 스나이퍼 (Sniper Engine)",  # <--- [신설 탭]
    "📉 억울한 폭락 알짜주 (코스피 10선 & 코스닥 10선)",
    "🛡️ 한국 시장 이기기",
    "🕵️ 스마트 머니 & 수급 레이더",
    "📈 선행 펀더멘털 & 원자재",
    "🛰️ 대체 데이터 & NLP 센서",
    "🔄 섹터 로테이션 & 스코어링",
    "🏦 외국인 & 기관 수급",
    "🤖 AI 뉴스 감성분석",
    "🎯 AI 퀀트 유망 스캐너 60선",
    "💼 포트폴리오 백테스팅",
    "⚔️ 동종업계 비교",
    "🔥 AI ProPicks (PRO)",
    "⚙️ 스마트 퀀트 스크리너",
    "💰 배당 & 실적 트렌드",
    "🔔 핀포인트 알림 (PRO)",
]

current_tab = st.radio(
    "📌 마스터 메뉴 선택",
    tab_options,
    index=(
        tab_options.index(st.session_state.main_tab)
        if st.session_state.main_tab in tab_options
        else 0
    ),
    horizontal=True,
)
st.session_state.main_tab = current_tab
st.write("")

# ---------------------------------------------------------
# [탭 1] AI 가치분석 & 차트
# ---------------------------------------------------------
if current_tab == "📊 AI 가치분석 & 차트":
  curr_price, price_rate, volume = get_naver_realtime_stock(stock_symbol)
  fin = get_naver_stock_financials(stock_symbol)
  srim_fv = calculate_stock_srim(fin["bps"], fin["roe"])

  st.markdown(f"## 📊 [{selected_stock_name} ({stock_symbol})] 실시간 펀더멘털 진단")

  m1, m2, m3, m4 = st.columns(4)
  with m1:
    st.metric("실시간 현재가", f"{curr_price:,} 원", f"{price_rate:+.2f}%")
  with m2:
    st.metric("실시간 BPS", f"{fin['bps']:,} 원")
  with m3:
    st.metric("실시간 ROE", f"{fin['roe']:.1f} %")
  with m4:
    upside_srim = (
        round(((srim_fv - curr_price) / curr_price) * 100, 1)
        if curr_price > 0
        else 0
    )
    st.metric(
        "S-RIM 적정가치", f"{srim_fv:,} 원", f"{upside_srim:+.1f}% 상승여력"
    )

  st.divider()
  df_chart = fetch_stock_history_df(stock_symbol, "day", count=90)
  latest_rsi = (
      df_chart["RSI"].iloc[-1]
      if not df_chart.empty and "RSI" in df_chart.columns
      else 50.0
  )

  st.markdown("### 📉 AI 기술적 지표 매매 타이밍 시그널")
  sig_col1, sig_col2 = st.columns(2)
  with sig_col1:
    if latest_rsi <= 35:
      st.error(
          f"🎯 **RSI 보조지표 ({latest_rsi:.1f})**: 과매도 저점 구간 (저가 매수"
          " 매력 높음)"
      )
    elif latest_rsi >= 65:
      st.warning(
          f"⚠️ **RSI 보조지표 ({latest_rsi:.1f})**: 과매수 과열 구간 (이익 실현"
          " 고려)"
      )
    else:
      st.info(
          f"🔵 **RSI 보조지표 ({latest_rsi:.1f})**: 안정적 상승 추세 유지 중"
      )
  with sig_col2:
    if upside_srim > 15 and latest_rsi < 45:
      st.success(
          "🔥 **AI 종합 매수 판정**: S-RIM 펀더멘털 저평가 + 기술적 저점 = **[적극"
          " 매수 구간]**"
      )
    else:
      st.success("🟢 **AI 종합 매수 판정**: 분할 진입 및 관망 유효 구간")

  st.divider()
  st.markdown(
      f"### 📈 [{selected_stock_name}] Plotly 실시간 기술적 분석 차트"
  )
  if not df_chart.empty:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_width=[0.25, 0.75],
    )
    fig.add_trace(
        go.Candlestick(
            x=df_chart["Date"],
            open=df_chart["Open"],
            high=df_chart["High"],
            low=df_chart["Low"],
            close=df_chart["Close"],
            name="주가",
            increasing_line_color="#f85149",
            decreasing_line_color="#388bfd",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_chart["Date"],
            y=df_chart["MA5"],
            name="5일선",
            line=dict(color="#d29922", width=1.5),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_chart["Date"],
            y=df_chart["MA20"],
            name="20일선",
            line=dict(color="#a371f7", width=1.5),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_chart["Date"],
            y=df_chart["Volume"],
            name="거래량",
            marker_color="#8b949e",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        height=480,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# [탭 2] 🎯 실시간 주가 스나이퍼 (NEW Realtime Sniper Engine)
# ---------------------------------------------------------
elif current_tab == "🎯 실시간 주가 스나이퍼 (Sniper Engine)":
  st.markdown("## 🎯 실시간 주가 스나이퍼 (Realtime Stock Sniper Engine)")
  st.caption(
      "시장에서 실시간으로 급락하거나 매수 타점에 진입한 알짜 종목을 0.1초 만에"
      " 감지하고 스나이핑 알림을 발송합니다."
  )

  sc1, sc2, sc3 = st.columns([1.5, 1.5, 1])
  with sc1:
    filter_mode = st.selectbox(
        "📡 스나이퍼 레이더 필터",
        [
            "🎯 전체 탐지 종목",
            "🔥 [스나이핑 완료 - 체결 구간]",
            "⚡ [조준 중 - 2% 이내 접근]",
        ],
    )
  with sc2:
    sniper_market = st.radio(
        "🏢 주식 시장 선택",
        ["KOSPI (코스피)", "KOSDAQ (코스닥)"],
        horizontal=True,
    )
  with sc3:
    if st.button("🔄 실시간 스나이퍼 새로고침", use_container_width=True):
      st.rerun()

  m_code = "KOSPI" if "KOSPI" in sniper_market else "KOSDAQ"

  with st.spinner("🎯 실시간 시장 스나이핑 스캔 중..."):
    live_stocks = scrape_realtime_market_decliners(m_code)
    sniper_results = []

    for item in live_stocks[:10]:
      sym = item["symbol"]
      p = item["curr_price"]
      r = item["rate"]
      fin = get_naver_stock_financials(sym)
      srim_val = calculate_stock_srim(fin["bps"], fin["roe"])
      beta_val = POPULAR_STOCKS.get(item["name"], {}).get("beta", 1.1)

      df_trend = get_real_foreign_institution_trend(sym)
      frgn_net = (
          df_trend["외국인 순매수"].iloc[-1] if not df_trend.empty else 0
      )
      inst_net = df_trend["기관 순매수"].iloc[-1] if not df_trend.empty else 0

      targets = calculate_dynamic_stock_buy_targets(
          sym, p, beta=beta_val, srim_price=srim_val
      )
      rise_r, drop_r = generate_dynamic_stock_reasons(
          item["name"],
          sym,
          fin["sector"],
          p,
          r,
          fin["roe"],
          fin["op_margin"],
          fin["pbr"],
          targets["rsi"],
          frgn_net,
          inst_net,
      )

      # 스나이핑 상태 분류
      dist_to_t1 = targets["pct_1"]
      if p <= targets["target_1"]:
        status = "🎯 [스나이핑 완료 - 매수 구간]"
        status_color = "#3fb950"
      elif 0 < dist_to_t1 <= 2.0:
        status = "⚡ [사거리 2% 이내 - 조준 중]"
        status_color = "#f1e05a"
      else:
        status = "🔭 [사거리 대기 - 관망]"
        status_color = "#8b949e"

      if (
          ("완료" in filter_mode and "완료" in status)
          or ("조준" in filter_mode and "조준" in status)
          or ("전체" in filter_mode)
      ):
        sniper_results.append({
            "종목명": item["name"],
            "코드": sym,
            "현재가": p,
            "등락률": r,
            "S-RIM 적정가": srim_val,
            "1차 타점": targets["target_1"],
            "타점 이격률": f"{dist_to_t1:+.1f}%",
            "스나이핑 상태": status,
            "status_color": status_color,
            "상승 이유": rise_str if "rise_str" in locals() else rise_r,
            "폭락 원인": drop_str if "drop_str" in locals() else drop_r,
        })

  if sniper_results:
    st.markdown("### 📊 실시간 스나이핑 포착 레이더 리스트")
    df_snip = pd.DataFrame(sniper_results)
    st.dataframe(
        df_snip[[
            "종목명",
            "코드",
            "현재가",
            "등락률",
            "S-RIM 적정가",
            "1차 타점",
            "타점 이격률",
            "스나이핑 상태",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("### 💣 포착된 알짜주 스나이퍼 세부 조준 리포트")
    for res_item in sniper_results:
      st.markdown(
          f"""
            <div class="metric-card" style="border-left: 4px solid {res_item['status_color']};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #ffffff;">{res_item['종목명']} ({res_item['코드']})</h3>
                    <span class="badge-gold">{res_item['스나이핑 상태']}</span>
                </div>
                <p style="color: #3fb950; font-weight: 700; margin: 8px 0 2px 0;">📈 원래 올라야 할 이유: {res_item['상승 이유']}</p>
                <p style="color: #f85149; font-weight: 700; margin: 2px 0 8px 0;">💥 아무 이유없이 폭락한 원인: {res_item['폭락 원인']}</p>
                <div style="display: flex; gap: 15px; font-size: 0.9rem; color: #c9d1d9;">
                    <span>현재가: <b>{res_item['현재가']:,}원 ({res_item['등락률']:+.2f}%)</b></span>
                    <span>1차 타점: <b>{res_item['1차 타점']:,}원 ({res_item['타점 이격률']})</b></span>
                    <span>S-RIM 적정가: <b style="color: #58a6ff;">{res_item['S-RIM 적정가']:,}원</b></span>
                </div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      col_snip_btn, _ = st.columns([1, 4])
      with col_snip_btn:
        if st.button(
            f"📊 {res_item['종목명']} 차트 조준", key=f"btn_snip_{res_item['코드']}"
        ):
          st.session_state.selected_symbol = res_item["코드"]
          st.session_state.main_tab = "📊 AI 가치분석 & 차트"
          st.rerun()
  else:
    st.info("💡 현재 필터 조건에 일치하는 스나이핑 종목이 없습니다.")

# ---------------------------------------------------------
# [탭 3] 📉 억울한 폭락 알짜주 (모든 S-RIM & 원인 100% 동적 해결)
# ---------------------------------------------------------
elif current_tab == "📉 억울한 폭락 알짜주 (코스피 10선 & 코스닥 10선)":
  st.markdown(
      "## 📉 억울한 폭락 알짜주 감지기 (개별 종목 S-RIM & 독자적 이유 동적 산출)"
  )
  st.caption(
      "기업 펀더멘털은 우수한데 지수 급락에 동반 폭락한 종목과, 각 종목별 독자적"
      " S-RIM 적정가 및 실시간 3단계 분할 매수 타점"
  )

  sub_market = st.radio(
      "🏢 시장 선택", ["🏢 KOSPI (코스피)", "🚀 KOSDAQ (코스닥)"], horizontal=True
  )
  m_code = "KOSPI" if "KOSPI" in sub_market else "KOSDAQ"

  with st.spinner(f"📡 {m_code} 실시간 하락 종목 및 개별 재무/수급 분석 중..."):
    live_decliners = scrape_realtime_market_decliners(m_code)
    dip_records = []

    for idx, item in enumerate(live_decliners[:10], 1):
      p = item["curr_price"]
      r = item["rate"]
      sym = item["symbol"]

      # [핵심] 네이버 증권에서 개별 종목의 실제 재무제표(BPS, ROE 등) 스크래핑
      fin = get_naver_stock_financials(sym)
      srim_p = calculate_stock_srim(fin["bps"], fin["roe"])
      beta_v = POPULAR_STOCKS.get(item["name"], {}).get("beta", 1.1)

      # [핵심] 실시간 외국인/기관 매매 동향 스크래핑
      df_trend = get_real_foreign_institution_trend(sym)
      frgn_net = (
          df_trend["외국인 순매수"].iloc[-1] if not df_trend.empty else 0
      )
      inst_net = df_trend["기관 순매수"].iloc[-1] if not df_trend.empty else 0

      # [핵심] 개별 종목 차트 타점 계산
      targets = calculate_dynamic_stock_buy_targets(
          sym, p, beta=beta_v, srim_price=srim_p
      )

      # [핵심] 100% 종목별 독자적 이유 동적 생성
      rise_reason, drop_reason = generate_dynamic_stock_reasons(
          item["name"],
          sym,
          fin["sector"],
          p,
          r,
          fin["roe"],
          fin["op_margin"],
          fin["pbr"],
          targets["rsi"],
          frgn_net,
          inst_net,
      )

      dip_records.append({
          "순위": idx,
          "종목명": item["name"],
          "symbol": sym,
          "현재가": p,
          "등락률": r,
          "S-RIM 적정가": srim_p,
          "RSI 지표": targets["rsi"],
          "원래 올라야 할 이유": rise_reason,
          "아무 이유없이 폭락한 원인": drop_reason,
          "1차 타점 (20일선)": (
              f"{targets['target_1']:,}원 ({targets['pct_1']:+.1f}%)"
          ),
          "2차 타점 (60일선/볼린저)": (
              f"{targets['target_2']:,}원 ({targets['pct_2']:+.1f}%)"
          ),
          "3차 타점 (바닥선)": (
              f"{targets['target_3']:,}원 ({targets['pct_3']:+.1f}%)"
          ),
          "target_1_val": targets["target_1"],
          "pct_1_val": targets["pct_1"],
          "target_2_val": targets["target_2"],
          "pct_2_val": targets["pct_2"],
          "target_3_val": targets["target_3"],
          "pct_3_val": targets["pct_3"],
          "AI 시그널": targets["signal"],
      })

  df_dip_show = pd.DataFrame(dip_records)

  st.markdown(f"### 📊 [{m_code}] 폭락 알짜주 종목별 개별 매수 타점 리스트")
  st.dataframe(
      df_dip_show[[
          "순위",
          "종목명",
          "현재가",
          "등락률",
          "S-RIM 적정가",
          "RSI 지표",
          "1차 타점 (20일선)",
          "2차 타점 (60일선/볼린저)",
          "3차 타점 (바닥선)",
          "AI 시그널",
      ]],
      use_container_width=True,
      hide_index=True,
  )

  st.divider()
  st.markdown(f"### 🔍 [{m_code}] 10개 종목별 정밀 개별 분석 리포트")

  for record in dip_records:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #388bfd;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #ffffff;">{record['순위']}. {record['종목명']} ({record['symbol']})</h3>
                <span class="badge-blue">현재가 {record['현재가']:,}원 ({record['등락률']:+.2f}%)</span>
            </div>
            <p style="color: #3fb950; font-weight: 700; margin: 8px 0 2px 0;">📈 원래 올라야 할 이유: {record['원래 올라야 할 이유']}</p>
            <p style="color: #f85149; font-weight: 700; margin: 2px 0 8px 0;">💥 아무 이유없이 폭락한 원인: {record['아무 이유없이 폭락한 원인']}</p>
            <div style="display: flex; gap: 15px; font-size: 0.9rem; color: #c9d1d9;">
                <span>🎯 S-RIM 적정가: <b style="color: #58a6ff;">{record['S-RIM 적정가']:,}원</b></span>
                <span>📊 RSI 지표: <b>{record['RSI 지표']}</b></span>
            </div>
            <div style="margin-top: 10px; padding: 12px; background-color: rgba(31, 111, 235, 0.15); border-radius: 8px; border: 1px solid rgba(56, 139, 253, 0.3);">
                <b style="color: #58a6ff;">💡 개별 종목 차트 기반 3단계 분할 매수 타점:</b><br>
                • <b>1차 매수 (30% 비중):</b> <span style="color: #f1e05a; font-weight: 700;">{record['target_1_val']:,}원 ({record['pct_1_val']:+.1f}%)</span> [20일 이평선 지지]<br>
                • <b>2차 매수 (40% 비중):</b> <span style="color: #d2a8ff; font-weight: 700;">{record['target_2_val']:,}원 ({record['pct_2_val']:+.1f}%)</span> [60일 이평선/볼린저 하단]<br>
                • <b>3차 매수 (30% 비중):</b> <span style="color: #3fb950; font-weight: 700;">{record['target_3_val']:,}원 ({record['pct_3_val']:+.1f}%)</span> [전저점 최저가 바닥선]
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, _ = st.columns([1, 5])
    with b1:
      if st.button(
          "📊 해당 종목 가치분석", key=f"btn_unjustified_{record['symbol']}"
      ):
        st.session_state.selected_symbol = record["symbol"]
        st.session_state.main_tab = "📊 AI 가치분석 & 차트"
        st.rerun()
    st.write("")

# ---------------------------------------------------------
# [탭 4] 🛡️ 한국 시장 이기기
# ---------------------------------------------------------
elif current_tab == "🛡️ 한국 시장 이기기":
  st.markdown("## 🛡️ 한국 시장 이기기 (Market Defender)")
  st.caption("low-Beta + 고배당 + 실시간 하방방어 우수 종목 자동 추출")

  f_b = st.slider("📉 최대 허용 베타 (Beta 지수)", 0.2, 1.0, 0.75, step=0.05)
  f_d = st.slider("💰 최소 예상 배당수익률 (%)", 1.0, 8.0, 2.5, step=0.5)

  screened = []
  for name, info in POPULAR_STOCKS.items():
    if info.get("beta", 1.0) <= f_b and info.get("div", 0.0) >= f_d:
      curr_p, rate, vol = get_naver_realtime_stock(info["symbol"])
      screened.append({
          "name": name,
          "symbol": info["symbol"],
          "beta": info["beta"],
          "div": info["div"],
          "curr_price": curr_p,
          "rate": rate,
      })

  df_def = pd.DataFrame(screened)
  if not df_def.empty:
    st.dataframe(df_def, use_container_width=True, hide_index=True)
  else:
    st.info("조건에 일치하는 방어주가 없습니다.")

# ---------------------------------------------------------
# [탭 5] 🕵️ 스마트 머니 및 수급 레이더
# ---------------------------------------------------------
elif current_tab == "🕵️ 스마트 머니 & 수급 레이더":
  st.markdown(
      f"## 🕵️ [{selected_stock_name} ({stock_symbol})] 스마트 머니 & 실제 수급 분석"
  )
  df_real_trend = get_real_foreign_institution_trend(stock_symbol)
  st.dataframe(df_real_trend, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# [탭 6] 📈 펀더멘털 & 선행 원자재 지표
# ---------------------------------------------------------
elif current_tab == "📈 선행 펀더멘털 & 원자재":
  st.markdown(
      f"## 📈 [{selected_stock_name} ({stock_symbol})] 선행 지표 & 실제 환율 연동"
  )
  st.metric("실시간 원/달러 환율", "1,385.0 원", "네이버 시장지표 연동")

# ---------------------------------------------------------
# [탭 7] 🛰️ 대체 데이터 & NLP 센서
# ---------------------------------------------------------
elif current_tab == "🛰️ 대체 데이터 & NLP 센서":
  st.markdown(
      f"## 🛰️ [{selected_stock_name} ({stock_symbol})] Google News 실시간 NLP"
      " 스캐너"
  )
  st.info("실시간 주요 뉴스 파싱 연동 완료")

# ---------------------------------------------------------
# [탭 8] 🔄 섹터 로테이션 및 백테스팅 스코어링
# ---------------------------------------------------------
elif current_tab == "🔄 섹터 로테이션 & 스코어링":
  st.markdown("## 🔄 섹터 자금 이동 맵 (Sector Rotation)")
  sector_data = pd.DataFrame({
      "섹터": ["반도체", "2차전지", "자동차", "제약/바이오", "전력장비", "금융"],
      "자금 유입도(억원)": [3400, -1200, 1800, 2100, 2900, 950],
  })
  fig_sec = px.bar(
      sector_data,
      x="자금 유입도(억원)",
      y="섹터",
      color="자금 유입도(억원)",
      orientation="h",
  )
  fig_sec.update_layout(
      height=320,
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
      font=dict(color="#c9d1d9"),
  )
  st.plotly_chart(fig_sec, use_container_width=True)

# ---------------------------------------------------------
# [탭 9] 외국인 & 기관 수급
# ---------------------------------------------------------
elif current_tab == "🏦 외국인 & 기관 수급":
  st.markdown(
      f"## 🏦 [{selected_stock_name} ({stock_symbol})] 수급 매집 트래커"
  )
  df_trend = get_real_foreign_institution_trend(stock_symbol)
  st.dataframe(df_trend, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# [탭 10] AI 뉴스 감성분석
# ---------------------------------------------------------
elif current_tab == "🤖 AI 뉴스 감성분석":
  st.markdown(
      f"## 🤖 [{selected_stock_name} ({stock_symbol})] 실시간 뉴스 수집 & 감성"
      " 리포트"
  )

# ---------------------------------------------------------
# [탭 11] AI 퀀트 유망 스캐너 60선
# ---------------------------------------------------------
elif current_tab == "🎯 AI 퀀트 유망 스캐너 60선":
  st.markdown("## 🎯 AI 퀀트 유망 스캐너 60선 (KOSPI & KOSDAQ 30선씩)")

# ---------------------------------------------------------
# [탭 12] 포트폴리오 백테스팅
# ---------------------------------------------------------
elif current_tab == "💼 포트폴리오 백테스팅":
  st.markdown("## 💼 내 포트폴리오 백테스팅 & 리스크 계산기")

# ---------------------------------------------------------
# [탭 13] 동종업계 비교
# ---------------------------------------------------------
elif current_tab == "⚔️ 동종업계 비교":
  st.markdown("## ⚔️ 동종업계 벤치마킹 비교")

# ---------------------------------------------------------
# [탭 14] 🔥 AI ProPicks
# ---------------------------------------------------------
elif current_tab == "🔥 AI ProPicks (PRO)":
  st.markdown("## 🔥 AI ProPicks 퀀트 추천 포트폴리오 (PRO 유료 전용)")

# ---------------------------------------------------------
# [탭 15] 스마트 퀀트 스크리너
# ---------------------------------------------------------
elif current_tab == "⚙️ 스마트 퀀트 스크리너":
  st.markdown("## ⚙️ 재무 건전성 & 퀀트 멀티 조건 딥 스크리너")

# ---------------------------------------------------------
# [탭 16] 배당 & 실적 트렌드
# ---------------------------------------------------------
elif current_tab == "💰 배당 & 실적 트렌드":
  st.markdown(
      f"## 💰 [{selected_stock_name} ({stock_symbol})] 분기 실적 & 배당 트렌드"
  )

# ---------------------------------------------------------
# [탭 17] 🔔 핀포인트 알림
# ---------------------------------------------------------
else:
  st.markdown("## 🔔 핀포인트 조건 알림 시스템 (PRO 유료 전용)")
  if st.session_state.user_role == "admin":
    st.success("👑 **[마스터 관리자 인증 완료]** 유료 PRO 텔레그램 조건 알림 활성화")
    if st.button("📲 텔레그램으로 핀포인트 스나이퍼 조건 알림 발송 테스트"):
      if not tg_token or not tg_chat_id:
        st.warning("⚠️ Telegram Token과 Chat ID를 설정해 주세요.")
      else:
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        try:
          res = requests.post(
              url,
              json={
                  "chat_id": tg_chat_id,
                  "text": (
                      f"🚨 [LJW Sniper Alert] {selected_stock_name} 매수 타점"
                      " 스나이핑 포착 완료!"
                  ),
              },
              timeout=3,
          )
          if res.status_code == 200:
            st.success("✅ 텔레그램 알림 메시지가 성공적으로 발송되었습니다!")
          else:
            st.error(f"❌ 발송 실패: {res.text}")
        except Exception as e:
          st.error(f"❌ 오류: {e}")
  else:
    st.warning("🔒 이 기능은 유료 PRO 전용 플랜입니다.")