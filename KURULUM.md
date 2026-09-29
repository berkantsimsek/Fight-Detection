# Violence Detection - Kurulum ve Kullanım

## Gereksinimler
- Python 3.12
- Webcam veya RTSP destekli IP kamera

## Kurulum

### 1. Sanal ortam oluştur ve aktif et

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Kütüphaneleri yükle
```bash
pip install -r requirements.txt
```

## Kullanım

### Gerçek zamanlı tespit (webcam veya IP kamera)
```bash
python main/real_time_testing.py
```

### Model test etme
```bash
python main/test_model.py
```

### Model eğitme
```bash
python main/train_model.py
```

## Notlar
- Eğitilmiş model `models/` klasöründe
- Tespit ekran görüntüleri `main/screenshots/` klasörüne kaydedilir
- PDF raporlar `main/pdfReports/` klasörüne oluşturulur
- IP kamera kullanmak için `real_time_testing.py` içindeki RTSP URL'ini güncelle
