#计算和streamlit界面结合尝试

import streamlit as st
from pymsis import msis
import datetime
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']      # 指定默认字体为黑体，否则matplotlib无法显示中文
plt.rcParams['axes.unicode_minus'] = False       # 解决负号显示问题

import pandas as pd
st.title("计算和streamlit界面结合尝试")

#1.计算任意时间、位置、高度的单点参数并展示
time=st.datetime_input(
    label="Time choose",
    max_value=datetime.datetime.now(),
    min_value=datetime.datetime(1980,1,1,0,0,0),
    value=datetime.datetime(2000,1,1,0,0,0),
)
lon=st.number_input(
    label="Longitude",
    min_value=-180.0,
    max_value=180.0,
    value=0.0,
    step=0.1,
    format="%.1f",
)
lat=st.number_input(
    label="Latitude",
    min_value=-90.0,
    max_value=90.0,
    value=0.0,
    step=0.1,
    format="%.1f",
)
alt=st.number_input(
    label="Altitude",
    min_value=0,
    max_value=1000,
    value=400,
    step=1,
)

single_point=msis.run(time,lon,lat,alt)#计算代码

tab1, tab2, tab3 = st.tabs(["单点计算", "垂直廓线", "全球分布"])
with tab1:
    st.header("单点大气参数")
    # 单点计算的代码
    st.metric(
    label="Temperature",
    value=single_point[0,10],
    )
    single_point=np.squeeze(single_point)
    # 显示温度指标（你已有的）
    st.metric(label="Temperature", value=f"{single_point[10]:.2f} K")

    # 创建参数列表
    param_names = [
        "总质量密度", "N₂数密度", "O₂数密度", "O数密度", "He数密度",
        "H数密度", "Ar数密度", "N数密度", "异常氧数密度", "NO数密度", "温度"
    ]
    units = ["kg/m³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "m⁻³", "K"]

    # 构建数据字典
    data = {
        "参数": param_names,
        "数值": [f"{single_point[i]:.2e}" for i in range(11)],
        "单位": units
    }

    # 使用 pandas DataFrame 显示表格
    df = pd.DataFrame(data)     #pandas构建字典表格
    st.dataframe(df, use_container_width=True)  #st直接展示出

with tab2:
    st.header("垂直廓线")
    # 廓线绘制的代码
    # 初始化 session_state
    # 初始化
    if 'alt_min' not in st.session_state:
        st.session_state.alt_min = 100
    if 'alt_max' not in st.session_state:
        st.session_state.alt_max = 500


    def update_alt_max():
        """当最小高度变化时，确保最大高度有效"""
        if st.session_state.alt_max <= st.session_state.alt_min:
            st.session_state.alt_max = st.session_state.alt_min + 1

    # 最小高度滑块
    alt_min = st.slider(
        "最小高度 (km)",
        min_value=0,
        max_value=999,
        key='alt_min',  # 直接使用 session_state 的 key
        on_change=update_alt_max  # 变化时调用回调
    )

    # 最大高度滑块
    alt_max = st.slider(
        "最大高度 (km)",
        min_value=st.session_state.alt_min + 1,
        max_value=1000,
        key='alt_max',
        on_change=update_alt_max
    )

    st.write(f"当前设置: 最小 {st.session_state.alt_min} km, 最大 {st.session_state.alt_max} km")
    # 高度步长滑块
    alt_step = st.slider(
        "高度步长 (km)",
        min_value=1,
        max_value=50,
        value=10,
        step=1
    )

    # 选择要绘制的参数
    param_options = {
        "总质量密度": 0,
        "N₂数密度": 1,
        "O₂数密度": 2,
        "O数密度": 3,
        "He数密度":4,
        "H数密度": 5,
        "Ar数密度": 6,
        "N数密度": 7,
        "异常氧数密度": 8,
        "NO数密度": 9,
        "温度": 10,      # 温度在你的版本中索引为10
    }
    selected_param = st.selectbox("选择参数", list(param_options.keys()))
    param_idx = param_options[selected_param]

    # 计算按钮
    if st.button("绘制廓线"):
        # 生成高度数组
        altitudes = np.arange(alt_min, alt_max + alt_step, alt_step)
        st.write(f"计算 {len(altitudes)} 个高度层: {alt_min} ~ {alt_max} km")

        # 调用 pymsis 计算所有高度
        with st.spinner("计算中..."):
            # 注意：传入时间、经纬度（这些变量已在前面定义）
            data = msis.run(time, lon, lat, altitudes)
            # data 形状: (1, 1, 1, len(altitudes), 11)
            data_squeezed = np.squeeze(data)  # 变成 (len(altitudes), 11)

        # 提取所选参数的值
        values = data_squeezed[:, param_idx]

        # 绘制廓线
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(values, altitudes, 'b-o', markersize=4)
        ax.set_xlabel(selected_param)
        ax.set_ylabel("高度 (km)")
        ax.set_title(f"{selected_param} height profile")
        ax.grid(True, alpha=0.3)

        # 显示图表
        st.pyplot(fig)

        # 可选：显示数据表格（简单版）
        with st.expander("查看数据"):
            import pandas as pd
            df = pd.DataFrame({
                "高度 (km)": altitudes,
                selected_param: values
            })
            st.dataframe(df)
alt_array=np.arange(alt_min, alt_max )

with tab3:
    st.header("全球分布")
    # 全球分布的代码
    #1.计算
    timer=st.datetime_input(
        label="time",
        max_value=datetime.datetime.now(),
        min_value=datetime.datetime(1980,1,1,0,0,0),
        value=datetime.datetime(2000,1,1,0,0,0),
    )
    lons=np.arange(-180,180,10)
    lats=np.arange(-90,90,5)
    alti=st.number_input(
        label="altitude",
        min_value=0,
        max_value=1000,
        value=400,
    )
grid_points=msis.run(timer,lons,lats,alti)#计算代码
# 查看形状（用于调试，可以注释掉）
st.write(f"grid_points 形状: {grid_points.shape}")

# 2.压缩数据,将一维的数据压缩掉，即时间和高度维度
data_3d = np.squeeze(grid_points)  # 形状变为 (len(lons), len(lats), 11)
st.write(f"压缩后形状: {data_3d.shape}")

# 3.参数选项，建立字典索引
param_options = {
    "总质量密度 (kg/m³)": 0,
    "N₂数密度 (m⁻³)": 1,
    "O₂数密度 (m⁻³)": 2,
    "O数密度 (m⁻³)": 3,
    "He数密度 (m⁻³)": 4,
    "H数密度 (m⁻³)": 5,
    "Ar数密度 (m⁻³)": 6,
    "N数密度 (m⁻³)": 7,
    "异常氧数密度 (m⁻³)": 8,
    "NO数密度 (m⁻³)": 9,
    "温度 (K)": 10,
}
selected_param = st.selectbox("选择参数", list(param_options.keys()))
idx = param_options[selected_param]

# 提取对应参数的二维数组
param_grid = data_3d[:, :, idx]  # 形状 (len(lons), len(lats))
#4.绘制图像
fig, ax = plt.subplots(figsize=(10, 6))  #创建一个10x6英寸的图像
im = ax.imshow(param_grid.T,            #.T转置为匹配地理上的行是纬度，列是经度
               extent=[lons[0], lons[-1], lats[0], lats[-1]],  #定义图像覆盖的坐标范围，依次为 [左, 右, 下, 上]
               # （即经度最小、经度最大、纬度最小、纬度最大）。这样图像上的每个像素就与实际的经纬度对应起来。
               origin='lower', #指定数组的第一行对应 Y 轴的最小值（即南纬）。默认 origin='upper' 会使第一行对应 Y 轴最大值（北纬），导致图像上下颠倒。
               aspect='auto',  #自动调整图像的纵横比，使其填满坐标轴区域。否则 imshow 会保持像素为正方形，可能导致地图变形。
               cmap='viridis')#设置颜色映射方案，viridis 是一个从紫色到黄色的渐变，适合连续数据。
ax.set_xlabel('经度')   #设置 X 轴标签为“经度”。
ax.set_ylabel('纬度')  #设置 Y 轴标签为“纬度”。
ax.set_title(f'{selected_param} 全球分布 @ {alti} km')#设置图形标题，包含所选参数名称 selected_param 和高度 alti（例如“温度 全球分布 @ 400 km”）。
ax.grid(True, linestyle='--', alpha=0.5)  #在图上添加网格线，便于观察位置。设置透明度为 0.5，使网格线不遮挡数据。
plt.colorbar(im, ax=ax, label=selected_param)  #为图像 im 添加颜色条（colorbar），将颜色与数值对应起来。

st.pyplot(fig)  #将 matplotlib 图形 fig 显示在 Streamlit 应用中。

