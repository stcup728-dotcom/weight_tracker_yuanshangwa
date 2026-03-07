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
name = st.selectbox("选择姓名", ALLOWED_NAMES)

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
    height_cm = st.number_input("身高(cm)", 160.0, 200.0, float(last_height))

with c2:
    weight_jin = st.number_input("体重(斤)", 100.0, 300.0, float(last_weight))

with c3:
    goal_weight = st.number_input("目标体重(斤)", 100.0, 200.0, float(last_goal_weight))

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
# 减重排行榜
# =====================

st.markdown("## 🏆 减重排行榜")

if len(df) > 0:
    result = []

    # 遍历所有人员，计算初始体重和当前体重
    for p in df["name"].unique():
        d = df[df["name"] == p].sort_values("date")
        start_w = d.iloc[0]["weight_jin"]  # 初始体重
        now_w = d.iloc[-1]["weight_jin"]   # 当前体重

        # 计算减重
        loss = start_w - now_w
        # 计算减重率
        loss_rate = (loss / start_w) * 100 if start_w != 0 else 0

        result.append([p, start_w, now_w, loss, round(loss_rate, 2)])

    # 将结果转化为 DataFrame
    rank = pd.DataFrame(result, columns=["姓名", "初始体重", "当前体重", "减重", "减重率(%)"])

    # 按减重率降序排序
    rank = rank.sort_values("减重率(%)", ascending=False).reset_index(drop=True)

    # 给前三名添加奖牌
    medals = ["🥇", "🥈", "🥉"]
    rank.insert(0, "排名", "")

    for i in range(len(rank)):
        if i < 3:
            rank.loc[i, "排名"] = medals[i]
        else:
            rank.loc[i, "排名"] = i + 1

    st.dataframe(rank, use_container_width=True, hide_index=True)
