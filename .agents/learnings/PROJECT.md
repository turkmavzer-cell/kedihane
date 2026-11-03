# Projeye Özel Öğrenimler ve Mimari Hafıza (`PROJECT.md`)

> **Kapsam:** Katman 3 — Kedihane Çoklu Ajan ve Uzmanlık Ekosistemi
> **Yerel Konum:** `.`
> **Kayıt Tarihi:** 2026-10-31 · **Commit Politikası:** `sor`

---

## 1. Mimari Belgeler ve Ortam Referansları

- **Claude Desktop Ekip Anayasası:** Detaylı ajan rolleri, teslimat, dürüstlük ve güvenlik kuralları için [`CLAUDE.md`](../../CLAUDE.md) belgesine bakın.
- **Antigravity Operasyon Anayasası:** Model yönlendirme, kota geçişi ve alt ajan köprüsü için [`GEMINI.md`](../../GEMINI.md) belgesine bakın.
- **Ajan Çalışma Kuralları ve Araçlar:** Geliştirme komutları, test araçları ve genel çalışma kuralları için [`AGENTS.md`](../../AGENTS.md) belgesine bakın.
- **Projeye Özel Hafıza:** Bu dosya yalnızca Kedihane projesine özgü mimari kararları, teknik öğrenimleri ve tuzakları tutar.

---

## 2. Proje Kararları, Öğrenimler ve Tuzaklar Kayıt Tablosu

**Kategoriler:** `mimari` · `tuzak` · `komut` · `kutuphane` · `api` · `tercih`

| Tarih | Kategori | Öğrenim / Karar / Tuzak | Bağlam / İlgili Dosya | Durum |
| :--- | :--- | :--- | :--- | :--- |
| 2026-10-31 | mimari | Kedihane `project-link` ile `antigravity_davran-sh` çok repolu sistemine bağlandı. | `REGISTRY.md`, `GEMINI.md` | aktif |
| 2026-10-31 | mimari | Çift ortam (Claude Desktop + Antigravity) için `GEMINI.md` anayasası genişletildi ve `CLAUDE.md` ile tam senkronize edildi. | `GEMINI.md`, `CLAUDE.md` | eski: GEMINI.md CLAUDE.md'ye atıf yapar |
| 2026-10-31 | mimari | Photoshop kanal ayırımı ve video/sosyal medya operasyonu araç seti doğrudan Kedihane'ye entegre edildi. Tek çatı altında çakışmasız çalışma garantilendi. | `tools/`, `bilgi/sosyal-medya-ve-video-operasyonu.md`, `GEMINI.md` | aktif |
| 2026-10-31 | kural | Müşteri gizliliği: Gerçek müşteri adları, telefon numaraları ve adresler repoya asla yazılmaz, yerel dizinde saklanır. WhatsApp link kuralı: Yalnızca `{{WHATSAPP_LINK}}` yer tutucusu kullanılır, düz numara yazılamaz. Aktif ürün ve fiyat listesi genel şablon olarak tutulur. | `bilgi/sosyal-medya-ve-video-operasyonu.md` | kural → CLAUDE.md §9 |
| 2026-10-31 | tercih | Token tasarrufu kuralı: Rehberler baştan sona okunamaz, fihristten satır aralığı belirlenip okunur. | `bilgi/*.md`, `GEMINI.md` | eski → CLAUDE.md §10 |
| 2026-10-31 | standart | Tüm ajan hafıza ve rehber dosyalarında katı alfabetik (`A-Z`) başlık düzeni zorunludur. | `bilgi/`, `MEMORY.md` | eski → CLAUDE.md §10 |
| 2026-10-31 | mimari | Self-hosted ve MCP servis rehberi (`bilgi/self-hosted-ve-mcp-servisler.md`) oluşturuldu; satır numaralı fihrist standardı uygulandı. | `bilgi/self-hosted-ve-mcp-servisler.md` | aktif (aralıklar `denetim.py --fihrist-duzelt` ile güncellenir) |
| 2026-10-31 | kural | Çıktı türü kuralı: ~10 satırı aşan kod veya ~1 sayfayı aşan raporlar sohbete basılmaz, dosya/artifact olarak teslim edilir. | `GEMINI.md` | kural → CLAUDE.md §12 |
| 2026-10-31 | tuzak | Dış repo/skill entegrasyonlarında hafızadan özetleme yapılmaz; GitHub raw kaynak dosyaları çekilip gerçek API (`Scrapling`, `OpenVoice V2`, `OpenBB v4`) ve orijinal kurallar birebir doğrulanır. | `.agents/skills/*/SKILL.md` | aktif |
| 2026-10-31 | mimari | Open-Generative-AI / Generative-Media-Skills incelendi; ücretli harici servis wrapper'ları elendi, Reasoning Brief sinematik kamera/lens ve katman-dostu prompt mimarisi Ankara ve Kaliko'ya eklendi. | `.agents/skills/medya-ve-katman/SKILL.md`, `.claude/agents/ankara.md` | aktif |
| 2026-10-31 | mimari | Kedihane 33 kaynak repo ile kıyaslanarak CLI/MCP yetkinlikleri ve araçları incelendi; gereksiz dış paketler elenip hafif, yerel çözümler korundu. | `tools/`, `.agents/skills/` | aktif |
| 2026-10-31 | mimari | Çapraz platform uyumluluğu: `fs_dither` C modülüne Windows için Python fallback eklendi (C ile çıktı eşitliği sınanmadı). | `tools/emprime/` | aktif |
| 2026-10-31 | mimari | `CLAUDE.md` ile `GEMINI.md` %100 senkronize edildi; Claude Desktop ve Antigravity ortamlarında Sarman iki aşamalı denetimi, teslimat ilkeleri (`i-have-adhd`, `no-ai-slop`, `karpathy`) ve gizlilik kuralları eşitlendi. | `CLAUDE.md`, `GEMINI.md` | eski: senkron değil, GEMINI.md CLAUDE.md'ye atıf yapar |
| 2026-10-31 | standart | Tüm ajan hafızaları (`.claude/agent-memory/`) eksiksiz 6 ajana tamamlandı, A-Z alfabetik alt başlık yapısı ve Sarman denetim kaydı eşitlendi. | `.claude/agent-memory/` | aktif |
| 2026-10-31 | kural | Çift repolu sosyal medya/işletme operasyonlarında (ör. Facebook cevapları verildiğinde) ne iş yapıldığı doğrudan ilgili işletme reposuna (`ilerleme.md`, `bekleyen-isler.md`, `yerel-kayitlar/`) kaydedilir. Kedihane kendi içine işletmeye ait kişisel/kurumsal bilgi almaz; yalnızca anonimleştirilmiş global/genel teknik öğrenimleri alabilir. | `CLAUDE.md`, `bilgi/sosyal-medya-ve-video-operasyonu.md` | kural → CLAUDE.md §14 |
| 2026-11-01 | tuzak | Video kurguda yaşanan hatalar (sabit görselde tam sayı crop kaydırma titremesi, ince dokuda PiP/sündürme, slide/wipe, dikey 4K displaymatrix, bayrak yuvası boyama) artık `tools/video/plan_render.py` ile önleniyor; ayrıntı `bilgi/video-kurgu.md` C ve D, dersler Kaliko hafızasında. | `bilgi/video-kurgu.md` | aktif |
| 2026-11-01 | mimari | Video kurgu iki modele bölündü: plan (`plan.json`) Argon, analiz/render/kontrol 3.8 Flash. Flash ffmpeg yazmaz; master kodlu kontrol kilidi ve 9 maddelik denetimden (FAIL = teslim yok) geçmeden çıkmaz. Geçişler tempoya göre (hareketli: kesme, yavaş: fade). | `tools/video/`, `bilgi/video-kurgu.md`, `GEMINI.md` | aktif |
| 2026-11-02 | mimari | Tek kaynak kuralı ve Bilgi Haritası kuruldu; yeni bilgi `bilgi/HARITA.md`'ye göre tek yere yazılır, her commit'te `tools/denetim.py` (Kontrol 7–8) çalışır. | `bilgi/HARITA.md`, `tools/denetim.py`, `.githooks/pre-commit` | aktif |
| 2026-11-02 | mimari | Minnak Tekir (haiku, hafızasız) eklendi: ajanlar hafızaya kendisi yazmaz, `Ders:` satırı verir; Minnak `bilgi/HARITA.md` Ekleme Prosedürü ile yerleştirir, Sarman fişi denetler, Stop hook unutmayı engeller. | `.claude/agents/minnak-tekir.md`, `bilgi/HARITA.md`, `.claude/hooks/minnak_kontrol.py`, `tools/denetim.py` (Kontrol 9–10) | aktif |
| 2026-11-03 | tercih | Sosyal medya yorum ve mesaj raporlamalarında 5 sütunlu tablo standardı (#, Soru Arapça, Soru Türkçe, Hazırlanan Cevap Arapça, Cevap Türkçe & Eklenti) bağlandı; {ISIM} yerine gerçek profil adının canlı yazılması ve ön onay kuralı kesinleştirildi. | `bilgi/sosyal-medya-ve-video-operasyonu.md`, `dis-isletme-reposu` | aktif |
