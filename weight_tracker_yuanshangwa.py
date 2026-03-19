import streamlit as st
import plotly.express as px
from datetime import datetime, timezone, timedelta
import pandas as pd
from github import Github
import io

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
# 基础配置与 GitHub API 初始化
# =====================
# 从 Streamlit Secrets 读取配置
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "weight_data.csv"

ALLOWED_NAMES = ["宋涛", "郭庆", "张博", "宋乐"]

# --- 新增：为每个人固定专属颜色字典 ---
COLOR_MAP = {
    "郭庆": "blue",
    "宋涛": "green",
    "张博": "black",
    "宋乐": "red"
}

beijing_tz = timezone(timedelta(hours=8))
today = datetime.now(beijing_tz).date()


# =====================
# GitHub 数据读写函数
# =====================
@st.cache_data(ttl=5)
def load_data_from_github():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        raw_bytes = contents.decoded_content

        # 恢复你之前的双重解码魔法：先尝试 utf-8，不行就退回到 gbk
        try:
            csv_data = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            csv_data = raw_bytes.decode("gbk")

        df = pd.read_csv(io.StringIO(csv_data))
        if len(df) > 0:
            df["date"] = pd.to_datetime(df["date"])
        return df, contents.sha
    except Exception as e:
        # 如果文件不存在，返回空 DataFrame
        df = pd.DataFrame(columns=["name", "date", "weight_jin", "height_cm", "goal_weight"])
        return df, None


def save_data_to_github(df, sha):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    # 转换日期格式防止保存时带时间戳
    df_save = df.copy()
    if len(df_save) > 0:
        df_save["date"] = pd.to_datetime(df_save["date"]).dt.date
    csv_data = df_save.to_csv(index=False, encoding="utf-8-sig")

    if sha:
        repo.update_file(FILE_PATH, f"Update weight data by Streamlit at {today}", csv_data, sha)
    else:
        repo.create_file(FILE_PATH, "Create weight data init", csv_data)


# =====================
# 初始化数据 (从 GitHub 读取)
# =====================
df, current_sha = load_data_from_github()

# =====================
# 标题
# =====================
st.markdown("# 🏋️ 塬上娃减肥打卡系统")

# =====================
# 今日打卡
# =====================
st.markdown("## 今日打卡")

name = st.selectbox("选择姓名", ALLOWED_NAMES)

# 获取最近一次打卡数据
last_record = df[df["name"] == name].sort_values("date", ascending=False).head(1)
if len(last_record) > 0:
    last_weight = last_record["weight_jin"].values[0]
    last_height = last_record["height_cm"].values[0]
    last_goal_weight = last_record["goal_weight"].values[0]
else:
    last_weight = 180.0
    last_height = 175.0
    last_goal_weight = 150.0

c1, c2, c3 = st.columns(3)
with c1:
    height_cm = st.number_input("身高(cm)", 160.0, 200.0, float(last_height))
with c2:
    weight_jin = st.number_input("体重(斤)", 100.0, 300.0, float(last_weight))
with c3:
    goal_weight = st.number_input("目标体重(斤)", 100.0, 200.0, float(last_goal_weight))

submit = st.button("提交")

if submit:
    # 提交时再次从 GitHub 拉取最新数据，防止多人同时打卡覆盖
    latest_df, latest_sha = load_data_from_github()

    if len(latest_df) > 0:
        latest_df["date"] = pd.to_datetime(latest_df["date"]).dt.date

    # 删除今天重复打卡
    latest_df = latest_df[~((latest_df["name"] == name) & (latest_df["date"] == today))]

    new_record = pd.DataFrame({
        "name": [name],
        "date": [today],
        "weight_jin": [weight_jin],
        "height_cm": [height_cm],
        "goal_weight": [goal_weight]
    })

    latest_df = pd.concat([latest_df, new_record], ignore_index=True)

    # 推送到 GitHub
    try:
        save_data_to_github(latest_df, latest_sha)
        st.success("✅ 打卡成功！数据已永久保存。")
        # 清除缓存强制刷新
        load_data_from_github.clear()
        # 刷新页面状态以显示最新数据
        st.rerun()
    except Exception as e:
        st.error(f"❌ 打卡失败，请重试。错误信息: {e}")

# =====================
# 重新加载最新数据用于下方展示
# =====================
df, _ = load_data_from_github()

# =====================
# 今日打卡情况
# =====================
if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"])
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

    show = latest[["name", "weight_jin", "height_cm", "BMI", "状态", "goal_weight", "距离目标"]]
    show.columns = ["姓名", "体重(斤)", "身高(cm)", "BMI", "状态", "目标体重", "距离目标(斤)"]
    st.dataframe(show, use_container_width=True, hide_index=True)

# =====================
# 体重变化曲线
# =====================
st.markdown("## 体重变化曲线")
if len(df) > 0:
    # 新增：加入了 color_discrete_map 参数
    fig = px.line(df, x="date", y="weight_jin", color="name", markers=True,
                  color_discrete_map=COLOR_MAP,
                  labels={"date": "日期", "weight_jin": "体重(斤)", "name": "姓名"})
    fig.update_layout(legend_title_text="",
                      xaxis=dict(title="日期", tickformat="%Y/%-m/%-d", rangeslider=dict(visible=True)),
                      yaxis=dict(title="体重(斤)"), hovermode="x unified",
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# =====================
# 最近7天趋势
# =====================
st.markdown("## 最近7天体重趋势")
if len(df) > 0:
    # 绝对锚定“今天”，不管今天有没有人打卡
    end_date = pd.to_datetime(today)
    start_date = end_date - pd.Timedelta(days=6)

    # 过滤出这7天内的数据
    last = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    # 新增：加入了 color_discrete_map 参数
    fig2 = px.line(last, x="date", y="weight_jin", color="name", markers=True,
                   color_discrete_map=COLOR_MAP,
                   labels={"date": "日期", "weight_jin": "体重(斤)", "name": "姓名"})

    # 生成一个严格包含这7天的列表，用于强制坐标轴刻度
    all_7_days = pd.date_range(start=start_date, end=end_date)

    fig2.update_layout(
        legend_title_text="",
        xaxis=dict(
            title="日期",
            tickformat="%Y/%-m/%-d",
            tickmode="array",  # 告诉系统：我要自己指定刻度
            tickvals=all_7_days,  # 指定刻度为这精确的7天
            range=[start_date, end_date]  # 锁死显示范围，切掉图表左右多余的留白
        ),
        yaxis=dict(title="体重(斤)"),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# =====================
# 减重排行榜
# =====================
st.markdown("## 🏆 减重排行榜")
if len(df) > 0:
    result = []
    for p in df["name"].unique():
        d = df[df["name"] == p].sort_values("date")
        start_w = d.iloc[0]["weight_jin"]
        now_w = d.iloc[-1]["weight_jin"]
        loss = start_w - now_w
        loss_rate = round((loss / start_w * 100 if start_w != 0 else 0), 2)
        result.append([p, start_w, now_w, loss, loss_rate])

    rank = pd.DataFrame(result, columns=["姓名", "初始体重", "当前体重", "减重", "减重率(%)"])
    rank = rank.sort_values("减重率(%)", ascending=False).reset_index(drop=True)
    medals = ["🥇", "🥈", "🥉"]
    rank.insert(0, "排名", "")
    for i in range(len(rank)):
        rank.loc[i, "排名"] = medals[i] if i < 3 else i + 1

    st.dataframe(rank, use_container_width=True, hide_index=True)
