import argparse
import os
import time
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from keras._tf_keras.keras.models import load_model
from keras._tf_keras.keras.preprocessing.image import ImageDataGenerator

# Ayarlar
IMG_SIZE = 224
BATCH_SIZE = 16
REPORTS_PATH = "reports"

def evaluate_test_set(model_path, test_dir):
    # Klasör ve model kontrolü
    if not os.path.exists(test_dir):
        raise FileNotFoundError(f"Test klasörü bulunamadı: {test_dir}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")

    # Test data generator
    test_datagen = ImageDataGenerator(rescale=1./255)
    test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        shuffle=False
    )

    # Modeli yükle
    model = load_model(model_path)

    # Test seti değerlendirmesi
    test_loss, test_accuracy = model.evaluate(test_generator, verbose=1)
    print(f"Test Accuracy: {test_accuracy:.4f}, Test Loss: {test_loss:.4f}")

    # Tahminler
    test_generator.reset()
    start_time = time.time()
    y_pred_proba = model.predict(test_generator, verbose=1)
    inference_time = time.time() - start_time
    print(f"Toplam inference süresi: {inference_time:.2f} saniye, örnek başına: {inference_time/len(test_generator.filenames):.4f} saniye")

    y_pred = (y_pred_proba > 0.5).astype("int32").flatten()
    y_true = test_generator.classes
    filenames = test_generator.filenames

    # Sonuçları yazdır
    print("\nTest Seti Üzerinde Tahminler:")
    for i in range(min(50, len(filenames))):
        pred_label = "Violence" if y_pred[i] == 1 else "Non-Violence"
        true_label = "Violence" if y_true[i] == 1 else "Non-Violence"
        prob = y_pred_proba[i][0]
        print(f"Dosya: {filenames[i]} | Tahmin: {pred_label} ({prob:.4f}) | Gerçek: {true_label}")

    # Performans metrikleri
    accuracy = accuracy_score(y_true, y_pred)
    print(f"\nTest Seti Doğruluğu: {accuracy:.4f}")
    print("\nSınıflandırma Raporu:")
    report = classification_report(y_true, y_pred, target_names=["Non-Violence", "Violence"])
    print(report)

    # Classification report'u kaydet
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    reports_path = os.path.join(REPORTS_PATH, timestamp)
    os.makedirs(reports_path, exist_ok=True)
    with open(os.path.join(reports_path, "test_classification_report.txt"), "w") as f:
        f.write(report)

    # Confusion matrix
    result_dir = f"results/{timestamp}"
    os.makedirs(result_dir, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=['Non-Violence', 'Violence'], yticklabels=['Non-Violence', 'Violence'])
    plt.title("Test Confusion Matrix")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.savefig(os.path.join(result_dir, "test_confusion_matrix.png"))
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Modeli test etme aracı")
    parser.add_argument("--test_dir", default="dataset/test", help="Test setinin klasörü")
    parser.add_argument("--model_path", default="violence_model_v4.keras", help="Eğitilmiş model dosyası")
    args = parser.parse_args()

    evaluate_test_set(args.model_path, args.test_dir)

if __name__ == "__main__":
    main()