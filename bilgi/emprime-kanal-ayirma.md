# Emprime / Serigrafi Renk (Kanal) Ayırma Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Alt Baskı (Underbase) ve Choke/Spread Kuralları](#a-alt-baskı-underbase-ve-chokespread-kuralları) | L30-L38 | Koyu kumaş beyaz taban, choke 5 px, spread kuralları |
| [B. AM Tramlama ve Açı Kuralları](#b-am-tramlama-ve-açı-kuralları) | L42-L50 | 45 LPI, 508 PPI, 22.5°/15° açı standardı ve moiré önleme |
| [C. Atölye Standartları ve Makine Kısıtları](#c-atölye-standartları-ve-makine-kısıtları) | L54-L58 | Maksimum 6 kafa, zıt renk kısıtları ve kurutma süreleri |
| [D. Dithering ve Difüzyon Yöntemleri](#d-dithering-ve-difüzyon-yöntemleri) | L62-L66 | Index color, 254 DPI dither + 2x büyütme standardı |
| [E. Doğrulanmayanlar ve Sınırlar](#e-doğrulanmayanlar-ve-sınırlar) | L70-L78 | Fiziksel film, elek tutma, gerçek moiré ve ölçüm sınırları |
| [F. Film Çıktısı Standartları](#f-film-çıktısı-standartları) | L82-L87 | 1-bit bitmap, pHYs etiketi ve dosya adlandırma |
| [G. İş Akışı: Tek Aşamalı vs İki Aşamalı Yöntem](#g-iş-akışı-tek-aşamalı-vs-iki-aşamalı-yöntem) | L91-L105 | bolge_am.py vs hibrit2.py adım adım yürütme |
| [H. Kalite Kontrol ve Hata Ölçümü](#h-kalite-kontrol-ve-hata-ölçümü) | L109-L118 | ΔE ≤ 12, kenar pürüzlülüğü ≤ 0.03 ve kalite_kontrol.py |
| [I. Kaynaklar ve Literatür](#i-kaynaklar-ve-literatür) | L122-L134 | MYK, Ryonet, Fresener, Anatol ve ISO-13660 standartları |
| [J. Tonlu Nesne ve Alt Taban Çalışma Stili](#j-tonlu-nesne-ve-alt-taban-çalışma-stili) | L138-L142 | Ton dilimli spot kanallar, sert alt taban ve şablon mantığı |
| [K. Önerilen Boru Hattı ve Ön Analiz Karar Eşikleri](#k-önerilen-boru-hattı-ve-ön-analiz-karar-eşikleri) | L146-L198 | 5 adımlı Python pipeline kodu ve analiz.py karar eşikleri |
| [L. Photoshop JSX Otomasyon Araçları](#l-photoshop-jsx-otomasyon-araçları) | L202-L209 | psd_olustur_tek_adim.jsx ile tek tıkla Multichannel PSD |
| [M. Sınama Sonuçları (Sentetik 2000×2000 px, 508 PPI)](#m-sınama-sonuçları-sentetik-20002000-px-508-ppi) | L213-L228 | Raggedness, sahte saçak, choke ve dither sentetik test tablosu |
| [N. Terimler Sözlüğü](#n-terimler-sözlüğü) | L232-L249 | MYK tanımları, mesh, tram, LPI, spot, choke/spread ve flash cure |
| [O. Tramsız Düz Renk Ayrımı](#o-tramsız-düz-renk-ayrımı) | L253-L261 | tramsiz.py ile vektörel grafik ayrımı ve trapping |

---

**Doğrulama durumu:** Sayılar sentetik görselde Python ile ölçüldü. Fiziksel film, gerçek elek, nokta tutma, gerçek moiré ve Photoshop'ta açılış **sınanmadı** (Bölüm E). Kaynakların çoğu ABD tişört serigrafi sektöründen (plastisol ağırlıklı).

---

## A. Alt Baskı (Underbase) ve Choke/Spread Kuralları

1. **Koyu Kumaş İhtiyacı:** Koyu renkli kumaşlarda (siyah, lacivert, koyu gri) üst renklerin canlı çıkması için alta opak beyaz astar (underbase) basılır; flash cure ile kurutulduktan sonra üst renkler basılır. Açık zeminli kumaşta fon basılmaz, kumaşın kendi rengi zemin kabul edilir.
2. **Choke (İçeri Daraltma) Standardı:**
   - Standart choke değeri: **5 piksel** (~0.25 mm @ 508 PPI).
   - Amacı: Üst renk kalıbı kumaşa binerken mekanik esneme veya kayıt kayması yaşansa dahi alttaki beyaz astarın kenardan sırıtmamasını sağlamaktır.
3. **İnce Çizgi ve Detay Choke İstisnası:**
   - 1 pt ve altındaki ince çizgilerde standart 5 px choke uygulanırsa alt taban tamamen yok olur.
   - Kural: İnce detaylara **choke 1 px** uygulanır veya üst renk **spread 2 px** (~0.10 mm) şişirilir.

---

## B. AM Tramlama ve Açı Kuralları

1. **Tramlama Standartları:**
   - **Çözünürlük:** **508 PPI** (kullanıcı talimatı ve atölye standardı, 200 dpcm).
   - **Tram Frekansı:** **45 LPI** (atölye eleklerine ve nokta tutma sınırına en uygun değer).
   - **Tram Açısı:** Tek açı **15° veya 22.5°**, elips nokta formu.
2. **Moiré Önleme:**
   - 0° açısı elek telleriyle birebir çakıştığı için en şiddetli moiré desenini üretir; kesinlikle yasaktır.
   - Çok renkli AM tramlarda renkler arası açı farkı en az 30° tutulur veya tek açılı (stochastic/FM dither) hibrit yöntem kullanılır.

---

## C. Atölye Standartları ve Makine Kısıtları

1. **6 Kafa Sınırı:** Atölye ahtapot baskı makinesi standart 6 kafalıdır (ara kurutma flash cure durumuna göre 7-8). Gereksiz kafa sayısından kaçınılır.
2. **Zıt Renk Karıştırma Yasağı:** Lab ton farkı > 110° olan renk çiftlerinin (örneğin lacivert ile turuncu) yan yana degrade karışımı çamurlaşma yaratır. Bu alanlar fiziksel olarak ayrı basılır veya siyah çizgiyle ayrılır.
3. **Flash Cure Kurutma:** Renkler arası ara kurutma yüzey sıcaklığı ≈93–110 °C, temas süresi 3–8 saniyedir.

---

## D. Dithering ve Difüzyon Yöntemleri

1. **Index Color / Difüzyon:** Eşit boyutlu kare noktalarla stokastik dağılım.
2. **Çözünürlük Kuralı:** Doğrudan 508 PPI'da dither yapılırsa noktaların %80'i tekil piksel (0.05 mm) kalır ve kalıpta tutmaz.
   - Çözüm: **254 DPI'da Floyd-Steinberg dither + x2 Nearest Neighbor büyütme** ile en küçük nokta 0.10 mm'ye çekilir; ΔE ton doğruluğu korunur.

---

## E. Doğrulanmayanlar ve Sınırlar

- Filmlerin Photoshop'ta Bitmap modunda ve 508 PPI olarak açılması.
- RIP/film yazıcı çıktısı, fiziksel film Dmax.
- Gerçek elekte 0,05 / 0,10 / 0,15 mm dither noktaları ile %5 / %8 halftone noktalarının tutması (sayılar fiziksel tutma kanıtı değildir).
- Gerçek moiré (yalnız simülasyon denendi).
- Choke 5 px'in gerçek baskıdaki kayıt toleransına yetmesi; spread ile şişen alt baskının üst rengin altında görünmez kalması.
- Gerçek görseller (yalnız sentetik denendi); PSD spot kanal tesliminin resmî Adobe belgesi; imagesetter çözünürlükleri (1270/2540 dpi).
- Kenar pürüzlülüğü için "0–1 oran" tanımlı kaynaklı bir ölçü bulunamadı. ISO/IEC 13660 raggedness: kenar R60 eşiğinde, uydurulan doğruya dik sapmaların standart sapması (pictorial işleri ve saydam çıktıları kapsamaz; uyarlama).

---

## F. Film Çıktısı Standartları

1. **1-Bit Mod:** Her renk filmi `mode="1"` (siyah-beyaz bitmap) olarak kaydedilir.
2. **Film Mantığı:** Basılacak mürekkep alanı **SİYAH (0)**, basılmayacak kumaş alanı **BEYAZ (1)** olarak yazılır.
3. **pHYs Etiketi:** 508 PPI piksel yoğunluğu PNG header'ına `pHYs = 20000 piksel/metre` olarak işlenir; RIP yazılımları filmi doğru fiziksel boyutta açar.
4. **Adlandırma:** `01_altbaski_beyaz.png`, `02_kirmizi.png`, `03_sari.png` şeklinde baskı sırasına göre numaralandırılır.

---

## G. İş Akışı: Tek Aşamalı vs İki Aşamalı Yöntem

Her işin başında kullanıcıya hangi yöntemin uygulanacağı sorulur:

1. **Tek Aşamalı Yöntem (Hızlı):**
   - Program renkleri otomatik seçer ve doğrudan 1-bit filmleri üretir:
   ```bash
   python tools/emprime/bolge_am.py girdi.png cikti_klasoru 6 508
   ```
2. **İki Aşamalı Yöntem (Kontrollü / Önerilen):**
   - **Adım 1:** Önizleme üretilir, renk paleti ve alt baskı kullanıcıya gösterilir.
   - **Adım 2:** Kullanıcı onayladıktan sonra 1-bit filmler ve Photoshop PSD dosyası üretilir:
   ```bash
   python tools/emprime/hibrit2.py girdi.png onizleme_klasoru
   ```

---

## H. Kalite Kontrol ve Hata Ölçümü

1. **Otomatik Kalite Denetimi (`tools/emprime/kalite_kontrol.py`):**
   ```bash
   python tools/emprime/kalite_kontrol.py cikti_klasoru kaynak.png
   ```
2. **Kritik Eşik Değerleri:**
   - **Renk Sapması:** Düz bölgelerde film rengi kaynaktan **ΔE ≤ 12**.
   - **Kenar Pürüzlülüğü (Raggedness):** 20° test kenarında standart sapma **≤ 0.03 mm**.
   - **Kayıp Detay:** 1 pt altındaki çizgilerde kopukluk bulunmamalıdır.

---

## I. Kaynaklar ve Literatür

- MYK, Serigrafi Baskı Operatörü Seviye 3 (13UMS0309-3), 2013: https://myk.gov.tr/images/articles/editor/Rega290513/Serigrafi_3_REGA_Ekli.pdf
- Ryonet, "A Crash Course in Halftones…", 24.02.2025: https://screenprinting.com/blogs/news/a-crash-course-in-halftones-for-screen-printing
- Solutions for Screen Printers, "Halftone Angles Demystified" (güncelleme 25.03.2026): https://support.solutionsforscreenprinters.com/hc/en-us/articles/26564295432212
- UMBC, "Bitmap for Screen Printing" (2022): https://artprint.umbc.edu/files/2022/04/Bitmap-for-Screen-Printing.pdf
- Fresener, "Index Color Separations…", 11.05.2011: https://t-biznetwork.com/?p=2298
- Fresener, "Choking, Trapping…", 01.01.2017: https://t-biznetwork.com/computergraphics/choking-trapping-cleaning-up-type-in-photoshop-by-scott-fresener/
- Fresener, "Simulated Process… Part Two", 10.04.2018: https://t-biznetwork.com/computergraphics/colorseparations/simulatedseps-part2/
- Anatol, "The Tricky Business of Screen Printing Underbase", 27.09.2018: https://anatol.com/blog/the-tricky-business-of-screen-printing-underbase
- Briggs ve ark., "Applications of ISO-13660", 1999: https://www.qea.com/wp-content/uploads/2015/04/Paper_1999_ISJ-JH_Applications_of_ISO-13660-newaddr.pdf
- Sharma, Wu, Dalal, CIEDE2000 (2005): https://hajim.rochester.edu/ece/sites/gsharma/ciede2000/
- Basak, Saritha, Paul, J. Graphic Eng. & Design 16(1), 2025: https://jged.uns.ac.rs/index.php/jged/article/download/1595/1460/2554

---

## J. Tonlu Nesne ve Alt Taban Çalışma Stili

1. **Ton Dilimli Spot Kanal:** Tonlu nesneler tek kanala sıkıştırılmaz; sert gövde / orta ton / açık ton dilimleri olarak basılır.
2. **Sert Alt Taban:** Koyu tişörtte alt taban tonlu değil, tüm baskı elemanlarının sert birleşim silüetidir.
3. **Kanal İsimleri:** Spot renk kanalları Pantone veya net isimlerle (`Flash White`, `Base White`, `Deep Red`, `Gold Yellow`) etiketlenir.

---

## K. Önerilen Boru Hattı ve Ön Analiz Karar Eşikleri

1. **Önerilen 5 Adımlı Boru Hattı:**
   - **Palet:** Lab k-means ile öner, birleşecek renkleri kullanıcı seçsin. Üst renk sayısı = makine sınırı (koyu tişörtte −1).
   - **Atama:** 4× Lanczos üst örnekle → en yakın renk → 4×4 çoğunluk oyu (`assign_ss`).
   - **Fotoğraflı bölüm:** 254 dpi'de dither + ×2 en yakın komşu büyütme (veya AM halftone 22,5°, en açık ton ≈%8).
   - **Koyu tişört:** alt baskı = basılan üst renklerin birleşimi, choke 5 px, ince detaya choke 1 (veya spread 2).
   - **Yaz:** 1-bit PNG, basılacak yer siyah, 508 PPI (`pHYs` = 20000 px/m).

```python
import numpy as np, cv2
from PIL import Image
from skimage.color import rgb2lab

def to_lab(u8): return rgb2lab(u8.astype(np.float32) / 255.0).astype(np.float32)

def assign_ss(rgb, pal_lab, ss=4):
    """4x Lanczos ust ornek -> en yakin palet rengi -> ss x ss cogunluk oyu."""
    h, w = rgb.shape[:2]; out = np.empty((h, w), np.int16)
    for y in range(0, h, 250):
        y0, y1 = max(0, y - 8), min(h, y + 258)
        up = cv2.resize(rgb[y0:y1], (w * ss, (y1 - y0) * ss), interpolation=cv2.INTER_LANCZOS4)
        Lu = to_lab(up); a = np.empty(Lu.shape[:2], np.int16)
        for i in range(0, Lu.shape[0], 200):
            X = Lu[i:i + 200]; a[i:i + 200] = ((X[..., None, :] - pal_lab) ** 2).sum(-1).argmin(-1)
        cnt = np.stack([(a == i).reshape(y1 - y0, ss, w, ss).sum(axis=(1, 3)) for i in range(len(pal_lab))], -1)
        out[y:y + 250] = cnt.argmax(-1)[y - y0:y - y0 + min(250, h - y)]
    return out

def disk(r): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def underbase(top, choke=5, thin_choke=1):   # top: basilan ust renklerin birlesimi (bool)
    t = top.astype(np.uint8)
    thick = cv2.morphologyEx(t, cv2.MORPH_OPEN, disk(choke)).astype(bool)
    thin = top & ~cv2.dilate(thick.astype(np.uint8), disk(1)).astype(bool)
    return cv2.erode(t, disk(choke)).astype(bool) | (cv2.erode(t, disk(thin_choke)).astype(bool) & thin)

def spread(mask, s=2): return cv2.dilate(mask.astype(np.uint8), disk(s)).astype(bool)

def save_1bit(ink, path, ppi=508):           # film mantigi: basilacak yer SIYAH (0)
    im = Image.fromarray(~ink.astype(bool)); assert im.mode == "1"
    im.save(path, dpi=(ppi, ppi), optimize=True)
```

2. **Ön Analiz Karar Eşikleri (`tools/emprime/analiz.py`):**
   - `duz_oran > 0.85` ve `doku_oran < 0.08`: Düz renkli grafik → Tramsız spot renk ayrımı (`tools/emprime/tramsiz.py`).
   - `doku_oran > 0.25` veya `kenar_oran > 0.25`: Dokulu/boyama → AM tram + çakışmasız karışım (45 LPI, 508 PPI; `tools/emprime/bolge_am.py`).
   - Aksi durumda: Karma/hibrit → Düz alanlar tramsız, geçişli alanlar tramlı (`tools/emprime/hibrit2.py`).
   - `gercek_renk_tahmini(>=1%) > 8`: Makine kafa sayısı kontrol edilir, palet birleştirme talep edilir.
   - Kağıt/zemin beyaz noktası `< 235`: Zemin kirli/gri; beyaza normalize edilmelidir.
   - Kenar zemin `std > 1.2`: Zeminde leke/fırça dokusu var; basılmayacaksa maskelenir.
   - İnce detay kalınlığı `< tram_hucre * 0.6`: 45 LPI hücrenin %60'ından dar çizgiler elekte kopabilir uyarısı üretilir.
   - JPEG blokluluk oranı `> 1.08`: 8x8 DCT blok artefaktları temizlenmeli veya netleştirilmelidir.

---

## L. Photoshop JSX Otomasyon Araçları

1. **Tek Adımda Multichannel PSD Üretimi:**
   - Script: `tools/photoshop/psd_olustur_tek_adim.jsx`
   - İşlev: Film klasöründeki 1-bit filmleri okur, Photoshop'ta Multichannel Spot Color belgesine dönüştürür, her kanala doğru Lab/RGB rengini atar ve PSD olarak kaydeder.
2. **Kanal Birleştirme ve Renk Atama:**
   - Script: `tools/photoshop/film_klasoru_multichannel.jsx` + `film_renk_ata.jsx`
   - İşlev: Set klasöründeki filmleri tek Multichannel belgede toplar, ardından renkleri `kanallar_hibrit.json`'dan Spot Color olarak atar.

---

## M. Sınama Sonuçları (Sentetik 2000×2000 px, 508 PPI)

| Konu | Sonuç |
|---|---|
| Spot atama | Tam kapsama: 4.000.000 pikselde boşluk 0, çakışma 0 |
| Düz kenar (20°) raggedness | 0,271 px = 0,0136 mm; 1-bit'te teorik alt sınır `1/√12·cos(açı)`. Üst örnekleme kenarı düzeltmez |
| Yanlış renk saçağı | 4× Lanczos üst örnekle + çoğunluk oyu: 2849 → 1033 px (%63,7 azalma) |
| İnce çizgi (1 / 0,5 / 0,25 pt) | 7 / 4 / 2 px genişlikte, kopuksuz |
| Choke 3 / 5 / 7 px | Taşma 0; kayıp alan %7,05 / %10,16 / %12,65 |
| 1 pt çizginin alt baskısı | Choke 3'te %14 kalır; choke ≥5'te tamamen kaybolur. 0,5 pt choke 3'te bile kaybolur |
| İnce detaya choke 1 veya spread 2 | 1 pt'nin %71'i, 0,5 pt'nin %50'si korunur. 0,25 pt hiçbir ayarda korunmaz |
| Dither 508'de doğrudan | Noktaların %80,9'u tekil piksel (0,05 mm), %94,4'ü 2 px'ten dar |
| Dither 254 dpi + ×2 büyütme | Tekil nokta %0 (en küçük 0,10 mm); ton doğruluğu aynı (ΔE 5,50 / 5,51) |
| Dither 169,33 dpi + ×3 | Tekil nokta %0 (0,15 mm); ΔE 5,54 |
| AM halftone %5 nokta | Mesh 230 (51,1 LPI): çap 0,126 mm; mesh 305 (67,8 LPI): 0,098 mm, %2 noktaların %15'i hiç oluşmuyor |
| Moiré (kaba sayısal) | 0° her iki elekte en kötü; 305 mesh/22,5°'de 6,4 mm'lik vuru görüldü |

---

## N. Terimler Sözlüğü

| Terim | Anlamı |
|---|---|
| Elek / kalıp / şablon | Serigrafi kalıbı (MYK standardı "elek şeklindeki kalıp" der) |
| Mesh | Elek sıklığı. MYK: 1 cm'deki iplik sayısı (T/cm). Mesh/inç = T/cm × 2,54 |
| Tram | Görüntüyü oluşturan küçük noktalar. Tramsız tek tonlu filme MYK "tire film" der |
| LPI | Tramın inç başına çizgi sayısı (Lines Per Inch) |
| Binme / kayıt | Renklerin üst üste denk gelmesi (registration) |
| Spot renk | Her mürekkep için tek film; logo ve keskin grafik |
| Simulated process | Spot mürekkeplerle fotoğrafik görüntü; koyu tişörtte yaygın |
| Index color | Eşit boy kare noktalar, diffusion dither (stochastic benzeri) |
| Alt baskı (underbase) | Koyu kumaşta renklerin canlı çıkması için önce basılan beyaz |
| Choke / spread (trap) | Choke: alt baskıyı içeri daraltma. Spread: üst rengi şişirme |
| Flash cure | Renkler arası ara kurutma (yüzey ≈93–110 °C, 3–8 sn; tek kaynak) |

*"Emprime" teriminin kaynaklı bir tanımı bulunamadı.*
*508 PPI piksel yoğunluğunun neden seçildiği kaynaklarda açıkça bulunamadı (metrik 200 dpcm karşılığıdır).*

---

## O. Tramsız Düz Renk Ayrımı

1. **Vektörel ve Keskin Grafikler (`tools/emprime/tramsiz.py`):**
   ```bash
   python tools/emprime/tramsiz.py girdi.jpg cikti_klasoru
   ```
2. **Özellikler:**
   - Tram içermeyen katı spot renkler.
   - `TRAP_PX = 4` (~0.17 mm): Açık renklerin koyu rengin altına taşması sağlanarak baskıdaki kayıt kaçıklıkları önlenir.
