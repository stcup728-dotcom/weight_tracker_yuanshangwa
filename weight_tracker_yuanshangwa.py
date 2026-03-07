import streamlit as st
import plotly.express as px
from datetime import datetime, timezone, timedelta
import pandas as pd
import os

# =====================
# 页面样式
# =====================

st.markdown("""
<style>
.stApp{
    background-color:white;
}

h1,h2,h3,label{
    text-align:center;
    color:black !important;
}

.stDataFrame td, .stDataFrame th{
    text-align:center !important;
    font-size:16px !important;
}

button{
    font-size:16px !important;
}
</style>
""", unsafe_allow_html=True)

# =====================
# 基础配置
# =====================

DATA_FILE = "weight_data.csv"

ALLOWED_NAMES = ["宋涛", "郭庆", "张博", "宋乐"]

beijing_tz = timezone(timedelta(hours=8))
today = datetime.now(beijing_tz).date()

# =====================
# 初始化数据
# =====================

if not os.path.exists(DATA_FILE):

    df = pd.DataFrame(columns=[
        "name",
        "date",
        "weight_jin",
        "height_cm",
        "goal_weight"
    ])

    df.to_csv(DATA_FILE, index=False, encoding="gbk")

df = pd.read_csv(DATA_FILE, encoding="gbk")

if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"])

# =====================
# 标题
# =====================

st.markdown("# 🏋️ 塬上娃减肥打卡系统")

# =====================
# 今日打卡
# =====================

st.markdown("## 今日打卡")

# 获取选定人的上一条打卡数据
name = st.selectbox("选择姓名", ALLOWED_NAMES, key="name_selectbox")

# 查找该人的最后一次打卡数据
last_record = df[df["name"] == name].sort_values("date", ascending=False).head(1)

# 如果有上一条打卡记录，则填充输入框
if len(last_record) > 0:
    last_weight = last_record["weight_jin"].values[0]
    last_height = last_record["height_cm"].values[0]
    last_goal_weight = last_record["goal_weight"].values[0]
else:
    last_weight = 180.0  # 默认体重
    last_height = 175.0  # 默认身高
    last_goal_weight = 150.0  # 默认目标体重

# 使用上一次的记录作为默认值
c1, c2, c3, c4 = st.columns(4)

with c1:
    height_cm = st.number_input("身高(cm)", 160.0, 200.0, last_height, key="height_cm")

with c2:
    weight_jin = st.number_input("体重(斤)", 100.0, 300.0, last_weight, key="weight_jin")

with c3:
    goal_weight = st.number_input("目标体重(斤)", 100.0, 200.0, last_goal_weight, key="goal_weight")

submit = st.button("提交")

if submit:

    df = pd.read_csv(DATA_FILE, encoding="gbk")

    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df[~((df["name"] == name) & (df["date"] == today))]

    new = pd.DataFrame({
        "name": [name],
        "date": [today],
        "weight_jin": [weight_jin],
        "height_cm": [height_cm],
        "goal_weight": [goal_weight]
    })

    df = pd.concat([df, new], ignore_index=True)

    df.to_csv(DATA_FILE, index=False, encoding="gbk")

    st.success("✅ 打卡成功")

df = pd.read_csv(DATA_FILE, encoding="gbk")

if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"])

# =====================
# 今日打卡情况
# =====================

st.markdown("## ⏰ 今日打卡情况")

if len(df) > 0:

    today_list = df[df["date"].dt.date == today]["name"].unique().tolist()

    not_check = [i for i in ALLOWED_NAMES if i not in today_list]

    if len(not_check) == 0:

        st.success("🎉 今天所有人都已打卡！")

    else:

        st.warning("未打卡人员：")

        st.write("、".join(not_check))

# =====================
# BMI分析
# =====================

st.markdown("## BMI体质指数分析")

if len(df) > 0:

    latest = df.sort_values("date").groupby("name").tail(1).copy()

    latest["weight_kg"] = latest["weight_jin"] / 2
    latest["height_m"] = latest["height_cm"] / 100

    latest["BMI"] = latest["weight_kg"] / (latest["height_m"] ** 2)

    def bmi_state(b):

        if b < 18.5:
            return "偏瘦"
        elif b < 23:
            return "正常"
        elif b < 25:
            return "超重"
        else:
            return "肥胖"

    latest["状态"] = latest["BMI"].apply(bmi_state)

    latest["距离目标"] = latest["weight_jin"] - latest["goal_weight"]

    show = latest[[
        "name",
        "weight_jin",
        "height_cm",
        "BMI",
        "状态",
        "goal_weight",
        "距离目标"
    ]]

    show.columns = [
        "姓名",
        "体重(斤)",
        "身高(cm)",
        "BMI",
        "状态",
        "目标体重",
        "距离目标(斤)"
    ]

    st.dataframe(show, use_container_width=True, hide_index=True)

# =====================
# 体重变化曲线
# =====================

st.markdown("## 体重变化曲线")

if len(df) > 0:

    fig = px.line(

        df,
        x="date",
        y="weight_jin",
        color="name",
        markers=True,

        labels={
            "date": "日期",
            "weight_jin": "体重(斤)",
            "name": "姓名"
        }
    )

    fig.update_layout(

        legend_title_text="",

        xaxis=dict(
            title="日期",
            tickformat="%Y/%-m/%-d",
            rangeslider=dict(visible=True)
        ),

        yaxis=dict(title="体重(斤)"),

        hovermode="x unified",

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================
# 最近7天趋势
# =====================

st.markdown("## 最近7天体重趋势")

if len(df) > 0:

    end = df["date"].max()

    start = end - pd.Timedelta(days=7)

    last = df[df["date"] >= start]

    fig2 = px.line(

        last,
        x="date",
        y="weight_jin",
        color="name",
        markers=True,

        labels={
            "date": "日期",
            "weight_jin": "体重(斤)",
            "name": "姓名"
        }
    )

    fig2.update_layout(

        legend_title_text="",

        xaxis=dict(
            title="日期",
            tickformat="%Y/%-m/%-d"
        ),

        yaxis=dict(
            title="体重(斤)"
        ),

        hovermode="x unified",

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig2, use_container_width=True)
