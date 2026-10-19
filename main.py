
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================================================
# 1. 페이지 기본 설정
# =========================================================
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏡",
    layout="wide"
)

# 따뜻한 크림색과 노란색 테마를 위한 CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF9EC;
    }

    h1, h2, h3 {
        color: #75552D;
    }

    div[data-testid="stSelectbox"] label {
        color: #75552D;
        font-weight: bold;
        font-size: 17px;
    }

    div[data-testid="stMetric"] {
        background-color: #FFF0C2;
        padding: 15px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏡 동네별 인구 피라미드")
st.markdown(
    "우리 동네에는 연령대별로 남자와 여자가 얼마나 살고 있을까요?"
)
st.divider()


# =========================================================
# 2. 데이터 불러오기
# =========================================================
# ZIP 주소를 먼저 사용하고, 읽기에 실패하면 CSV 주소를 시도합니다.
DATA_URLS = [
    (
        "https://raw.githubusercontent.com/"
        "first2022-cyber/contents/main/"
        "population_ts_yearly_gender.zip"
    ),
    (
        "https://raw.githubusercontent.com/"
        "wldo77/my-mbti/main/"
        "population_ts_yearly_gender.csv"
    ),
]


@st.cache_data(show_spinner="전국 인구 데이터를 불러오는 중입니다...")
def load_data():
    """인터넷에서 데이터를 읽고 열 이름과 자료형을 정리합니다."""
    errors = []

    for url in DATA_URLS:
        try:
            # ZIP 파일은 압축을 자동으로 해제하도록 지정합니다.
            # CSV 파일에도 같은 함수를 사용할 수 있습니다.
            compression = "zip" if url.endswith(".zip") else "infer"

            data = pd.read_csv(
                url,
                compression=compression,
                encoding="utf-8-sig",
                low_memory=False
            )

            # 열 이름 앞뒤의 공백 제거
            data.columns = data.columns.astype(str).str.strip()

            # 필수 지역 정보 열이 있는지 확인
            required = ["연도", "시도", "시군구", "동"]
            missing = [col for col in required if col not in data.columns]

            if missing:
                raise ValueError(
                    f"필수 열이 없습니다: {', '.join(missing)}"
                )

            # 연도 열을 숫자로 변환
            data["연도"] = pd.to_numeric(
                data["연도"], errors="coerce"
            )

            data = data.dropna(subset=["연도"]).copy()
            data["연도"] = data["연도"].astype(int)

            # 지역 이름은 문자열로 통일
            for col in ["시도", "시군구", "동"]:
                data[col] = data[col].fillna("").astype(str).str.strip()

            # 남자·여자 연령별 인구 열 찾기
            age_columns = [
                col for col in data.columns
                if (
                    col.startswith("남_") or col.startswith("여_")
                )
                and (
                    col.endswith("세") or col.endswith("세 이상")
                )
            ]

            if not age_columns:
                raise ValueError(
                    "남_0세, 여_0세 형식의 인구 열을 찾지 못했습니다."
                )

            # 인구 열은 숫자로 변환합니다.
            for col in age_columns:
                data[col] = pd.to_numeric(
                    data[col].astype(str).str.replace(",", "", regex=False),
                    errors="coerce"
                ).fillna(0)

            return data

        except Exception as e:
            errors.append(f"{url}\n오류: {e}")

    raise RuntimeError(
        "모든 데이터 주소에서 읽기에 실패했습니다.\n\n"
        + "\n\n".join(errors)
    )


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(e))
    st.info(
        "데이터 주소가 공개되어 있는지, 파일 형식과 열 이름이 "
        "올바른지 확인해 주세요."
    )
    st.stop()


# =========================================================
# 3. 가장 최신 연도 데이터만 선택
# =========================================================
latest_year = int(df["연도"].max())
latest_df = df[df["연도"] == latest_year].copy()

st.success(f"📅 현재 표시하는 데이터: {latest_year}년")


# =========================================================
# 4. 나이 라벨을 0세부터 100세 이상까지 순서대로 만들기
# =========================================================
# 숫자를 정렬하는 대신, 원하는 순서의 라벨 목록을 직접 만듭니다.
age_labels = [f"{age}세" for age in range(101)]
age_labels[-1] = "100세 이상"

# 열 이름이 실제로 존재하는지 확인하면서 나이별 열 목록 구성
male_columns = {}
female_columns = {}

for age in range(101):
    label = "100세 이상" if age == 100 else f"{age}세"

    male_col = f"남_{label}"
    female_col = f"여_{label}"

    if male_col in latest_df.columns:
        male_columns[label] = male_col

    if female_col in latest_df.columns:
        female_columns[label] = female_col

if not male_columns or not female_columns:
    st.error(
        "남자 또는 여자 인구 열을 충분히 찾지 못했습니다. "
        "데이터 열 이름을 확인해 주세요."
    )
    st.stop()


# =========================================================
# 5. 지역 선택 드롭다운 3개
# =========================================================
st.subheader("📍 우리 동네 선택하기")

col1, col2, col3 = st.columns(3)

# 첫 번째: 시도
sido_list = sorted(latest_df["시도"].unique().tolist())

with col1:
    selected_sido = st.selectbox(
        "① 시도",
        sido_list,
        key="sido"
    )

# 선택한 시도에 속한 시군구만 표시
sido_df = latest_df[latest_df["시도"] == selected_sido]
sigungu_list = sorted(sido_df["시군구"].unique().tolist())

with col2:
    selected_sigungu = st.selectbox(
        "② 시군구",
        sigungu_list,
        key="sigungu"
    )

# 선택한 시도와 시군구에 속한 동만 표시
sigungu_df = sido_df[
    sido_df["시군구"] == selected_sigungu
]
dong_list = sorted(sigungu_df["동"].unique().tolist())

with col3:
    selected_dong = st.selectbox(
        "③ 동",
        dong_list,
        key="dong"
    )


# =========================================================
# 6. 선택한 동네의 인구 데이터 추출
# =========================================================
selected_df = latest_df[
    (latest_df["시도"] == selected_sido)
    & (latest_df["시군구"] == selected_sigungu)
    & (latest_df["동"] == selected_dong)
]

if selected_df.empty:
    st.warning("선택한 지역의 데이터가 없습니다.")
    st.stop()

# 같은 지역의 행이 여러 개라면 연령별 인구를 합산합니다.
# 누락된 연령 열은 0명으로 처리합니다.
row = selected_df.iloc[0]

male_population = []
female_population = []

for label in age_labels:
    male_col = male_columns.get(label)
    female_col = female_columns.get(label)

    if male_col is not None:
        male_value = selected_df[male_col].sum()
    else:
        male_value = 0

    if female_col is not None:
        female_value = selected_df[female_col].sum()
    else:
        female_value = 0

    male_population.append(int(male_value))
    female_population.append(int(female_value))


# =========================================================
# 7. 전체 인구 요약
# =========================================================
total_male = sum(male_population)
total_female = sum(female_population)
total_population = total_male + total_female

st.markdown(
    f"### 📌 {selected_sido} {selected_sigungu} {selected_dong}"
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric("전체 인구", f"{total_population:,}명")
metric2.metric("남자 인구", f"{total_male:,}명")
metric3.metric("여자 인구", f"{total_female:,}명")


# =========================================================
# 8. 인구 피라미드 그리기
# =========================================================
# 남자 인구는 음수로 바꾸어 왼쪽에 표시합니다.
male_negative = [-value for value in male_population]

fig = go.Figure()

# 남자: 왼쪽
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_negative,
        name="남자",
        orientation="h",
        marker_color="#78A9D1",
        hovertemplate=(
            "나이: %{y}<br>"
            "남자 인구: %{customdata:,}명"
            "<extra></extra>"
        ),
        customdata=male_population
    )
)

# 여자: 오른쪽
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_population,
        name="여자",
        orientation="h",
        marker_color="#E99A9A",
        hovertemplate=(
            "나이: %{y}<br>"
            "여자 인구: %{x:,}명"
            "<extra></extra>"
        )
    )
)

# 가장 큰 인구를 기준으로 좌우 축 범위를 대칭으로 설정합니다.
max_population = max(
    max(male_population, default=0),
    max(female_population, default=0),
    1
)

axis_limit = max_population * 1.12

fig.update_layout(
    title={
        "text": f"{selected_dong} 연령별 인구 피라미드 ({latest_year}년)",
        "x": 0.5,
        "xanchor": "center"
    },
    barmode="overlay",
    bargap=0.12,
    height=1000,
    paper_bgcolor="#FFF9EC",
    plot_bgcolor="#FFFDF7",
    font=dict(
        family="Malgun Gothic, AppleGothic, sans-serif",
        size=12,
        color="#5B4630"
    ),
    xaxis=dict(
        title="인구수 (명)",
        range=[-axis_limit, axis_limit],
        tickmode="array",
        tickvals=[
            -axis_limit,
            -axis_limit * 0.5,
            0,
            axis_limit * 0.5,
            axis_limit
        ],
        ticktext=[
            f"{axis_limit:,.0f}",
            f"{axis_limit * 0.5:,.0f}",
            "0",
            f"{axis_limit * 0.5:,.0f}",
            f"{axis_limit:,.0f}"
        ],
        zeroline=True,
        zerolinecolor="#8C7853",
        zerolinewidth=2,
        gridcolor="#E9DFC9"
    ),

    # 중요: y축에 라벨을 직접 지정합니다.
    # categoryarray는 0세부터 100세 이상까지의 순서를 그대로 유지합니다.
    # autorange='normal'을 사용해 0세가 아래, 100세 이상이 위에 옵니다.
    yaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=age_labels,
        autorange="normal",
        tickmode="array",
        tickvals=age_labels,
        ticktext=age_labels,
        showgrid=False
    ),

    legend=dict(
        title="성별",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    margin=dict(l=75, r=35, t=100, b=70)
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "왼쪽은 남자, 오른쪽은 여자입니다. "
    "막대가 길수록 해당 나이의 인구가 많습니다."
)


# =========================================================
# 9. 나이 축 순서 확인
# =========================================================
# 그래프에 실제로 적용한 나이 라벨의 첫 항목과 마지막 항목을 확인합니다.
st.markdown("#### 🔎 나이 축 순서 확인")

check_col1, check_col2 = st.columns(2)

with check_col1:
    st.info(f"그래프 맨 아래: **{age_labels[0]}**")

with check_col2:
    st.info(f"그래프 맨 위: **{age_labels[-1]}**")

# 데이터 표를 펼쳐서 확인할 수 있습니다.
with st.expander("📋 선택한 동네의 연령별 인구 표 보기"):
    population_table = pd.DataFrame({
        "나이": age_labels,
        "남자 인구": male_population,
        "여자 인구": female_population
    })

    st.dataframe(
        population_table,
        hide_index=True,
        use_container_width=True
    )

st.markdown("---")
st.caption("데이터 출처: 지정된 공개 GitHub 데이터 파일")
