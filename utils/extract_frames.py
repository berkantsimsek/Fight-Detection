import cv2
import os
import argparse

def extract_frames(video_path, output_folder, target_fps=5, max_duration=10):
    # Video adını al (uzantısız)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    # Video için özel çıktı klasörü oluştur yoksa
    video_output_folder = os.path.join(output_folder, video_name)
    if not os.path.exists(video_output_folder):
        os.makedirs(video_output_folder)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Hata: {video_path} açılamadı.")
        return

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    if original_fps <= 0:  # Geçersiz FPS kontrolü
        original_fps = 30  # Varsayılan değer
    frame_interval = max(int(original_fps / target_fps), 1)  # En az 1 olsun
    max_frames = int(max_duration * target_fps)

    frame_count = 0
    saved_count = 0
    while cap.isOpened() and saved_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame = cv2.resize(frame, (224, 224))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # RGB’ye çevir
            output_path = f"{video_output_folder}/{video_name}_frame_{saved_count:05d}.jpg"
            if cv2.imwrite(output_path, cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)):  # BGR olarak kaydet
                saved_count += 1
            else:
                print(f"Hata: {output_path} kaydedilemedi.")
        frame_count += 1

    cap.release()
    print(f"{video_path}: {saved_count} kare çıkarıldı (orijinal FPS: {original_fps}).")

def main():
    parser = argparse.ArgumentParser(description="Videolardan kare çıkarma aracı")
    parser.add_argument("--violence_dir", default="dataset/violence",
                        help="Violence videolarının klasörü")
    parser.add_argument("--nonViolence_dir", default="dataset/nonViolence",
                        help="NonViolence videolarının klasörü")
    parser.add_argument("--output_base", default="dataset",
                        help="Çıktı klasörlerinin ana dizini")
    args = parser.parse_args()

    violence_dir = args.violence_dir
    nonViolence_dir = args.nonViolence_dir
    output_base = args.output_base

    # Çıktı klasörleri
    violence_output = os.path.join(output_base, "violence_frames")
    nonViolence_output = os.path.join(output_base, "nonViolence_frames")

    # Violence videolarını işle
    if os.path.exists(violence_dir):
        for video in os.listdir(violence_dir):
            if video.lower().endswith((".mp4", ".avi", ".mov")):  # Daha fazla format
                video_path = os.path.join(violence_dir, video)
                extract_frames(video_path, violence_output)
    else:
        print(f"Hata: {violence_dir} bulunamadı.")

    # NonViolence videolarını işle
    if os.path.exists(nonViolence_dir):
        for video in os.listdir(nonViolence_dir):
            if video.lower().endswith((".mp4", ".avi", ".mov")):  # Daha fazla format
                video_path = os.path.join(nonViolence_dir, video)
                extract_frames(video_path, nonViolence_output)
    else:
        print(f"Hata: {nonViolence_dir} bulunamadı.")

if __name__ == "__main__":
    main()