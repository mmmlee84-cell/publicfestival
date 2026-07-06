# -*- coding: utf-8 -*-
"""
전국 문화축제 표준데이터 - 지역축제 분석 대시보드
데이터 출처: 한국관광공사 (전국문화축제표준데이터.csv)
실행:  streamlit run app.py
"""

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# 기본 설정
# ----------------------------------------------------------------------------
st.set_page_config(page_title="전국 지역축제 분석", page_icon="🎪", layout="wide")

CSV_PATH = Path(__file__).parent / "전국문화축제표준데이터.csv"

# 광역시·도 표준 이름 (주소 앞부분 매칭용)
SIDO_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충청북": "충청북도",
    "충남": "충청남도",
    "충청남": "충청남도",
    "전북": "전북특별자치도",
    "전라북": "전북특별자치도",
    "전남": "전라남도",
    "전라남": "전라남도",
    "경북": "경상북도",
    "경상북": "경상북도",
    "경남": "경상남도",
    "경상남": "경상남도",
    "제주": "제주특별자치도",
}


# ----------------------------------------------------------------------------
# 데이터 로딩 & 전처리
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    # 표준데이터는 CP949(EUC-KR) 인코딩이 일반적이며, 안 되면 UTF-8로 재시도
    try:
        df = pd.read_csv(path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8")

    # 날짜 변환
    df["시작일"] = pd.to_datetime(df["축제시작일자"], errors="coerce")
    df["종료일"] = pd.to_datetime(df["축제종료일자"], errors="coerce")

    # 축제 기간(일)
    df["기간(일)"] = (df["종료일"] - df["시작일"]).dt.days + 1

    # 개최 연도 / 월
    df["연도"] = df["시작일"].dt.year
    df["월"] = df["시작일"].dt.month

    # 좌표 숫자화
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    # 지역(시·도) 추출: 도로명주소 > 지번주소 > 소재지 컬럼 순으로 시도
    df["시도"] = df.apply(_extract_sido, axis=1)

    return df


def _extract_sido(row: pd.Series) -> str:
    """주소 문자열에서 광역시·도 이름을 추출한다."""
    for col in ("소재지도로명주소", "소재지지번주소", "주최기관명", "주관기관명"):
        text = str(row.get(col, "") or "").strip()
        if not text or text == "nan":
            continue
        head = text.replace(" ", "")[:4]
        for key, full in SIDO_MAP.items():
            if head.startswith(key):
                return full
    return "기타/미상"


# ----------------------------------------------------------------------------
# 앱 UI
# ----------------------------------------------------------------------------
if not CSV_PATH.exists():
    st.error(f"데이터 파일을 찾을 수 없습니다: {CSV_PATH}")
    st.stop()

df = load_data(CSV_PATH)

st.title("🎪 전국 지역축제 분석 대시보드")
st.caption("데이터: 전국문화축제표준데이터 (한국관광공사)")

# --- 사이드바 필터 ---------------------------------------------------------
st.sidebar.header("🔎 필터")

sido_options = sorted(df["시도"].dropna().unique().tolist())
sel_sido = st.sidebar.multiselect("지역(시·도) 선택", sido_options, default=[])

month_options = sorted([int(m) for m in df["월"].dropna().unique()])
sel_month = st.sidebar.multiselect(
    "개최 월 선택", month_options, default=[], format_func=lambda m: f"{m}월"
)

keyword = st.sidebar.text_input("축제명 검색", "")

# 필터 적용
fdf = df.copy()
if sel_sido:
    fdf = fdf[fdf["시도"].isin(sel_sido)]
if sel_month:
    fdf = fdf[fdf["월"].isin(sel_month)]
if keyword.strip():
    fdf = fdf[fdf["축제명"].str.contains(keyword.strip(), case=False, na=False)]

# --- 핵심 지표 -------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 축제 수", f"{len(fdf):,} 개")
c2.metric("지역(시·도) 수", f"{fdf['시도'].nunique():,} 개")
avg_days = fdf["기간(일)"].dropna()
c3.metric("평균 개최 기간", f"{avg_days.mean():.1f} 일" if len(avg_days) else "-")
peak_month = fdf["월"].mode()
c4.metric("최다 개최 월", f"{int(peak_month.iloc[0])}월" if len(peak_month) else "-")

st.divider()

# --- 탭 구성 ---------------------------------------------------------------
tab1, tab2, tab5, tab6, tab3, tab4 = st.tabs(
    [
        "📊 지역별 분석",
        "📅 월별 분석",
        "📈 연도별 추이",
        "🏛️ 주관기관 순위",
        "🗺️ 축제 지도",
        "📋 데이터 표",
    ]
)

# 탭 1: 지역별
with tab1:
    st.subheader("지역(시·도)별 축제 개최 현황")
    region_cnt = (
        fdf["시도"].value_counts().rename_axis("시도").reset_index(name="축제수")
    )
    if region_cnt.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        chart_type = st.radio(
            "그래프 종류",
            ["원그래프", "막대그래프"],
            horizontal=True,
            key="region_chart",
        )
        col_a, col_b = st.columns([2, 1])
        with col_a:
            if chart_type == "원그래프":
                fig = px.pie(
                    region_cnt,
                    names="시도",
                    values="축제수",
                    title=f"시·도별 축제 비중 (총 {len(region_cnt)}개 지역)",
                    hole=0.35,  # 도넛형으로 가독성 향상
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    textfont_size=12,
                )
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", x=1.0, y=0.5),
                    margin=dict(t=50, b=20, l=20, r=20),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(region_cnt.set_index("시도")["축제수"])
        with col_b:
            st.dataframe(region_cnt, use_container_width=True, hide_index=True)

        top = region_cnt.iloc[0]
        st.success(
            f"가장 많은 축제가 열리는 지역은 **{top['시도']}** "
            f"({int(top['축제수'])}개) 입니다."
        )

# 탭 2: 월별
with tab2:
    st.subheader("월별 축제 개최 분포")
    month_cnt = (
        fdf.dropna(subset=["월"])
        .assign(월=lambda d: d["월"].astype(int))
        .groupby("월")
        .size()
        .reindex(range(1, 13), fill_value=0)
    )
    month_cnt.index = [f"{m}월" for m in month_cnt.index]
    st.bar_chart(month_cnt)

    st.subheader("계절별 축제 현황")

    def _season(m):
        if m in (3, 4, 5):
            return "봄 (3~5월)"
        if m in (6, 7, 8):
            return "여름 (6~8월)"
        if m in (9, 10, 11):
            return "가을 (9~11월)"
        return "겨울 (12~2월)"

    months = fdf["월"].dropna().astype(int)
    if len(months):
        season_order = ["봄 (3~5월)", "여름 (6~8월)", "가을 (9~11월)", "겨울 (12~2월)"]
        season_colors = {
            "봄 (3~5월)": "#7FC97F",
            "여름 (6~8월)": "#F4A259",
            "가을 (9~11월)": "#D9534F",
            "겨울 (12~2월)": "#5B9BD5",
        }
        season_cnt = (
            months.map(_season)
            .value_counts()
            .reindex(season_order, fill_value=0)
            .rename_axis("계절")
            .reset_index(name="축제수")
        )
        col_p, col_t = st.columns([2, 1])
        with col_p:
            fig_season = px.pie(
                season_cnt,
                names="계절",
                values="축제수",
                title="계절별 축제 비중",
                hole=0.35,
                category_orders={"계절": season_order},
                color="계절",
                color_discrete_map=season_colors,
            )
            fig_season.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont_size=13,
                sort=False,
            )
            fig_season.update_layout(margin=dict(t=50, b=20, l=20, r=20))
            st.plotly_chart(fig_season, use_container_width=True)
        with col_t:
            st.dataframe(season_cnt, use_container_width=True, hide_index=True)

        top_season = season_cnt.sort_values("축제수", ascending=False).iloc[0]
        st.success(
            f"축제가 가장 많이 열리는 계절은 **{top_season['계절']}** "
            f"({int(top_season['축제수'])}개) 입니다."
        )
    else:
        st.info("월 데이터가 없습니다.")

    st.subheader("축제 기간(일) 분포")
    dur = fdf["기간(일)"].dropna()
    dur = dur[(dur > 0) & (dur <= 60)]  # 이상치 제거
    if len(dur):
        dur_cnt = dur.astype(int).value_counts().sort_index()
        dur_cnt.index = [f"{d}일" for d in dur_cnt.index]
        st.bar_chart(dur_cnt)
    else:
        st.info("기간 데이터가 없습니다.")

# 탭 5: 연도별 추이
with tab5:
    st.subheader("연도별 축제 개최 추이")
    year_cnt = (
        fdf.dropna(subset=["연도"])
        .assign(연도=lambda d: d["연도"].astype(int))
        .groupby("연도")
        .size()
    )
    if year_cnt.empty:
        st.info("연도 데이터가 없습니다.")
    else:
        # 전 구간 연도를 채워 선그래프가 끊기지 않도록 처리
        full_idx = range(int(year_cnt.index.min()), int(year_cnt.index.max()) + 1)
        year_cnt = year_cnt.reindex(full_idx, fill_value=0)
        year_cnt.index = [f"{y}년" for y in year_cnt.index]
        st.line_chart(year_cnt)
        st.dataframe(
            year_cnt.rename_axis("연도").reset_index(name="축제수"),
            use_container_width=True,
            hide_index=True,
        )

        # 전년 대비 증감
        vals = year_cnt.values
        if len(vals) >= 2 and vals[-2] > 0:
            growth = (vals[-1] - vals[-2]) / vals[-2] * 100
            arrow = "증가" if growth >= 0 else "감소"
            st.info(
                f"최근 연도는 전년 대비 축제 수가 **{abs(growth):.1f}% {arrow}**했습니다. "
                "(개최 예정 데이터가 포함되어 최신 연도 수치는 변동될 수 있습니다.)"
            )

# 탭 6: 주관기관 순위
with tab6:
    st.subheader("주관기관별 축제 개최 순위")
    top_n = st.slider("표시할 상위 기관 수", 5, 30, 15, key="top_org")
    org_cnt = (
        fdf["주관기관명"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .head(top_n)
        .rename_axis("주관기관명")
        .reset_index(name="축제수")
    )
    if org_cnt.empty:
        st.info("주관기관 데이터가 없습니다.")
    else:
        st.bar_chart(org_cnt.set_index("주관기관명")["축제수"])
        st.dataframe(org_cnt, use_container_width=True, hide_index=True)
        st.caption(f"필터 결과 내 주관기관 종류: {fdf['주관기관명'].nunique():,}개")

# 탭 3: 지도
with tab3:
    st.subheader("축제 개최지 지도")
    map_df = fdf.dropna(subset=["위도", "경도"]).rename(
        columns={"위도": "latitude", "경도": "longitude"}
    )
    # 대한민국 좌표 범위 내로 필터
    map_df = map_df[
        map_df["latitude"].between(33, 39) & map_df["longitude"].between(124, 132)
    ]
    if len(map_df):
        st.map(map_df[["latitude", "longitude"]])
        st.caption(f"지도 표시 축제: {len(map_df):,}개 (좌표 정보 보유 건)")
    else:
        st.info("표시할 좌표 데이터가 없습니다.")

# 탭 4: 데이터 표
with tab4:
    st.subheader("축제 상세 데이터")
    show_cols = [
        "축제명",
        "시도",
        "개최장소",
        "축제시작일자",
        "축제종료일자",
        "기간(일)",
        "주관기관명",
        "전화번호",
        "홈페이지주소",
    ]
    show_cols = [c for c in show_cols if c in fdf.columns]
    st.dataframe(
        fdf[show_cols].sort_values("축제시작일자"),
        use_container_width=True,
        hide_index=True,
    )

    # 다운로드 버튼
    csv_bytes = fdf[show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 현재 결과 CSV 다운로드",
        data=csv_bytes,
        file_name="지역축제_분석결과.csv",
        mime="text/csv",
    )
