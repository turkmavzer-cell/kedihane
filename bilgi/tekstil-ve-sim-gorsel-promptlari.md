# Tekstil ve Sim Kumaş Görsel Prompt Mühendisliği Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Altın Kurallar, Doku Sadakati ve Görsel Yasaklar](#a-altın-kurallar-doku-sadakati-ve-görsel-yasaklar) | L15-L31 | Referans sadakati, 3:4 dikey oran, yetişkin manken ve astar kuralı |
| [B. Giydirme Promptları — Şal ve Aksesuar Ayrımı](#b-giydirme-promptları--şal-ve-aksesuar-ayrımı) | L35-L42 | Şalın ceket/kimonoya dönüşmesini önleyen negatif formül |
| [C. Kumaş Zemini, Poz ve Taş (Rhinestone) Detayı](#c-kumaş-zemini-poz-ve-taş-rhinestone-detayı) | L46-L54 | Homojen kumaş zemini, klişe poz yasağı, taş kesimi ve ışık kırılması |
| [D. Sim (Glitter) Kumaş ve Makro Işık Prompt Mühendisliği](#d-sim-glitter-kumaş-ve-makro-ışık-prompt-mühendisliği) | L58-L76 | 1-2 mm serpme sim dağılımı, loş ışıkta zemin rengi koruma |

---

## A. Altın Kurallar, Doku Sadakati ve Görsel Yasaklar

Tekstil, kumaş baskı, sim (glitter) ve taş dizimi (rhinestone) görsel üretimlerinde gerçekçi katalog standardını sağlamak için şu temel kurallar uygulanır:

1. **Desen ve Kumaş Sadakati:**
   - Referans görseldeki taş veya nakış deseni adli bir şema kabul edilir. Desen kumaş kıvrımlarını doğal olarak takip etmeli, düz yapıştırma gibi durmamalıdır.
   - Referans görselin siyah veya gri arka planı desene ait değildir; yalnızca taş/baskı motifleri kumaşın üzerine giydirilir.
   - Taş veya simler kesinlikle modelin tenine, saçına veya arka plan boşluğuna taşırılamaz.
2. **Kırpma ve Çerçeveleme:**
   - Zemin, masa kenarı veya duvar boşlukları kadrajı boşa harcamamalı; kumaş ve desen odaklı sıkı çerçeveleme yapılmalıdır.
   - Yapay zekâ ile üretilen tüm pazarlama görselleri teslimatta *"temsili / örnek uygulama"* olarak etiketlenir.
3. **Format ve Çözünürlük:**
   - Katalog görselinde varsayılan format **3:4 dikey** (`1792x2400` veya `2160x2880` 4K).
4. **Manken ve Kıyafet Standartları:**
   - **Yaş Kriteri:** Yalnızca yetişkin modeller kullanılır. Çocuk veya ergen modeller kesinlikle yasaktır.
   - **Hedef Pazar:** Kıyafet, iklim ve sahne hedef bölgenin kültür ve mevsim kurallarına uygun seçilir; görev tanımında belirtilmemişse sorulur.
   - **Abiye / Ev Giyimi:** Dekolte veya sırt kesimi içeren modellerde **opak astar zorunludur**; iç çamaşırı görünmez, çıplaklık kesinlikle yasaktır. Promptlarda "luxury loungewear / evening catalog" terimleri kullanılır.

---

## B. Giydirme Promptları — Şal ve Aksesuar Ayrımı

Şal ve örtü giydirmelerinde modelin giysisi ile aksesuarın birbirine karışmaması için katı negatif ve pozitif tanımlar kullanılır.

1. **Omuz Şalı ve Kolsuz Duruş Kuralı:** Yapay zekânın şalı ceket, hırka, kimono veya kollu bir giysiye dönüştürmesini önlemek için şu formül zorunludur:
   `rectangular long shawl draped over shoulders, both ends hanging freely, NOT a jacket, NOT a robe, NOT a kimono, NO sleeves, sleeveless undergarment.`
2. **Desen Uygulaması:** `the exact motif from the reference image, applied realistically along the fabric folds with natural light reflections` ifadesi desenin düz yapıştırılmasını önler.
3. **Arka Işık:** Koyu kumaşta kenar ışığı (`warm backlight rimming the edges of the fabric`) dokuyu belirginleştirir.

---

## C. Kumaş Zemini, Poz ve Taş (Rhinestone) Detayı

1. **Doku ve Kumaş Koruma:**
   - Kumaş yüzeyleri (saten, şifon, kadife, krep) homojen baskı zeminleri olarak korunur; desen zemini bozmamalıdır.
2. **Doğal Poz Standartları:**
   - Yapay zekânın sıkça tekrarladığı "eli saçında / başında tutma" klişesi yasaktır (`NO hands in hair, NO hand touching head`).
   - Pozlar doğal, iki el serbest veya zarifçe belde/yanlarda konumlanmış kendinden emin duruşlar olmalıdır.
3. **Taş Detayı:**
   - Taş dizilimleri kumaş kıvrımında kristal yansımalar üretmeli; taşların tek tek kesimleri (~2-3 mm) ve ışık kırılmaları belirgin olmalı, taşlar öbekleşmemelidir.

---

## D. Sim (Glitter) Kumaş ve Makro Işık Prompt Mühendisliği

Simli kumaş tasarımlarında simlerin pullara, payetlere veya yoğun lekelere dönüşmemesi için mikro mühendislik ilkeleri uygulanır.

1. **Üfleme ve Serpme İlkesi:**
   - Simler hava püskürtmesiyle serpiştirilmiş gibi homojen ve aralıklı durmalıdır.
   - Temel formülasyon:
     `randomly scattered individual fine glitter particles, clear fabric visible between particles, NO clusters, NO patterns, NO large sequins.`
2. **Sim Boyutu ve Işıklandırma:**
   - Sim taneleri 1–2 mm ultra ince mikro simler olmalıdır.
   - Işıklandırma: Loş iç mekânda zemin kumaş rengi bozulmadan ve kararmadan, noktasal yönlü ışık (pinpoint light / rim light) ile her bir simin minik parlama noktaları oluşturması sağlanır.
3. **Master Simli Kumaş Prompt Şablonu:**
   ```text
   Fashion photography, 3:4 vertical framing, 4K resolution.
   An adult model wearing a solid deep ruby-red premium crepe scarf draped softly over her shoulders.
   The entire scarf is evenly misted with fine 1-2mm sparkling holographic glitter specks that catch the light delicately with every fold.
   No clumping, no large sequins, no dense clusters; the solid fabric remains the dominant base with a sophisticated shimmering overlay.
   Warm interior studio lighting with subtle edge sparkle. Photorealistic, ultra-detailed fabric weave and pristine skin texture.
   ```
