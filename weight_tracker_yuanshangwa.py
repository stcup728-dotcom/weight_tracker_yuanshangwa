import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
import os

# ----------------------
# 页面样式
# ----------------------
st.markdown(
    """
    <style>
    .stApp h1, .stApp h2, .stApp h3, .stApp label {
        color: black !important;
    }

    .stApp {
        background-color: white;
    }

    .stDataFrame table {
        font-size:16px;
    }

    button {
        font-size:16px !important;
        color:black !important;
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
# 允许打卡名单
# ----------------------
ALLOWED_NAMES = ["宋涛","郭庆","张博","宋乐"]

# ----------------------
# 页面标题
# ----------------------
st.markdown("<h1 style='text-align:center;'>🏋️ 塬上娃减肥打卡系统</h1>", unsafe_allow_html=True)

# ----------------------
# 初始化数据
# ----------------------
if not os.path.exists(DATA_FILE):

    df = pd.DataFrame(columns=[
        "name","date","weight_jin","height_cm","goal_weight"
    ])

    df.to_csv(DATA_FILE,index=False)

df = pd.read_csv(DATA_FILE)

# =====================
# 今日打卡
# =====================

st.markdown("<h2 style='text-align:center;'>今日打卡</h2>", unsafe_allow_html=True)

col1,col2,col3,col4 = st.columns(4)

with col1:
    name = st.text_input("姓名")

with col2:
    height_cm = st.number_input("身高（厘米）",140,220)

with col3:
    weight_jin = st.number_input("体重（斤）",30.0,400.0,step=0.1)

with col4:
    goal_weight = st.number_input("目标体重（斤）",30.0,300.0,step=0.1)

submit = st.button("提交")

if submit:

    if name not in ALLOWED_NAMES:

        st.error("❌ 你不在允许名单中")

    else:

        beijing_tz = timezone(timedelta(hours=8))

        now = datetime.now(beijing_tz)

        today = now.strftime("%Y-%m-%d")

        df = pd.read_csv(DATA_FILE)

        df = df[~((df["name"]==name) & (df["date"]==today))]

        new = pd.DataFrame({

            "name":[name],
            "date":[today],
            "weight_jin":[weight_jin],
            "height_cm":[height_cm],
            "goal_weight":[goal_weight]

        })

        df = pd.concat([df,new],ignore_index=True)

        df.to_csv(DATA_FILE,index=False)

        st.success("✅ 打卡成功")

df = pd.read_csv(DATA_FILE)

# =====================
# BMI分析
# =====================

st.markdown("<h2 style='text-align:center;'>BMI体质指数分析</h2>", unsafe_allow_html=True)

if len(df)>0:

    latest = df.sort_values("date").groupby("name").tail(1)

    latest["weight_kg"] = latest["weight_jin"]/2

    latest["height_m"] = latest["height_cm"]/100

    latest["BMI"] = latest["weight_kg"]/(latest["height_m"]**2)

    def bmi_status(b):

        if b<18.5:
            return "偏瘦"

        elif b<23:
            return "正常"

        elif b<25:
            return "超重"

        else:
            return "肥胖"

    latest["状态"] = latest["BMI"].apply(bmi_status)

    latest["距离目标(斤)"] = latest["weight_jin"]-latest["goal_weight"]

    show = latest[[
        "name","weight_jin","height_cm","BMI","状态","goal_weight","距离目标(斤)"
    ]]

    show.columns = [
        "姓名","体重(斤)","身高(cm)","BMI","状态","目标体重","距离目标"
    ]

    st.dataframe(show,use_container_width=True,hide_index=True)

# =====================
# 体重变化曲线
# =====================

st.markdown("<h2 style='text-align:center;'>体重变化曲线</h2>", unsafe_allow_html=True)

if len(df)>0:

    df["date"] = pd.to_datetime(df["date"])

    fig = px.line(

        df,
        x="date",
        y="weight_jin",
        color="name",
        markers=True,

        labels={
            "date":"日期",
            "weight_jin":"体重(斤)",
            "name":"姓名"
        }

    )

    fig.update_traces(

        hovertemplate="<b>%{fullData.name}</b><br>日期:%{x|%Y-%m-%d}<br>体重:%{y}斤<extra></extra>"

    )

    fig.update_layout(

        legend_title_text="",

        xaxis=dict(
            title="日期",
            tickformat="%Y-%m-%d",
            rangeslider=dict(visible=True)
        ),

        yaxis=dict(
            title="体重(斤)"
        ),

        hovermode="x unified",

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig,use_container_width=True)

# =====================
# 最近7天趋势
# =====================

st.markdown("<h2 style='text-align:center;'>最近7天体重趋势</h2>", unsafe_allow_html=True)

if len(df)>0:

    last = df.copy()

    last["date"] = pd.to_datetime(last["date"])

    end = last["date"].max()

    start = end - pd.Timedelta(days=7)

    last = last[last["date"]>=start]

    fig2 = px.line(

        last,
        x="date",
        y="weight_jin",
        color="name",
        markers=True,

        labels={
            "date":"日期",
            "weight_jin":"体重(斤)",
            "name":"姓名"
        }

    )

    fig2.update_layout(

        legend_title_text="",

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig2,use_container_width=True)

# =====================
# 减重排行榜
# =====================

st.markdown("<h2 style='text-align:center;'>🏆 减重排行榜</h2>", unsafe_allow_html=True)

if len(df)>0:

    result=[]

    for p in df["name"].unique():

        d=df[df["name"]==p].sort_values("date")

        start=d.iloc[0]["weight_jin"]

        now=d.iloc[-1]["weight_jin"]

        loss=start-now

        result.append([p,start,now,loss])

    rank=pd.DataFrame(

        result,
        columns=["姓名","初始体重","当前体重","减重"]

    )

    rank["减重率(%)"]=(rank["减重"]/rank["初始体重"]*100).round(2)

    rank=rank.sort_values("减重率(%)",ascending=False).reset_index(drop=True)

    st.dataframe(rank,use_container_width=True,hide_index=True)
