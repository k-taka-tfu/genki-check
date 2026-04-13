import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="元気点検",
    page_icon="🌿",
    layout="wide",
)

CATEGORIES = ["食", "息", "眠", "温", "動", "想", "愛", "環", "安心"]

SCORE_LABELS = {
    5: "5点　全く（常に）その通り",
    4: "4点　ほぼその通り",
    3: "3点　どちらかと言えばその通り",
    2: "2点　どちらかと言えば違う",
    1: "1点　全く（常に）違う",
}

DEFAULT_QUESTIONS = [
    {"category": "食", "question": "食事は3食を規則的に摂っています"},
    {"category": "食", "question": "栄養バランスを意識して食べています"},
    {"category": "食", "question": "水分をこまめに摂っています"},
    {"category": "息", "question": "深呼吸や呼吸を整える時間があります"},
    {"category": "息", "question": "緊張した時に呼吸を意識して落ち着けます"},
    {"category": "息", "question": "息苦しさや息切れを感じにくいです"},
    {"category": "眠", "question": "十分な睡眠時間を確保できています"},
    {"category": "眠", "question": "寝つきや目覚めは比較的良いです"},
    {"category": "眠", "question": "日中に強い眠気を感じにくいです"},
    {"category": "温", "question": "身体を冷やしすぎないようにしています"},
    {"category": "温", "question": "入浴や保温で身体を温める習慣があります"},
    {"category": "温", "question": "寒さや暑さへの対策ができています"},
    {"category": "動", "question": "日常的に体を動かす習慣があります"},
    {"category": "動", "question": "座りっぱなしを避けるようにしています"},
    {"category": "動", "question": "無理のない範囲で運動できています"},
    {"category": "想", "question": "前向きに物事を考える時間があります"},
    {"category": "想", "question": "自分の気持ちに気づくことができます"},
    {"category": "想", "question": "悩みを抱え込みすぎず整理できます"},
    {"category": "愛", "question": "家族や身近な人とのつながりを感じます"},
    {"category": "愛", "question": "感謝や思いやりを表現できています"},
    {"category": "愛", "question": "困った時に頼れる人がいます"},
    {"category": "環", "question": "生活空間はおおむね整っています"},
    {"category": "環", "question": "過ごす場所に安心感や快適さがあります"},
    {"category": "環", "question": "自然や季節を感じる機会があります"},
    {"category": "安心", "question": "将来への不安が強すぎず過ごせています"},
    {"category": "安心", "question": "困った時の相談先を把握しています"},
    {"category": "安心", "question": "お金や生活の見通しがある程度立っています"},
    {"category": "安心", "question": "自分の健康状態をある程度把握しています"},
    {"category": "安心", "question": "医療や支援を受ける方法を知っています"},
    {"category": "安心", "question": "日々の暮らしに基本的な安心感があります"},
]


def clean_question_text(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"^(食|息|眠|温|動|想|愛|環|安心)\s*\d*\s*[\.．]?\s*", "", text)
    return text.strip()


def detect_category(text: str) -> str | None:
    text = str(text).strip()
    m = re.match(r"^(安心|食|息|眠|温|動|想|愛|環)", text)
    return m.group(1) if m else None


def load_questions() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("Excelファイルを選択", type=["xlsx"])

    if uploaded is not None:
        df = pd.read_excel(uploaded)
        return normalize_questions(df)

    excel_files = list(Path(".").glob("*.xlsx"))
    if excel_files:
        selected = st.sidebar.selectbox(
            "同じフォルダ内のExcelを使う",
            options=excel_files,
            format_func=lambda x: x.name,
        )
        df = pd.read_excel(selected)
        return normalize_questions(df)

    return pd.DataFrame(DEFAULT_QUESTIONS)


def normalize_questions(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}

    if "question" not in cols:
        raise ValueError("Excelに 'question' 列が必要です。")

    question_col = cols["question"]
    category_col = cols.get("category")

    records = []
    for _, row in df.iterrows():
        q = str(row[question_col]).strip()
        cat = str(row[category_col]).strip() if category_col else detect_category(q)

        if cat not in CATEGORIES:
            continue

        records.append(
            {
                "category": cat,
                "question": clean_question_text(q),
            }
        )

    out = pd.DataFrame(records)
    out = out[out["category"].isin(CATEGORIES)].reset_index(drop=True)

    if out.empty:
        raise ValueError("有効な設問を読み込めませんでした。")
    return out


def build_radar_chart(summary_df: pd.DataFrame) -> go.Figure:
    cats = summary_df["category"].tolist()
    values = summary_df["average"].tolist()

    cats_closed = cats + [cats[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=cats_closed,
            fill="toself",
            name="平均点",
            line=dict(color="#2F7D6B", width=3),
            fillcolor="rgba(47,125,107,0.25)",
        )
    )

    fig.update_layout(
        showlegend=False,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                gridcolor="rgba(0,0,0,0.08)",
            )
        ),
        margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor="white",
    )
    return fig


st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px;}
    h1, h2, h3 {color: #23423a;}
    .category-card {
        background: #f7fbf9;
        border: 1px solid #dcebe5;
        border-radius: 16px;
        padding: 18px 18px 8px 18px;
        margin-bottom: 18px;
    }
    .score-guide {
        background: #f4f6f8;
        border-radius: 14px;
        padding: 14px 18px;
        border: 1px solid #e2e8ee;
    }
    .stButton>button, .stFormSubmitButton>button {
        background: #2F7D6B;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌿 元気点検")
st.caption("9カテゴリー・30問の5段階評価")

with st.sidebar:
    st.markdown("### 評価基準")
    for k in [5, 4, 3, 2, 1]:
        st.write(SCORE_LABELS[k])

try:
    questions_df = load_questions()
except Exception as e:
    st.error(f"設問の読み込みに失敗しました: {e}")
    st.stop()

st.markdown(
    """
    <div class="score-guide">
    それぞれの設問について、もっとも近いものを選んでください。
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("genki_check_form"):
    responses = []

    for category in CATEGORIES:
        group = questions_df[questions_df["category"] == category]
        if group.empty:
            continue

        st.markdown(f'<div class="category-card">', unsafe_allow_html=True)
        st.subheader(f"{category} カテゴリー")

        for idx, row in group.reset_index(drop=True).iterrows():
            q_no = len(responses) + 1
            answer = st.radio(
                f"{q_no}. {row['question']}",
                options=[5, 4, 3, 2, 1],
                format_func=lambda x: SCORE_LABELS[x],
                horizontal=False,
                key=f"{category}_{idx}",
                index=2,
            )
            responses.append(
                {
                    "category": category,
                    "question": row["question"],
                    "score": answer,
                }
            )

        st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("結果を表示")

if submitted:
    result_df = pd.DataFrame(responses)

    total_score = int(result_df["score"].sum())
    max_score = int(len(result_df) * 5)

    summary = (
        result_df.groupby("category", as_index=False)
        .agg(total=("score", "sum"), count=("score", "count"), average=("score", "mean"))
    )
    summary["average"] = summary["average"].round(2)
    summary["category"] = pd.Categorical(summary["category"], categories=CATEGORIES, ordered=True)
    summary = summary.sort_values("category")

    c1, c2, c3 = st.columns(3)
    c1.metric("総得点", f"{total_score} / {max_score}")
    c2.metric("設問数", len(result_df))
    c3.metric("平均点", f"{result_df['score'].mean():.2f}")

    st.subheader("カテゴリ別結果")
    show_df = summary.copy()
    show_df.columns = ["カテゴリー", "合計点", "設問数", "平均点"]
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    st.subheader("レーダーチャート")
    fig = build_radar_chart(summary)
    st.plotly_chart(fig, use_container_width=True)