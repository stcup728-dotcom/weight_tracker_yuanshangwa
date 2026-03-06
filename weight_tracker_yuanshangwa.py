import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime
import os
import urllib.request

# ----------------------
# 配置 matplotlib 显示中文（自动下载字体）
# ----------------------
FONT_PATH = "SimHei.ttf"
FONT_URL = "https://raw.githubusercontent.com/stcup728-dotcom/weight_tracker_yuanshangwa/main/SimHei.ttf"  # 请确认用户名/仓库名是否正确

# 如果字体文件不存在，则从 GitHub 下载
if not os.path.exists(FONT_PATH):
    try:
        with st.spinner("正在下载中文字体，首次运行需几秒钟..."):
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        st.success("✅ 字体下载成功，中文将正常显示")
    except Exception as e:
        st.warning("⚠️ 字体下载失败，中文可能显示为方框")

# 将字体添加到 matplotlib 字体库
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = fm.FontProperties(fname=FONT_PATH).get_name()
else:
    # 备选方案：尝试常见 Linux 中文字体
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ----------------------
# 数据文件
# ----------------------
DATA_FILE = "weight_data.csv"

# ----------------------
# 私人名单（只有名单内的人可以打卡）
# ----------------------
ALLOWED_NAMES = ["宋涛", "郭庆", "张博", "宋乐"]

# ----------------------
# 页面标题
# ----------------------
st.title("🏋️ 塬上娃减肥打卡系统")

# ----------------------
# 初始化数据文件
# ----------------------
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["name", "date", "weight", "height"])
    df.to_csv(DATA_FILE, index=False)

df = pd.read_csv(DATA_FILE)

# =====================
# 今日打卡区
# =====================
st.header("今日打卡")

name = st.text_input("姓名")
height = st.number_input("身高(cm)", min_value=140, max_value=220)
weight = st.number_input("体重(kg)", min_value=30.0, max_value=200.0)

if st.button("提交"):
    if name not in ALLOWED_NAMES:
        st.error("❌ 你不在允许名单中，无法提交记录！")
    elif name == "" or height <= 0:
        st.error("❌ 请填写有效姓名和身高！")
    else:
        new_data = pd.DataFrame({
            "name":[name],
            "date":[datetime.now().strftime("%Y-%m-%d")],
            "weight":[weight],
            "height":[height]
        })
        df = pd.concat([df, new_data])
        df.to_csv(DATA_FILE, index=False)
        st.success("✅ 记录成功！")

# 重新读取数据
df = pd.read_csv(DATA_FILE)

# =====================
# BMI计算 + 健康提示
# =====================
st.header("BMI分析")

if len(df) > 0:
    latest = df.sort_values("date").groupby("name").tail(1)
    latest["BMI"] = latest["weight"] / ((latest["height"]/100)**2)

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
    st.dataframe(latest[["name","weight","height","BMI","状态"]])

# =====================
# 体重变化曲线
# =====================
st.header("体重变化曲线")

if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"])
    fig, ax = plt.subplots(figsize=(8,5))

    for person in df["name"].unique():
        person_data = df[df["name"] == person]
        ax.plot(
            person_data["date"],
            person_data["weight"],
            marker='o',
            label=person
        )

    ax.set_xlabel("日期")
    ax.set_ylabel("体重 (kg)")
    ax.legend()
    st.pyplot(fig)

# =====================
# 减肥排行榜
# =====================
st.header("🏆 减重排行榜")

if len(df) > 0:
    result = []
    for person in df["name"].unique():
        person_data = df[df["name"] == person].sort_values("date")
        start = person_data.iloc[0]["weight"]
        latest_weight = person_data.iloc[-1]["weight"]
        loss = start - latest_weight
        result.append([person, start, latest_weight, loss])

    rank_df = pd.DataFrame(
        result,
        columns=["姓名","初始体重","当前体重","减重(kg)"]
    )
    rank_df = rank_df.sort_values("减重(kg)", ascending=False)
    st.dataframe(rank_df)