# Görsel Düzeltme ve Desen Mühendisliği Rehberi (MeChi 3.3 — Nano Banana Pro)

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Amaç ve Temel Felsefe](#a-amaç-ve-temel-felsefe) | L19-L22 | Adli referans, idealize düz yüzeyde yeniden yaratma |
| [B. Ankara İçin Prompt Kuralları](#b-ankara-için-prompt-kuralları) | L26-L34 | İngilizce metin, 4K, tek görsel ve kesin yasaklar |
| [C. Hata ve Çözüm Tablosu (9 Satırlık Tam Tablo)](#c-hata-ve-çözüm-tablosu-9-satırlık-tam-tablo) | L38-L50 | Kıvrım, silüet, bozuk yazı ve renk revizyonları (9 hata çözümü) |
| [D. Kaliko'nun Payı ve İşleme Adımları](#d-kalikonun-payı-ve-işleme-adımları) | L54-L60 | 4K büyütme, şeffaf zemin ve kenar halesi temizliği |
| [E. Lisansa Takılmayan En Yakın Tasarım](#e-lisansa-takılmayan-en-yakın-tasarım) | L64-L70 | Filigran/marka yönetimi, korunan ve değişen öğeler |
| [F. Modüler Master Prompt Mimarisi ve MeChi 3.3 Çelişki Giderme Notları](#f-modüler-master-prompt-mimarisi-ve-mechi-33-çelişki-giderme-notları) | L74-L110 | 4K tek görsel İngilizce Master Prompt şablonu ve MeChi 3.3 kuralları |
| [G. Sarman Kontrol Listesi ve Denetim](#g-sarman-kontrol-listesi-ve-denetim) | L114-L127 | Tek parça, 4K, sıfır kumaş izi, düz yazı denetimi ve kanıtlar |
| [H. Yedi Parametreli Mikro Analiz Listesi](#h-yedi-parametreli-mikro-analiz-listesi) | L131-L140 | Kapsam, mikro detay, stil, palet, zemin, onarım, metin protokolü |

---

## A. Amaç ve Temel Felsefe

1. **Yeniden Yaratma Prensibi:** Kullanımı imkânsız, bozuk, kırışık kumaş üzerindeki veya manken üzerinde giyilmiş giysi fotoğraflarındaki desenleri "temizlemek veya ütülemek" değil; bozuk görseli bir **adli referans şeması (forensic reference)** kabul ederek idealize edilmiş 2D gergin tuvalde sıfırdan yeniden inşa etmektir.
2. **Tek Görsel Kuralı:** Çıktı daima **tek bir parça halinde** üretilir. Katman, panel, varyant veya çoklu çıktı kesinlikle yasaktır. Katman ayırma işi temiz görsel elde edildikten sonra ayrı bir iş olarak Kaliko tarafından yürütülür.

---

## B. Ankara İçin Prompt Kuralları

- Prompt **her zaman İngilizce** ve **yalnızca prompt** olarak verilir. Açıklama, selam, soru yok. Tek satır Türkçe not (varsayımlar) en fazla.
- Üç katmanlı yapı zorunlu: **Ana Görev → Sadakat → Kritik Yasaklar.**
- Tek görsel kuralı: Yasaklar bölümünde mutlaka "ONE image only, no layers, no parts" bulunur.
- Zemin rengi: Kaynak zemin açıksa **beyaz**, koyuysa **siyah**; zemin tasarımın parçasıysa (pembe, lila vb.) o rengin idealize edilmiş hali. Graffiti desenlerinde her zaman beyaz.
- Çözünürlük: En az 4K (3840 px genişlik). Model daha azını verirse Kaliko büyütür.
- Format: PNG tercih edilir. Gerçek şeffaflığı çoğu yapay zekâ aracı üretemez; düz zeminli görsel iste, şeffaflaştırmayı Kaliko yapar.
- Her promptta bozuk görselin özelliklerini (renk, stil, motif, yazı) somut yaz; "güzel desen" gibi genel ifadeler kullanma.

---

## C. Hata ve Çözüm Tablosu (9 Satırlık Tam Tablo)

| Karşılaşılan Sorun | Uygulanacak Çözüm / Prompt Revizyonu |
|---|---|
| Kumaş/giysi çıktıda kalıyor | Yasak listesini güçlendir, "standalone graphic" ekle. 2-3 denemede olmazsa dur: desen kumaşın parçası olabilir (ağartma, asit yıkama). |
| Desen giysi siluetine sıkışıyor | "Full-frame rectangular, extend edge to edge, DO NOT confine to the shape of the garment" ekle. |
| Yazı eğri/bozuk kalıyor | Kusurlu yazıyı referans olmaktan çıkar: "COMPLETELY DISCARD the source text shape"; yeni yazıyı düz taban çizgisiyle sıfırdan tarif et. |
| Bulanık yazı "anlamlı" yazıya dönüştü | "Treat it as a shape to be drawn, not as text to be read. DO NOT replace it with new text" ekle. |
| Renkler soluk/ışıktan bozuk | Paleti hex veya net renk adıyla ver: "clean solid idealized colors". |
| Model birden çok parça/katman üretti | Yasaklara "ONE image only, no layers, no parts, no variants" ekle; görevi tek cümleye indir. |
| Model detay uydurdu | Sadakat bölümüne "do not add any element not in the original" ekle ve eksik kısmın stilini somut tarif et. |
| Model komutları yarım uyguluyor | Promptu protokol biçimine çevir: [PRESERVATION], [REPLACEMENT], [FIDELITY]; her madde tek komut olsun. |
| Görev çok soyut ("yeni desen yarat") | "Sadece gördüğün deseni temizle" seviyesine sadeleştir. |

---

## D. Kaliko'nun Payı ve İşleme Adımları

- Çözünürlük 4K'nın altındaysa kayıpsız büyütme (yöntemini ve oranını raporla).
- Düz zeminden şeffaf PNG üretme; kenar halesi (halo) kontrolü.
- Orijinalle renk ve konum kıyası (yan yana önizleme).
- Çıktıyı yeni adla kaydet (`_duzeltme_v1`); kaynak dosyaya dokunma.
- Katman/kanal ayırma istenirse bu **ayrı bir görevdir**, bu rehbere dahil değildir.

---

## E. Lisansa Takılmayan En Yakın Tasarım

Kaynak görselde telifli logo, marka, stok sitesi filigranı veya tanınmış karakter varsa:
1. **Korunanlar:** Çizim tekniği ve çizgi dili, renk paleti, kompozisyon düzeni (yerleşim, oran, yazı bandının yeri), baskı amacı ve görsel enerji.
2. **Mutlaka Değişenler:** Ana figür/motif farklı bir tasarım olur (aynı pozun aynı çizimi değil); sembol ve süs öğeleri yeniden kurgulanır; marka yazıları yerine `[YOUR OWN TEXT]` bırakılır.
3. **Kesinlikle Girmeyenler:** Filigran, stok sitesi yazısı, marka, logo, tanınmış karakter.
4. **Sarman Denetimi:** Çıktıyı kaynakla karşılaştırır; figür veya sembol kaynağın aynısıysa Ankara promptu daha fazla farklılaştırarak yeniden yazar (en fazla 3 deneme).

---

## F. Modüler Master Prompt Mimarisi ve MeChi 3.3 Çelişki Giderme Notları

1. **4K Tek Görsel İngilizce Master Prompt Şablonu:**

```text
From the provided image, recreate the complete printed design as ONE single,
flat, full-frame rectangular digital illustration at high resolution
(4K, at least 3840 px wide), crystal-clear and sharp.

FIDELITY: Faithfully replicate the original's [MOTIFS], its exact
[COLOR PALETTE] rendered as clean solid idealized colors, its [LINE/OUTLINE
STYLE], its [TEXT/LETTER SHAPES if any], and its exact composition and
positions. Where a part is hidden by folds or damage, complete it by
continuing the original's own style and logic. Blurry or tiny details must be
redrawn sharply as the same shapes; never replace, simplify or omit them.
The design must extend continuously from edge to edge of the canvas.

GEOMETRY: Perfectly flat orthographic 2D. All lines geometrically precise.
Text and rows aligned on straight baselines, correcting any curvature from
the source.

BACKGROUND: Clean solid [WHITE / BLACK / idealized original color].

CRITICAL: Output exactly ONE image. DO NOT split the design into layers,
parts, panels, channels, variants or multiple outputs. DO NOT include any
garment, t-shirt, fabric, weave, wrinkles, folds, pleats, drapes, shadows,
highlights, reflections or mockup. DO NOT add any element that is not in the
original. DO NOT remove, reduce or reinterpret any element. DO NOT beautify.
DO NOT include watermarks, stock-site text, brand names, logos or characters.
[CASE-SPECIFIC PROHIBITIONS: brands, logos, text to exclude]
```

2. **MeChi 3.3 Çelişki Giderme Notları:**
   - **Tek Görsel Zorunluluğu:** Eski "Full_Combined…" adı ve katman mantığı kaldırıldı; çıktı tek bir parça olmak zorundadır.
   - **Şeffaf Arka Plan + JPG Çelişkisi:** JPG formatı şeffaflık taşıyamaz. Düz renk zemin istenir, şeffaflaştırmayı Kaliko yapar.
   - **Detay Uydurma Çelişkisi:** "Orijinalde olmayan detay ekleme" ile "gizli detayı yeniden oluştur" çelişkisi giderildi: Eksik kısımlar yalnızca orijinalin kendi stili ve simetrisiyle tamamlanır, yeni motif uydurulmaz.
   - **Çözünürlük Standardı:** Eski 2K hedefi 4K (en az 3840 px) olarak güncellendi.

---

## G. Sarman Kontrol Listesi ve Denetim

Sarman görsel düzeltme teslimatlarını şu kontrol listesiyle denetler:

- [ ] Tek parça mı? Katman, panel, varyant yok mu?
- [ ] Orijinalle yan yana kıyasta eksik veya fazla motif var mı?
- [ ] Kumaş izi, kırışıklık, gölge, yansıma, silüet kalmış mı?
- [ ] Yazılar düz taban çizgisinde mi, orijinalin şekline sadık mı?
- [ ] Renkler orijinal paletle uyuşuyor mu?
- [ ] Çözünürlük en az 3840 px genişlik mi, kenarlar keskin mi?
- [ ] Zemin kurala uygun mu, istenmişse şeffaflık temiz mi (halo yok)?
- [ ] Orijinal kaynak dosyaya dokunulmamış mı?

**Kaliko Kanıt Teslimi:** Kaliko denetim makbuzuna `ffprobe` veya `identify` çıktısını, orijinal ve sonucun küçültülmüş yan yana kopyasını ekler.

---

## H. Yedi Parametreli Mikro Analiz Listesi

Prompt yazılmadan önce görsel şu 7 parametre açısından mikro düzeyde taranır:
1. **Desen Türü (`[KAPSAM]`):** Tam tuval metraj desen mi yoksa tekil parça/tişört göğüs baskısı mı?
2. **Ana Motifler (`[ANA OBJE VE MİKRO DETAYLAR]`):** Figürler, geometrik yapılar, nokta dizilimleri ve iç içe geçme sırası.
3. **Teknik Üslup (`[STİL VE TEKNİK ÖZELLİKLER]`):** Düz vektör, noktalama (stippling), gravür/tarama çizgileri veya fırça darbeleri.
4. **İdealize Palet (`[RENK PALETİ]`):** Fotoğraftaki kirli/gölgeli renkler değil; baskıdaki homojen (solid) renkler ve yaklaşık HEX kodları.
5. **Zemin Rengi (`[ZEMİN RENGİ]`):** Açık kumaş için beyaz (`#FFFFFF`), koyu kumaş için siyah (`#000000`) veya idealize fon rengi.
6. **Onarım Alanları (`[ONARIM BÖLGELERİ]`):** Kıvrım veya kol altında kaybolan kısımların simetri mantığıyla tamamlanması.
7. **Tipografi Durumu (`[METİN PROTOKOLÜ]`):** Harf harf doğru yazılış, font stili ve düz taban çizgisine hizalama.
