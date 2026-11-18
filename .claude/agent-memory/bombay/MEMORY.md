# Bombay — Hafıza

> Biçim ve kurallar: `bilgi/HARITA.md` Ekleme Prosedürü.

## Dersler (Alfabetik Sektör / İş Sırası)

### Algoritmalar ve Optimizasyon
- 2026-10-19: Mürekkep renkleri biliniyorsa alfayı palet izdüşümüyle hesapla (α=⟨c−b,Fk−b⟩/|Fk−b|²); Color to Alpha en küçük alfayı seçtiği için düz mürekkepte α<1 kalır.
- 2026-10-20: Kısıtlı en küçük kareler (w≥0, Σw=1) için alt küme sayımı + ceza yöntemi 3–4 mürekkepte hızlı ve kararlıdır.
- 2026-10-20: Kontur oturtma yarıçapını morfolojik konturdan değil geçişin %50 noktalarından ölç.

### Donanım ve Sunucu Mimarisi
- 2026-11-11: Çoklu tüketici GPU kurulumlarında NVLink olmadığı için VRAM havuzlama değil, bağımsız paralel iş kuyruğu ve çoklu ajan iş bölümü mimarisiyle verim alınır.

### Görüntü İşleme ve PSD
- 2026-10-19: Color to Alpha kendi zemininde her zaman hata 0 verir (yanıltıcı); doğruluğu koyu bir zemine bindirerek ölç.
- 2026-10-19: psd-tools frompil(RGBA) arkaplan piksellerinde RGB=(255,255,255) yazar; katman oluştururken piksel kanallarını doğrudan ata.
- 2026-10-19: Alfalı görseli yalnız premultiplied uzayda ölç/ölçekle/bulanıklaştır; straight alfayla kenarda 49 seviyeye kadar hale oluşur.
- 2026-10-20: Büyük PSD'de kanalları RLE satır tablosundan seyrek oku, tam tuvali belleğe açma; PPI = ham değer/65536.
- 2026-10-20: Tram frekansı/açısı kırpmanın FFT tepe noktasından ölçülür (lpi = PPI × frekans).

### Ortam ve Paket Yönetimi
- 2026-10-19: Sandbox'ta `pip install --break-system-packages <paket>` çalışır; ağ yalnız paket kayıtlarına açık.
