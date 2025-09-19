import os
import math
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit.components.v1 import html


st.set_page_config(layout="centered", page_title="Wardriver Viewer", page_icon="📡")
st.title("📡 Wardriver Viewer")

# ----------------------------
# Helpers
# ----------------------------
def fullscreen_html(html_code):
    return """
            <style>
            .st-btn {
                background-color: #fff;
                color: #000;
                border: 2px solid rgba(0, 0, 0, 0.2);
                border-radius: 2px;
                text-align: center;
                font-size: 22px;
                cursor: pointer;
                width: 40px;
                height: 40px;
                font-weight: bold;
                line-height: 28px;
                position: absolute;
                z-index: 9999;
                right: 15px;
                top: 15px;
            }
            .st-btn:hover {
                background-color: #f0f2f6;
                border-color: #c0c0c0;
            }
            </style>
            <button class="st-btn" onclick="openFullscreen()">&#x26F6;</button>
            <div id="map-container" style="width:100%; height:400px; background:lightblue; text-align:center; line-height:400px;">
                """ + html_code + """
            </div>
            <script>
            function openFullscreen() {
            var elem = document.getElementById("map-container");
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.mozRequestFullScreen) { /* Firefox */
                elem.mozRequestFullScreen();
            } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE/Edge */
                elem.msRequestFullscreen();
            }
            }
            </script>
            """

def filtre_data(df, auth_filter, type_filter):

    if auth_filter != "ALL" and type_filter != "BLE":
        df = df[df["AuthMode"] == auth_filter]

    if type_filter != "ALL":
        df = df[df["Type"] == type_filter]

    return df


def make_map(df, auth_filter, type_filter, radius_from_rssi):
    df = filtre_data(df, auth_filter, type_filter)

    if df.CurrentLatitude.isna().all() or df.CurrentLongitude.isna().all():
        return "<h4>No GPS data available</h4>"

    fmap = folium.Map(location=[df.CurrentLatitude.mean(), df.CurrentLongitude.mean()], zoom_start=15)

    for lat, lon, ssid, dev_type, mac, auth, first_seen, rssi in df[
        ["CurrentLatitude", "CurrentLongitude", "SSID", "Type", "MAC", "AuthMode", "FirstSeen", "RSSI"]
    ].values:
        if math.isnan(lat) or math.isnan(lon):
            continue

        # Marker color
        color = "red"
        if dev_type == "WIFI":
            if auth == "[OPEN]":
                color = "green"
        elif dev_type == "BLE":
            color = "blue"

        # Radius
        radius = 2
        if radius_from_rssi:
            radius = max(1, 100 + rssi)

        popup_info = f"""
        <b>Type:</b> {dev_type}<br>
        <b>Auth:</b> {auth}<br>
        <b>SSID:</b> {ssid}<br>
        <b>MAC:</b> {mac}<br>
        <b>RSSI:</b> {rssi}<br>
        <b>GPS:</b> {lat}, {lon}<br>
        <b>First Seen:</b> {first_seen}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=popup_info,
        ).add_to(fmap)

    return fmap #._repr_html_()



# ----------------------------
# UI
# ----------------------------
uploaded_file = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=False)

if uploaded_file:

    df = pd.read_csv(uploaded_file, on_bad_lines="skip", header=1, delimiter=",")

    type_filter = st.selectbox("Device type filter", ["ALL", "WIFI", "BLE"])
    if type_filter != "BLE":
        auth_filter = st.selectbox("WiFi Authentication filter", ["ALL", "OPEN", "WPA", "WPA2", "WEP"])
    else:
        auth_filter = "ALL"
    
    df = filtre_data(df, auth_filter, type_filter)

    tab1, tab2 = st.tabs(["📋 Table", "🗺️ Map"])

    with tab1:
        st.dataframe(df)
        st.write(f"Found {len(df)} records.")
    with tab2:
        radius_from_rssi = st.checkbox("Radius scaled by RSSI", value=False)
        fmap = make_map(df, auth_filter, type_filter, radius_from_rssi)
        #st_folium(fmap, width=900, height=600)
        html(fullscreen_html(fmap._repr_html_()), height=600, scrolling=False)




