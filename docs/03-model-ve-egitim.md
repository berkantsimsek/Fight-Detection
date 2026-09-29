# 03 - Model ve Kullanım Akışı

Bu bölüm, Canlı Kavga Tespiti ve Raporlanması Projesi'nde kullanılan görüntü analiz modelinin proje içindeki yerini özetler. Sunum dokümanı teknik mimari ayrıntılarına girmeden, modelin uygulama akışındaki rolünü açıklar.

## Modelin Rolü

Model, canlı kameradan alınan karelerde şiddet / şiddet değil kararını desteklemek için kullanılır. Uygulama önce hareket kontrolü yapar; hareket yoksa gereksiz analiz çalıştırılmaz. Hareket varsa kare uygun boyuta getirilir ve karar modeli sonucu hesaplanır.

## Canlı Uygulamadaki Akış

1. Kamera veya RTSP akışından kare alınır.
2. Hareket filtresi statik sahneleri eler.
3. Gerekli kareler analiz için hazırlanır.
4. Sonuç, güven skoru, FPS ve gecikme UI üzerinde gösterilir.
5. Güven skoru eşik üstündeyse alarm, ekran görüntüsü ve olay kaydı süreci çalışır.

## Model Dosyası

Canlı uygulama varsayılan olarak şu modeli kullanır:

```text
models/violence_model_v4.keras
```

Bu yol `main/violence_detection/config.py` içindeki `MODEL_PATH` ayarıyla yönetilir.

## Raporlama İlişkisi

Model sonucu doğrudan PDF rapora yazılmaz. Rapor, yalnızca olay kayıtlarını, güven skorlarını, tarih bilgilerini ve varsa ekran görüntülerini özetler. Böylece rapor, sunum ve olay inceleme odaklı kalır.

## Not

Bu doküman İstanbul Topkapı Üniversitesi bitirme projesi sunumu için sadeleştirilmiştir. Eğitim betikleri proje içinde korunur; ancak sunum akışında odak canlı izleme, olay kaydı ve raporlama deneyimidir.
