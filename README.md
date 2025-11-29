# Aquanexus: AI & ML Driven Aquaponics Health Monitoring System

Aquanexus is an AI, ML, and IoT-powered aquaponics monitoring system designed to track **fish health**, **plant health**, and **water quality** in real time. The system integrates Raspberry Pi sensors with computer vision models deployed via Roboflow, providing a complete smart farming dashboard for sustainable aquaponics management.

---

## 🌱 Overview

This project monitors:
- **pH levels** using ADS1115 + pH probe  
- **Light intensity** using BH1750  
- **Fish health** using a Roboflow-trained object detection model  
- **Plant (Mint) health** using another Roboflow detection model  

A custom-built **Streamlit dashboard** allows users to view data, watch real-time detections, and observe trends for better decision-making.

---

## 🧩 Features

### 🔹 Sensor Dashboard
- Real-time pH and light readings  
- pH calculation using calibrated voltage  
- Light intensity in lux  
- Line charts for pH and light over time  
- Auto-updating history log  

### 🔹 Fish Monitor
- Opens webcam feed  
- Sends frames to Roboflow API  
- Draws bounding boxes, labels, and confidence  
- Uses threaded inference for smooth real-time detection  
- Close the window using **q**

### 🔹 Plant (Mint) Monitor
- Similar setup as Fish Monitor  
- Detects mint plant health issues  
- Useful for early-stage disease detection or stress analysis  

---

## 🧱 Hardware Requirements

- Raspberry Pi (with I2C enabled)
- ADS1115 ADC module
- pH probe
- BH1750 light sensor
- USB or Pi Camera
- Aquaponics tank system

---

## 🛠️ Software Requirements

- Python 3.x  
- Streamlit  
- OpenCV  
- Pandas  
- smbus2  
- Requests  
- Roboflow API Key  

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/aquanexus.git
cd aquanexus
