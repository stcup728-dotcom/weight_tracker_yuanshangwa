import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
import os

# ----------------------
# 页面全局样式（黑色文字 + 大字体）
# ----------------------
st.markdown(
    """
    <style>
    /* 所有标题和文本强制黑色 */
    .stApp h1, .stApp h2, .stApp h3, .stApp .stTextInput label, .stApp .stNumberInput label,
    .stApp .stDataFrame td, .stApp .stDataFrame th {
        color: black !important;
    }
    /* 表格字体大小 */
    .stApp [data-testid="stDataFrame"] table {
        font-size: 16px !important;
    }
    /* 输入框标签字体 */
    .stApp .stTextInput label, .stApp .stNumberInput label {
        font-size: 16px !important;
        font-weight: 500;
    }
    /* 按钮文字 */
    .stApp button {
        font-size: 16px !important;
        color: black !important;
    }
    /* 全局背景保持白色（可选） */
    .stApp {
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------
# 数据文件
# ----------------------
DATA_FILE = "weight_data.csv"

# ----------------------
# 私人名单（只有名单内的人可以打卡）
# ----------------------
ALLOWED_NAMES = ["宋涛", "郭庆", "张博", "宋乐"]

# ----------------------
# 页面标题（居中）
# ----------------------
st.markdown("<h1 style='text-align: center; color: black;'>🏋️ 塬上娃减肥打卡系统</h1>", unsafe_allow_html=True)

# ----------------------
# 初始化数据文件（如果不存在则创建）
# ----------------------
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["name", "date", "weight_jin", "height_cm"])
    df.to_csv(DATA_FILE, index=False)

# 读取数据
df = pd.read_csv(DATA_FILE)

# =====================
# 兼容旧数据文件：将旧列名转换为新列名
# =====================
if 'weight' in df.columns and 'weight_jin' not in df.columns:
    df.rename(columns={'weight': 'weight_jin'}, inplace=True)
if 'height' in df.columns and 'height_cm' not in df.columns:
    df.rename(columns={'height': 'height_cm'}, inplace=True)

# =====================
# 数据清洗：确保每人每天只有一条最新记录
# =====================
if not df.empty:
    df = df.sort_index()
    df = df.groupby(['name', 'date'], as_index=False).last()
    df.to_csv(DATA_FILE, index=False)

# =====================
# 今日打卡区
# =====================
st.markdown("<h2 style='text-align: center; color: black;'>今日打卡</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    name = st.text_input("姓名")
with col2:
    height_cm = st.number_input("身高（厘米）", min_value=140, max_value=220, step=1)
with col3:
    weight_jin = st.number_input("体重（斤）", min_value=30.0, max_value=400.0, step=0.1)

col_btn = st.columns([1, 2, 1])[1]
with col_btn:
    submitted = st.button("提交", use_container_width=True)

if submitted:
    if name not in ALLOWED_NAMES:
        st.error("❌ 你不在允许名单中，无法提交记录！")
    elif name == "" or height_cm <= 0:
        st.error("❌ 请填写有效姓名和身高！")
    else:
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        date_str = now_beijing.strftime("%Y-%m-%d")

        df = pd.read_csv(DATA_FILE)
        df = df[~((df['name'] == name) & (df['date'] == date_str))]

        new_data = pd.DataFrame({
            "name": [name],
            "date": [date_str],
            "weight_jin": [weight_jin],
            "height_cm": [height_cm]
        })
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("✅ 记录成功！")

df = pd.read_csv(DATA_FILE)

# =====================
# BMI体质指数分析
# =====================
st.markdown("<h2 style='text-align: center; color: black;'>BMI体质指数分析</h2>", unsafe_allow_html=True)

if len(df) > 0:
    latest = df.sort_values("date").groupby("name").tail(1).copy()
    latest["weight_kg"] = latest["weight_jin"] / 2
    latest["height_m"] = latest["height_cm"] / 100
    latest["BMI"] = latest["weight_kg"] / (latest["height_m"] ** 2)

    def bmi_status(bmi):
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 23:
            return "正常"
        elif bmi < 25:
            return "超重"
        else:
            return "肥胖"

    latest["状态"] = latest["BMI"].apply(bmi_status)

    display_df = latest[["name", "weight_jin", "height_cm", "BMI", "状态"]].copy()
    display_df.columns = ["姓名", "体重(斤)", "身高(厘米)", "BMI体质指数", "状态"]
    st.dataframe(display_df, hide_index=True, use_container_width=True)

# =====================
# 体重变化曲线（使用 Plotly，优化颜色和字体）
# =====================
st.markdown("<h2 style='text-align: center; color: black;'>体重变化曲线</h2>", unsafe_allow_html=True)

if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"])

    fig = px.line(
        df,
        x="date",
        y="weight_jin",
        color="name",
        markers=True,
        title=None,
        labels={"date": "日期", "weight_jin": "体重 (斤)", "name": ""}  # 图例标题置空
    )

    # 自定义悬停模板（避免出现 undefined）
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>日期: %{x|%Y-%m-%d}<br>体重: %{y:.1f} 斤<extra></extra>"
    )

    # 全局字体设置（黑色 + 大小）
    fig.update_layout(
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        xaxis=dict(
            title="日期",
            titlefont=dict(size=16, color="black"),
            tickfont=dict(size=14, color="black"),
            rangeslider=dict(visible=True),
            type="date",
            tickformat="%Y-%m-%d"
        ),
        yaxis=dict(
            title="体重 (斤)",
            titlefont=dict(size=16, color="black"),
            tickfont=dict(size=14, color="black")
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color="black"),
            title_text=""  # 确保图例标题为空
        ),
        title_x=0.5,
        plot_bgcolor="white",  # 背景白色
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================
# 减重排行榜
# =====================
st.markdown("<h2 style='text-align: center; color: black;'>🏆 减重排行榜</h2>", unsafe_allow_html=True)

if len(df) > 0:
    result = []
    for person in df["name"].unique():
        person_data = df[df["name"] == person].sort_values("date")
        if len(person_data) >= 1:
            start = person_data.iloc[0]["weight_jin"]
            latest_weight = person_data.iloc[-1]["weight_jin"]
            loss = start - latest_weight
            result.append([person, start, latest_weight, loss])

    rank_df = pd.DataFrame(
        result,
        columns=["姓名", "初始体重(斤)", "当前体重(斤)", "减重(斤)"]
    )
    rank_df = rank_df.sort_values("减重(斤)", ascending=False).reset_index(drop=True)

    st.dataframe(rank_df, hide_index=True, use_container_width=True)
