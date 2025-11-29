# dashboard.py
#
# Streamlit dashboard for:
# 1) Sensor Dashboard (pH + light)
# 2) Fish Monitor (real-time threaded Roboflow inference)
# 3) Plant/Mint Monitor (real-time threaded Roboflow inference)

import threading
import time
import statistics
from datetime import datetime

import cv2
import pandas as pd
import requests
import streamlit as st
from smbus2 import SMBus

#                 COMMON CONFIG

ROBOFLOW_API_KEY = "BtzrtfhjiBcQCBwgRanJ"
ROBOFLOW_BASE_URL = "https://detect.roboflow.com"

FISH_MODEL_ID = "fish-detection-wqhuw/2"
MINT_MODEL_ID = "mint-yo73o/2"

#                 pH SENSOR (ADS1115)

I2C_ADDRESS = 0x48
REG_CONVERSION = 0x00
REG_CONFIG = 0x01
CONFIG_TEMPLATE = 0x8583          # A0 single-ended, Â±4.096V, 128 SPS
DIVIDER_SCALING = 0.6             # adjust for your divider

# Calibration points
V7 = 2.512   # voltage at pH 7 buffer (after scaling)
V4 = 3.026   # voltage at pH 4 buffer (after scaling)
SLOPE = (4.00 - 7.00) / (V4 - V7)
INTERCEPT = 7.00 - SLOPE * V7


def read_adc(bus, channel=0):
    mux = {0: 0x4000, 1: 0x5000, 2: 0x6000, 3: 0x7000}[channel]
    config = (CONFIG_TEMPLATE & ~0x7000) | mux
    bus.write_i2c_block_data(
        I2C_ADDRESS,
        REG_CONFIG,
        [(config >> 8) & 0xFF, config & 0xFF],
    )
    time.sleep(0.12)
    data = bus.read_i2c_block_data(I2C_ADDRESS, REG_CONVERSION, 2)
    raw = (data[0] << 8) | data[1]
    if raw > 0x7FFF:
        raw -= 0x10000
    return raw


def read_voltage(bus, channel=0):
    raw = read_adc(bus, channel)
    measured = raw * 4.096 / 32768.0
    actual = measured * DIVIDER_SCALING
    return actual


def get_filtered_voltage(bus, channel=0, samples=10, delay=0.05):
    readings = [read_voltage(bus, channel) for _ in range(samples)]
    time.sleep(delay)
    return statistics.median(readings)


def voltage_to_ph(voltage):
    return SLOPE * voltage + INTERCEPT


#                 LIGHT SENSOR (BH1750)


BH1750_ADDR = 0x23
POWER_ON = 0x01
CONT_HIGH_RES_MODE = 0x10


def bh1750_init(bus):
    bus.write_byte(BH1750_ADDR, POWER_ON)
    time.sleep(0.1)
    bus.write_byte(BH1750_ADDR, CONT_HIGH_RES_MODE)
    time.sleep(0.2)


def bh1750_read_lux(bus):
    data = bus.read_i2c_block_data(BH1750_ADDR, CONT_HIGH_RES_MODE, 2)
    raw = (data[0] << 8) | data[1]
    lux = raw / 1.2
    return lux


#                 ROBOFLOW THREADED MONITOR


FRAME_WIDTH = 640           # camera output width
INFER_EVERY_SECONDS = 1.0   # how often to call API (>= 0.7 recommended)


def roboflow_threaded_monitor(model_id: str, window_name: str):
    """
    Blocking function which opens a camera window and runs
    real-time threaded inference using the given Roboflow model.
    Close the window with the 'q' key to return to Streamlit.
    """
    latest_predictions = []
    latest_error = None
    infer_busy = False
    lock = threading.Lock()

    def call_roboflow(frame_small):
        nonlocal latest_predictions, latest_error, infer_busy
        try:
            ok, encoded = cv2.imencode(".jpg", frame_small)
            if not ok:
                raise RuntimeError("Failed to encode frame")

            img_bytes = encoded.tobytes()

            response = requests.post(
                f"{ROBOFLOW_BASE_URL}/{model_id}",
                params={"api_key": ROBOFLOW_API_KEY},
                files={"file": ("frame.jpg", img_bytes, "image/jpeg")},
                timeout=20,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"API Error {response.status_code}: {response.text[:150]}"
                )

            preds = response.json().get("predictions", [])

            with lock:
                latest_predictions = preds
                latest_error = None

        except Exception as e:
            with lock:
                latest_error = str(e)
                latest_predictions = []
        finally:
            infer_busy = False

    def draw_predictions(frame, predictions, error_text=None):
        for pred in predictions:
            x, y = int(pred["x"]), int(pred["y"])
            w, h = int(pred["width"]), int(pred["height"])
            label = pred.get("class", "object")
            conf = pred.get("confidence", 0)

            x1, y1 = x - w // 2, y - h // 2
            x2, y2 = x + w // 2, y + h // 2

            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{label} ({conf:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        msg = "OK" if error_text is None else error_text
        color = (0, 255, 0) if error_text is None else (0, 0, 255)

        cv2.rectangle(frame, (5, 5), (600, 30), (0, 0, 0), -1)
        cv2.putText(
            frame,
            msg,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
        return frame

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Could not open webcam. Check connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_WIDTH * 3 // 4)

    print("Camera opened for model:", model_id)
    print("Press 'q' in the camera window to quit.")

    last_infer_time = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            continue

        # Prepare smaller frame for API
        h, w = frame.shape[:2]
        scale = 416 / max(h, w)
        if scale < 1.0:
            frame_small = cv2.resize(frame, (int(w * scale), int(h * scale)))
        else:
            frame_small = frame

        now = time.time()
        if (now - last_infer_time >= INFER_EVERY_SECONDS) and not infer_busy:
            infer_busy = True
            last_infer_time = now
            t = threading.Thread(target=call_roboflow, args=(frame_small,))
            t.daemon = True
            t.start()

        with lock:
            preds_copy = list(latest_predictions)
            err_copy = latest_error

        annotated = draw_predictions(frame.copy(), preds_copy, err_copy)
        cv2.imshow(window_name, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ============================================================
#                 STREAMLIT UI
# ============================================================

st.set_page_config(page_title="Aquaponics Dashboard", layout="wide")

st.sidebar.title("Aquaponics Panel")
page = st.sidebar.radio(
    "Select a page:",
    ["Sensor Dashboard", "Fish Monitor", "Plant (Mint) Monitor"],
)

if "sensor_history" not in st.session_state:
    st.session_state.sensor_history = []


def page_sensor_dashboard():
    st.title("Sensor Dashboard")
    st.caption("Live pH and light readings from Raspberry Pi (ADS1115 + BH1750).")

    max_points = st.sidebar.slider(
        "Max points in chart history", 20, 300, 100, key="max_points"
    )

    try:
        with SMBus(1) as bus:
            bh1750_init(bus)
            voltage = get_filtered_voltage(bus, channel=0)
            ph_value = voltage_to_ph(voltage)
            lux = bh1750_read_lux(bus)
            scaled_lux = lux * 1000
    except Exception as e:
        st.error(f"Error reading sensors: {e}")
        return

    now = datetime.now().strftime("%H:%M:%S")

    st.session_state.sensor_history.append(
        {"time": now, "pH": ph_value, "voltage": voltage, "light_lux": scaled_lux}
    )
    if len(st.session_state.sensor_history) > max_points:
        st.session_state.sensor_history = st.session_state.sensor_history[-max_points:]

    df = pd.DataFrame(st.session_state.sensor_history)

    col1, col2, col3 = st.columns(3)
    col1.metric("Current pH", f"{ph_value:.2f}")
    col2.metric("Sensor Voltage (V)", f"{voltage:.3f}")
    col3.metric("Light Intensity (lux)", f"{scaled_lux:.0f}")

    st.markdown("---")

    if not df.empty:
        df_indexed = df.set_index("time")
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("pH Over Time")
            st.line_chart(df_indexed[["pH"]])

        with c2:
            st.subheader("Light Intensity Over Time")
            st.line_chart(df_indexed[["light_lux"]])

        st.subheader("Recent Readings")
        st.dataframe(df.tail(20), use_container_width=True)

    st.info(
        "To update the values again, click the Rerun button in the top-right "
        "or refresh the page. (This page reads the sensors once per run.)"
    )


def page_fish_monitor():
    st.title("Fish Monitor")
    st.caption(
        "Opens a camera window and runs real-time threaded inference "
        "using the fish Roboflow model. Close the camera window with 'q' to return here."
    )

    if st.button("Start fish monitoring"):
        roboflow_threaded_monitor(FISH_MODEL_ID, "Fish Monitor")


def page_mint_monitor():
    st.title("Plant (Mint) Monitor")
    st.caption(
        "Opens a camera window and runs real-time threaded inference "
        "using the mint/plant Roboflow model. Close the camera window with 'q'."
    )

    if st.button("Start mint monitoring"):
        roboflow_threaded_monitor(MINT_MODEL_ID, "Mint Monitor")


# Route to selected page
if page == "Sensor Dashboard":
    page_sensor_dashboard()
elif page == "Fish Monitor":
    page_fish_monitor()
else:
    page_mint_monitor()


