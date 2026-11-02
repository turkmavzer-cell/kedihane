# Bilgi Haritası (Konu → Asıl Yer)

> **Ne zaman okunur:** Yalnız repoya yeni bilgi yazılırken veya bir konunun yeri aranırken. Her oturumda yüklenmez.
> **Tek kaynak kuralı:** Bir bilgi yalnız asıl yerine yazılır; başka her yerde en fazla tek satır atıf olur. `tools/denetim.py` Kontrol 7 ve 8 bunu her commit'te denetler.

## Yerleştirme Karar Ağacı

Yeni bilgi sırayla bu sorulardan geçer; ilk "evet" asıl yerdir.

1. Gizli, kişisel, müşteri, marka, proje adı, telefon, adres, hesap veya fiyat içeriyor mu? → Kedihane'ye yazılmaz (CLAUDE.md Bölüm 9 ve 14). Arındırılabiliyorsa genel hale getirilir; arındırılamıyorsa Cihan'a bildirilir.
2. Tüm ekibi bağlayan bir kural mı (güvenlik, onay, dil, hafıza, yönlendirme)? → `CLAUDE.md` ilgili bölüm. Güvenlik veya onay kuralına dokunuyorsa Cihan onayı şarttır.
3. Yalnız Antigravity'ye özgü mü (model seçimi, kota, `invoke_subagent`)? → `GEMINI.md` ilgili bölüm.
4. Yöntem, standart, eşik veya araç kullanımı mı? → Aşağıdaki tablodaki asıl rehber + harfli bölüm. Bölüm yoksa harf sırasına göre yeni `## X.` açılır, fihriste satır eklenir, ardından `python tools/denetim.py --fihrist-duzelt` çalıştırılır.
5. Bir ajanın işte öğrendiği, doğrulanmış tek satırlık ders mi? → `.claude/agent-memory/<ajan>/MEMORY.md`, ilgili `### konu` (A–Z). Yöntemin kendisi rehberdeyse hafızaya yalnız atıf yazılır. Doğrulanmamış bilgi hafızaya girmez; rehbere "doğrulanmadı" notuyla girer.
6. Kedihane reposunun kendisine dair mimari karar veya tuzak mı? → `.agents/learnings/PROJECT.md` tablosu.
7. Bir dosya değişikliğinin kaydı mı? → `CHANGELOG.md`.
8. Hiçbiri değil ya da iki yere eşit uyuyor → Cihan'a tek soru sorulur.

Yeni bir rehber veya konu eklenirse bu tabloya satır eklenir (Kontrol 8 haritada olmayan rehberi hata sayar).

## Ekleme Prosedürü

Uygulayan: Minnak Tekir (`.claude/agents/minnak-tekir.md`). Elle ekleme yapan herkes de aynı adımları izler. Fişi Sarman denetler, commit için Tekir Cihan'a sorar (CLAUDE.md Bölüm 14).

**Ders satırı (ajan raporunun sonunda, ders yoksa `Ders: yok`):**
`Ders: [doğrulandı | doğrulanmadı | Cihan: iyi | Cihan: kötü] <projeden bağımsız tek cümle> (iş türü: <ör. video kurgu>)`

0. `git status --porcelain` boş değilse dur. `git config core.hooksPath` boşsa `git config core.hooksPath .githooks`. `python tools/denetim.py` çalıştır, mevcut HATA'ları "önceden var" diye not et.
1. Girdiyi atomik birimlere böl: bir birim = tek kural, tek eşik ya da tek ders.
2. Gizlilik (Bölüm 9, 14): müşteri, marka, hesap, telefon, adres, fiyat, proje adı, kişisel yol ve tek görsele özgü ölçü/koordinat/renk çıkarılır. Çıkarılamıyorsa birim yazılmaz.
3. Yer: yukarıdaki karar ağacı, sonra Konu Haritası. Yöntem/standart rehbere gider; hafızaya yalnız `doğrulandı` ya da `Cihan: iyi` olan tek satırlık ders girer (yöntem rehberdeyse yalnız atıf). `doğrulanmadı` → rehbere "doğrulanmadı" notuyla. `Cihan: kötü` → rehberdeki hatalı adım düzeltilir. Yer belirsizse dur.
4. Tekrar ve çelişki (zorunlu; denetim anlamca tekrarı yakalamaz): 2–4 ayırt edici terim seç (sayı+birim, araç, parametre; genel sözcük değil). `git grep -n -i -E "t1|t2|t3" -- '*.md' ':!CHANGELOG.md'` (40 satırı aşarsa daralt). Asıl yerde varsa ekleme yapma. Başka yerde varsa asıl yere taşı, eski yeri `> Bu konu: [dosya §X](yol)` atfına çevir. Farklı değer varsa dur.
5. Yaz: rehberde hedef bölümün biçimiyle, konuya en yakın `###` altına. Hafızada `- YYYY-AA-GG: ders`, ilgili `###` altına (A–Z; yoksa sırasındaki yerde aç). Değer değişirse satırı yerinde güncelle, sonuna `(güncellendi YYYY-AA-GG; önceki: X)`. "doğrulanmadı" notu silinmez, metin özetlenip kısaltılmaz.
6. Yeni konu/bölüm → Konu Haritası satırı. Denetimin bildiği birimde (çözünürlük, fps, mbps, lufs, lpi, ppi) sayısal standart → Sayısal Standartlar satırı.
7. `python tools/denetim.py --fihrist-duzelt`, sonra `python tools/denetim.py`. Kendi hatanı 2 turda düzeltemezsen dur.

**Okuma bütçesi:** bu dosya + hedef fihrist + hedef bölüm (`## X.` → sonraki `## `) + grep eşleşmelerinin ±3 satırı + hedef `MEMORY.md`. Tam okuma ve tam tarama yasak.
**Dur ve sor:** kirli çalışma ağacı, yer belirsiz, çelişki, gizlilik, Bölüm 8/9/11 ya da onay kuralı, `MEMORY.md` 100 satır, silme, geçmeyen denetim.

## Konu Haritası

| Konu | Anahtar sözcükler (başlık uyarısı) | Asıl dosya | Asıl başlık | Sahip |
|---|---|---|---|---|
| Ekip kuralları, güvenlik, hafıza | onay kuralı | `CLAUDE.md` | §9, §10, §14 | Tekir |
| Bilgi yerleştirme prosedürü, ders satırı | ders satırı | `bilgi/HARITA.md` | Ekleme Prosedürü | Minnak Tekir |
| Antigravity model ve kota | kota geçiş | `GEMINI.md` | §2 | Tekir |
| Kedihane mimari kararları | proje kararları | `.agents/learnings/PROJECT.md` | tümü | Tekir |
| Teslimat ve kodlama ilkeleri | no-ai-slop, karpathy | `bilgi/teslimat-ve-kodlama-ilkeleri.md` | tümü | herkes |
| Emprime / serigrafi kanal ayırma | kanal ayırma, tramlama, alt baskı | `bilgi/emprime-kanal-ayirma.md` | tümü | Kaliko |
| Katman ayırma ve PSD | bölge grupları | `bilgi/katman-ayirma.md` | tümü | Kaliko, Bombay |
| Bozuk görseli yeniden yaratma promptu | mikro analiz, mechi | `bilgi/gorsel-duzeltme.md` | tümü | Ankara, Kaliko |
| Tekstil ve sim kumaş promptları | glitter, giydirme | `bilgi/tekstil-ve-sim-gorsel-promptlari.md` | tümü | Ankara |
| Video kurgu akışı, çıktı standardı, denetim | plan.json, kurgu dili | `bilgi/video-kurgu.md` | A, B, C, D, E | Kaliko |
| Araç dışı FFmpeg ve Premiere XML | premiere, xfade | `bilgi/sosyal-medya-ve-video-operasyonu.md` | C | Kaliko |
| Arapça / RTL tipografi | rtl | `bilgi/sosyal-medya-ve-video-operasyonu.md` | A | Kaliko |
| Yuvalara görsel yerleştirme, bitiş kartı | bitiş kart | `bilgi/sosyal-medya-ve-video-operasyonu.md` | B | Kaliko |
| Müşteri yanıtlama (onay, WhatsApp yer tutucu) | müşteri yanıt | `bilgi/sosyal-medya-ve-video-operasyonu.md` | D | Ankara, Kaliko |
| Sosyal hesap güvenliği, yerel kayıt | yerel kayıt | `bilgi/sosyal-medya-ve-video-operasyonu.md` | E | Kaliko |
| Self-hosted servisler ve MCP kurulumu | coolify, n8n, context7, postiz, documenso, twenty | `bilgi/self-hosted-ve-mcp-servisler.md` | tümü | Bombay |
| 21st / Magic MCP kurulumu | magic mcp | `bilgi/self-hosted-ve-mcp-servisler.md` | M | Bombay |
| Arayüz tasarımı ve web testi | bento, kontrast, playwright | `.agents/skills/frontend-ve-ui/SKILL.md` | tümü | Bombay, Ankara |
| Güvenlik denetimi, hata ayıklama, repomix | enjeksiyon, repomix | `.agents/skills/guvenlik-denetimi/SKILL.md` | tümü | Sarman, Bombay |
| Rötuş, Remotion, ses klonlama, FFmpeg analizi | remotion, openvoice, vtracer | `.agents/skills/medya-ve-katman/SKILL.md` | tümü | Kaliko |
| Görsel üretim promptu, kamera | reasoning brief | `.agents/skills/medya-ve-katman/SKILL.md` | T | Ankara |
| Pazarlama, CRO, e-posta, SEO, sosyal içerik | cro, seo | `.agents/skills/pazarlama-ve-buyume/SKILL.md` | tümü | Ankara, Van |
| Finans verisi, algoritmik ticaret | openbb, freqtrade | `.agents/skills/veri-ve-finans/SKILL.md` | F | Bombay, Van |
| Fiyatlandırma stratejisi | fiyatlandırma | `.agents/skills/veri-ve-finans/SKILL.md` | P | Van |
| Web veri kazıma, belge dönüştürme | scrapling, markitdown | `.agents/skills/veri-ve-finans/SKILL.md` | V, R | Bombay, Siyam |
| Kariyer ve iş başvuru otomasyonu | ats | `.agents/skills/veri-ve-finans/SKILL.md` | K | Ankara, Bombay |

## Sayısal Standartlar

Bağlam deseni (regex) eşleşen bir satırda aynı birimden farklı bir değer asıl dosya dışında geçerse Kontrol 7 hata verir.

| Standart | Birim | Değer | Bağlam deseni | Asıl dosya |
|---|---|---|---|---|
| Dikey video master | çözünürlük | 1080x1920 | `dikey master\|master çıktı\|reels\|shorts\|tiktok` | `bilgi/video-kurgu.md` |
| Kısa video müzik yüksekliği | lufs | -14 | `müzik\|reels\|shorts\|tiktok\|youtube` | `bilgi/video-kurgu.md` |
| Emprime tram frekansı | lpi | 45 | `tram\|moiré\|film` | `bilgi/emprime-kanal-ayirma.md` |
| Emprime film çözünürlüğü | ppi | 508 | `tram\|film\|emprime\|dither` | `bilgi/emprime-kanal-ayirma.md` |
