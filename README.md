# 🎪 전국 지역축제 분석 대시보드

전국문화축제표준데이터(한국관광공사)를 활용한 지역축제 분석 Streamlit 앱입니다.

## 주요 기능

- **핵심 지표**: 총 축제 수 · 지역 수 · 평균 개최 기간 · 최다 개최 월
- **사이드바 필터**: 지역(시·도) · 개최 월 · 축제명 검색
- **6개 분석 탭**
  - 📊 지역별 분석 (원/막대 그래프 전환)
  - 📅 월별 분석 (월별 분포 + 계절별 원그래프 + 기간 분포)
  - 📈 연도별 추이
  - 🏛️ 주관기관 순위
  - 🗺️ 축제 지도
  - 📋 데이터 표 (CSV 다운로드)

## 파일 구성

| 파일 | 설명 |
|------|------|
| `app.py` | Streamlit 앱 본체 |
| `전국문화축제표준데이터.csv` | 원본 데이터 (CP949 인코딩) |
| `requirements.txt` | 의존 패키지 |
| `.streamlit/config.toml` | 테마/서버 설정 |

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 위 파일들을 GitHub 저장소에 push
   (`app.py`, `requirements.txt`, `전국문화축제표준데이터.csv`, `.streamlit/config.toml`)
2. [share.streamlit.io](https://share.streamlit.io) 접속 → **New app**
3. 저장소 / 브랜치 선택, **Main file path** 를 `app.py` 로 지정
4. **Deploy** 클릭

> 데이터 출처: 공공데이터포털 · 한국관광공사 「전국문화축제표준데이터」
