import argparse
import time
from threading import Thread
from .video_stream import VideoStream
from .violence_detector import ViolenceDetector
from .detection_gui import DetectionGUI
from .alarm_manager import AlarmManager
from .report_generator import ReportGenerator
from .config import SETTINGS
import tkinter as tk

def main():
    parser = argparse.ArgumentParser(description="RTSP ile gerçek zamanlı şiddet tespiti")
    parser.add_argument("--rtsp_url", required=False, help="Tapo C100 RTSP adresi")
    parser.add_argument("--model_path", default=SETTINGS["MODEL_PATH"], help="Eğitilmiş model dosyası")
    parser.add_argument("--target_fps", type=int, default=SETTINGS["TARGET_FPS"], help="Hedef FPS değeri")
    parser.add_argument("--test", action="store_true", help="Test modunu aktif et")
    args = parser.parse_args()

    # Modülleri başlat
    stream_source = args.rtsp_url if args.rtsp_url else 0
    stream = VideoStream(stream_source, args.target_fps)
    detector = ViolenceDetector(args.model_path, test_mode=args.test)
    alarm = AlarmManager(
        SETTINGS["ALARM_SOUND"],
        SETTINGS["SCREENSHOT_DIR"],
        SETTINGS["DB_PATH"],
        SETTINGS["SCREENSHOT_INTERVAL"]
    )
    report_generator = ReportGenerator(SETTINGS["DB_PATH"], SETTINGS["REPORT_PATH"])
    root = tk.Tk()
    gui = DetectionGUI(
        root,
        SETTINGS["CANVAS_WIDTH"],
        SETTINGS["CANVAS_HEIGHT"],
        detector,
        alarm_manager=alarm,
        report_generator=report_generator
    )

    def on_closing():
        stream.stop()
        alarm.stop()
        gui.stop()
        root.quit()
        root.destroy()
        print("Program tamamlandı.")

    def run_detection():
        try:
            frame_count = 0
            fps_start_time = time.time()
            fps_frame_count = 0
            stream_generator = None
            label = "Non-Violence"
            confidence = 0.0
            motion = False

            while True:
                if gui.running and stream_generator is None:
                    stream_generator = stream.start()
                elif not gui.running and stream_generator is not None:
                    stream.stop()
                    stream_generator = None
                    frame_count = 0

                if gui.running and stream_generator is not None:
                    try:
                        frame = next(stream_generator)
                        frame_count += 1
                        fps_frame_count += 1
                        loop_start_time = time.time()

                        if frame_count % SETTINGS["DETECTION_INTERVAL"] == 0:
                            label, confidence, motion = detector.detect(frame, SETTINGS["MOTION_THRESHOLD"])
                            print(f"Tahmin: {label}, Confidence: {confidence:.3f}, Motion: {motion}")

                        # Alarm ve ekran görüntüsü
                        if frame_count % SETTINGS["DETECTION_INTERVAL"] == 0:
                            alarm.trigger(
                                label,
                                confidence,
                                frame.copy(),
                                gui.fps,
                                gui.latency,
                                SETTINGS["CONFIDENCE_THRESHOLD"],
                                SETTINGS["ALARM_COOLDOWN"]
                            )

                        # FPS hesapla
                        elapsed_fps_time = time.time() - fps_start_time
                        if elapsed_fps_time >= 1.0:
                            fps = fps_frame_count / elapsed_fps_time
                            fps_frame_count = 0
                            fps_start_time = time.time()
                        else:
                            fps = args.target_fps

                        latency = time.time() - loop_start_time

                        # GUI güncelle
                        gui.frame = frame
                        gui.label = label
                        gui.confidence = confidence
                        gui.fps = fps
                        gui.latency = latency

                    except StopIteration:
                        stream.stop()
                        stream_generator = None

                time.sleep(0.01)
        except Exception as e:
            print(f"Error in detection thread: {e}")

    # Thread ile çalıştır
    detection_thread = Thread(target=run_detection, daemon=True)
    detection_thread.start()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
