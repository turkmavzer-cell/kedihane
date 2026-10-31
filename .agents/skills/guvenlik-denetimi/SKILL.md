---
name: guvenlik-denetimi
description: Sarman ve Bombay için kod güvenlik denetimi (security-guidance), tehlikeli kalıp yakalama ve Strix otonom sızma testi rehberi.
---

# Kod Güvenlik Denetimi ve Otonom Pentest Rehberi

> [!IMPORTANT]
> **Kedihane Token Tasarrufu Kuralı:** Bu rehberin tamamı tek seferde okunmaz. Yapacağınız işleme göre aşağıdaki alfabetik fihristten ilgili satır aralığını tespit edip yalnızca o aralığı okuyun.

### Alfabetik Fihrist (A-Z)
| Başlık | Kapsam ve Odak | Satır Aralığı |
| :--- | :--- | :--- |
| [A. API, Kimlik Doğrulama ve Yetkilendirme](#a-api-kimlik-doğrulama-ve-yetkilendirme) | JWT/OAuth2, IDOR/BOLA denetimi, rate-limiting ve güvenli CORS politikası | L24-L71 |
| [B. Bağımlılık ve Gizli Bilgi (Secret) Güvenliği](#b-bağımlılık-ve-gizli-bilgi-secret-güvenliği) | .env izolasyonu, gitleaks/trufflehog taraması, npm/pip zafiyet analizi | L75-L106 |
| [D. Doğrulama ve Kanıt İlkesi (Verification Before Completion)](#d-doğrulama-ve-kanıt-ilkesi-verification-before-completion) | obra/superpowers Demir Yasası: Kanıt olmadan tamamlandı iddiası yasağı, 5 adımlı doğrulama kapısı | L110-L151 |
| [G. Girdi Doğrulama ve Enjeksiyon Koruması](#g-girdi-doğrulama-ve-enjeksiyon-koruması) | Parametreli SQL/NoSQL, XSS, DOM Injection, exec vs execFile, Path Traversal | L155-L210 |
| [K. Kod İçi Tehlikeli Kalıplar ve 3 Katmanlı Denetim](#k-kod-içi-tehlikeli-kalıplar-ve-3-katmanlı-denetim) | security-guidance 3 katman, 25 regex kuralı (torch, yaml, pickle, crypto, SRI, CI/CD) | L214-L235 |
| [R. Repo Paketleme ve Mimari Analiz (Repomix)](#r-repo-paketleme-ve-mimari-analiz-repomix) | yamadashy/repomix CLI kullanımı, XML/MD formatı, kod sıkıştırma (--compress) ve Secretlint | L239-L289 |
| [S. Sistematik Hata Ayıklama (Systematic Debugging) ve Strix Pentest](#s-sistematik-hata-ayıklama-systematic-debugging-ve-strix-pentest) | obra/superpowers 4 fazlı kök neden protokolü, 3 başarısız deneme sonrası duruş kuralı ve Strix pentest | L293-L357 |

---

## A. API, Kimlik Doğrulama ve Yetkilendirme

API uç noktalarında zayıf kimlik doğrulama ve yetki kontrolleri sistemin en zayıf halkasıdır. Sarman denetiminde her endpoint bu kurallarla taranır.

### 1. Yetkilendirme ve IDOR / BOLA Kontrolü
- Kullanıcıdan gelen nesne ID'lerine (`/api/orders/:id`, `/api/profile?user_id=123`) asla körü körüne güvenilmez.
- Her veri erişiminde oturum açmış kullanıcının nesne üzerindeki mülkiyeti sorgu seviyesinde doğrulanmalıdır:
  ```ts
  // GÜVENLİ: Oturum açan kullanıcının kimliği zorunlu filtredir
  const order = await db.order.findFirst({
    where: {
      id: orderId,
      userId: session.user.id // BOLA / IDOR koruması
    }
  });
  if (!order) {
    throw new NotFoundError("Kayıt bulunamadı veya yetkiniz yok.");
  }
  ```

### 2. JWT ve Oturum Güvenliği
- JWT token'ları asla `localStorage` içinde tutulmaz (XSS saldırılarına karşı açık).
- `httpOnly`, `Secure`, `SameSite=Lax` (veya katıysa `Strict`) özellikli çerezler (cookie) zorunludur.
- Token imzalama algoritmalarında `none` algoritması reddedilmeli, güçlü anahtarlar (`HMAC-SHA256` veya `RS256`) kullanılmalıdır.
- Access token ömrü kısa (maksimum 15 dakika), Refresh token ise tek kullanımlık (token rotation) ve veritabanı kontrollü olmalıdır.

### 3. Hız Sınırlama (Rate Limiting) ve Kaba Kuvvet Koruması
- Kimlik doğrulama uç noktaları (`/api/login`, `/api/register`, `/api/forgot-password`) IP ve kullanıcı adı bazlı sıkı sınırlamaya tabi tutulmalıdır (ör. 15 dakikada en fazla 5 başarısız deneme).
- Genel API uç noktalarında token bucket veya leaky bucket algoritması ile kullanıcı başına kota uygulanmalıdır.

### 4. CORS (Cross-Origin Resource Sharing) Yapılandırması
- `Access-Control-Allow-Origin: *` ve `credentials: true` kombinasyonu kesinlikle yasaktır.
- Yalnızca doğrulanmış domain listesine (whitelist) izin verilmelidir:
  ```ts
  const allowedOrigins = ['https://kedihane.app', 'https://admin.kedihane.app'];
  app.use(cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error('CORS politikası tarafından engellendi.'));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
  }));
  ```

---

## B. Bağımlılık ve Gizli Bilgi (Secret) Güvenliği

Gizli bilgilerin sızması ve savunmasız açık kaynak paketleri projenin güvenliğini tehlikeye atan en yaygın risklerdir.

### 1. `.env` ve Hassas Bilgi İzolasyonu
- Hiçbir API anahtarı, veritabanı bağlantı metni, webhook gizli dizisi veya özel anahtar kaynak koda doğrudan (hardcoded) yazılamaz.
- Tüm değişkenler `.env` dosyalarında tutulmalı ve `.env`, `.env.local`, `.env.*.local` dosyaları mutlaka `.gitignore` içinde yer almalıdır.
- Repoya yalnızca boş veya sahte değerler içeren `.env.example` commit edilebilir.

### 2. Gizli Bilgi Taraması (Pre-commit / CI Guard)
- Kod commit edilmeden önce yerel tarama araçlarıyla gizli anahtar kalıpları (`sk_live_...`, `AKIA...`, `ghp_...`, `Bearer ...`) taranmalıdır.
- Sarman onayından önce şu komut çalıştırılarak kontrol edilir:
  ```bash
  # Ripgrep ile hızlı API key ve secret avı
  rg -i "(api_key|secret_key|private_key|aws_access_key_id|bearer [a-z0-9_-]{20,})" --glob "!*.example" --glob "!node_modules/**"
  ```

### 3. Bağımlılık Zafiyet Taraması (Dependency Audit)
- Projede yeni bir paket eklenirken veya teslimat öncesi bağımlılık açıkları taranmalıdır:
  ```bash
  # Node.js projeleri için
  npm audit --audit-level=high
  # Python projeleri için
  pip install pip-audit && pip-audit
  ```
- Bilinen kritik (Critical/High) CVE içeren paketler güncellenmeden veya güvenli muadiliyle değiştirilmeden kod yayına alınamaz.

### 4. Müşteri Verisi, Sosyal Medya ve Katalog Gizlilik Protokolü
Sosyal medya otomasyonu, müşteri mesajlaşması ve video kurgu süreçleri için tekil doğruluk kaynağı `bilgi/sosyal-medya-ve-video-operasyonu.md` rehberidir. Sarman denetiminde şu 3 temel güvenlik kuralı öz olarak denetlenir:
1. **Müşteri Gizliliği:** Gerçek müşteri isimleri, telefonları ve sohbet geçmişleri repoya asla yazılmaz; yalnızca `.gitignore` altındaki yerel kasada (`yerel-kayitlar/`) tutulur.
2. **WhatsApp Bağlantı Güvenliği:** Arapça ve RTL yanıtlarda telefon numarası asla düz metin rakam olarak yazılmaz (karakter yönü bozulması ve güvenlik); yalnızca `{{WHATSAPP_LINK}}` (`https://wa.me/<ULKE_KODU_NUMARA>`) bağlantısı kullanılır.
3. **Ek Dosya Doğrulaması:** Müşteriye gönderilecek belge yalnızca onaylı güncel sürüm olmalı; eski veya onaysız sürümler paylaşılmamalıdır.

---

## D. Doğrulama ve Kanıt İlkesi (Verification Before Completion)

`obra/superpowers` standardı gereğince Kedihane ekibinde hiçbir iş kanıt olmadan tamamlanmış sayılamaz. Başarı iddiaları varsayımlarla değil, taze ve doğrulanabilir kanıtlarla desteklenmelidir.

### 1. Demir Yasa (The Iron Law)
```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
(TAZE DOĞRULAMA KANITI OLMADAN TAMAMLANMA İDDİASI KESİNLİKLE YASAKTIR)
```
Eğer geçerli mesaj veya tur içinde doğrulama komutunu bizzat çalıştırıp terminal çıktısını görmediyseniz, kodun çalıştığını veya testlerin geçtiğini kesinlikle iddia edemezsiniz.

### 2. Emprime ve Medya Kalite Doğrulaması
- **Emprime Renk Ayrımı:** `tools/emprime/kalite_kontrol.py` çalıştırılarak dE <= 12 ve kenar pürüzlülüğü <= 0.03 kanıtı makbuza eklenmeden iş teslim edilemez.
- **Video Kurgu:** 1080x1920 dikey çözünürlük, 30 fps, ses senkronu ve görev tanımındaki logo/altyazı kuralları doğrulanmalıdır.

### 3. Beş Adımlı Doğrulama Kapısı (The Gate Function)
Herhangi bir teslimat veya başarı bildiriminde bulunmadan önce sırasıyla şu 5 adım zorunludur:
1. **IDENTIFY (Tanımla):** Bu iddiayı hangi kesin komutun kanıtlayacağını belirleyin (test komutu, linter, derleme veya runtime doğrulaması).
2. **RUN (Çalıştır):** Komutun tamamını taze olarak baştan sona çalıştırın (önceki çalıştırmalara, önbelleğe veya varsayımlara güvenmeyin).
3. **READ (Oku):** Çıktının tamamını dikkatle okuyun, çıkış kodunu (`exit 0`) ve hata/uyarı sayılarını kontrol edin.
4. **VERIFY (Doğrula):** Çıktı iddiayı %100 doğruluyor mu?
   - **HAYIR:** Gerçek durumu somut hata kanıtıyla birlikte bildirin, gizlemeyin.
   - **EVET:** İddianızı terminal çıktısını veya log kanıtını iliştirerek sunun.
5. **ONLY THEN (Ancak O Zaman):** Görevin tamamlandığını veya hatanın çözüldüğünü beyan edin. Bu adımlardan herhangi birini atlamak doğrulama değil, aldatmacadır.

### 3. Kırmızı Bayraklar ve Rasyonelleştirme Yasağı (Red Flags)
Aşağıdaki durumlar tespit edildiğinde işlem DERHAL durdurulmalı ve kanıt toplanmalıdır:
- "Büyük ihtimalle düzeldi", "çalışması lazım", "görünüşe göre oldu", "tamam gibi" (`should`, `probably`, `seems to`) gibi temelsiz ifadeler kullanmak.
- Doğrulama komutu çalıştırılmadan "Harika!", "Bitti!", "Kusursuz!" gibi başarı/memnuniyet ifadeleri dile getirmek.
- Taze doğrulama yapılmadan `git commit`, `push` veya PR aşamasına geçmek.
- Alt ajanların yalnızca "başarılı" raporuna güvenip çıktıyı bizzat doğrulamamak.
- Linter geçmesini derleme/test başarısı yerine saymak (linter tip veya derleme hatasını garanti etmez).

### 4. İddia ve Kanıt Matrisi
| Beyan Edilen Durum | Zorunlu Kanıt | Yetersiz / Geçersiz Sayılan |
| :--- | :--- | :--- |
| **Testler geçiyor** | Test komutu terminal çıktısı: `0 failures`, `All passed` | Önceki test çıktısı, "kod mantıklı duruyor" demek |
| **Linter temiz** | Linter komut çıktısı: `0 errors, 0 warnings` | Kısmi dosya kontrolü, linter çalıştırmamak |
| **Build başarılı** | Derleme komutu çıkış kodu: `exit code 0` | Yalnızca linter geçmesi, logları okumadan varsaymak |
| **Bug çözüldü** | Orijinal semptomu tetikleyen testin yeniden koşulup geçmesi | Kodu değiştirip "çalışması gerekir" demek |
| **Regresyon testi hazır** | TDD Red-Green döngüsü: Test önce kasten patlatıldı, sonra geçti | Testi yalnızca düzeltme sonrası tek sefer çalıştırmak |
| **Gereksinimler karşılandı** | Görev isterleri satır satır işaretlenmiş kontrol listesi | "Testler geçiyor o halde hazırdır" varsayımı |

---

## G. Girdi Doğrulama ve Enjeksiyon Koruması

Dış dünyadan gelen her girdi zehirli kabul edilir. Doğrulama yapılmadan hiçbir veri işlenemez, kaydedilemez veya çalıştırılamaz.

### 1. SQL ve NoSQL Enjeksiyonu Koruması
- String birleştirme (concatenation) veya şablon dizgisi (`${var}`) ile sorgu oluşturmak kesinlikle yasaktır.
- Parametreli sorgular veya modern ORM/Query Builder'lar (Prisma, Drizzle, SQLAlchemy) zorunludur:
  ```ts
  // YASAK: SQL Injection açığı
  // await db.query(`SELECT * FROM users WHERE email = '${req.body.email}'`);

  // GÜVENLİ: Parametreli sorgu
  await db.query('SELECT * FROM users WHERE email = $1', [req.body.email]);
  ```
- NoSQL (MongoDB) sorgularında `$where`, `$gt` operatör enjeksiyonunu önlemek için nesne tipi doğrulayıcılar (Zod / Joi) zorunludur.

### 2. Siteler Arası Betik Çalıştırma (XSS) ve DOM Enjeksiyonu
- React/Vue içinde `dangerouslySetInnerHTML`, `v-html`, ham `innerHTML`, `outerHTML`, `insertAdjacentHTML` veya `document.write` kullanımı yasaktır.
- Zengin metin (Rich text / Markdown) gösterimi zorunluysa, içerik mutlaka `DOMPurify` veya `sanitize-html` ile sterilize edilmelidir:
  ```ts
  import DOMPurify from 'isomorphic-dompurify';

  const cleanHTML = DOMPurify.sanitize(dirtyUserInput, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'li', 'code', 'pre'],
    ALLOWED_ATTR: ['href', 'target', 'rel']
  });
  ```

### 3. Komut Enjeksiyonu (Command Injection) Koruması
- Node.js üzerinde `child_process.exec()` veya `execSync()` kullanımı kesinlikle yasaktır! `exec` alt kabuk (sh/cmd) başlattığı için parametre birleştirmelerinde komut zincirleme (`&`, `;`, `|`) saldırılarına açıktır.
- Her zaman `execFile` veya `spawn` kullanılmalı ve argümanlar bağımsız bir dizi olarak iletilmelidir:
  ```ts
  // YASAK: child_process.exec(`ffmpeg -i ${userInput} output.mp4`);

  // GÜVENLİ: child_process.execFile
  import { execFile } from 'child_process';
  execFile('ffmpeg', ['-i', validatedFilePath, 'output.mp4'], (error, stdout, stderr) => {
    // İşlem sonucu
  });
  ```
- Python tarafında `os.system` veya `subprocess.Popen(..., shell=True)` yasaktır; her zaman liste argümanları ile `subprocess.run(['ffmpeg', '-i', path, 'out.mp4'])` kullanılmalıdır.

### 4. Dizin Gezinimi (Path Traversal) Koruması
- Kullanıcıdan gelen dosya adları asla doğrudan dosya sistemi yollarına birleştirilemez (`../../etc/passwd`).
- Dosya adı `path.basename()` ile soyutlanmalı ve izin verilen güvenli dizinin dışına çıkıp çıkmadığı `path.resolve()` ile kontrol edilmelidir:
  ```ts
  import path from 'path';

  const SAFE_DIR = path.resolve('cikti');
  const safeFileName = path.basename(req.body.filename);
  const targetPath = path.resolve(SAFE_DIR, safeFileName);

  if (!targetPath.startsWith(SAFE_DIR)) {
    throw new SecurityError('Geçersiz dosya konumu!');
  }
  ```

---

## K. Kod İçi Tehlikeli Kalıplar ve 3 Katmanlı Denetim

Anthropic `security-guidance` (`anthropics/claude-plugins-official` reposundaki `plugins/security-guidance`) mimarisi temel alınarak Kedihane ekibinde 3 katmanlı güvenlik denetimi ve 25 kritik regex güvenlik kuralı uygulanır:

### 1. Üç Katmanlı Güvenlik Mimarisi
1. **Katman 1 — Desen Uyarıları (Pattern Warnings):** Kod yazımı veya düzenlemesi (`Edit`/`Write`) sırasında 25 bilinen tehlikeli kalıba karşı anlık statik regex uyarıları.
2. **Katman 2 — LLM Diff İncelemesi (Diff Review):** Model her turu bitirdiğinde oluşan git farkı (diff) otomatik taranır; yüksek önem dereceli açıklar kullanıcıya sunulmadan önce tespit edilir.
3. **Katman 3 — Ajanlı Commit İncelemesi (Agentic Review):** `git commit` aşamasında çapraz dosya veri akışı izlenerek tek dosya analizinde kaçabilecek IDOR, yetki atlatma (auth bypass) ve çapraz dosya SSRF zafiyetleri denetlenir.

### 2. Bilinen 34 Güvenlik Kuralı / 25 Kritik Kalıp ve Çözümleri
1. **GitHub Actions CI/CD Enjeksiyonu:** Workflow dosyalarında (`.github/workflows/*.yml`) asla `${{ github.event.issue.title }}`, `${{ github.event.pull_request.body }}` veya `${{ github.event.head_commit.message }}` doğrudan `run:` içine yazılamaz. Her zaman `env:` bloğuna atanıp `run: echo "$TITLE"` şeklinde tırnak içinde kullanılmalıdır. `actions/checkout` içindeki `ref:` parametrelerine gelen kullanıcı girdisi regex ile (`^[0-9]+$`) doğrulanmalıdır.
2. **PyTorch Güvensiz Model Yükleme (`torch.load`):** `torch.load()` varsayılan olarak `weights_only=False` olduğundan zararlı nesneleri deserialise ederek rastgele kod çalıştırabilir (RCE). Her zaman `weights_only=True` verilmeli veya `TORCH_FORCE_WEIGHTS_ONLY_LOAD=1` ortam değişkeni tanımlanmalıdır.
3. **Güvensiz Deserialization (Geniş Spektrum):** Python'da `pickle`, `cPickle`, `cloudpickle`, `dill`, `marshal`, `shelve`, `joblib`, `pandas.read_pickle` veya `numpy(allow_pickle=True)` ile güvenilmeyen veri yüklenemez. JSON veya şema doğrulamalı `msgspec.Struct` / `pydantic` kullanılmalıdır.
4. **PyYAML Güvensiz Yükleme:** `yaml.load()` veya `yaml.unsafe_load()` `!!python/object` etiketleri üzerinden rastgele kod çalıştırır. Her zaman `yaml.safe_load()` zorunludur.
5. **Kriptografik Zayıflıklar (IV ve Mod Hataları):**
   - Node.js `crypto.createCipher` IV (Initialization Vector) içermediğinden güvensizdir; her zaman `crypto.createCipheriv` kullanılmalıdır.
   - `aes-ecb` modu tekrarlayan bloklarda yapısal desen sızdırdığı için yasaktır; `aes-256-gcm` veya `aes-256-cbc` tercih edilmelidir.
6. **TLS Doğrulamasının Kapatılması:** `rejectUnauthorized: false` (Node.js) veya `verify=False` (Python Requests/httpx) kesinlikle yasaktır; Man-in-the-Middle (MitM) saldırılarına kapı açar.
7. **Harici Kaynak Bütünlüğü (Subresource Integrity - SRI):** Harici CDN'lerden yüklenen `<script src="...">` ve `<link rel="stylesheet">` etiketlerinde `integrity="sha384-..."` ve `crossorigin="anonymous"` öznitelikleri zorunludur.
8. **XML Varlık Genişlemesi (XXE):** XML ayrıştırıcılarında harici varlık çözme (external entity resolution) ve DTD işleme kapatılmalıdır (`defusedxml` kullanılmalıdır).
9. **Dinamik Kod Çalıştırma:** JS'te `eval()`, `new Function()`, `setTimeout("kod", ...)`; Python'da `eval()`, `exec()`, `compile()` kesinlikle yasaktır.
10. **SSRF ve Açık Yönlendirme (Open Redirect):** Dışarı yapılan HTTP isteklerinde özel IP aralıkları (`127.0.0.1`, `10.0.0.0/8`, AWS `169.254.169.254`) DNS seviyesinde filtrelenmeli; `?redirect=` parametreleri yalnızca göreli yollara izin vermelidir.

---

## R. Repo Paketleme ve Mimari Analiz (Repomix)

`yamadashy/repomix`, tüm repository kod tabanını LLM'ler ve ajanlar için AI-dostu tek bir dosyada birleştiren, token sayımı ve güvenlik filtrelemesi yapan resmi CLI aracıdır.

### 1. Temel Repomix CLI Komutları ve Formatlama
Repomix kurulmadan doğrudan `npx` ile çalıştırılabilir veya global kurulabilir:

```bash
# 1. Hızlı tek seferlik çalıştırma (Varsayılan olarak repomix-output.xml üretir)
npx repomix@latest

# 2. Global kurulum
npm install -g repomix

# 3. Özel çıktı dosya adı ve dizini belirleme
repomix -o cikti/kedihane-repo.xml

# 4. Çıktı stilini belirleme (xml, markdown veya plain)
repomix --style xml        # LLM etiket ayrıştırması için önerilen format
repomix --style markdown   # Okunabilir markdown formatı
```

### 2. Kapsam Yönetimi, Filtreleme ve Ağaç Sıkıştırma
Büyük repolarda token tasarrufu sağlamak için Repomix şu parametrelerle optimize edilir:

```bash
# Belirli dizin veya dosya kalıplarını dahil etme (Glob patterns)
repomix --include "src/**/*.ts,**/*.md"

# İlgisiz veya ağır dizinleri hariç tutma
repomix --ignore "**/*.log,tmp/**,dist/**,node_modules/**"

# Tree-sitter ile kod sıkıştırma (--compress)
# Fonksiyon/sınıf gövdelerini budayarak kodun iskeletini ve imzasını korur; token yükünü %50-70 azaltır
repomix --compress

# Dosya listesini stdin üzerinden borulama (Pipe via stdin)
git ls-files "*.ts" | repomix --stdin
rg -l "TODO|FIXME" --type ts | repomix --stdin

# Git geçmişi ve diff entegrasyonu
repomix --include-logs --include-logs-count 15 --include-diffs
```

### 3. Uzak Repo Paketleme ve Güvenlik Filtresi
- **Uzak GitHub Reposu Çekme:**
  ```bash
  repomix --remote yamadashy/repomix --remote-branch main --compress
  ```
- **Dahili Secretlint Güvenlik Taraması:**
  Repomix bünyesinde barındırdığı `secretlint` motoruyla API anahtarlarını, şifreleri ve `.env` kalıplarını otomatik olarak tespit eder ve paketlenen dosyadan çıkararak dışarıya secret sızmasını önler.

---

## S. Sistematik Hata Ayıklama (Systematic Debugging) ve Strix Pentest

Hata ayıklama süreci tahminlerle değil; `obra/superpowers` sistematik kök neden analizi ve `usestrix/strix` otonom penetrasyon testi standartlarıyla yürütülür.

### 1. Demir Yasa (The Iron Law)
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
(KÖK NEDEN ARAŞTIRILMADAN ASLA DÜZELTME YAPILAMAZ)
```
Semptomları geçici yamalarla gizlemek bir çözüm değil, başarısızlıktır. Faz 1 tamamlanmadan kod değişikliği veya çözüm önerilemez.

### 2. Dört Fazlı Hata Ayıklama Protokolü
1. **Faz 1 — Kök Neden Araştırması (Root Cause Investigation):**
   - **Hata Mesajlarını Dikkatle Oku:** Stack trace'i atlamadan tam oku; satır numaralarını, dosya yollarını ve hata kodlarını not et.
   - **Tutarlı Şekilde Yeniden Üret:** Hatayı tetikleyen adımları tam ve deterministik olarak belirle. Üretilemiyorsa tahmin yürütme; log ve telemetri topla.
   - **Son Değişiklikleri İncele:** Git diff, son commit'ler, yeni eklenen bağımlılıklar ve konfigürasyon farklarını kontrol et.
   - **Çok Bileşenli Sistemlerde Tanılama:** Sistem sınırlarına (API -> servis -> veritabanı) teşhis logları ekleyerek verinin nerede bozulduğunu somutlaştır.
   - **Veri Akışını Geriye İzle (Trace Data Flow):** Hatalı değerin ilk doğduğu kaynağa kadar geriye doğru git; semptomun çıktığı yerde değil, hatanın doğduğu kaynakta düzelt.
2. **Faz 2 — Desen Analizi (Pattern Analysis):**
   - Repoda çalışan benzer kod örneklerini bul ve referans uygulamayı satır satır incele.
   - Çalışan kod ile kırık kod arasındaki tüm farkları listele ("bundan olamaz" varsayımı yapma).
   - Çevresel ve bağımlılık varsayımlarını ortaya çıkar.
3. **Faz 3 — Hipotez ve Test (Hypothesis and Testing):**
   - Tek ve net bir hipotez kur: *"Hatanın kök nedeni X'tir çünkü Y gerçekleşmektedir."*
   - Hipotezi test etmek için en küçük cerrahi değişikliği yap (aynı anda birden fazla değişkeni değiştirme).
   - Test başarısız olursa hipotezi çöpe atıp yeni hipotez kur; yama üstüne yama ekleme.
   - Bilmediğin bir kütüphane veya davranış varsa açıkça belirt ve araştır.
4. **Faz 4 — Uygulama ve Doğrulama (Implementation):**
   - Önce hatayı gösteren başarısız bir test vakası (failing test) yaz (TDD).
   - Tespit edilen kök nedeni çözen tekil düzeltmeyi uygula (yan refactor yapma).
   - Düzeltmeyi taze test çalıştırmasıyla doğrula (Verification Before Completion).
   - **3 Başarısız Deneme Sonrası Mimari Duruş Kuralı:** Eğer uyguladığın 3 farklı düzeltme denemesi de başarısız olduysa **DERHAL DUR!** 4. düzeltme denemesine geçme. 3 başarısız deneme sorunun yerel bir bug değil, mimari/tasarımsal bir uyumsuzluk olduğunu gösterir. Durumu, mimari açmazı ve seçenekleri Cihan'a sun.

### 3. Strix ile Otonom Sızma Testi (Pentest) Akışı
Kedihane sisteminde üretilen uygulamaların canlıya çıkmadan önce otonom sızma testi aracı `Strix` (`usestrix/strix`) ile yerel olarak taranması ve bulunan açıkların kapatılması esastır.

**Kurulum:**
```bash
# Hızlı bash script ile kurulum
curl -sSL https://strix.ai/install | bash

# veya pip ile kurulum:
pip install strix-agent
```

**Zorunlu Ortam Değişkenleri:**
```bash
export STRIX_LLM="anthropic/claude-sonnet-4-5"
export LLM_API_KEY="your_api_key_here"
```

**Hedefli Tarama ve Pentest Komutları:**
```bash
# Canlı yerel web sunucusunu tarama
strix --target http://localhost:3000

# Belirli bir kaynak dizinini ve talimatı hedefleme
strix -t ./app-directory --instruction "Özellikle kimlik doğrulama, SQL enjeksiyonu ve yetkisiz veri erişimi açıklarını tara"
```

### 4. Sarman Kalite & Güvenlik Onay Süreci
1. **Rapor İncelemesi:** Strix veya statik tarama sonucu oluşan bulgular (CVSS skoru 7.0 ve üzeri olanlar) listelenir.
2. **Yalancı Pozitif (False Positive) Ayıklaması:** Sarman, bildirilen PoC'nin gerçek bir istismar mı yoksa test ortamı gürültüsü mü olduğunu doğrular.
3. **Yama ve Doğrulama:** Bombay ilgili zafiyeti yukarıdaki guardrail kurallarına göre kapatır.
4. **Tekrar Test (Regression):** Strix yalnızca ilgili uç noktada tekrar koşturulur; yeşil onay alınmadan sürüm teslim edilmez.
