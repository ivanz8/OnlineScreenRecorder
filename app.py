from flask import Flask, send_file, render_template, request
import cv2
import numpy as np
import pyautogui
import os
import threading

app = Flask(__name__)

VIDEO_PATH = os.path.join(os.getcwd(), "video.mp4")
recording = False
out = None

def record_screen():
    global recording, out
    SCREEN_SIZE = tuple(pyautogui.size())
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4v codec for MP4 format
    fps = 12.0
    out = cv2.VideoWriter(VIDEO_PATH, fourcc, fps, SCREEN_SIZE)
    
    while recording:
        img = pyautogui.screenshot()  # Capture the entire screen
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV

        out.write(frame)  # Write the frame to the video file

        # Optional: Save a few frames for debugging
        # cv2.imwrite("frame.png", frame)

    out.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording
    if not recording:
        recording = True
        threading.Thread(target=record_screen).start()
        return "Recording started!"
    return "Already recording!"

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording
    if recording:
        recording = False
        return "Recording stopped!"
    return "No recording in progress!"

@app.route('/download_video')
def download_video():
    if os.path.exists(VIDEO_PATH):
        try:
            return send_file(VIDEO_PATH, as_attachment=True)
        except Exception as e:
            return f"Error serving file: {e}"
    else:
        return "No video found."

if __name__ == '__main__':
    app.run(debug=True)
