# Self-Hosted ve MCP Servisler Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Servis Fihristi (A-Z)

| Servis / Araç | İlgili Ajanlar | Kategori | Satır Aralığı |
| :--- | :--- | :--- | :--- |
| **A. AgenticSeek** (`Fosowl/agenticSeek`) | Bombay & Tekir | Yerel Otonom Masaüstü Ajanı | L21-L54 |
| **C. Context7 MCP** (`upstash/context7`) | Bombay & Tekir | Dokümantasyon MCP Sunucusu | L58-L84 |
| **Ç. Coolify** (`coollabsio/coolify`) | Bombay | Self-Hosted PaaS & Sunucu Yönetimi | L88-L108 |
| **D. Documenso** (`documenso/documenso`) | Van & Bombay | Açık Kaynak Dijital İmza / Sözleşme | L112-L139 |
| **M. Magic MCP / 21st.dev** (`21st MCP`) | Bombay & Ankara | Modern UI Bileşen MCP Sunucusu | L143-L181 |
| **N. n8n** (`n8n-io/n8n`) | Bombay & Van | Görsel İş Akışı & Meta Sosyal Medya | L185-L222 |
| **O. Open-Notebook** (`lfnovo/open-notebook`) | Siyam & Kaliko | Self-Hosted NotebookLM & Podcast | L226-L256 |
| **P. Postiz** (`gitroomhq/postiz-app`) | Ankara & Van | Açık Kaynak Sosyal Medya Takvimi | L260-L299 |
| **T. Twenty CRM** (`twentyhq/twenty`) | Van & Bombay | Açık Kaynak Satış ve Müşteri CRM | L303-L332 |

---

## A. AgenticSeek (`Fosowl/agenticSeek`) — Yerel Masaüstü Ajan Alternatifi

**Sorumlu:** Bombay (Teknik entegrasyon) & Tekir (Görev delegasyonu)  
**Repo:** `https://github.com/Fosowl/agenticSeek`  
**Lisans:** `GPL-3.0`  
**Amaç:** Bilgisayarda yerel çalışan, bağımsız ve gizlilik odaklı masaüstü otomasyon ajanı.

### 1. Temel Yetenekler
- Yerel LLM'ler (Ollama, LM Studio, vLLM) veya ticari API'ler ile çalışabilir.
- Masaüstü GUI kontrolü, web tarayıcı otomasyonu ve yerel terminal komut yürütme desteği.
- Antigravity sandbox'ının dışındaki yerel masaüstü işlerinde (ör. yerel programları kontrol etme) alternatif kanal sunar.

### 2. Kurulum ve Çalıştırma
```bash
# Depoyu klonla
git clone https://github.com/Fosowl/agenticSeek.git
cd agenticSeek

# Ortam değişkenlerini hazırla
cp .env.example .env

# Docker ile arka plan servislerini (SearXNG + Redis) başlat
# Windows:
start start_services.cmd full
# Linux / macOS:
./start_services.sh full

# Uygulamayı uv veya Python ile CLI modunda çalıştır
uv run cli.py
```

### 3. Kedihane Entegrasyon Notları
- Cihan'ın yerel makinesinde API kotası tüketmeden yerel modelle uzun süreli tarama veya masaüstü görevleri yürütülürken devreye alınabilir.
- Dosya operasyonları öncesinde `GEMINI.md` Bölüm 11 gereği kaynak dosyaların kopyası alınmalıdır.

---

## C. Context7 MCP (`upstash/context7`) — Güncel Kütüphane Dokümantasyonu

**Sorumlu:** Bombay (Kodlama ve mimari) & Tekir (Model yönlendirme)  
**Repo / Paket:** `https://github.com/upstash/context7` · `@upstash/context7-mcp`  
**Amaç:** LLM'lerin kütüphane dokümantasyonlarına (Next.js 15, Tailwind v4, React 19 vb.) güncel ve optimize bağlamla erişmesini sağlamak.

### 1. Neden Gerekli?
- LLM'lerin eğitim kesim tarihlerinden sonra çıkan yeni sürümlerde (ör. Tailwind v4 CSS yönergeleri, React 19 hook'ları) halüsinasyon görmesini engeller.
- Ham dokümantasyon sayfalarını indirmek yerine doğrudan fonksiyon/API seviyesinde özetlenmiş, token tasarruflu içerik sunar.

### 2. Antigravity & Claude MCP Kurulumu
Antigravity ayarlarındaki `mcp_servers` yapılandırmasına veya `claude_desktop_config.json` dosyasına eklenir:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

### 3. Kullanım Senaryoları ve Araçlar
- **Kütüphane Kimliği Çözümleme (`resolve-library-id`):** Framework veya kütüphanenin Context7 veritabanındaki kesin ID'sini belirler. CLI alternatifi: `npx ctx7 library <paket-adi>`.
- **Hedefli Dokümantasyon Sorgulama (`query-docs`):** Yalnızca ihtiyaç duyulan API modülünü ve güncel kullanım kurallarını çeker (ör. `lucide-react`, `zod`, `drizzle-orm`). CLI alternatifi: `npx ctx7 docs <library-id> [sorgu]`.

---

## Ç. Coolify (`coollabsio/coolify`) — Self-Hosted PaaS ve Sunucu Yönetimi

**Sorumlu:** Bombay (Altyapı, dağıtım ve sunucu güvenliği)  
**Repo:** `https://github.com/coollabsio/coolify`  
**Amaç:** Hetzner, DigitalOcean veya yerel bir Linux sunucu üzerinde Heroku/Vercel benzeri tek tıkla self-hosted uygulama ve veritabanı dağıtımı.

### 1. Avantajlar ve Kedihane Rolü
- Kedihane'nin ihtiyaç duyduğu tüm yan servisler (Documenso, Twenty CRM, Open-Notebook, PostgreSQL, Redis) Coolify altında izole Docker konteynerlerinde çalışır.
- Otomatik SSL (Let's Encrypt), ters vekil sunucu (Traefik), kaynak izleme ve yedekleme yönetimi sağlar.

### 2. Sunucuya Kurulum (Tek Komut)
```bash
# Ubuntu/Debian 22.04+ sunucuda root yetkisiyle:
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```
Kurulum tamamlandıktan sonra web paneline `http://<sunucu-ip>:8000` üzerinden erişilir.

### 3. Bombay Dağıtım Standartları
- Tüm veritabanlarında günlük otomatik yedekleme aktif edilir.
- Uygulamalar GitHub webhook'ları ile `main` branch'ine push yapıldığında otomatik güncellenir.
- Canlı sunucuya erişim şifreleri repoya asla yazılmaz, `.env` içerisinde saklanır.

---

## D. Documenso (`documenso/documenso`) — Açık Kaynak Belge ve Sözleşme İmzalama

**Sorumlu:** Van (Sözleşme ve süreç yönetimi) & Bombay (API entegrasyonu)  
**Repo:** `https://github.com/documenso/documenso`  
**Lisans:** `AGPLv3`  
**Amaç:** DocuSign alternatifi, self-hosted, yasal geçerliliğe uygun dijital imza ve doküman onay platformu.

### 1. Kedihane Kullanım Senaryosu
- Van'ın hazırladığı müşteri sözleşmeleri, teklif formları, serbest çalışan anlaşmaları ve gizlilik sözleşmelerinin (NDA) güvenli imzalatılması.
- Üçüncü taraf bulut servislerine müşteri ve fiyat verisi göndermeden yerel sunucuda imza süreçlerini tamamlamak.

### 2. Docker ile Dağıtım (Coolify veya Doğrudan Docker)
Documenso çalışmak için mutlaka bir PostgreSQL veritabanına ihtiyaç duyar; veritabanı değişkeni olmadan tek başına konteyner çöküşe geçer. Coolify üzerindeki resmi PostgreSQL şablonuyla bağlanabilir veya şu parametrelerle başlatılır:

```bash
# PostgreSQL bağlantısı ve zorunlu secret ile çalıştırma
docker run -d \
  --name documenso \
  -p 3000:3000 \
  -e NEXTAUTH_URL="http://localhost:3000" \
  -e NEXTAUTH_SECRET="en_az_32_karakterli_gizli_anahtar" \
  -e DATABASE_URL="postgresql://kullanici:sifre@postgres:5432/documenso?schema=public" \
  documenso/documenso:latest
```

### 3. API ve Webhook Özellikleri
- REST API üzerinden şablon bazlı otomatik belge oluşturma.
- Belge imzalandığında tetiklenen webhook'lar sayesinde Twenty CRM veya bildirim botlarına otomatik durum güncellemesi iletme.

---

## M. Magic MCP / 21st.dev (`21st MCP`) — Modern UI Bileşen Sunucusu

**Sorumlu:** Bombay (Bileşen montajı) & Ankara (Tasarım yönü ve estetik)  
**Resmi Paket / Servis:** `21st MCP` (Eski `@21st-dev/magic-mcp` paketi kullanımdan kaldırılmıştır)  
**Platform:** `https://21st.dev`  
**Amaç:** 21st.dev topluluğundaki modern, animasyonlu, shadcn/ui ve Tailwind tabanlı bileşenleri AI modellerine MCP aracılığıyla doğrudan sunmak.

### 1. Neden Kullanıyoruz?
- `no-ai-slop` ve `frontend-ve-ui` standartlarını sağlamak için hazır, yüksek kaliteli UI kalıpları sunar.
- Ajanların sıfırdan jenerik CSS yazması yerine rafine mikro etkileşimler, bento gridler ve modern buton/kart tasarımları üretmesini sağlar.

### 2. Antigravity & Claude MCP Kurulumu

**Hızlı CLI Başlatma:**
```bash
npx @21st-dev/cli@latest init
```

**Resmi HTTP MCP Sunucusu (Önerilen):**
Antigravity veya Claude Desktop MCP ayarlarına HTTP SSE/stream olarak eklenir:
- URL: `https://21st.dev/api/mcp`
- Başlık (Header): `x-api-key: <API_KEY_21ST>` (Ortam değişkeni: `API_KEY_21ST`)

**Stdio Alternatifi (Yerel npx Çalıştırma):**
```json
{
  "mcpServers": {
    "21st": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest", "API_KEY=your_api_key_here"]
    }
  }
}
```

### 3. İş Akışı
1. Ankara arayüzün tasarım dilini ve bileşen türünü (ör. Hero section, animasyonlu modal) belirler.
2. Bombay 21st MCP araçlarıyla ilgili bileşenin temiz TSX/Tailwind kodunu ve Lucide/Framer-Motion bağımlılıklarını çeker.
3. Projeye gereksiz ek kütüphane eklemeden bileşen projeye entegre edilir.

---

## N. n8n (`n8n-io/n8n`) — Görsel İş Akışı ve Sosyal Medya Otomasyon Motoru (Bombay & Van)

**Sorumlu:** Bombay (Entegrasyon, webhook ve kod node'ları) & Van (İş akışları ve süreç otomasyonu)  
**Repo:** `https://github.com/n8n-io/n8n`  
**Lisans:** `Fair-code (Sustainable Use License)`  
**Amaç:** Açık kaynaklı, görsel tuvalde (canvas) çalışan, 1500+ servis entegrasyonu ve yerel yapay zekâ ajanı desteği sunan gelişmiş iş akışı ve sosyal medya otomasyon motoru.

### 1. Öne Çıkan Yetenekler
- **AI Agent Düğümleri:** LangChain tabanlı otonom ajanlar, hafıza (memory) ve araç (tool) düğümleri ile akıllı yanıt akışları.
- **Webhook ve Event-Driven Tetikleyiciler:** Meta Graph API, Telegram, WhatsApp, Stripe ve yerel veritabanı olaylarına anında tepki verme.
- **Python / JavaScript Desteği:** Görsel düğümlerin yetersiz kaldığı noktalarda özel veri dönüşümleri ve regex filtreleme.

### 2. Docker ile Hızlı Kurulum
```bash
# Veri birimi oluştur
docker volume create n8n_data

# n8n konteynerini çalıştır
docker run -d \
  --name n8n \
  --restart always \
  -p 5678:5678 \
  -e N8N_SECURE_COOKIE=false \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```
*Arayüz erişimi:* `http://localhost:5678` (veya Coolify üzerinden ters proxy / SSL ile alan adına bağlama).

### 3. Meta Graph API (Facebook & Instagram) ve Kurumsal Sosyal Medya Otomasyon Mimarisi
Kedihane ekibinin kurumsal ve sosyal medya sayfalarında otomatik içerik yayını ve etkileşim döngüsü:
1. **İçerik Zamanlama & Tetikleme:** Google Sheets / Airtable / Supabase veya CRON düğümü ile tetiklenen içerik akışı.
2. **Meta Graph API Düğümü (Facebook Sayfası & Instagram Business):**
   - *Facebook Post Yayını:* `POST /v21.0/{page-id}/feed` (mesaj, bağlantı ve Kaliko'nun hazırladığı görsel/video).
   - *Instagram Medya Yayını:* İki adımlı container akışı (`POST /v21.0/{ig-user-id}/media` -> `POST /v21.0/{ig-user-id}/media_publish`).
3. **Webhook ile Gelen Yorum / DM Otomasyonu:**
   - Sayfaya yeni bir yorum veya mesaj geldiğinde Meta Webhook n8n'e JSON yükü fırlatır.
   - n8n içindeki AI Ajan düğümü (Ankara prompt yönergeleriyle) bağlamı analiz eder; spam/küfür filtrelemesi yapar.
   - Önceden tanımlı onaylı yanıt veya otomatik müşteri bilgilendirmesi Meta Graph API (`POST /{comment-id}/comments` veya mesaj API) ile 15 saniye içinde iletilir.

---

## O. Open-Notebook (`lfnovo/open-notebook`) — Self-Hosted NotebookLM ve Podcast Üretimi

**Sorumlu:** Siyam (Bilgi sentezi ve araştırma havuzu) & Kaliko (Medya / Podcast çıktısı)  
**Repo:** `https://github.com/lfnovo/open-notebook`  
**Amaç:** Google NotebookLM'in açık kaynaklı, verilerin kendi sunucumuzda kaldığı yerel alternatifi. Çoklu kaynak analizi ve iki sesli podcast üretimi.

### 1. Öne Çıkan Yetenekler
- PDF, DOCX, web sayfaları, YouTube transkriptleri ve ses dosyalarını RAG havuzuna ekleme.
- Ollama veya ticari LLM API'leri (Gemini 1.5/2.0, Claude 3.5) ile kaynaklara dayalı soru-cevap.
- Metin kaynaklarından otomatik iki sesli (host & co-host) podcast senaryosu ve TTS ile ses üretimi.

### 2. Dağıtım (Docker Compose) ve Ortam Değişkenleri
`OPEN_NOTEBOOK_ENCRYPTION_KEY` ortam değişkeni verilerin ve API anahtarlarının şifrelenmesi için zorunludur; tanımlanmazsa servis ayağa kalkmaz.
- **Web UI Portu:** `8502` (`http://localhost:8502`)
- **API Portu:** `5055` (`http://localhost:5055`)

```bash
git clone https://github.com/lfnovo/open-notebook.git
cd open-notebook

# Ortam değişkenlerini düzenle (.env)
cp .env.example .env
# OPEN_NOTEBOOK_ENCRYPTION_KEY="..." (openssl rand -hex 32 ile üretilir)

# Başlat
docker compose up -d
```

### 3. Kedihane Görev Dağılımı
- **Siyam:** Araştırma verilerini ve akademik PDF'leri yükler, çelişkili bilgileri ayıklar ve kaynak doğrulaması yapar.
- **Kaliko:** Çıkan sesli özetleri (Audio Overview) kontrol eder, LUFS seviyesini dengeler ve gerekirse arka plan müziği ekler.

---

## P. Postiz (`gitroomhq/postiz-app`) — Açık Kaynak Sosyal Medya Takvim ve Paylaşım Platformu (Ankara & Van)

**Sorumlu:** Ankara (İçerik takvimi, metin ve yaratıcı planlama) & Van (Yayın programı ve çoklu kanal yönetimi)  
**Repo:** `https://github.com/gitroomhq/postiz-app`  
**Lisans:** `AGPLv3`  
**Amaç:** Buffer ve Hootsuite alternatifi, tamamen açık kaynaklı (AGPLv3), tek merkezden çoklu sosyal platform (Facebook, Instagram, TikTok, X, LinkedIn, YouTube, Pinterest, Reddit vb.) zamanlama ve paylaşım platformu.

### 1. Öne Çıkan Yetenekler
- **Görsel Takvim & Çoklu Kanal:** Haftalık ve aylık içerik takvimi; tek tıkla aynı görseli ve uyarlanmış metni tüm kanallara senkronize dağıtma.
- **Ajanik Yüzeyler (Agentic Surfaces & MCP):** Claude, Antigravity ve yerel ajanlar için dahili MCP ve REST API uç noktaları.
- **Ekip ve Müşteri Grupları:** Sınırsız kanal ve kullanıcı desteği; gönderi taslakları için yönetici onay akışı.

### 2. Docker Compose ile Dağıtım
```bash
# Depoyu klonla veya docker-compose.yaml indir
git clone https://github.com/gitroomhq/postiz-app.git
cd postiz-app

# Ortam değişkenlerini düzenle (.env)
cp .env.example .env
# JWT_SECRET, DATABASE_URL ve REDIS_URL alanlarını belirleyin

# Başlat
docker compose up -d
```
*Varsayılan arayüz:* `http://localhost:4007`

### 3. REST API ile Ajanlardan Otomatik Paylaşım
Kedihane ajanları (Tekir'in onayıyla) üretilen gönderiyi doğrudan Postiz API'sine iletebilir:
```bash
curl -X POST "http://localhost:4007/api/posts" \
  -H "Authorization: Bearer YOUR_POSTIZ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Yeni dönem kurumsal tasarımları yayında!",
    "platforms": ["facebook", "instagram"],
    "scheduledAt": "2026-11-01T14:00:00Z",
    "media": ["https://sunucu.adresi/uploads/post_1.png"]
  }'
```

---

## T. Twenty CRM (`twentyhq/twenty`) — Açık Kaynak Müşteri ve Satış Yönetimi

**Sorumlu:** Van (Müşteri ilişkileri, bütçe ve pipeline) & Bombay (Veritabanı ve API)  
**Repo:** `https://github.com/twentyhq/twenty`  
**Lisans:** `AGPLv3 + Commercial`  
**Amaç:** Modern, açık kaynaklı, GraphQL ve REST API destekli CRM platformu.

### 1. Van İçin Yönetim Alanları
- Müşteri adayları (Leads), aktif anlaşmalar (Deals) ve satış hunisi takibi.
- Müşteri iletişim geçmişi, notlar ve görev takibi.
- Fiyat tekliflerinin durumu ve tahsilat takvimleri.

### 2. Coolify / Docker Compose ile Dağıtım
Twenty CRM'i başlatmadan önce `.env` dosyası hazırlanmalı; özellikle oturum ve şifreleme için `APP_SECRET` ile PostgreSQL veritabanı bağlantısı için `PG_DATABASE_URL` (veya `DATABASE_URL`) değişkenleri tanımlanmalıdır.

```bash
# Docker Compose dosyasını indir
curl -fsSL https://raw.githubusercontent.com/twentyhq/twenty/main/packages/twenty-docker/docker-compose.yml -o docker-compose.yml

# .env yapılandırması
# APP_SECRET="en_az_32_karakterli_gizli_anahtar"
# PG_DATABASE_URL="postgres://twenty:twenty@postgres:5432/twenty"

# Konteynerleri ayağa kaldır
docker compose up -d
```

### 3. Bombay Otomasyon Köprüsü
- Webhook desteği ile yeni müşteri kaydında Tekir ve Van'a otomatik bilgilendirme.
- Documenso ile entegrasyon: Sözleşme imzalandığında CRM anlaşma durumunun otomatik olarak "Kazanıldı (Closed Won)" yapılması.
