import os
import shutil
import random
import argparse

def split_dataset(violence_input, nonViolence_input, train_output, test_output, train_ratio=0.8):
    # Eğitim ve test klasörlerini oluştur
    for folder in [train_output, test_output]:
        for subfolder in ["violence", "nonViolence"]:
            os.makedirs(os.path.join(folder, subfolder), exist_ok=True)

    # Girdi klasörlerini kontrol et
    if not os.path.exists(violence_input):
        raise FileNotFoundError(f"Violence kareleri klasörü bulunamadı: {violence_input}")
    if not os.path.exists(nonViolence_input):
        raise FileNotFoundError(f"NonViolence kareleri klasörü bulunamadı: {nonViolence_input}")

    # Her sınıf için işlem yap
    for class_name, class_input in [("violence", violence_input), ("nonViolence", nonViolence_input)]:
        all_files = []
        for subfolder in os.listdir(class_input):
            subfolder_path = os.path.join(class_input, subfolder)
            if os.path.isdir(subfolder_path):
                for img_file in os.listdir(subfolder_path):
                    if img_file.endswith(".jpg"):
                        all_files.append(os.path.join(subfolder_path, img_file))

        # Rastgele karıştır
        random.shuffle(all_files)

        # Eğitim ve test setlerine böl
        train_size = int(len(all_files) * train_ratio)
        train_files = all_files[:train_size]
        test_files = all_files[train_size:]

        # Eğitim setini kopyala
        for file in train_files:
            shutil.copy(file, os.path.join(train_output, class_name, os.path.basename(file)))

        # Test setini kopyala
        for file in test_files:
            shutil.copy(file, os.path.join(test_output, class_name, os.path.basename(file)))

        print(f"{class_name}: {len(train_files)} eğitim, {len(test_files)} test karesi ayrıldı.")

def main():
    parser = argparse.ArgumentParser(description="Veri setini eğitim ve test olarak bölme aracı")
    parser.add_argument("--violence_frames", default="dataset/violence_frames_augmented",
                        help="Artırılmış violence karelerinin klasörü")
    parser.add_argument("--nonViolence_frames", default="dataset/nonViolence_frames_augmented",
                        help="Artırılmış nonViolence karelerinin klasörü")
    parser.add_argument("--output_base", default="dataset",
                        help="Eğitim ve test setlerinin ana dizini")
    parser.add_argument("--train_ratio", type=float, default=0.8,
                        help="Eğitim setinin oranı (0-1 arası)")
    args = parser.parse_args()

    train_output = os.path.join(args.output_base, "train")
    test_output = os.path.join(args.output_base, "test")

    # Mevcut klasörleri temizle
    if os.path.exists(train_output):
        shutil.rmtree(train_output)
    if os.path.exists(test_output):
        shutil.rmtree(test_output)

    # Tek çağrıda her iki sınıfı işle
    split_dataset(args.violence_frames, args.nonViolence_frames, train_output, test_output, args.train_ratio)

if __name__ == "__main__":
    main()