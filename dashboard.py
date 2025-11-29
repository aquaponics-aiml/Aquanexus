import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Aquaponics — Preview",
    layout="wide",
)

# -------------------------------------------------
# Custom CSS for pretty UI
# -------------------------------------------------
st.markdown(
    """
    <style>
    /* Global background + font */
    .stApp {
        background: linear-gradient(135deg, #dff8ff 0%, #f6fff7 40%, #ffffff 100%);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #0f172a;
    }

    /* Top bar */
    .top-bar {
        background: linear-gradient(90deg, #7ee6ff, #4ade80);
        border-radius: 24px;
        padding: 18px 26px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 18px 30px rgba(15, 23, 42, 0.13);
        margin-bottom: 28px;
    }

    .brand-left {
        display: flex;
        align-items: flex-start;
        gap: 14px;
    }

    .brand-icon {
        width: 40px;
        height: 40px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #ecfeff;
        font-size: 22px;
    }

    .brand-title {
        font-weight: 800;
        font-size: 20px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #065f46;
    }

    .brand-subtitle {
        font-size: 13px;
        color: #064e3b;
    }

    .top-buttons {
        display: flex;
        gap: 10px;
    }

    .pill-btn {
        border: none;
        border-radius: 999px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
    }

    .pill-primary {
        background: linear-gradient(90deg, #22c55e, #14b8a6);
        color: white;
    }

    .pill-secondary {
        background: white;
        color: #047857;
    }

    /* Section wrappers */
    .panel {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 28px;
        padding: 28px 26px 22px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
        margin-bottom: 26px;
    }

    /* Summary metrics cards */
    .summary-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-top: 18px;
    }

    .summary-card {
        background: white;
        border-radius: 18px;
        padding: 16px 18px;
        min-width: 180px;
        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.06);
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .summary-label {
        font-size: 13px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .summary-value {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
    }

    .summary-sub {
        font-size: 13px;
        color: #0f766e;
        font-weight: 600;
    }

    /* Sensor cards */
    .sensor-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 18px;
        margin-top: 18px;
    }

    .sensor-card {
        background: white;
        border-radius: 20px;
        padding: 18px 18px 14px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
        position: relative;
        overflow: hidden;
    }

    .sensor-badge {
        position: absolute;
        right: 14px;
        top: 14px;
        background: #dcfce7;
        color: #16a34a;
        font-size: 11px;
        font-weight: 700;
        border-radius: 999px;
        padding: 4px 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .sensor-title {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 4px;
    }

    .sensor-value {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
    }

    .sensor-unit {
        font-size: 13px;
        color: #94a3b8;
        margin-left: 4px;
    }

    .sensor-bar {
        margin-top: 12px;
        height: 7px;
        border-radius: 999px;
        background: linear-gradient(90deg, #22c55e, #0ea5e9, #818cf8);
    }

    /* Health panels */
    .health-header {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-bottom: 6px;
    }

    .health-title {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
    }

    .health-sub {
        font-size: 13px;
        color: #64748b;
    }

    .tag-healthy {
        font-size: 13px;
        color: #0f766e;
        font-weight: 700;
    }

    .soft-btn-row {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 14px;
    }

    .soft-btn {
        border-radius: 999px;
        padding: 6px 16px;
        border: none;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    }

    .soft-btn-primary {
        background: linear-gradient(90deg, #22c55e, #06b6d4);
        color: white;
    }

    .soft-btn-outline {
        background: white;
        color: #0f172a;
    }

    .health-time {
        font-size: 11px;
        color: #94a3b8;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Fake time-series data for charts (static)
# -------------------------------------------------
now = datetime.now()
time_points = [now - timedelta(hours=h) for h in [20, 16, 12, 8, 4, 0]]

fish_scores = [94, 96, 95, 96, 97, 98]
plant_scores = [92, 93, 94, 93, 95, 96]

fish_df = pd.DataFrame({"Time": time_points, "Health": fish_scores}).set_index("Time")
plant_df = pd.DataFrame({"Time": time_points, "Health": plant_scores}).set_index("Time")

# -------------------------------------------------
# Top bar
# -------------------------------------------------
st.markdown(
    """
    <div class="top-bar">
        <div class="brand-left">
            <div class="brand-icon">💧</div>
            <div>
                <div class="brand-title">AQUAPONICS — PREVIEW</div>
                <div class="brand-subtitle">Realtime ecosystem monitoring • AI-assisted insights</div>
            </div>
        </div>
        <div class="top-buttons">
            <button class="pill-btn pill-primary">Preview Dark</button>
            <button class="pill-btn pill-secondary">Logout</button>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Hero + top metrics
# -------------------------------------------------
st.markdown(
    """
    <div class="panel">
        <h1 style="font-size: 34px; font-weight: 800; margin-bottom: 4px; color:#0f172a;">
            Sustainable Aquaponics
        </h1>
        <p style="font-size: 14px; color:#64748b; max-width: 640px;">
            Symbiotic cycle: fish → nutrient-rich water → plants. This dashboard visualizes the living system
            and alerts you when parameters drift.
        </p>

        <div class="summary-row">
            <div class="summary-card">
                <div class="summary-label">Fish Count</div>
                <div class="summary-value">12</div>
                <div class="summary-sub">Tank A · Live</div>
            </div>

            <div class="summary-card">
                <div class="summary-label">Plant Status</div>
                <div class="summary-value">Fresh</div>
                <div class="summary-sub">Mint & leafy greens</div>
            </div>

            <div class="summary-card">
                <div class="summary-label">System Health</div>
                <div class="summary-value">98%</div>
                <div class="summary-sub">AI-assessed · Stable</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Sensor cards (static values)
# -------------------------------------------------
st.markdown(
    """
    <div class="panel">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h2 style="font-size: 20px; font-weight: 800; margin: 0;">Water & Environment</h2>
            <span style="font-size:13px; color:#94a3b8;">All values simulated · Demo view</span>
        </div>

        <div class="sensor-grid">
            <div class="sensor-card">
                <div class="sensor-badge">Optimal</div>
                <div class="sensor-title">pH Level</div>
                <div>
                    <span class="sensor-value">7.39</span>
                    <span class="sensor-unit">pH</span>
                </div>
                <div class="sensor-bar"></div>
            </div>

            <div class="sensor-card">
                <div class="sensor-badge">Optimal</div>
                <div class="sensor-title">Turbidity</div>
                <div>
                    <span class="sensor-value">15</span>
                    <span class="sensor-unit">NTU</span>
                </div>
                <div class="sensor-bar"></div>
            </div>

            <div class="sensor-card">
                <div class="sensor-badge">Optimal</div>
                <div class="sensor-title">Humidity</div>
                <div>
                    <span class="sensor-value">71</span>
                    <span class="sensor-unit">%</span>
                </div>
                <div class="sensor-bar"></div>
            </div>

            <div class="sensor-card">
                <div class="sensor-badge">Optimal</div>
                <div class="sensor-title">Light Intensity</div>
                <div>
                    <span class="sensor-value">864</span>
                    <span class="sensor-unit">lux</span>
                </div>
                <div class="sensor-bar"></div>
            </div>

            <div class="sensor-card">
                <div class="sensor-badge">Optimal</div>
                <div class="sensor-title">Temperature</div>
                <div>
                    <span class="sensor-value">23.3</span>
                    <span class="sensor-unit">°C</span>
                </div>
                <div class="sensor-bar"></div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Fish & Plant health charts (static)
# -------------------------------------------------
col_fish, col_plant = st.columns(2)

with col_fish:
    st.markdown(
        """
        <div class="panel">
            <div class="health-header">
                <div>
                    <div class="health-title">Fish Health & Activity</div>
                    <div class="health-sub">
                        AI vision indicates: <span class="tag-healthy">Healthy (94.2% confidence)</span>
                    </div>
                </div>
            </div>
            <div class="soft-btn-row">
                <button class="soft-btn soft-btn-primary">Run Scan</button>
                <button class="soft-btn soft-btn-outline">Download Report</button>
            </div>
            <div class="health-time">
                Last checked: {time}
            </div>
        """.format(
            time=now.strftime("%I:%M:%S %p")
        ),
        unsafe_allow_html=True,
    )

    st.line_chart(fish_df, height=220)
    st.markdown("</div>", unsafe_allow_html=True)

with col_plant:
    st.markdown(
        """
        <div class="panel">
            <div class="health-header">
                <div>
                    <div class="health-title">Plant Health & Growth</div>
                    <div class="health-sub">
                        AI vision indicates: <span class="tag-healthy">Fresh (91.8% confidence)</span>
                    </div>
                </div>
            </div>
            <div class="soft-btn-row">
                <button class="soft-btn soft-btn-primary">Run Scan</button>
                <button class="soft-btn soft-btn-outline">Download Report</button>
            </div>
            <div class="health-time">
                Last checked: {time}
            </div>
        """.format(
            time=now.strftime("%I:%M:%S %p")
        ),
        unsafe_allow_html=True,
    )

    st.line_chart(plant_df, height=220)
    st.markdown("</div>", unsafe_allow_html=True)
