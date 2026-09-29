# 02 — Veri hazırlığı

Bu bölüm, `main/train_model.py` dosyasının beklediği veri düzenini ve **eğitime başlamadan önce** veriyi neden düzenli hazırlamanız gerektiğini özetler.

## Kodun beklediği klasör yapısı

Veri yükleme akışı klasör adlarını **sınıf etiketi** olarak okur. Tipik yapı:

```
dataset/
├── train/
│   ├── Non-Violence/    # veya projenizde kullandığınız negatif sınıf klasör adı
│   │   └── *.jpg, *.png, ...
│   └── Violence/        # pozitif sınıf
│       └── ...
└── test/
    ├── Non-Violence/
    └── Violence/
```

- **Eğitim** (`--train_dir`, varsayılan `dataset/train`): hem eğitim hem de kod içindeki `validation_split=0.2` ile doğrulama alt kümesi buradan üretilir.
- **Test** (`--test_dir`, varsayılan `dataset/test`): Eğitimden bağımsız tutulmalıdır; böylece genelleme performansı gerçekçi ölçülür.

Klasör adları `train_model.py` içinde sabit değildir; `flow_from_directory` alfabetik sıraya göre sınıf indekslerini atar. **İkili sınıflandırma** için `class_mode='binary'` kullanıldığından tam iki alt klasör beklenir.

## Eğitimden önce veri hazırlamak neden gereklidir?

### 1. Etiket tutarlılığı ve güvenilir öğrenme

Model, piksellerden istatistiksel örüntü öğrenir. Yanlış veya tutarsız etiketler (örneğin şiddet içeren bir karenin yanlışlıkla “şiddet değil” klasöründe olması) doğrudan üst sınıra taşınır. Bu nedenle **her görüntünün sınıfı net** olmalı ve klasör yapısı bu etiketi yansıtmalıdır.

### 2. Train / validation / test ayrımı ve sızıntıyı önleme

- Kod, eğitim klasörünün **%20’sini** doğrulama için ayırır (`validation_split=0.2`).
- Ayrı bir **test** klasörü vardır. Test görüntüleri, eğitim sırasında hiç kullanılmamalıdır; aksi halde “ezber” veya iyimser metrikler elde edilir.
- Aynı videodan alınan ardışık kareler hem eğitimde hem testte olmamalıdır; kareler arası korelasyon **veri sızıntısı** yaratır ve test doğruluğunu şişirir.

### 3. Sınıf dengesi

İkili sınıflandırmada bir sınıf çok daha fazlaysa model çoğunluk sınıfına yaslanabilir. Dengesiz veri setlerinde:

- mümkünse her iki sınıftan benzer sayıda örnek toplayın veya
- örnekleme/ağırlıklı kayıp gibi stratejileri (bu projede varsayılan olarak yok) ayrıca değerlendirin.

Bu depodaki eğitim betiği `loss='binary_crossentropy'` kullanır; sınıf ağırlıkları tanımlı değildir — dengesizlik varsa metrikleri (precision/recall) birlikte okumak önemlidir.

### 4. Görüntü formatı ve çözünürlük

Model **224×224** giriş bekler; `flow_from_directory` içinde `target_size=(224, 224)` ile otomatik yeniden boyutlandırma yapılır. Ham çözünürlük yüksek olsa da anlamlı detayın korunması için çok düşük çözünürlüklü karelerden kaçınmak genelde iyidir.

### 5. Eğitim zamanı artırımı (augmentation) ile uyum

`train_model.py` içinde eğitim tarafında şu dönüşümler uygulanır (doğrulama ve test tarafında yalnızca `rescale=1./255`):

- `rotation_range=30`
- `width_shift_range=0.3`, `height_shift_range=0.3`
- `shear_range=0.3`, `zoom_range=0.3`
- `horizontal_flip=True`
- `fill_mode='nearest'`

Bu, modelin hafif geometrik değişimlere karşı daha dayanıklı olmasına yardımcı olur. Veri hazırlığında **orijinal kareleri bozmadan** saklamak yeterlidir; artırım eğitim sırasında uygulanır. Test setinde artırım kullanılmaması, tarafsız değerlendirme içindir.

## Özet kontrol listesi

- [ ] `dataset/train` ve `dataset/test` altında iki sınıf klasörü var.
- [ ] Test görüntüleri eğitimle örtüşmüyor (aynı sahne/kare kopyası yok).
- [ ] Etiketler klasör adlarıyla uyumlu ve tutarlı.
- [ ] Mümkünse sınıf dağılımı makul.

Sonraki adım: [03-model-ve-egitim.md](03-model-ve-egitim.md).
