# Projeye Özel Öğrenimler ve Mimari Hafıza (`PROJECT.md`)

> **Kapsam:** Kedihane Çoklu Ajan ve Uzmanlık Ekosistemi
> **Yerel Konum:** `.`
> **Kayıt Tarihi:** 2026-10-31 · **Commit Onayı:** Cihan onayıyla

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
| 2026-10-31 | mimari | Kedihane `project-link` ile `antigravity_davran-sh` çok repolu sistemine bağlandı. | `REGISTRY.md`, `GEMINI.md` | değiştirildi |
| 2026-10-31 | mimari | Self-hosted ve MCP servis rehberi (`bilgi/self-hosted-ve-mcp-servisler.md`) oluşturuldu; satır numaralı fihrist standardı uygulandı. | `bilgi/self-hosted-ve-mcp-servisler.md` | aktif (aralıklar `denetim.py --fihrist-duzelt` ile güncellenir) |
| 2026-10-31 | tuzak | Dış repo/skill entegrasyonlarında hafızadan özetleme yapılmaz; GitHub raw kaynak dosyaları çekilip gerçek API (`Scrapling`, `OpenVoice V2`, `OpenBB v4`) ve orijinal kurallar birebir doğrulanır. | `.agents/skills/*/SKILL.md` | aktif |
| 2026-10-31 | mimari | Open-Generative-AI / Generative-Media-Skills incelendi; ücretli harici servis wrapper'ları elendi, Reasoning Brief sinematik kamera/lens ve katman-dostu prompt mimarisi Ankara ve Kaliko'ya eklendi. | `.agents/skills/medya-ve-katman/SKILL.md`, `.claude/agents/ankara.md` | aktif |
| 2026-10-31 | mimari | Kedihane 33 kaynak repo ile kıyaslanarak CLI/MCP yetkinlikleri ve araçları incelendi; gereksiz dış paketler elenip hafif, yerel çözümler korundu. | `tools/`, `.agents/skills/` | aktif |
| 2026-10-31 | standart | Tüm ajan hafızaları (`.claude/agent-memory/`) eksiksiz 6 ajana tamamlandı, A-Z alfabetik alt başlık yapısı ve Sarman denetim kaydı eşitlendi. | `.claude/agent-memory/` | aktif |
| 2026-11-01 | tuzak | Video kurguda yaşanan hatalar (sabit görselde tam sayı crop kaydırma titremesi, ince dokuda PiP/sündürme, slide/wipe, dikey 4K displaymatrix, bayrak yuvası boyama) artık `tools/video/plan_render.py` ile önleniyor; ayrıntı `bilgi/video-kurgu.md` C ve D, dersler Kaliko hafızasında. | `bilgi/video-kurgu.md` | aktif |
| 2026-11-01 | mimari | Video kurgu iki modele bölündü: plan (`plan.json`) Argon, analiz/render/kontrol 3.8 Flash. Flash ffmpeg yazmaz; master kodlu kontrol kilidi ve 9 maddelik denetimden (FAIL = teslim yok) geçmeden çıkmaz. Geçişler tempoya göre (hareketli: kesme, yavaş: fade). | `tools/video/`, `bilgi/video-kurgu.md`, `GEMINI.md` | aktif |
| 2026-11-02 | mimari | Tek kaynak kuralı ve Bilgi Haritası kuruldu; yeni bilgi `bilgi/HARITA.md`'ye göre tek yere yazılır, her commit'te `tools/denetim.py` (Kontrol 7–8) çalışır. | `bilgi/HARITA.md`, `tools/denetim.py`, `.githooks/pre-commit` | aktif |
| 2026-11-02 | mimari | Minnak Tekir (haiku, hafızasız) eklendi: ajanlar hafızaya kendisi yazmaz, `Ders:` satırı verir; Minnak `bilgi/HARITA.md` Ekleme Prosedürü ile yerleştirir, Sarman fişi denetler, Stop hook unutmayı engeller. | `.claude/agents/minnak-tekir.md`, `bilgi/HARITA.md`, `.claude/hooks/minnak_kontrol.py`, `tools/denetim.py` (Kontrol 9–10) | aktif |
| 2026-11-07 | mimari | Toplu sosyal medya yorum/mesajlarında "Paralel Beyin, Sıralı Parmak" mimarisi bağlandı: 5 sütunlu cevap tablosu geçici paralel kopya ajanlarla (Flash, iz bırakmadan silinen) hazırlanır; gönderim ise sekme çakışması ve Meta anti-bot kilidini önlemek için tek sekmede sıralı (3-5 sn jitter) yapılır. | `bilgi/sosyal-medya-ve-video-operasyonu.md` | aktif |
| 2026-11-15 | mimari | Emprime/katman araçları ve rehberleri `PS-Desemp` (eski adı: `PS-Kanal-Ayirimi`) reposuna, tekstil/sim promptları ve Meta DOM detayları harici sosyal medya işletme reposuna (`dis-isletme-reposu`) ayrıştırıldı; Kedihane'de yalnız genel/global çoklu ajan mimarisi, metodolojiler ve ortak çekirdek araçlar (`tools/denetim.py`, `tools/video/`, `tools/psd_worker/`, `tools/webapp_testing/`) bırakıldı. | `bilgi/HARITA.md`, `AGENTS.md`, `GEMINI.md` | aktif |
| 2026-11-19 | tuzak | 3D kumaş kıvrımı üzerindeki el çizimi/fırça yazı ve kutular fotoğraftan piksel/maske olarak çıkarılıp 1D dikey kaydırmayla düzeltilemez (yatay sıkışma ve dalgalanma kalır); Sarman kontrol listesine (`bilgi/gorsel-duzeltme.md` §C) yatay sıkışma/dalgalı çerçeve FAIL kuralı eklendi, `PS-Desemp` Modül C4 ile sıfırdan geometrik kurulum zorunlu kılındı. | `bilgi/gorsel-duzeltme.md` | aktif |
| 2026-11-16 | mimari | `antigravity_davran-sh` v2.1.0 entegrasyonu güncellendi: `Gemini 4 Hydrogen` uygulama/test modeli eklendi ve karmaşık işlerde iki aşamalı `Argon (plan) → Hydrogen (uygulama)` devir protokolü `AGENTS.md`, `GEMINI.md` ve `CLAUDE.md`'ye işlendi. | `AGENTS.md`, `GEMINI.md`, `CLAUDE.md` | değiştirildi |
| 2026-11-17 | mimari | `antigravity_davran-sh` bağlantısı projeden kaldırıldı; `antigravity_manual` çok repolu sistemine geçildi. | `AGENTS.md`, `GEMINI.md`, `CLAUDE.md` | kaldırıldı |
| 2026-11-19 | mimari | `antigravity_manual` bağlantısı ve iki aşamalı manuel Argon→Hydrogen geçiş kuralı projeden kaldırıldı; Kedihane kendi anayasasıyla bağımsız çalışır. | `AGENTS.md`, `GEMINI.md`, `.agents/learnings/PROJECT.md` | aktif |
| 2026-11-21 | mimari | Antigravity ortamında tüm tekil araç/beceriler tam otomatik (Tekir Otopilot), kota yüzdesi okunamadığından `swarm` (ve çoklu ajanlı `run_workflow`) tek satır onay + model havuzu seçimiyle (Kota Kalkanı) ve 8 arayüz komutu eşikli tek satır öneriyle `GEMINI.md` §5'e bağlandı; `Gemini 4 Neon` §2 model tablosuna eklendi. | `GEMINI.md` | aktif |
