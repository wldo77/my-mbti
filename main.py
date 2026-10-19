
import json
import re
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="전국 고령화 단계구분도",
    page_icon="🗺️",
    layout="wide",
)

POPULATION_URL = (
    "https://raw.githubusercontent.com/"
    "first2022-cyber/contents/main/"
    "population_ts_yearly_gender.zip"
)

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "first2022-cyber/contents/main/"
    "sigungu_kr.geojson"
)

st.title("🗺️ 전국 고령화 단계구분도")
st.caption(
    "2026년 6월 기준 · 시군구별 65세 이상 인구 비율"
)

st.markdown(
    """
    시군구별 고령화율을 지도에서 비교해 보세요.
    색이 진할수록 65세 이상 인구 비율이 높습니다.
    """
)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
@st.cache_data(ttl=3600)
def load_population():
    response = requests.get(POPULATION_URL, timeout=60)
    response.raise_for_status()

    # URL에서 받은 ZIP 파일을 메모리에서 바로 읽기
    df = pd.read_csv(
        BytesIO(response.content),
        compression="zip",
        dtype={"코드": "string"},
    )

    required = {"연도", "시도", "시군구", "동", "코드"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"인구 데이터에 필요한 열이 없습니다: {sorted(missing)}"
        )

    df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
    df = df.loc[df["연도"] == 2026].copy()

    if df.empty:
        raise ValueError("인구 데이터에 2026년 자료가 없습니다.")

    df["코드"] = (
        df["코드"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(10)
    )

    # 시군구 코드: 동 코드의 앞 5자리
    df["시군구코드"] = df["코드"].str[:5]

    # 계_로 시작하는 열만 사용 (남_·여_ 열 제외)
    total_cols = [
        col for col in df.columns
        if col.startswith("계_")
    ]

    if not total_cols:
        raise ValueError("'계_'로 시작하는 인구 열이 없습니다.")

    # 65세 이상 열: 65세부터 100세 이상까지
    elderly_cols = [
        col for col in total_cols
        if re.match(r"^계_(?:[6-9]\d|100)세(?:\s*이상)?$", col)
        and int(re.search(r"\d+", col).group()) >= 65
    ]

    if "계_65세" not in elderly_cols:
        raise ValueError(
            "'계_65세' 열을 찾을 수 없습니다. 실제 열 이름을 확인하세요."
        )

    def to_number(series):
        return pd.to_numeric(
            series.astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0)

    # 각 연령별 열을 숫자로 변환
    for col in set(total_cols):
        df[col] = to_number(df[col])

    df["전체인구"] = df[total_cols].sum(axis=1)
    df["고령인구"] = df[elderly_cols].sum(axis=1)

    # 읍·면·동 자료를 시군구 단위로 합산
    grouped = (
        df.groupby("시군구코드", as_index=False)
        .agg(
            전체인구=("전체인구", "sum"),
            고령인구=("고령인구", "sum"),
        )
    )

    # 인구 비율은 시군구 인구 합계를 기준으로 계산
    grouped["고령화율"] = np.where(
        grouped["전체인구"] > 0,
        grouped["고령인구"] / grouped["전체인구"] * 100,
        np.nan,
    )

    return grouped


@st.cache_data(ttl=3600)
def load_geojson():
    response = requests.get(GEOJSON_URL, timeout=60)
    response.raise_for_status()
    geojson = response.json()

    if "features" not in geojson:
        raise ValueError(
            "GeoJSON에 features 항목이 없습니다."
        )

    # 코드 속성을 문자열로 통일
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        code = props.get("코드")

        if code is not None:
            code = str(code).strip()
            if code.endswith(".0"):
                code = code[:-2]
            props["코드"] = code.zfill(5)

    return geojson


# --------------------------------------------------
# 데이터 처리 및 코드 기준 결합
# --------------------------------------------------
try:
    with st.spinner("인구 데이터와 행정구역 경계를 불러오는 중..."):
        population = load_population()
        geojson = load_geojson()

    # 지도 코드와 인구 데이터 코드의 자료형 및 형식 통일
    population["시군구코드"] = (
        population["시군구코드"]
        .astype("string")
        .str.zfill(5)
    )

    # 이름이 아닌 코드로 정확히 연결
    geo_codes = {
        feature["properties"].get("코드")
        for feature in geojson["features"]
    }

    map_df = population[
        population["시군구코드"].isin(geo_codes)
    ].copy()

    # 지도에 표시할 지역 이름은 GeoJSON 속성에서 가져옴
    geo_names = {
        feature["properties"]["코드"]:
        feature["properties"].get("시군구", "")
        for feature in geojson["features"]
    }

    map_df["시군구"] = map_df["시군구코드"].map(geo_names)

    # 유효한 고령화율이 있는 지역만 지도에 표시
    map_df = map_df.dropna(subset=["고령화율"])
    map_df = map_df[map_df["전체인구"] > 0].copy()

    if map_df.empty:
        st.error(
            "인구 데이터와 지도 경계가 일치하지 않습니다. "
            "두 파일의 코드 형식을 확인해 주세요."
        )
        st.stop()

    # 단계 구분 색상: 고령화율이 높을수록 진한 색
    min_rate = float(map_df["고령화율"].min())
    max_rate = float(map_df["고령화율"].max())

    if min_rate == max_rate:
        bins = [min_rate - 0.001, max_rate + 0.001]
        labels = [f"{min_rate:.1f}%"]
    else:
        # 실제 데이터 범위를 5단계로 구분
        bins = np.linspace(min_rate, max_rate, 6)
        bins[-1] += 1e-9
        labels = [
            f"{bins[i]:.1f}~{bins[i + 1]:.1f}%"
            for i in range(5)
        ]

    map_df["고령화단계"] = pd.cut(
        map_df["고령화율"],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    # 지도 데이터의 코드 순서에 맞춰 GeoJSON을 구성
    # 이름이 아니라 코드로 매칭하므로 동명 지역도 혼동하지 않음
    map_df["코드"] = map_df["시군구코드"].astype(str)

    # 전국 시군구를 모두 유지하되, 인구 데이터가 없는 지역은
    # 지도에서 회색으로 표시
    rate_by_code = map_df.set_index("코드")["고령화율"].to_dict()
    name_by_code = map_df.set_index("코드")["시군구"].to_dict()

    for feature in geojson["features"]:
        props = feature["properties"]
        code = props.get("코드")

        props["고령화율"] = rate_by_code.get(code)
        props["표시이름"] = name_by_code.get(
            code, props.get("시군구", "")
        )

    # --------------------------------------------------
    # 요약 지표
    # --------------------------------------------------
    c1, c2, c3 = st.columns(3)

    c1.metric("지도에 표시된 시군구", f"{len(map_df):,}개")
    c2.metric("전국 시군구 평균 고령화율", f"{map_df['고령화율'].mean():.2f}%")

    highest = map_df.loc[map_df["고령화율"].idxmax()]
    c3.metric(
        "고령화율이 가장 높은 시군구",
        str(highest["시군구"]),
        f"{highest['고령화율']:.2f}%",
    )

    # --------------------------------------------------
    # Plotly 단계구분도
    # --------------------------------------------------
    # Plotly choropleth는 지도 타일 없이 GeoJSON 경계만 표시
    # 범례는 고령화율 실제 수치에 대응하도록 연속형으로 구성
    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="코드",
        featureidkey="properties.코드",
        color="고령화율",
        color_continuous_scale=[
            [0.0, "#fff7bc"],
            [0.25, "#fec44f"],
            [0.5, "#fe9929"],
            [0.75, "#ec7014"],
            [1.0, "#993404"],
        ],
        range_color=(min_rate, max_rate) if min_rate != max_rate else None,
        hover_name="시군구",
        hover_data={
            "코드": False,
            "고령화율": ":.2f",
        },
        labels={"고령화율": "고령화율(%)"},
        title="2026년 시군구별 65세 이상 인구 비율",
    )

    fig.update_traces(
        marker_line_color="#666666",
        marker_line_width=0.45,
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "고령화율: %{z:.2f}%"
            "<extra></extra>"
        ),
        z=map_df["고령화율"],
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        height=760,
        margin=dict(l=0, r=0, t=65, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="고령화율(%)",
            ticksuffix="%",
            thickness=18,
            len=0.72,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "자료: 제공된 2026년 인구 CSV 및 시군구 GeoJSON. "
        "고령화율 = 65세 이상 인구 합계 ÷ 전체 인구 합계 × 100. "
        "지도 경계와 인구 자료는 시군구 코드로 연결했습니다."
    )

    # --------------------------------------------------
    # 상세 표
    # --------------------------------------------------
    with st.expander("시군구별 고령화율 표 보기"):
        detail = map_df[
            ["코드", "시군구", "전체인구", "고령인구", "고령화율"]
        ].copy()

        detail = detail.sort_values(
            "고령화율", ascending=False
        )

        detail = detail.rename(
            columns={
                "코드": "시군구 코드",
                "전체인구": "전체 인구",
                "고령인구": "65세 이상 인구",
                "고령화율": "고령화율(%)",
            }
        )

        st.dataframe(
            detail.style.format(
                {
                    "전체 인구": "{:,.0f}",
                    "65세 이상 인구": "{:,.0f}",
                    "고령화율(%)": "{:.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

except Exception as e:
    st.error("앱을 실행하는 중 문제가 발생했습니다.")
    st.exception(e)
    st.info(
        "인구 데이터 URL, GeoJSON URL, 열 이름 및 코드 형식을 확인해 주세요."
    )
