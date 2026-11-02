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
- 2026-11-01: Dairesel bayrak/amblem şablonlarında kenar boşluklarını asla elle boyayarak kapatma; orijinal delikli üst katman şablonunu kullan ve alt katmandaki görseli delik çapını taşacak şekilde Lanczos ile büyütüp sembol merkezini (hilal-yıldız vb.) yatay eksende dengele.

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
- 2026-11-01: İnce dokulu (taş, strass, sim, nakış) katalog görsellerinde küçük PiP kutusu, dar ekran bölmesi veya 3:4'ten 9:16'ya doğrudan sündürme yapma; 1:1 piksel oranını koruyarak detay bölgesinden 9:16 tam ekran kırpım (Lanczos + UnsharpMask) al.
- 2026-11-01: Sabit görsellerde FFmpeg crop='x0+dx*(t/dur)' kaydırması tam-sayı piksel yuvarlaması yüzünden 1 piksellik sıçrama (takılma) yaratır; görselleri %100 sabit tut ve sert slide/wipe yerine vuruşa kilitli 0.40 sn yumuşak optik erime (xfade=transition=fade) kullan.
- 2026-11-01: Dikey 4K telefon videolarında (-90 derece displaymatrix) -noautorotate kullanma; filter_complex sonrası ara MP4 segmentine kopyalanabilen displaymatrix yan verisini xfade öncesinde ffmpeg -display_rotation 0 -i seg.mp4 -c copy ile temizle.
- 2026-11-01: Çoklu -loop 1 PNG katmanını tek FFmpeg geçişinde açmak RAM şişmesi ve -t unutulduğunda sonsuz döngü yaratır; sabit filigran ve alt yazı PNG'lerini Pillow alpha_composite ile segment bazında birleştirip tek geçişte render al.
