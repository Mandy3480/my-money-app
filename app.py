import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from datetime import datetime

# 1. 讓 matplotlib 支援中文顯示
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

# 2. 定義存檔的檔案名稱
CSV_FILE = "mandy_ledger.csv"

# 3. 自動讀取或初始化資料檔案 (永久存檔機制)
if os.path.exists(CSV_FILE):
    # 如果有舊檔案，直接讀進來，並確保格式正確
    df_existing = pd.read_csv(CSV_FILE)
    df_existing['金額'] = df_existing['金額'].astype(int)
    st.session_state.ledger = df_existing
else:
    # 沒有舊檔案就開一個新的
    st.session_state.ledger = pd.DataFrame(columns=['日期', '月份', '品項', '金額', '分類'])

# 網頁大標題
st.title("💬 Mandy 的對話記帳 App")
st.write("請在下方輸入你的花費，例如：「買保養品1000」或「500吃」")

# 對話輸入框
user_input = st.text_input("輸入記帳內容...", key="input_text")

# 按下送出按鈕後的動作
if st.button("送出記帳") and user_input:
    amount = 0
    category = "其他"
    
    # 取得今天日期與月份
    today_str = datetime.today().strftime('%Y-%m-%d')
    month_str = datetime.today().strftime('%Y-%m') # 格式例如：2026-06
    
    # 【超級防錯小雷達】只抓取文字中的純數字
    numbers = re.findall(r'\d+', user_input)
    if numbers:
        amount = int(numbers[0])
    
    # 【關鍵字智慧判定】
    if any(x in user_input for x in ["交通", "車", "捷運", "公車", "計程車", "油錢", "高鐵", "火車", "悠遊卡"]):
        category = "交通運輸"
    elif any(x in user_input for x in ["保養品", "化妝品", "衣服", "玩", "看電影", "買", "娛樂", "包包", "鞋子"]):
        category = "美妝娛樂"
    elif any(x in user_input for x in ["吃", "飯", "喝", "晚餐", "午餐", "早餐", "食品", "點心", "飲料", "咖啡"]):
        category = "餐飲食品"
    elif any(x in user_input for x in ["房租", "水電", "瓦斯", "網路", "生活用品", "衛生紙", "日常", "家"]):
        category = "居家生活"
    elif any(x in user_input for x in ["看醫生", "醫", "藥", "保健食品", "診所", "口罩"]):
        category = "醫療保健"

    # 新增資料
    new_data = pd.DataFrame([{'日期': today_str, '月份': month_str, '品項': user_input, '金額': int(amount), '分類': category}])
    st.session_state.ledger = pd.concat([st.session_state.ledger, new_data], ignore_index=True)
    
    # 【核心】立刻把資料寫進硬碟檔案裡！
    st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    st.success(f"🎉 記帳成功並已永久存檔！已歸類到【{category}】，金額：{amount} 元")

# --- 下半部：進階月結算儀表板 ---
st.markdown("---")
st.header("📊 Mandy 的月結算與趨勢分析")

if not st.session_state.ledger.empty:
    # 讓資料內的金額強制維持數字
    st.session_state.ledger['金額'] = st.session_state.ledger['金額'].astype(int)
    
    # 功能一：歷史月份消費變化折線圖
    st.subheader("📈 歷史每月總消費變化趨勢")
    monthly_trend = st.session_state.ledger.groupby('月份')['金額'].sum()
    
    fig_trend, ax_trend = plt.subplots(figsize=(7, 3))
    ax_trend.plot(monthly_trend.index, monthly_trend.values, marker='o', color='#4CAF50', linewidth=2)
    ax_trend.set_title("每月花費走勢圖 (看你的消費是變多還是變少)")
    ax_trend.set_xlabel("月份")
    ax_trend.set_ylabel("總花費金額")
    ax_trend.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig_trend)
    
    st.markdown("---")
    
    # 功能二：月份切換器
    all_months = sorted(st.session_state.ledger['月份'].unique(), reverse=True)
    selected_month = st.selectbox("📆 請選擇你想查看的結算月份：", all_months)
    
    # 篩選出該月份的資料
    month_df = st.session_state.ledger[st.session_state.ledger['月份'] == selected_month]
    
    # 顯示該月明細
    st.subheader(f"📋 {selected_month} 月份詳細紀錄")
    st.dataframe(month_df[['日期', '品項', '金額', '分類']])
    
    # 計算該月分類總和
    category_totals = month_df.groupby('分類')['金額'].sum()
    
    # 顯示該月圓餅圖
    st.subheader(f"🍕 {selected_month} 消費比例")
    fig_pie, ax_pie = plt.subplots(figsize=(5, 5))
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6']
    ax_pie.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=90, colors=colors[:len(category_totals)])
    ax_pie.axis('equal') 
    st.pyplot(fig_pie)
    
    # 顯示該月文字統計
    st.subheader(f"💡 {selected_month} 各分類花費統計")
    total_spend = category_totals.sum()
    
    st.write(f"💰 **該月總花費：** {total_spend} 元")
    st.write(f"🍔 **餐飲食品：** {category_totals.get('餐飲食品', 0)} 元")
    st.write(f"🛍️ **美妝娛樂：** {category_totals.get('美妝娛樂', 0)} 元")
    st.write(f"🏠 **居家生活：** {category_totals.get('居家生活', 0)} 元")
    st.write(f"🚗 **交通運輸：** {category_totals.get('交通運輸', 0)} 元")
    st.write(f"🏥 **醫療保健：** {category_totals.get('醫療保健', 0)} 元")
    st.write(f"📦 **其他：** {category_totals.get('其他', 0)} 元")
    
else:
    st.info("目前還沒有任何記帳資料，快在上方輸入第一筆花費吧！")