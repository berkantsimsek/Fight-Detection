import time
import subprocess
import os
import cv2
import sqlite3
import platform
from datetime import datetime

class AlarmManager:
    def __init__(self, sound_file, screenshot_dir, db_path, screenshot_interval):
        self.sound_file = self._resolve_path(sound_file)
        self.screenshot_dir = screenshot_dir
        self.db_path = db_path
        self.screenshot_interval = screenshot_interval
        self.last_alarm_time = 0
        self.last_screenshot_time = 0
        self.process = None
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self._init_db()

    def _resolve_path(self, path):
        if os.path.isabs(path) or os.path.exists(path):
            return path
        package_path = os.path.join(os.path.dirname(__file__), path)
        return package_path if os.path.exists(package_path) else path

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS events (
                                                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                 timestamp TEXT,
                                                                 label TEXT,
                                                                 confidence REAL,
                                                                 screenshot_path TEXT,
                                                                 fps REAL,
                                                                 latency REAL
                           )
                           """)
            # Mevcut tabloya fps ve latency sütunları ekle (varsa hata vermez)
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN fps REAL")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN latency REAL")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def trigger(self, label, confidence, frame, fps, latency, threshold=0.6, cooldown=5):
        current_time = time.time()
        if label == "Violence" and confidence > threshold and current_time - self.last_alarm_time > cooldown:
            print(f"Alarm tetiklendi: {label}, Confidence: {confidence:.2f}, Zaman: {current_time}")
            self._play_sound()
            self.last_alarm_time = current_time

            # Ekran görüntüsü ve veritabanı kaydı
            if current_time - self.last_screenshot_time > self.screenshot_interval:
                self._save_event(label, confidence, frame, fps, latency)
            return True
        return False

    def _play_sound(self):
        if not os.path.exists(self.sound_file):
            print(f"Alarm sesi bulunamadi: {self.sound_file}")
            return
        try:
            if platform.system() == "Darwin":
                self.process = subprocess.Popen(["afplay", self.sound_file])
                return
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(self.sound_file)
                pygame.mixer.music.play()
            except Exception as pygame_error:
                print(f"Alarm sesi calinamadi: {pygame_error}")
        except Exception as e:
            print(f"Alarm sesi baslatilirken hata: {e}")

    def _save_event(self, label, confidence, frame, fps, latency):
        try:
            if frame is None:
                raise ValueError("Screenshot icin kare bulunamadi.")
            os.makedirs(self.screenshot_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"violence_{timestamp}.png")
            saved = cv2.imwrite(screenshot_path, frame)
            if not saved:
                raise RuntimeError(f"Screenshot kaydedilemedi: {screenshot_path}")
            self._log_event(label, confidence, screenshot_path, fps, latency)
            self.last_screenshot_time = time.time()
            print(f"Ekran görüntüsü kaydedildi: {screenshot_path}")
        except Exception as e:
            print(f"Screenshot/olay kaydi hatasi: {e}")

    def _log_event(self, label, confidence, screenshot_path, fps, latency):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = str(label)
        screenshot_path = str(screenshot_path)
        # Confidence'ın float olduğundan emin ol
        try:
            confidence = float(confidence)
        except (TypeError, ValueError) as e:
            print(f"Confidence dönüşüm hatası: {confidence}, hata: {e}")
            confidence = 0.0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO events (timestamp, label, confidence, screenshot_path, fps, latency) VALUES (?, ?, ?, ?, ?, ?)",
                    (timestamp, label, confidence, screenshot_path, fps, latency)
                )
                conn.commit()
                print(f"Veritabanına kaydedildi: timestamp={timestamp}, label={label}, confidence={confidence:.2f}")
        except Exception as e:
            print(f"Veritabanına kayıt hatası: {e}")

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            print("Alarm süreci sonlandırıldı.")
