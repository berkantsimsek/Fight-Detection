import os
import cv2
import numpy as np
from keras._tf_keras.keras.preprocessing.image import ImageDataGenerator
import argparse

def augment_frames(input_folder, output_folder, num_augmented=5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # RGB için veri artırma ayarları
    datagen = ImageDataGenerator(
        rotation_range=30,          # -30° ile +30° arası döndürme
        width_shift_range=0.1,      # Yatayda %10 kaydırma
        height_shift_range=0.1,     # Dikeyde %10 kaydırma
        brightness_range=[0.8, 1.2],# Parlaklık %80-%120 arası
        horizontal_flip=True,       # Yatay aynalama
        fill_mode="nearest"         # Boşlukları yakındaki piksellerle doldur
    )

    # Her alt klasörü işle
    for subfolder in os.listdir(input_folder):
        subfolder_path = os.path.join(input_folder, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        output_subfolder = os.path.join(output_folder, subfolder)
        if not os.path.exists(output_subfolder):
            os.makedirs(output_subfolder)

        for img_file in os.listdir(subfolder_path):
            if img_file.endswith(".jpg"):
                img_path = os.path.join(subfolder_path, img_file)
                # RGB olarak oku
                img = cv2.imread(img_path)  # BGR formatında gelir
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # RGB’ye çevir
                img = cv2.resize(img, (224, 224))  # 224x224’e küçült
                img = np.expand_dims(img, axis=0)  # (1, 224, 224, 3) şekline getir

                # Artırılmış kareleri kaydet
                i = 0
                for batch in datagen.flow(img, batch_size=1, save_to_dir=output_subfolder,
                                          save_prefix=f"{subfolder}_aug", save_format="jpg"):
                    i += 1
                    if i >= num_augmented:
                        break
        print(f"{subfolder}: {num_augmented} artırılmış kare oluşturuldu.")

def main():
    parser = argparse.ArgumentParser(description="Kareleri artırma aracı")
    parser.add_argument("--violence_frames", default="dataset/violence_frames",
                        help="Orijinal violence karelerinin klasörü")
    parser.add_argument("--nonViolence_frames", default="dataset/nonViolence_frames",
                        help="Orijinal nonViolence karelerinin klasörü")
    parser.add_argument("--output_base", default="dataset",
                        help="Artırılmış karelerin ana dizini")
    parser.add_argument("--num_augmented", type=int, default=5,
                        help="Her kare için oluşturulacak artırılmış kare sayısı")
    args = parser.parse_args()

    violence_input = args.violence_frames
    nonViolence_input = args.nonViolence_frames
    output_base = args.output_base
    num_augmented = args.num_augmented

    # Çıktı klasörleri
    violence_output = os.path.join(output_base, "violence_frames_augmented")
    nonViolence_output = os.path.join(output_base, "nonViolence_frames_augmented")

    # Violence karelerini artır
    if os.path.exists(violence_input):
        augment_frames(violence_input, violence_output, num_augmented)
    else:
        print(f"Hata: {violence_input} bulunamadı.")

    # NonViolence karelerini artır
    if os.path.exists(nonViolence_input):
        augment_frames(nonViolence_input, nonViolence_output, num_augmented)
    else:
        print(f"Hata: {nonViolence_input} bulunamadı.")

if __name__ == "__main__":
    main()