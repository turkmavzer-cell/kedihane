# Kaliko — Hafıza

En fazla 100 satır. Dersler sektör/iş başlıklarına göre alfabetik sıralıdır.
Her ders tek satır ve tarihli: `- YYYY-AA-GG: ders`.
Yeni dersler doğrudan ilgili alt başlığın altına eklenir; alt başlık yoksa alfabetik sırayı bozmadan yeni başlık açılır.

## Dersler (Alfabetik Sektör / İş Sırası)

### Arapça / RTL Tipografi ve Şablon Üretimi
- 2026-10-24: Windows Pillow'da libraqm olmadığı için Cairo fontuyla Arapça yazarken ArabicReshaper({'use_unshaped_instead_of_isolated': True, 'delete_harakat': True}) + get_display kullan; aksi halde ayrık harfler (0xFE8D) kutu çıkar ve tenvin taşar.
- 2026-10-24: RTL satır içindeki ardışık Latin ve rakam kelimelerini tek soldan-sağa (LTR) blok olarak birleştir; kelime kelime dizilirse rakam grupları ters döner.
- 2026-10-24: Rakam ve ince metin kenarlarında tırtıklanmayı önlemek için PNG şablonları 4x çözünürlükte çizip LANCZOS ile küçült; metin fontlarında emoji glifi olmadığından yalnız vektör ikon kullan.
- 2026-10-24: Dairesel veya çerçeveli yuvaya bayrak/görsel yerleştirirken önce dış beyaz boşlukları getbbox ile kırp (autocrop) ve kırpılmış yüksekliği daire çapını tam dolduracak şekilde ölçekle.

### Emprime ve Serigrafi Baskı
- 2026-10-19: Koyu tişörtte alt baskı da bir film sayılır; makine N renk basıyorsa üst renk en fazla N−1.
- 2026-10-19: 508 PPI'da dither'ı doğrudan yapma; 254 dpi'de yapıp ×2 en yakın komşuyla büyüt (tekil nokta %81 → %0, ton doğruluğu aynı).
- 2026-10-19: Alan ağırlıklı k-means küçük, doygun veya koyu renkleri yutar; renk birleştirme kararını insan onaylar, ortalama ΔE yerine renk bazında rapor ver.
- 2026-10-19: Film PNG'si: Pillow mod '1' + dpi=(508,508) yazar (pHYs 20000 px/m); basılacak yer siyah (maskenin tersi).
- 2026-10-19: Dosya adı birleşen renkleri doğru yansıtmalı (yanlış adlı film hatası görüldü).
- 2026-10-20: Tonlu nesneyi spot kanala sert gövde / orta ton / açık ton diye dilimle; alt taban sert birleşim silüetidir.
- 2026-10-20: Nihai tonlu film 1 bit AM tram (45 lpi, 15°, 508 PPI) ve ayrı sert logo kanalı; sürekli ton kanalı yalnız çalışma kopyası.
- 2026-10-20: Spot kanalları anlamlı ASCII adla ve Lab renk tanımıyla kaydet; boş kanal bırakma.

### Photoshop Katman ve Bölge Ayırma
- 2026-10-20: Bölge grubu + renk katmanı isteğinde bölgeleri ayrık bölümle (örtüşme 0, boşluk 0); maskeyi yapı pikselinden kur, dikdörtgen/kaba çokgen denetimde reddedilir.
- 2026-10-20: Mürekkep rengini bölge başına, uç değer medyanıyla kestir (en parlak/koyu %20); düz medyan soluk çıkar. Dokulu kırmızıya ikinci (açık) tonu ekle.
- 2026-10-20: Mürekkep başına sızıntı cezası (≈8 seviye) kırmızı sızıntısını %15,9'dan %2,5'e indirdi; yeniden birleştirmeyi her turda ölç.
- 2026-10-20: psd-tools'ta Türkçe katman adı create_* içinde MacRoman hatası verir; ad sonradan atanır, ama proje ASCII istiyorsa baştan ASCII ver.

### Video Kurgu, FFmpeg ve Premiere
- 2026-10-20: Premiere .prproj dosyası gzip'li XML'dir; klip zamanları tick/254016000000 sn formülüyle salt-okunur çıkarılır, FCP7 xmeml'de Basic Motion center sekansa değil klibin kendi piksel boyutuna göre normalize edilir.
- 2026-10-24: FFmpeg xfade zincirinde timebase hatasını önlemek için tüm girdileri setpts=PTS-STARTPTS,fps=30,settb=1/30,format=yuv420p ile normalize et; tam libx264 için imageio-ffmpeg kullan.

## Konu Dosyaları (İlgili satırlar indeks üzerinden okunmalıdır)

- `bilgi/emprime-kanal-ayirma.md`: Emprime ve Serigrafi baskı metotları
- `bilgi/katman-ayirma.md`: Photoshop katman ve bölge ayırma metotları
- `bilgi/sosyal-medya-ve-video-operasyonu.md`: Video kurgu ve sosyal medya operasyonu standartları
