import cv2
import numpy as np
from keras._tf_keras.keras.models import load_model
import time

def preprocess_frame(frame):
    # Kareyi 224x224 RGB formatına çevir
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV BGR'den RGB'ye
    resized = cv2.resize(rgb, (224, 224))         # 224x224'e boyutlandır
    normalized = resized / 255.0                  # Normalizasyon (0-1 arası)
    input_frame = np.expand_dims(normalized, axis=0)  # (1, 224, 224, 3) şekline getir
    return input_frame

def detect_violence_in_stream(model_path="violence_model_v4.keras", target_fps=15):
    # Webcam'i başlat
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hata: Kamera açılamadı.")
        return

    # Kameranın FPS'sini hedef değere ayarla (eğer destekliyorsa)
    cap.set(cv2.CAP_PROP_FPS, target_fps)

    # Modeli yükle
    model = load_model(model_path)

    # Hedef FPS'ye göre bekleme süresini hesapla
    frame_interval = 1.0 / target_fps  # Her kare arasındaki süre (saniye)

    frame_count = 0
    pred_label = "Non-Violence"  # Başlangıç varsayımı
    confidence = 0.0  # Başlangıç güven skoru
    fps_start_time = time.time()  # FPS hesaplaması için başlangıç zamanı
    fps_frame_count = 0  # FPS hesaplaması için kare sayacı

    while True:
        loop_start_time = time.time()

        # Kareyi oku
        ret, frame = cap.read()
        if not ret:
            print("Hata: Kare okunamadı.")
            break

        frame_count += 1
        fps_frame_count += 1

        # Her 5 karede bir tahmin yap
        if frame_count % 5 == 0:
            input_frame = preprocess_frame(frame)
            pred_proba = model.predict(input_frame, verbose=0)[0][0]  # Olasılık (0-1 arası)
            pred_label = "Violence" if pred_proba > 0.5 else "Non-Violence"
            confidence = pred_proba if pred_label == "Violence" else 1 - pred_proba

        # FPS hesapla (her saniye bir ortalama)
        current_time = time.time()
        elapsed_fps_time = current_time - fps_start_time
        if elapsed_fps_time >= 1.0:  # Her saniye FPS güncelle
            measured_fps = fps_frame_count / elapsed_fps_time
            fps_frame_count = 0
            fps_start_time = current_time
        else:
            measured_fps = target_fps  # İlk saniye için varsayılan değer

        # Sonucu kare üzerine yaz
        label = f"{pred_label} ({confidence:.2f}) | FPS: {measured_fps:.1f}"
        color = (0, 0, 255) if pred_label == "Violence" else (0, 255, 0)  # Kırmızı: Şiddet, Yeşil: Şiddetsiz
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

        # Kareyi göster
        cv2.imshow("Violence Detection", frame)

        # Hedef FPS'ye göre bekleme süresi
        elapsed_time = time.time() - loop_start_time
        wait_time = max(1, int((frame_interval - elapsed_time) * 1000))  # ms cinsinden
        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            break

    # Kaynakları serbest bırak
    cap.release()
    cv2.destroyAllWindows()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Modeli test etme aracı")
    parser.add_argument("--model_path", default="models/violence_model_v4.keras", help="Eğitilmiş model dosyası")
    parser.add_argument("--target_fps", type=int, default=15, help="Hedef FPS değeri")
    args = parser.parse_args()

    detect_violence_in_stream(args.model_path, args.target_fps)

if __name__ == "__main__":
    main()