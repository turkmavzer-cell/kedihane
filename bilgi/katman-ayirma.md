# Görseli Katmanlara Ayırma Rehberi (yumuşak alfa)

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Amaç ve Kapsam](#a-amaç-ve-kapsam) | L27-L35 | C = αF + (1−α)B modeli, desen + zemin ayrımı |
| [B. Bölge Grupları ve Mürekkep Katmanları (Az Mürekkepli Baskı)](#b-bölge-grupları-ve-mürekkep-katmanları-az-mürekkepli-baskı) | L39-L84 | Bölge maskesi, PSD grubu, simplex_ls kodu, sızıntı cezası |
| [C. Doğrulanmayan Yöntemler ve Literatür](#c-doğrulanmayan-yöntemler-ve-literatür) | L88-L96 | Photoshop açılışı, gerçek kumaş/baskı ve sınanmamış modeller |
| [D. Kalite Kontrol ve Sayısal Eşik Ölçümü](#d-kalite-kontrol-ve-sayısal-eşik-ölçümü) | L100-L106 | Geri bindirme, koyu zemin bindirme ölçümü ve kenar inceleme |
| [E. Kaynaklar ve Açık Kaynak Atıflar](#e-kaynaklar-ve-açık-kaynak-atıflar) | L110-L121 | Alvy Ray Smith, GIMP, Aksoy, Tan, FSCS, PyMatting, psd-tools |
| [F. Photoshop Karşılıkları ve Kanal/Katman Kuralları](#f-photoshop-karşılıkları-ve-kanalkatman-kuralları) | L125-L132 | Select and Mask, Decontaminate Colors, Defringe ve modlar |
| [G. Tuzaklar ve Ölçülmüş Hatalar](#g-tuzaklar-ve-ölçülmüş-hatalar) | L136-L158 | Uzay uyuşmazlığı, zemin gradyanı, JPEG, hale ve psd-tools tuzağı |
| [H. Varsayılan Boru Hattı (Matematiksel Model ve Kod)](#h-varsayılan-boru-hattı-matematiksel-model-ve-kod) | L162-L200 | Medyan zemin, polinom yüzey, k-means, palette_alpha kodu |
| [I. Yöntem Seçimi ve Sentetik Sınama Sonuçları](#i-yöntem-seçimi-ve-sentetik-sınama-sonuçları) | L204-L218 | Palet izdüşümü, Color to Alpha, triangulation, rembg kıyaslaması |

---

**Yürüten:** Kaliko (Bombay kodu yazar). **Denetim:** Sarman.  
**Kaynak:** Siyam'ın kaynaklı araştırması + Bombay'ın sentetik görsellerle Python sınaması.  
**Son güncelleme:** 2026-10-31  

**Doğrulama durumu:** Sayılar sentetik görselde Python ile ölçüldü. Photoshop'ta
açılış ve gerçek tarama/fotoğraf üzerinde sınama **yapılmadı** (Bölüm C).

## A. Amaç ve Kapsam

Bir görseli katmanlara bölmek. Varsayılan iş: **arka plan + desen** iki katman;
desenin solduğu veya silindiği yerlerde **yarı saydam (alfa)** geçiş korunur.
Çıktı Photoshop'ta açılabilmeli: ayrı şeffaf PNG ve/veya katmanlı PSD.

Temel denklem: `C = αF + (1−α)B` (C piksel, F desen rengi, B zemin rengi).
Tek zeminde 3 denklem, 4 bilinmeyen vardır (F'nin 3 kanalı ve α); çözüm tek
değildir. Fiziksel alt sınır: `α ≥ max(α_R, α_G, α_B)`.

---

## B. Bölge Grupları ve Mürekkep Katmanları (Az Mürekkepli Baskı)

Ölçüldü: 1254×1254, 3 mürekkepli (krem kâğıt / siyah / kırmızı) baskı görseli, 4 bölge.
Doğrulama durumu: Python'da yeniden birleştirme ölçüldü, Sarman denetledi; Photoshop'ta açılış sınanmadı.

**İş tanımı:** Kullanıcı "bölge bölge grup, her grubun içinde renk renk katman" isterse.
Yapı: her bölge bir PSD grubu; grubun içinde alttan üste Krem → Kırmızı(lar) → Siyah katmanları;
en altta gizli "Orijinal (referans)".

**Yöntem**
1. **Bölgeler ayrık bölümleme olsun** (her piksel tek bölge, örtüşme 0, boşluk 0). Birleşim = tüm tuval; yeniden birleştirme böylece birebir kalır.
2. **Bölge maskesi yapıdan çıkar, dikdörtgenden değil.** Kaba çokgen/blok maske denetimde reddedildi (bina sınırı dikdörtgen basamak, dağ düz kesik). Maske, bölgenin yapı piksellerinden (renk/koyuluk ile bulunan bileşenler) kurulur; çokgen yalnız kaba kılavuz.
3. **Kontur oturtma yarıçapı, morfolojik kontur değil, geçişin %50 noktalarından** ölçülür.
4. **Mürekkep renkleri her bölge için ayrı** kestirilir (tek global renk sınır pikselini bozar). Krem = kâğıt pikselleri içinde en parlak %20'nin medyanı; siyah = en koyu %20 medyanı; kırmızı = kırmızı piksellerin en koyu %2'sinin medyanı. **Düz medyan değil uç değer medyanı** (düz medyan mürekkebi soluk bulur).
5. **Doku varsa tek kırmızı yetmez:** "Açık Kırmızı" (en doygun, en parlak %10 içinden) ekle. Bölgede o mürekkep yoksa (siyah veya kırmızı) katmanı hiç açma ya da siyahı komşu bölgeden al.
6. **Piksel = w_krem·krem + w_kırmızı·kırmızı + w_siyah·siyah**, w≥0, Σw=1 (kısıtlı en küçük kareler; `simplex_ls`, aşağıda). **Sızıntı cezası:** her mürekkebe seviye cinsinden ceza ver (ör. 8); rengi açıklamaya katkısı cezadan küçük mürekkep kullanılmaz. Kırmızı sızıntısı %15,9 → %2,5.
7. **Üst üste binen alfa:** Krem opak (bölge maskesi içinde). Üstteki katman alfaları `a_k = w_k`, `a_r = w_r/(w_krem + w_r)` (yığılma). Alfa <0,02 → 0, 8-bit'e yuvarla, sonra yeniden birleştirip **ölç**.
8. **Ölçüt:** yeniden birleştirme hatası ort ≈3,4, %99 ≈19, max 45 (JPEG benzeri kaynak). Katman sayısı sorusu işten önce sorulur.

**Tuzaklar:** (a) psd-tools'ta Türkçe katman adı `create_*` içine verilirse MacRoman hatası; ad önce ASCII verilir, sonra `layer.name = "Türkçe ad"` atanır ve eski Pascal ad `layer._record.name` ile ASCII yazılır. Proje kuralı ASCII adı zorunlu kılıyorsa baştan ASCII kullan. (b) Siyah katman kâğıt dokusunu yarı saydam taşır; kabul edilebilirliği kullanıcıya sorulur. (c) Dikdörtgen/kaba maske kabul edilmez. (d) İlk teslimde denetim (Sarman) maske sınırı hatasını yakaladı; maskeyi önce gözle %100 kesitte kontrol et.

**Kısıtlı en küçük kareler kodu (sınandı):**
```python
import numpy as np, itertools
def simplex_ls(px,E,penalty=None):
    """px Nx3, E kx3. min ||px - w@E||, w>=0, sum w=1, yuz numaralandirma.
    penalty: murekkep basina ceza (seviye); secim = hata + kullanilan murekkeplerin cezasi.
    Boylece rengi aciklamaya katkisi cezadan kucuk olan murekkep kullanilmaz (sizinti azalir)."""
    N=len(px); k=len(E); pen=np.zeros(k) if penalty is None else np.asarray(penalty,float)
    best=np.full(N,np.inf); W=np.zeros((N,k)); RES=np.full(N,np.inf)
    for s in range(1,k+1):
        for sub in itertools.combinations(range(k),s):
            sub=list(sub); e0=E[sub[0]]
            if s==1: w=np.ones((N,1))
            else:
                D=(E[sub[1:]]-e0); G=D@D.T
                if abs(np.linalg.det(G))<1e-6: continue
                u=((px-e0)@D.T)@np.linalg.inv(G); w=np.c_[1-u.sum(1),u]
            ok=(w>=-1e-9).all(1)
            r=np.sqrt(((px-np.clip(w,0,None)@E[sub])**2).sum(1))
            sc=np.where(ok,r+pen[sub].sum(),np.inf)
            upd=sc<best
            Wf=np.zeros((N,k)); Wf[:,sub]=np.clip(w,0,None)
            best[upd]=sc[upd]; W[upd]=Wf[upd]; RES[upd]=r[upd]
    return W,RES
```

---

## C. Doğrulanmayan Yöntemler ve Literatür

- PSD/PNG'nin Photoshop'ta açılışı; RGBA PSD'nin 4. kanalının Photoshop'ta
  nasıl göründüğü.
- Gerçek tarama/fotoğraf: kumaş üstündeki mürekkep sRGB ya da linear karışım
  gibi davranmayabilir (multiply benzeri olabilir).
- GIMP 2.10+ eşik (transparency/opacity threshold) matematiği.
- Pillow'un RGBA ölçeklemeyi içeride premultiplied yaptığı (yalnız sayısal belirti).
- Tan 2018 ve FSCS denenmedi.

---

## D. Kalite Kontrol ve Sayısal Eşik Ölçümü

1. Geri bindirme: `αF + (1−α)B` orijinalle kıyasla (kendi zemininde 0 çıkması
   doğruluk kanıtı **değildir**).
2. **Koyu zemine bindir** ve gerçek sonuçla kıyasla (asıl ölçüt).
3. Zemin bölgesinde ortalama α≈0, düz desen bölgesinde α≈1 olmalı.
4. Kontrast zeminde (siyah, macenta) kenarı %100 büyütmede incele.

---

## E. Kaynaklar ve Açık Kaynak Atıflar

- Smith & Blinn, "Blue Screen Matting", SIGGRAPH 1996: https://www.alvyray.com/Papers/CG/blusig96.pdf
- GIMP 3.2 Color to Alpha: https://docs.gimp.org/en/gimp-filter-color-to-alpha.html
- Aksoy ve ark., ACM TOG 2017 (Unmixing-Based Soft Color Segmentation): https://la.disneyresearch.com/wp-content/uploads/Unmixing-Based-Soft-Color-Segmentation-for-Image-Manipulation-Paper.pdf
- Tan ve ark. 2016 / 2018: https://cragl.cs.gmu.edu/singleimage , https://cragl.cs.gmu.edu/fastlayers
- Akimoto ve ark., CVPR 2020 (FSCS): https://github.com/pfnet-research/FSCS
- PyMatting: https://github.com/pymatting/pymatting
- psd-tools: https://psd-tools.readthedocs.io/en/stable/usage.html
- W3C PNG 3. sürüm (24.06.2025), alfa bölümü: https://www.w3.org/TR/png-3/
- Inigo Quilez, premultiplied alpha: https://iquilezles.org/articles/premultipliedalpha
- Adobe, Select and Mask (24.05.2023): https://www.adobe.com/nl/learn/photoshop/web/selection-masking-space

---

## F. Photoshop Karşılıkları ve Kanal/Katman Kuralları

Tek adımlık tam Color to Alpha yok. `Select and Mask > Decontaminate Colors`
yarı saydam kenarda eski zemin rengini temizler (Adobe belgesi). `Layer >
Matting > Defringe / Remove White Matte` kenar halesini giderir. `Select >
Color Range` yumuşak maske verir ama rengi arındırmaz. Divide karışım modu renk
kaymasını giderir ama alfa üretmez. Karışım modlarının (Multiply/Divide)
Adobe'nin kendi açıklaması **doğrulanamadı**.

---

## G. Tuzaklar ve Ölçülmüş Hatalar

- **Uzay uyuşmazlığı:** Görsel sRGB'de birleştirilmişken hesabı linear'de yapmak
  geçiş bölgesinde α'yı 0,543 yerine 0,704'e çıkarır (tersi 0,33); kenarda
  13,6–18 seviye hata. Uyumlu uzayda 0,34–1,49.
- **Zemin rengi hatası asimetrik:** Color to Alpha'da zemini olduğundan koyu
  vermek çok zararlı (−15 seviyede zemin α 0,36; +15'te 0,07). Palet yöntemi
  her iki durumda da küçük hata verir (≤0,054).
- **Işık gradyanı (±%8):** Color to Alpha'da zemin α 0,144, en büyük hata 0,80;
  palet + polinom zeminde 0,002. Normalize Gauss ile zemin kestirimi desen
  altında patlar (en çok 234 seviye); kullanma.
- **JPEG:** Kenar alfa hatası PNG'ye göre 2,2× (q95 4:4:4) ile 10,4× (q70 4:2:0)
  artar. Aynı kalitede 4:2:0, 4:4:4'ten kötüdür.
- **Hale:** Straight alfayla %50 küçültme kenarda en çok 49 seviyelik açık hale
  yapar; premultiplied kutu filtrede hata 0. Lanczos'ta en çok 12 seviye kalır
  (filtre taşması).
- **PNG straight alfa saklar.** Hesap premultiplied yapıldıysa yazmadan önce
  `F = P/α` ile geri böl.
- **PSD tuzağı:** psd-tools 1.25'te `PSDImage.new("RGB")` + RGBA katman yazınca
  alfa saydamlık kanalına değil **katman maskesine** gider. `PSDImage.new("RGBA")`
  kullan: alfa `TRANSPARENCY_MASK` kanalında birebir korunur. Yazma "deneysel"
  işaretli; pytoshop 2018'den beri bakımsız.
- **Mürekkep üst üste binen bölgeler:** Palet yöntemi tek renk seçer; sınanmadı.

---

## H. Varsayılan Boru Hattı (Matematiksel Model ve Kod)

1. Kaynak PNG/TIFF olmalı. JPEG zorunluysa q≥95 ve 4:4:4.
2. Zemin rengi `b`: geniş düz bölgenin **medyanı** (tek piksel değil).
3. Zeminde ışık gradyanı varsa: ilk α>0,15 bölgesini 6 px genişletip dışarıda
   bırak, kalan zemine **2. derece polinom yüzey** uydur (ortalama hata 2,5 seviye).
4. Palet `{Fk}`: bilinen mürekkep renkleri, yoksa α>0,8 piksellerde k-means
   (k=8, birbirine 12 seviyeden yakın merkezleri birleştir, 20 pikselden
   küçük kümeleri at). k=4 ile mürekkep kaçırdı.
5. Alfa: `α = clip(⟨c−b, Fk−b⟩ / |Fk−b|², 0, 1)`, her piksel için en iyi `Fk`.
6. Eşik: `α < 0,02 → α = 0` (zemin gürültü kalıntısını %63,9'dan %0,1'e indirir;
   0,05 ek kazanç getirmez).
7. Çıktı: straight RGBA PNG + `PSDImage.new("RGBA", ...)` ile PSD.
8. Ölçekleme/bulanıklaştırma gerekirse **premultiplied** uzayda yap.

Hesap, görselin birleştirildiği uzayda yapılmalıdır (dijital tasarım için sRGB).

```python
import numpy as np

def palette_alpha(c, b, palette):
    """Bilinen murekkep renkleriyle alfa: her piksel icin en iyi Fk, a=<c-b,Fk-b>/|Fk-b|^2."""
    c = np.asarray(c, np.float64); b = np.broadcast_to(np.asarray(b, np.float64), c.shape)
    best = np.full(c.shape[:2], np.inf); A = np.zeros(c.shape[:2]); F = np.zeros_like(c)
    for Fk in palette:
        d = np.asarray(Fk) - b
        a = np.clip(((c - b) * d).sum(-1) / np.maximum((d * d).sum(-1), 1e-9), 0, 1)
        r = ((c - b - a[..., None] * d) ** 2).sum(-1); s = r < best
        best[s], A[s], F[s] = r[s], a[s], np.asarray(Fk)
    return A, F

def premultiply(a, F):      return F * a[..., None]
def unpremultiply(a, P, eps=1e-6):
    return np.where(a[..., None] > eps, P / np.maximum(a, eps)[..., None], 0.0)
```

Color to Alpha formülü (yedek yöntem, kanallar 0–1): her kanal için
`a_i = (c_i−b_i)/(1−b_i)` (c_i>b_i), `a_i = (b_i−c_i)/b_i` (c_i<b_i), eşitse 0;
`α = max(a_R,a_G,a_B)`; `F = (c−b)/α + b`; `α<1e-4` ise tam saydam.

---

## I. Yöntem Seçimi ve Sentetik Sınama Sonuçları

| Yöntem | Ne zaman | Sonuç |
|---|---|---|
| **Palet izdüşümü** (varsayılan) | Mürekkep/desen renkleri biliniyor ya da çıkarılabiliyor | Alfa hatası 0,004; koyu zemine bindirme hatası 0,46 seviye |
| Color to Alpha (GIMP/GEGL) | Palet bulunamazsa yedek | Alfa hatası 0,063; tam mürekkepte α yalnız 0,82–0,91; koyu zemine bindirme hatası 11–13 seviye (düz bölgede 28) |
| İki zeminde çekim (triangulation) | Desen ayrı taşıyıcıdaysa (kâğıt, asetat) | Kumaşa basılı desende uygulanamaz. `α = 1 − (ΣI1−ΣI2)/(ΣB1−ΣB2)` |
| PyMatting (trimap'li) | Eşitsiz zeminde zemini temizlemek için | Zemin temiz ama keskin kenarda ve ince çizgide kötü (çizgi hatası 0,48–0,57); 5–7 sn. Bu iş için uygun değil |
| Soft color segmentation (Aksoy 2017, Tan 2016/2018, FSCS 2020) | Çok renkli, çok katmanlı desen | **Sınanmadı.** Tan 2018 Python kodu, FSCS MIT lisanslı (7 katman hazır model) |
| rembg / SAM | Ayrı bir nesne (ürün, kişi, logo kartı) | Desen kumaşın parçasıysa, ince çizgi veya soluk geçiş varsa uygun değil; renk arındırması yapmaz. rembg `-ppm` yarı saydamlığı siler |

Color to Alpha neden varsayılan değil: her pikselde mümkün olan **en küçük**
alfayı seçer; düz mürekkepte α<1 kalır ve renk uca itilir. Kendi zemininde
orijinali birebir geri verdiği için (hata 0) bu ölçüt yanıltıcıdır: doğruluk
yalnız **farklı (koyu) bir zemine bindirerek** ölçülür.
