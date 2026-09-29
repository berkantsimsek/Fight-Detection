import argparse
import os
import time
from datetime import datetime
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from keras._tf_keras.keras.applications import MobileNetV2
from keras._tf_keras.keras.models import Model
from keras._tf_keras.keras.layers import Dense, GlobalAveragePooling2D, Input
from keras._tf_keras.keras.preprocessing.image import ImageDataGenerator
from keras._tf_keras.keras.optimizers import Adam
from keras._tf_keras.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

# M1 için mixed precision
from keras._tf_keras.keras.mixed_precision import set_global_policy
set_global_policy('mixed_float16')

# Ayarlar
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 15
REPORTS_PATH = "reports"

def train_model(train_dir, test_dir, model_path="violence_model_v4.keras"):
    # Klasörler yoksa oluştur
    os.makedirs(REPORTS_PATH, exist_ok=True)

    # Veri klasörlerini kontrol et
    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"Eğitim klasörü bulunamadı: {train_dir}")
    if not os.path.exists(test_dir):
        raise FileNotFoundError(f"Test klasörü bulunamadı: {test_dir}")

    # Data generator'lar
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=30,
        width_shift_range=0.3,
        height_shift_range=0.3,
        shear_range=0.3,
        zoom_range=0.3,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )

    val_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)
    test_datagen = ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        subset='training',
        shuffle=True
    )

    val_generator = val_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        subset='validation',
        shuffle=False
    )

    test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        shuffle=False
    )

    base_model = MobileNetV2(weights='imagenet', include_top=False, input_tensor=Input(shape=(IMG_SIZE, IMG_SIZE, 3)))
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    output = Dense(1, activation='sigmoid', dtype='float32')(x)

    model = Model(inputs=base_model.input, outputs=output)
    model.compile(optimizer=Adam(learning_rate=0.0001), loss='binary_crossentropy', metrics=['accuracy'])

    model.summary()
    time.sleep(5)

    # Callbacks
    checkpoint = ModelCheckpoint(model_path, monitor='val_accuracy', save_best_only=True, verbose=1)
    early_stop = EarlyStopping(monitor='val_accuracy', patience=7, verbose=1, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=2, min_lr=1e-6, verbose=1)

    # İlk eğitim
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )

    # Fine-tuning
    base_model.trainable = True
    for layer in base_model.layers[:-30]:  # Son 30 katmanı eğit
        layer.trainable = False
    model.compile(optimizer=Adam(learning_rate=1e-5), loss='binary_crossentropy', metrics=['accuracy'])

    # Fine-tuning eğitimi
    history_fine = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )

    # Tahmin ve metrikler (doğrulama seti)
    val_generator.reset()
    preds = model.predict(val_generator, verbose=1)
    y_pred = (preds > 0.5).astype(int)
    y_true = val_generator.classes

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_path = os.path.join(REPORTS_PATH, timestamp)
    os.makedirs(reports_path, exist_ok=True)  # Rapor klasörünü oluştur

    # Classification report
    report = classification_report(y_true, y_pred, target_names=list(val_generator.class_indices.keys()))
    with open(os.path.join(reports_path, "classification_report.txt"), "w") as f:
        f.write(report)

    # Klasör oluştur (tarih ve saatle)
    result_dir = f"results/{timestamp}"
    os.makedirs(result_dir, exist_ok=True)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=val_generator.class_indices.keys(), yticklabels=val_generator.class_indices.keys())
    plt.title("Confusion Matrix")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.savefig(os.path.join(result_dir, "confusion_matrix.png"))
    plt.close()

    # ROC Curve
    fpr, tpr, thresholds = roc_curve(y_true, preds)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.savefig(os.path.join(result_dir, "roc_curve.png"))
    plt.close()

    # Accuracy ve Loss grafikleri
    plt.figure()
    plt.plot(history.history["accuracy"] + history_fine.history["accuracy"], label="Train Accuracy")
    plt.plot(history.history["val_accuracy"] + history_fine.history["val_accuracy"], label="Validation Accuracy")
    plt.title("Accuracy")
    plt.legend()
    plt.savefig(os.path.join(result_dir, "accuracy.png"))
    plt.close()

    plt.figure()
    plt.plot(history.history["loss"] + history_fine.history["loss"], label="Train Loss")
    plt.plot(history.history["val_loss"] + history_fine.history["val_loss"], label="Validation Loss")
    plt.title("Loss")
    plt.legend()
    plt.savefig(os.path.join(result_dir, "loss.png"))
    plt.close()

    # Eğitim geçmişini kaydet
    with open(os.path.join(reports_path, "train_history.pkl"), "wb") as f:
        pickle.dump({"initial": history.history, "fine_tune": history_fine.history}, f)

    # Test seti değerlendirmesi
    test_generator.reset()
    test_loss, test_accuracy = model.evaluate(test_generator, verbose=1)
    print(f"Test Accuracy: {test_accuracy:.4f}, Test Loss: {test_loss:.4f}")

    test_preds = model.predict(test_generator, verbose=1)
    test_y_pred = (test_preds > 0.5).astype(int)
    test_y_true = test_generator.classes
    test_report = classification_report(test_y_true, test_y_pred, target_names=list(test_generator.class_indices.keys()))
    with open(os.path.join(reports_path, "test_classification_report.txt"), "w") as f:
        f.write(test_report)

    # Test confusion matrix
    test_cm = confusion_matrix(test_y_true, test_y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(test_cm, annot=True, fmt='d', xticklabels=test_generator.class_indices.keys(), yticklabels=test_generator.class_indices.keys())
    plt.title("Test Confusion Matrix")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.savefig(os.path.join(result_dir, "test_confusion_matrix.png"))
    plt.close()

    print("Saved training history and test results, exiting.")

def main():
    parser = argparse.ArgumentParser(description="Görüntü analiz modelini eğitme aracı")
    parser.add_argument("--train_dir", default="dataset/train", help="Eğitim setinin klasörü")
    parser.add_argument("--test_dir", default="dataset/test", help="Test setinin klasörü")
    parser.add_argument("--model_path", default="violence_model_v4.keras", help="Kaydedilecek model dosyası")
    args = parser.parse_args()

    train_model(args.train_dir, args.test_dir, args.model_path)

if __name__ == "__main__":
    main()
