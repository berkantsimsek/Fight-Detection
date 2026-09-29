import os
import argparse

def rename_videos(folder_path, prefix, extension=".mp4"):
    # Klasörün varlığını kontrol et
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Klasör bulunamadı: {folder_path}")

    # Klasördeki dosyaları listele
    files = [f for f in os.listdir(folder_path) if f.endswith(extension)]
    files.sort()

    # Her dosyayı yeniden adlandır
    for i, old_name in enumerate(files, 1):
        new_name = f"{prefix}{i:03d}{extension}"
        old_path = os.path.join(folder_path, old_name)
        new_path = os.path.join(folder_path, new_name)
        if os.path.exists(new_path):
            print(f"Hata: {new_name} zaten var, atlanıyor.")
        else:
            os.rename(old_path, new_path)
            print(f"{old_name} → {new_name}")

def main():
    # Komut satırı argümanlarını tanımla
    parser = argparse.ArgumentParser(description="Videoları yeniden adlandırma aracı")
    parser.add_argument("--violence_dir", default="dataset/violence",
                        help="Violence videolarının bulunduğu klasör")
    parser.add_argument("--nonViolence_dir", default="dataset/nonViolence",
                        help="NonViolence videolarının bulunduğu klasör")
    args = parser.parse_args()

    # Klasör yollarını al
    violence_dir = args.violence_dir
    nonViolence_dir = args.nonViolence_dir

    # Yeniden adlandır
    try:
        rename_videos(violence_dir, "violence")
        rename_videos(nonViolence_dir, "nonViolence")
    except FileNotFoundError as e:
        print(e)
        print("Klasör bulunamadı yada bir şeyler yanlış gitti!")

if __name__ == "__main__":
    main()