# 05 — Gerçek zamanlı kullanım

## Ön işlemenin eğitimle uyumu

Canlı veya video akışından gelen kareler, eğitimdekiyle aynı mantıkta işlenmelidir:

1. OpenCV varsayılan olarak **BGR** okur; model **RGB** bekler — `cv2.cvtColor(..., COLOR_BGR2RGB)`.
2. Boyut **224×224** (`cv2.resize`).
3. Piksel değerleri **255.0’a bölünerek** [0, 1] aralığına getirilir.
4. Model girişi için batch boyutu eklenir: `np.expand_dims(..., axis=0)` → şekil `(1, 224, 224, 3)`.

Bu adımlar `main/violence_detection/violence_detector.py` içindeki `preprocess_frame` ile yapılır; `main/real_time_testing.py` içinde benzer bir `preprocess_frame` bulunur.

## Hareket ön filtresi (MOG2)

`ViolenceDetector` içinde `cv2.createBackgroundSubtractorMOG2()` kullanılır. Özet akış:

1. Arka plan çıkarımı ile ön plan maskesi üretilir.
2. `cv2.countNonZero(fgmask)` ile hareket piksel sayısı ölçülür.
3. Bu sayı `motion_threshold` (varsayılan 1000; `config.py` üzerinden `MOTION_THRESHOLD`) altındaysa model **çağrılmaz** ve sonuç **Non-Violence**, güven 0.0 döner.

**Amaç**: Statik sahnelerde gereksiz model çalışmasını azaltmak ve bazı durumlarda yanlış pozitifleri sınırlamak. Eşik, sahneye göre ayarlanabilir; çok düşük olursa model sık çalışır, çok yüksek olursa gerçek hareket kaçabilir.

## İki çalıştırma yolu

### 1. Basit webcam testi

`main/real_time_testing.py`: webcam açılır, varsayılan model yolu `violence_model_v4.keras` (betik içi varsayılan). Her 5 karede bir tahmin yapılır ([KURULUM.md](../KURULUM.md)).

### 2. Tam uygulama (GUI, alarm, rapor)

Paket modülü:

```bash
python -m main.violence_detection.main --rtsp_url "<rtsp_url>"
```

`--model_path` ile model dosyası geçilebilir; verilmezse `config.py` içindeki `MODEL_PATH` kullanılır: `models/violence_model_v4.keras`.

Kök [README.md](../README.md) dosyasında RTSP veya yerel kamera için ek notlar vardır.

## Model yolu tutarlılığı

| Bileşen | Varsayılan model yolu |
|---------|------------------------|
| `train_model.py` | `violence_model_v4.keras` (çalışma dizini) |
| `test_model.py` | `violence_model_v4.keras` |
| `real_time_testing.py` | `violence_model_v4.keras` |
| `violence_detection/config.py` | `models/violence_model_v4.keras` |

Eğitimden sonra canlı uygulamayı çalıştıracaksanız dosyayı `models/` altına koyun veya `--model_path` / `MODEL_PATH` ile aynı dosyayı gösterin.

## Diğer ilgili ayarlar (`config.py`)

- `TARGET_FPS`: akış hedefi.
- `SCREENSHOT_DIR`, `REPORT_PATH`, `DB_PATH`: olay ve rapor çıktıları.
- `SCREENSHOT_INTERVAL`: ardışık ekran görüntüsü için minimum süre (saniye).

Dokümantasyon indeksi: [README.md](README.md).
