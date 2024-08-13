import cv2
import numpy as np
import mss
import time
import threading
import logging
import tempfile
import os
from flask import Flask, request, jsonify, send_file, render_template
from plyer import notification

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

app = Flask(__name__)

# Global variables
recorder = None
recording_thread = None
stop_event = threading.Event()

class ScreenRecorder:
    def __init__(self, filename, frame_rate, codec):
        self.filename = filename
        self.frame_rate = frame_rate
        self.codec = codec
        self.screen_size = (1920, 1080)  # Set default resolution; you can adjust as needed
        self.video = None
        self.paused = False
        self.start_time = None

    def start_recording(self):
        try:
            # Initialize video writer
            self.video = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*self.codec), self.frame_rate, self.screen_size)
            notification.notify(
                title='SCREEN RECORDING!',
                message="Your screen is being recorded...",
                app_name="Screen Recorder"
            )
            print("Status: Recording...")

            self.start_time = time.time()
            self.recording_loop()

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            print("Status: Error occurred during recording")

    def recording_loop(self):
        try:
            with mss.mss() as sct:
                while not stop_event.is_set():
                    if not self.paused:
                        img = sct.grab(sct.monitors[1])  # Capture the first monitor
                        frame = np.array(img)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)  # Convert RGBA to BGR

                        if self.video is not None:
                            self.video.write(frame)

                    time.sleep(1 / self.frame_rate)

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            print("Status: Error occurred during recording")

    def stop_recording(self):
        if self.video:
            self.video.release()
            self.video = None
            cv2.destroyAllWindows()
            notification.notify(
                title='RECORDING ENDED!',
                message="Recording stopped. Your file has been saved successfully.",
                app_name="Screen Recorder"
            )
            print("Status: Recording stopped")

    def get_video_file(self):
        return self.filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recorder, recording_thread, stop_event
    if recorder and recording_thread and recording_thread.is_alive():
        return jsonify({"error": "Recording is already in progress"}), 400

    filename = 'output.avi'
    frame_rate = int(request.form.get('frame_rate', 30))
    codec = request.form.get('codec', 'MJPG')

    # Create a temporary file for video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.avi') as temp_file:
        temp_filename = temp_file.name

    recorder = ScreenRecorder(temp_filename, frame_rate, codec)
    stop_event.clear()
    recording_thread = threading.Thread(target=recorder.start_recording)
    recording_thread.start()

    return jsonify({"status": "Recording started"}), 200

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recorder, recording_thread, stop_event
    if not recorder or not recording_thread or not recording_thread.is_alive():
        return jsonify({"error": "No recording in progress"}), 400

    stop_event.set()
    recording_thread.join()
    recorder.stop_recording()

    # Provide the recorded file as a downloadable response
    video_file = recorder.get_video_file()
    return send_file(video_file, as_attachment=True, download_name='recording.avi')

@app.route('/status', methods=['GET'])
def status():
    global recorder, recording_thread
    if recorder and recording_thread and recording_thread.is_alive():
        return jsonify({"status": "Recording in progress"}), 200
    return jsonify({"status": "No recording in progress"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
