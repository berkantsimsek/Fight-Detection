# 04 — Değerlendirme ve test

## `main/test_model.py` ile test seti değerlendirmesi

Betik:

1. `ImageDataGenerator(rescale=1./255)` ile `dataset/test` (veya `--test_dir`) altından görüntüleri yükler.
2. `load_model(model_path)` ile eğitilmiş `.keras` dosyasını açar.
3. `model.evaluate` ile test kaybı ve doğruluğu yazdırır.
4. Tüm test örnekleri için tahmin süresini ölçer ve örnek başına ortalama çıkarım süresini raporlar.
5. İlk 50 örnek için dosya adı, tahmin olasılığı ve gerçek etiket özetini konsola basar.
6. `classification_report`, confusion matrix görseli ve metin raporu `reports/<timestamp>/` ve `results/<timestamp>/` altına kaydedilir.

Çalıştırma (depo kökünden, [KURULUM.md](../KURULUM.md) ile uyumlu):

```bash
python main/test_model.py --test_dir dataset/test --model_path models/violence_model_v4.keras
```

Model yolu, eğitimde kullandığınız dosya ile aynı olmalıdır.

## `main/train_model.py` ile üretilen ek metrikler

Eğitim betiği doğrulama kümesi üzerinde:

- `classification_report`
- confusion matrix
- ROC eğrisi ve **AUC**

üretir ve `results/` altına grafik olarak yazar. Test kümesi için de ayrı sınıflandırma raporu ve confusion matrix kaydedilir.

## Tahmin eşikleri: 0.5 ile alarm eşiği farkı

### Model sınıf kararı (`violence_detector.detect`)

Model çıktısı sigmoid olasılığıdır. Kodda ikili etiket:

- `pred_proba > 0.5` → **Violence**
- aksi halde **Non-Violence**

Yani **sınıflandırma kararı için kullanılan eşik 0.5**’tir.

### Alarm ve kayıt (`AlarmManager.trigger`)

`main/violence_detection/main.py` içinde `alarm.trigger(..., SETTINGS["CONFIDENCE_THRESHOLD"], ...)` çağrılır. `config.py` içinde `CONFIDENCE_THRESHOLD` **0.7** olarak tanımlıdır.

`alarm_manager.py` içinde tetikleme koşulu:

- `label == "Violence"`
- `confidence > threshold` (çağrıda gelen değer; pratikte 0.7)
- soğuma süresi (`ALARM_COOLDOWN`, saniye) aşılmış olmalı

Burada `confidence`, `violence_detector` tarafından şöyle verilir: etiket Violence ise model olasılığı, Non-Violence ise `1 - pred_proba`. Dolayısıyla alarm için **Violence** seçilmiş ve modele göre güven **0.7 üstü** olmalıdır.

**Özet**: Model hâlâ 0.5 ile Violence/Non-Violence ayırır; alarm gürültüyü azaltmak için **daha yüksek bir güven eşiği** ister. Bu iki eşiği karıştırmamak, raporlama ve ayar yaparken önemlidir.

Sonraki adım: [05-gercek-zamanli-kullanim.md](05-gercek-zamanli-kullanim.md).
