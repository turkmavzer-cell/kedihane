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
| 2026-10-31 | mimari | Çift ortam (Claude Desktop + Antigravity) için `GEMINI.md` anayasası genişletildi ve `CLAUDE.md` ile tam senkronize edildi. | `GEMINI.md`, `CLAUDE.md` | aktif |
| 2026-10-31 | mimari | Photoshop kanal ayırımı ve video/sosyal medya operasyonu araç seti doğrudan Kedihane'ye entegre edildi. Tek çatı altında çakışmasız çalışma garantilendi. | `tools/`, `bilgi/sosyal-medya-ve-video-operasyonu.md`, `GEMINI.md` | aktif |
| 2026-10-31 | kural | Müşteri gizliliği: Gerçek müşteri adları, telefon numaraları ve adresler repoya asla yazılmaz, yerel dizinde saklanır. WhatsApp link kuralı: Yalnızca `{{WHATSAPP_LINK}}` yer tutucusu kullanılır, düz numara yazılamaz. Aktif ürün ve fiyat listesi genel şablon olarak tutulur. | `bilgi/sosyal-medya-ve-video-operasyonu.md` | aktif |
| 2026-10-31 | tercih | Token tasarrufu kuralı: Rehberler baştan sona okunamaz, fihristten satır aralığı belirlenip okunur. | `bilgi/*.md`, `GEMINI.md` | aktif |
| 2026-10-31 | standart | Tüm ajan hafıza ve rehber dosyalarında katı alfabetik (`A-Z`) başlık düzeni zorunludur. | `bilgi/`, `MEMORY.md` | aktif |
| 2026-10-31 | mimari | Self-hosted ve MCP servis rehberi (`bilgi/self-hosted-ve-mcp-servisler.md`) oluşturuldu; satır numaralı fihrist standardı uygulandı. | `bilgi/self-hosted-ve-mcp-servisler.md` | aktif |
| 2026-10-31 | kural | Çıktı türü kuralı: ~10 satırı aşan kod veya ~1 sayfayı aşan raporlar sohbete basılmaz, dosya/artifact olarak teslim edilir. | `GEMINI.md` | aktif |
| 2026-10-31 | tuzak | Dış repo/skill entegrasyonlarında hafızadan özetleme yapılmaz; GitHub raw kaynak dosyaları çekilip gerçek API (`Scrapling`, `OpenVoice V2`, `OpenBB v4`) ve orijinal kurallar birebir doğrulanır. | `.agents/skills/*/SKILL.md` | aktif |
| 2026-10-31 | mimari | Open-Generative-AI / Generative-Media-Skills incelendi; ücretli harici servis wrapper'ları elendi, Reasoning Brief sinematik kamera/lens ve katman-dostu prompt mimarisi Ankara ve Kaliko'ya eklendi. | `.agents/skills/medya-ve-katman/SKILL.md`, `.claude/agents/ankara.md` | aktif |
| 2026-10-31 | mimari | Kedihane 33 kaynak repo ile kıyaslanarak CLI/MCP yetkinlikleri ve araçları incelendi; gereksiz dış paketler elenip hafif, yerel çözümler korundu. | `tools/`, `.agents/skills/` | aktif |
| 2026-10-31 | mimari | Çapraz platform uyumluluğu: `fs_dither` C modülüne Windows için Python fallback eklendi (C ile çıktı eşitliği sınanmadı). | `tools/emprime/` | aktif |
| 2026-10-31 | mimari | `CLAUDE.md` ile `GEMINI.md` %100 senkronize edildi; Claude Desktop ve Antigravity ortamlarında Sarman iki aşamalı denetimi, teslimat ilkeleri (`i-have-adhd`, `no-ai-slop`, `karpathy`) ve gizlilik kuralları eşitlendi. | `CLAUDE.md`, `GEMINI.md` | aktif |
| 2026-10-31 | standart | Tüm ajan hafızaları (`.claude/agent-memory/`) eksiksiz 6 ajana tamamlandı, A-Z alfabetik alt başlık yapısı ve Sarman denetim kaydı eşitlendi. | `.claude/agent-memory/` | aktif |
| 2026-10-31 | kural | Çift repolu sosyal medya/işletme operasyonlarında (ör. Facebook cevapları verildiğinde) ne iş yapıldığı doğrudan ilgili işletme reposuna (`ilerleme.md`, `bekleyen-isler.md`, `yerel-kayitlar/`) kaydedilir. Kedihane kendi içine işletmeye ait kişisel/kurumsal bilgi almaz; yalnızca anonimleştirilmiş global/genel teknik öğrenimleri alabilir. | `CLAUDE.md`, `bilgi/sosyal-medya-ve-video-operasyonu.md` | aktif |
| 2026-10-31 | mimari | Siyah zeminli grafik/streetwear tişört desenleri için renk kümelemeli ve kenar yumuşatmalı (color-to-alpha knockout) çok katmanlı PSD üretim aracı (`tools/katman/for_enddo_psd_olustur.py`) geliştirildi. | `tools/katman/`, `GEMINI.md` | aktif |
| 2026-11-01 | tuzak | FFmpeg'de sabit görsellere `crop=w:h:'x0+dx*(t/dur)'` ile pan/zoom vermek tam-sayı piksel yuvarlaması nedeniyle `1 piksellik` sıçrama (takılma/göz yorma) yaratır; ayrıca `3:4` taş/sim detaylı görsellerde küçük PiP veya sündürme detayları yok eder. Görseller `1:1` oranlı tam ekran (`9:16` kırpım + `UnsharpMask`) ve `%100 sabit` tutulmalı, geçişlerde sert `slide`/`wipe` yerine `0.40 sn` yumuşak `xfade=transition=fade` kullanılmalıdır. | `.claude/agent-memory/kaliko/MEMORY.md` | aktif |
| 2026-11-01 | tuzak | Dikey `4K` telefon videolarında (`displaymatrix: rotation of -90.00 degrees`) `-noautorotate` kullanılmaz; `filter_complex` sonrası ara MP4 segmentlerine kopyalanabilen `displaymatrix` yan verisi `xfade` öncesinde `ffmpeg -display_rotation 0 -i seg.mp4 -c copy` ile sıfırlanır. Çoklu `-loop 1` PNG katmanları ise Pillow `alpha_composite` ile birleştirilir. | `.claude/agent-memory/kaliko/MEMORY.md` | aktif |
