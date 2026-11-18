# Görsel Düzeltme, Telif Stratejisi ve Kalite Kontrol Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Kaliko'nun Payı ve İşleme Adımları](#a-kalikonun-payı-ve-işleme-adımları) | L14-L20 | 4K büyütme, şeffaf zemin ve kenar halesi temizliği |
| [B. Lisansa Takılmayan En Yakın Tasarım](#b-lisansa-takılmayan-en-yakın-tasarım) | L24-L30 | Filigran/marka yönetimi, korunan ve değişen öğeler |
| [C. Sarman Kontrol Listesi ve Denetim](#c-sarman-kontrol-listesi-ve-denetim) | L34-L47 | Tek parça, 4K, sıfır kumaş izi, düz yazı denetimi ve kanıtlar |

---

## A. Kaliko'nun Payı ve İşleme Adımları

- Çözünürlük 4K'nın altındaysa kayıpsız büyütme (yöntemini ve oranını raporla).
- Düz zeminden şeffaf PNG üretme; kenar halesi (halo) kontrolü.
- Orijinalle renk ve konum kıyası (yan yana önizleme).
- Çıktıyı yeni adla kaydet (`_duzeltme_v1`); kaynak dosyaya dokunma.
- Katman/kanal ayırma istenirse bu **ayrı bir görevdir**, bu rehbere dahil değildir.

---

## B. Lisansa Takılmayan En Yakın Tasarım

Kaynak görselde telifli logo, marka, stok sitesi filigranı veya tanınmış karakter varsa:
1. **Korunanlar:** Çizim tekniği ve çizgi dili, renk paleti, kompozisyon düzeni (yerleşim, oran, yazı bandının yeri), baskı amacı ve görsel enerji.
2. **Mutlaka Değişenler:** Ana figür/motif farklı bir tasarım olur (aynı pozun aynı çizimi değil); sembol ve süs öğeleri yeniden kurgulanır; marka yazıları yerine `[YOUR OWN TEXT]` bırakılır.
3. **Kesinlikle Girmeyenler:** Filigran, stok sitesi yazısı, marka, logo, tanınmış karakter.
4. **Sarman Denetimi:** Çıktıyı kaynakla karşılaştırır; figür veya sembol kaynağın aynısıysa Ankara promptu daha fazla farklılaştırarak yeniden yazar (en fazla 3 deneme).

---

## C. Sarman Kontrol Listesi ve Denetim

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
