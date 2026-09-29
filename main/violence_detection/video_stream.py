import cv2
import time

class VideoStream:
    def __init__(self, rtsp_url, target_fps):
        self.rtsp_url = rtsp_url
        self.target_fps = target_fps
        self.cap = None
        self.running = False

    def _initialize(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.rtsp_url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        if not self.cap.isOpened():
            raise RuntimeError(f"RTSP akışı açılamadı: {self.rtsp_url}")

    def start(self):
        self._initialize()
        self.running = True
        frame_interval = 1.0 / self.target_fps
        while self.running:
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                print("Uyarı: Kare okunamadı, akış devam ediyor...")
                time.sleep(0.1)
                continue
            yield frame
            elapsed = time.time() - start_time
            time.sleep(max(0, frame_interval - elapsed))

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()