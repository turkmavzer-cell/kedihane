# Kedihane — Antigravity & Ajan Çalışma Kuralları (`AGENTS.md`)

> Bu repo `antigravity_davran-sh` v2.0.0 çok repolu çalışma sistemine bağlıdır.
> Projeye özel mimari kararlar ve öğrenimler `.agents/learnings/PROJECT.md` dosyasında tutulur.
> **Detaylı Ortam Belgeleri:**
> - Antigravity ortamında operasyon anayasası: [`GEMINI.md`](GEMINI.md)
> - Claude Desktop ortamında ekip kuralları: [`CLAUDE.md`](CLAUDE.md)

---

## 1. Proje Amacı ve Özeti
- **Proje Adı:** kedihane
- **Amaç:** Cihan'ın 7 ajanlı çoklu yapay zekâ uzmanlık ekosistemi (Tekir şefliğinde Bombay, Sarman, Siyam, Ankara, Kaliko, Van).
- **Teknoloji Yığını:** Python (psd-tools, numpy, PIL), Shell/PowerShell, Markdown, Multi-Agent Mimarisi, Antigravity Customizations (Skills, Rules, MCP).

## 2. Geliştirme, Test ve Araç Komutları
- **Emprime & Serigrafi Renk Ayrımı:** `python tools/emprime/bolge_am.py` (AM tram 45 LPI, 508 PPI), `tools/emprime/tramsiz.py` (düz spot), `tools/emprime/kalite_kontrol.py`
- **Photoshop Multichannel PSD Otomasyonu:** `tools/photoshop/psd_olustur_tek_adim.jsx` (ExtendScript)
- **PSD Katman Ayırma Araçları:** `tools/psd_worker/` (Node.js) ve `tools/katman/` (Python)
- **Web App Test & Doğrulama:** `python tools/webapp_testing/with_server.py` (arka plan test sunucusu)
- **Repo Kalite ve Gizlilik Denetimi:** `python tools/denetim.py` (Sarman denetim ve ihlal tarama betiği)
- **Bağımlılık ve Paket Yönetimi:** `requirements.txt` (`pip install -r requirements.txt`)
- **Video Kurgu:** `python tools/video/analiz.py <kaynak_klasor> --muzik <m>`, `python tools/video/plan_render.py _calisma/plan.json --dogrula|--onizleme|--master` (kilit, 9 maddelik denetim, Premiere XML; akış: `bilgi/video-kurgu.md`)
- **Sosyal Medya ve Video Operasyonu:** `bilgi/sosyal-medya-ve-video-operasyonu.md`, `bilgi/tekstil-ve-sim-gorsel-promptlari.md`
- **Rehber ve Bilgi Dosyaları:** `bilgi/` altında indeksli dokümanlar
- **Antigravity Çekirdek Becerileri:** `.agents/skills/` altında 5 uzmanlık paketi

## 3. Mimari Standartlar ve Kurallar
- **Token Tasarrufu:** Rehberlerin ve hafıza dosyalarının tamamı asla baştan sona okunmaz; fihristten satır aralığı belirlenerek (`read_file`) okunur.
- **Katı Alfabetik Düzen (`A-Z`):** Tüm rehberler, hafızalar ve skill dokümanlarında başlıklar alfabetik sıra ile düzenlenir.
- **Sarman Kalite Denetimi:** Her kod, dosya ve kritik çıktıda `📋 Sarman Denetim Makbuzu` zorunludur.
- **Güvenlik ve Veri Gizliliği:** `.env`, API anahtarı, şifre ve kişisel veriler asla repoya yazılmaz; kaynak dosyalar korunur.

## 4. Projeye Özel Hafıza ve Öğrenme Kuralı (Katman 3)
1. Görev başında `.agents/learnings/PROJECT.md` dosyasını kontrol et ve oradaki mimari kararlara/tuzaklara dikkat et.
2. Bu projeye özgü yeni bir bilgi keşfettiğinde veya kullanıcı projeye özel bir düzeltme yaptığında:
   - Bunu core repoya değil, bu projedeki `.agents/learnings/PROJECT.md` tablosuna tarihli olarak ekle.
3. **Commit Politikası (`sor`):**
   - `.agents/learnings/PROJECT.md` dosyasını güncelledikten sonra ayrı bir `docs(learnings): ...` commit'i hazırlamayı teklif et; **kullanıcı onaylamadan bu proje reposunda commit/push yapma**.
