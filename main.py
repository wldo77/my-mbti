# main.py
# 동네별 인구 피라미드
# Streamlit Cloud 배포용 앱

import re
import io

import pandas as pd
import streamlit as st
import plotly.graph_objects as go


# --------------------------------------------------
# 1. 앱 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏘️",
    layout="wide",
)

# 원본 CSV 압축 파일 주소
DATA_URL = (
    "https://raw.githubusercontent.com/first2022-cyber/"
    "contents/main/population_ts_yearly_gender.zip"
)

# 나이 라벨을 0세부터 100세 이상까지 순서대로 생성
AGE_LABELS = [f"{age}세" for age in range(101)]
AGE_LABELS[-1] = "100세 이상"


# --------------------------------------------------
# 2. 데이터 불러오기
# --------------------------------------------------
@st.cache_data(show_spinner="전국 인구 데이터를 불러오는 중입니다...")
def load_data():
    """압축된 CSV를 읽고 최신 연도 데이터만 반환합니다."""

    # URL에서 ZIP 파일을 읽습니다.
    # pandas는 ZIP 압축된 CSV도 바로 읽을 수 있습니다.
    df = pd.read_csv(DATA_URL, compression="zip")

    # 열 이름에 숨어 있을 수 있는 앞뒤 공백 제거
    df.columns = df.columns.astype(str).str.strip()

    # 지역 및 연도 열 확인
    required_columns = ["연도", "시도", "시군구", "동"]
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"필수 열을 찾을 수 없습니다: {missing_columns}"
        )

    # 연도 열을 숫자로 변환합니다.
    # 변환할 수 없는 값은 결측치로 처리합니다.
    df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
    df = df.dropna(subset=["연도"]).copy()
    df["연도"] = df["연도"].astype(int)

    if df.empty:
        raise ValueError("사용할 수 있는 연도 데이터가 없습니다.")

    # 데이터에 실제로 존재하는 가장 최신 연도를 선택합니다.
    latest_year = int(df["연도"].max())
    df = df.loc[df["연도"] == latest_year].copy()

    # 지역 이름의 결측치와 공백을 정리합니다.
    for col in ["시도", "시군구", "동"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 남_0세, 여_0세, ..., 남_100세 이상, 여_100세 이상 열 확인
    age_columns = []
    for age in AGE_LABELS:
        age_columns.extend([f"남_{age}", f"여_{age}"])

    missing_age_columns = [
        col for col in age_columns if col not in df.columns
    ]

    if missing_age_columns:
        raise ValueError(
            "일부 나이별 인구 열을 찾을 수 없습니다: "
            + ", ".join(missing_age_columns[:10])
        )

    # 인구 열을 숫자로 변환합니다.
    # 쉼표가 포함된 숫자 문자열도 처리합니다.
    for col in age_columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0)

    return df, latest_year


# --------------------------------------------------
# 3. 따뜻한 색상의 화면 디자인
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF9F3;
    }

    h1, h2, h3 {
        color: #704735;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #F0DDCE;
        padding: 16px;
        border-radius: 12px;
    }

    div[data-testid="stSelectbox"] label {
        color: #704735;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 4. 앱 제목과 설명
# --------------------------------------------------
st.title("🏘️ 동네별 인구 피라미드")
st.markdown(
    """
    우리 동네에는 연령대별로 얼마나 많은 사람이 살고 있을까요?

    시도, 시군구, 동을 차례로 선택하면 최신 연도의
    남녀별 인구 분포를 확인할 수 있습니다.
    """
)

st.divider()


# --------------------------------------------------
# 5. 데이터 불러오기 및 오류 안내
# --------------------------------------------------
try:
    df, latest_year = load_data()
except Exception as exc:
    st.error(
        "데이터를 불러오지 못했습니다. "
        "인터넷 연결, 원본 ZIP 주소, CSV의 열 이름을 확인해 주세요."
    )
    st.exception(exc)
    st.stop()

st.caption(f"📅 분석 기준 연도: **{latest_year}년**")


# --------------------------------------------------
# 6. 시도 → 시군구 → 동 선택
# --------------------------------------------------
st.subheader("📍 지역 선택")

col1, col2, col3 = st.columns(3)

# 시도 목록
sido_list = sorted(
    [value for value in df["시도"].unique() if value]
)

if not sido_list:
    st.warning("선택할 수 있는 시도 데이터가 없습니다.")
    st.stop()

with col1:
    selected_sido = st.selectbox(
        "① 시도",
        options=sido_list,
        key="selected_sido",
    )

# 선택한 시도에 속하는 시군구만 표시
sido_df = df.loc[df["시도"] == selected_sido]

sigungu_list = sorted(
    [value for value in sido_df["시군구"].unique() if value]
)

if not sigungu_list:
    st.warning("선택한 시도에 시군구 데이터가 없습니다.")
    st.stop()

with col2:
    selected_sigungu = st.selectbox(
        "② 시군구",
        options=sigungu_list,
        key="selected_sigungu",
    )

# 선택한 시도와 시군구에 속하는 동만 표시
sigungu_df = sido_df.loc[
    sido_df["시군구"] == selected_sigungu
]

dong_list = sorted(
    [value for value in sigungu_df["동"].unique() if value]
)

if not dong_list:
    st.warning("선택한 시군구에 동 데이터가 없습니다.")
    st.stop()

with col3:
    selected_dong = st.selectbox(
        "③ 동",
        options=dong_list,
        key="selected_dong",
    )


# --------------------------------------------------
# 7. 선택한 동네의 인구 데이터 추출
# --------------------------------------------------
selected_df = df.loc[
    (df["시도"] == selected_sido)
    & (df["시군구"] == selected_sigungu)
    & (df["동"] == selected_dong)
]

if selected_df.empty:
    st.warning("선택한 지역의 인구 데이터가 없습니다.")
    st.stop()

# 같은 지역에 여러 행이 있을 경우 나이별 인구를 합산합니다.
# 단, 원본 데이터에 중복 집계가 있는지 별도로 확인하는 것이 좋습니다.
age_data = {}

for age in AGE_LABELS:
    male_col = f"남_{age}"
    female_col = f"여_{age}"

    age_data[age] = {
        "남자": selected_df[male_col].sum(),
        "여자": selected_df[female_col].sum(),
    }

age_df = pd.DataFrame.from_dict(age_data, orient="index")
age_df.index.name = "나이"

# 그래프의 가로축에 사용할 남녀 인구
# 남자는 음수로 바꿔 왼쪽에 표시합니다.
age_df["남자_그래프"] = -age_df["남자"]
age_df["여자_그래프"] = age_df["여자"]


# --------------------------------------------------
# 8. 주요 인구 지표
# --------------------------------------------------
total_male = int(age_df["남자"].sum())
total_female = int(age_df["여자"].sum())
total_population = total_male + total_female

metric1, metric2, metric3 = st.columns(3)

metric1.metric("전체 인구", f"{total_population:,}명")
metric2.metric("남자 인구", f"{total_male:,}명")
metric3.metric("여자 인구", f"{total_female:,}명")

st.markdown(
    f"### {selected_sido} {selected_sigungu} {selected_dong}"
    f" 인구 피라미드"
)


# --------------------------------------------------
# 9. 인구 피라미드 그리기
# --------------------------------------------------
fig = go.Figure()

# 남자: 음수 값이므로 중앙의 0을 기준으로 왼쪽에 표시
fig.add_trace(
    go.Bar(
        name="남자",
        y=AGE_LABELS,
        x=age_df.loc[AGE_LABELS, "남자_그래프"],
        orientation="h",
        marker_color="#C96F50",
        customdata=age_df.loc[AGE_LABELS, "남자"],
        hovertemplate=(
            "나이: %{y}<br>"
            "남자 인구: %{customdata:,.0f}명"
            "<extra></extra>"
        ),
    )
)

# 여자: 양수 값이므로 중앙의 0을 기준으로 오른쪽에 표시
fig.add_trace(
    go.Bar(
        name="여자",
        y=AGE_LABELS,
        x=age_df.loc[AGE_LABELS, "여자_그래프"],
        orientation="h",
        marker_color="#E9AD8B",
        hovertemplate=(
            "나이: %{y}<br>"
            "여자 인구: %{x:,.0f}명"
            "<extra></extra>"
        ),
    )
)

# 가로축 눈금은 남자 쪽도 양수 인구처럼 보이게 표시합니다.
max_population = max(
    float(age_df["남자"].max()),
    float(age_df["여자"].max()),
    1.0,
)

# 좌우 축 범위를 대칭으로 설정하여 비교하기 쉽게 만듭니다.
axis_limit = max_population * 1.12

tick_step = max(1, int(axis_limit / 5))
tick_limit = ((int(axis_limit) + tick_step - 1) // tick_step) * tick_step

tick_values_positive = list(range(0, tick_limit + 1, tick_step))
tick_values = [-value for value in tick_values_positive[:0:-1]]
tick_values += tick_values_positive

tick_text = [f"{abs(value):,}" for value in tick_values]

fig.update_layout(
    template="plotly_white",
    barmode="overlay",
    height=1050,
    margin=dict(l=80, r=40, t=40, b=70),
    plot_bgcolor="#FFFCF8",
    paper_bgcolor="#FFFCF8",
    font=dict(
        family="Arial, sans-serif",
        size=12,
        color="#5E473B",
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="center",
        x=0.5,
        title_text="성별",
    ),
    xaxis=dict(
        title="인구 (명)",
        range=[-axis_limit, axis_limit],
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_text,
        zeroline=True,
        zerolinecolor="#8C7668",
        zerolinewidth=2,
        showgrid=True,
        gridcolor="#F0E5DC",
    ),
    yaxis=dict(
        title="나이",
        type="category",

        # 핵심: 나이 라벨을 0세부터 100세 이상까지 직접 고정합니다.
        # categoryorder='array'와 categoryarray를 함께 지정합니다.
        # Plotly의 범주축은 배열의 마지막 항목이 위쪽에 오므로
        # 아래 0세, 위 100세 이상 순서를 명확히 지정합니다.
        categoryorder="array",
        categoryarray=AGE_LABELS,

        # 축 전체를 뒤집는 autorange='reversed'는 사용하지 않습니다.
        showgrid=True,
        gridcolor="#F0E5DC",
        tickfont=dict(size=10),
    ),
    bargap=0.12,
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 10. 나이 축 순서 확인
# --------------------------------------------------
# AGE_LABELS가 0세부터 100세 이상까지 순서대로 생성되었고,
# y축 categoryarray에도 같은 목록을 넣었으므로
# 아래쪽은 0세, 위쪽은 100세 이상이 됩니다.
st.caption(
    "축 순서 확인: 맨 아래 0세 → 맨 위 100세 이상. "
    "남자는 왼쪽, 여자는 오른쪽입니다."
)


# --------------------------------------------------
# 11. 나이별 인구 표
# --------------------------------------------------
with st.expander("📋 나이별 남녀 인구 표 보기"):
    display_df = age_df[["남자", "여자"]].copy()
    display_df["합계"] = display_df["남자"] + display_df["여자"]

    # 화면에 표시할 숫자를 천 단위 쉼표 형식으로 정리합니다.
    display_df = display_df.astype(int).map(
        lambda value: f"{value:,}"
    )
    display_df.index.name = "나이"

    st.dataframe(
        display_df,
        use_container_width=True,
    )

    # 표 데이터를 CSV 파일로 내려받을 수 있습니다.
    download_df = age_df[["남자", "여자"]].copy()
    download_df["합계"] = (
        download_df["남자"] + download_df["여자"]
    )
    download_df.index.name = "나이"

    csv_data = download_df.to_csv(
        index=True,
        encoding="utf-8-sig",
    )

    st.download_button(
        label="📥 나이별 인구 CSV 다운로드",
        data=csv_data,
        file_name=(
            f"인구피라미드_{latest_year}_"
            f"{selected_sido}_{selected_sigungu}_{selected_dong}.csv"
        ),
        mime="text/csv",
    )

st.divider()

st.caption(
    "데이터 출처: "
    "first2022-cyber/contents GitHub 저장소의 "
    "population_ts_yearly_gender.zip"
)
