# Kaliko — Hafıza

> Biçim ve kurallar: `bilgi/HARITA.md` Ekleme Prosedürü.

## Dersler (Alfabetik Sektör / İş Sırası)

### Arapça / RTL Tipografi ve Şablon Üretimi
- 2026-10-24: Windows Pillow libraqm eksikliği ve Arapça harf şekillendirme → bilgi/sosyal-medya-ve-video-operasyonu.md §A
- 2026-10-24: RTL satır içindeki ardışık Latin ve rakam kelimelerini tek soldan-sağa (LTR) blok olarak birleştir; kelime kelime dizilirse rakam grupları ters döner.
- 2026-10-24: Rakam ve ince metin kenarlarında tırtıklanmayı önlemek için PNG şablonları 4x çözünürlükte çizip LANCZOS ile küçült; metin fontlarında emoji glifi olmadığından yalnız vektör ikon kullan.
- 2026-10-24: Dairesel veya çerçeveli yuvaya bayrak/görsel yerleştirirken önce dış beyaz boşlukları getbbox ile kırp (autocrop) ve kırpılmış yüksekliği daire çapını tam dolduracak şekilde ölçekle.

### Video Kurgu, FFmpeg ve Premiere
- 2026-10-20: Premiere .prproj dosyası gzip'li XML'dir; klip zamanları tick/254016000000 sn formülüyle salt-okunur çıkarılır, FCP7 xmeml'de Basic Motion center sekansa değil klibin kendi piksel boyutuna göre normalize edilir.
- 2026-10-24: FFmpeg xfade timebase normalizasyonu → bilgi/sosyal-medya-ve-video-operasyonu.md §C
- 2026-11-01: İnce dokulu (taş, strass, sim, nakış) katalog görsellerinde küçük PiP kutusu, dar ekran bölmesi veya 3:4'ten 9:16'ya doğrudan sündürme yapma; 1:1 piksel oranını koruyarak detay bölgesinden 9:16 tam ekran kırpım (Lanczos + UnsharpMask) al.
- 2026-11-01: Sabit görsellerde FFmpeg crop='x0+dx*(t/dur)' kaydırması tam-sayı piksel yuvarlaması yüzünden 1 piksellik sıçrama (takılma) yaratır; görselleri %100 sabit tut ve sert slide/wipe yerine vuruşa kilitli 0.40 sn yumuşak optik erime (xfade=transition=fade) kullan.
- 2026-11-01: Dikey 4K telefon videolarında (-90 derece displaymatrix) -noautorotate kullanma; filter_complex sonrası ara MP4 segmentine kopyalanabilen displaymatrix yan verisini xfade öncesinde ffmpeg -display_rotation 0 -i seg.mp4 -c copy ile temizle.
- 2026-11-01: Çoklu -loop 1 PNG katmanını tek FFmpeg geçişinde açmak RAM şişmesi ve -t unutulduğunda sonsuz döngü yaratır; sabit filigran ve alt yazı PNG'lerini Pillow alpha_composite ile segment bazında birleştirip tek geçişte render al.
