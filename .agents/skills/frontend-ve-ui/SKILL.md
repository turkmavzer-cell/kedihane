---
name: frontend-ve-ui
description: Bombay ve Ankara için özgün arayüz tasarımı (frontend-design), yapay zeka klişelerini önleme ve 21st.dev modern UI bileşen entegrasyon rehberi.
---

# Frontend ve Özgün UI Tasarım Rehberi

> [!IMPORTANT]
> **Kedihane Token Tasarrufu Kuralı:** Bu rehberin tamamı tek seferde okunmaz. Yapacağınız işleme göre aşağıdaki alfabetik fihristten ilgili satır aralığını tespit edip yalnızca o aralığı okuyun.

### Alfabetik Fihrist (A-Z)
| Başlık | Kapsam ve Odak | Satır Aralığı |
| :--- | :--- | :--- |
| [A. Antigravity & 21st.dev Bileşen İş Akışı](#a-antigravity--21stdev-bileşen-iş-akışı) | 21st.dev, shadcn/ui, Magic UI, Aceternity entegrasyon ve modülerlik kuralları | L24-L85 |
| [B. Boşluk, Grid ve Görsel Hiyerarşi](#b-boşluk-grid-ve-görsel-hiyerarşi) | Asimetrik denge, negatif alan, bento grid, z-index ölçeği ve responsive kırılımlar | L89-L133 |
| [K. Klişe Yasağı (Anti-AI Slop UI)](#k-klişe-yasağı-anti-ai-slop-ui) | Anthropic frontend-design 5 AI klişe kümesi, mor gradyan ve tipografik tell yasakları | L137-L153 |
| [M. Mikro Etkileşimler ve MCP Sunucu Geliştirme (MCP Builder)](#m-mikro-etkileşimler-ve-mcp-sunucu-geliştirme-mcp-builder) | Animasyon easing/timing, prefers-reduced-motion ve Anthropic mcp-builder 4 fazlı protokol | L157-L213 |
| [R. Renk, Kontrast ve Tema Sistemi](#r-renk-kontrast-ve-tema-sistemi) | 60-30-10 kuralı, CSS değişkenleri/tokens, WCAG AA/AAA ve gerçek koyu tema | L217-L265 |
| [T. Tipografi, İki Aşamalı Süreç (2-Pass) ve Tasarımda Metin](#t-tipografi-iki-aşamalı-süreç-2-pass-ve-tasarımda-metin) | 2-Pass tasarım planı, ASCII wireframe, akıcı tipografi ve arayüz içi metin kuralları | L269-L292 |
| [W. Web Uygulaması Testi ve Doğrulama (Playwright & Webapp-Testing)](#w-web-uygulaması-testi-ve-doğrulama-playwright--webapp-testing) | Anthropic webapp-testing karar ağacı, with_server.py, networkidle ve görsel kanıt | L296-L373 |

---

## A. Antigravity & 21st.dev Bileşen İş Akışı

21st.dev ("The NPM for Design Engineers"), shadcn/ui ve Tailwind ekosistemi üzerindeki modern UI bileşenlerini projeye entegre ederken "kopyala-yapıştır ve unut" yaklaşımı kesinlikle yasaktır.

### 1. Bileşen Seçim ve Entegrasyon Protokolü
1. **İhtiyaç Analizi:** Bileşen sırf havalı göründüğü için değil, kullanıcı akışındaki belirli bir bilişsel yükü azalttığı için seçilmelidir (ör. karmaşık filtreleme için command palette, hiyerarşi için bento grid).
2. **21st.dev & Magic UI & Aceternity Seçimi:**
   - Ham Tailwind + Radix primitive tabanlı bileşenler tercih edilir.
   - Harici ağır kütüphaneler (ör. devasa Three.js canvasları) yalnızca amaca yönelikse ve lazy-loaded ise kabul edilir.
3. **Modülerlik ve Kod İzolasyonu:**
   - Bileşen kodunu doğrudan projenin `src/components/ui/` dizinine yerleştirin.
   - Her bileşen bağımsız bir dosya olmalı, stiller Tailwind utility sınıfları ve CSS değişkenleri (`var(--primary)`) üzerinden beslenmelidir.
   - Harici ikon kütüphanelerinde (Lucide React vb.) yalnızca kullanılan ikonları import edin (tree-shaking koruması).

### 2. Bileşeni Projeye Uyarlama Kontrol Listesi
- [ ] **Tailwind Config Senkronizasyonu:** `tailwind.config.js` içine gerekli keyframe, animasyon ve renk değişkenleri eklendi mi?
- [ ] **Erişilebilirlik (A11y):** Radix UI / Headless UI primitive'leri korunarak klavye gezinimi (`Tab`, `Escape`, `Arrow Keys`) ve ARIA etiketleri doğrulandı mı?
- [ ] **Props Sadeleştirmesi:** Kullanılmayan dummy props veya aşırı soyutlamalar temizlendi mi?

```tsx
// Örnek: 21st.dev uyumlu ve erişilebilir Card bileşeni şablonu
import React from 'react';
import { cn } from '@/lib/utils';

interface InteractiveCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'surface' | 'elevated' | 'glass';
  glowEffect?: boolean;
}

export const InteractiveCard = React.forwardRef<HTMLDivElement, InteractiveCardProps>(
  ({ className, variant = 'surface', glowEffect = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative overflow-hidden rounded-2xl border transition-all duration-300",
          // Surface varyantı
          variant === 'surface' && "bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-strong)]",
          // Glass varyantı (kontrollü blur)
          variant === 'glass' && "bg-[var(--bg-glass)] backdrop-blur-md border-[var(--border-glass)] shadow-sm",
          // Hover ve Odaklanma mikro-etkileşimi
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
          className
        )}
        {...props}
      >
        {glowEffect && (
          <div 
            aria-hidden="true" 
            className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100 bg-radial-glow" 
          />
        )}
        {children}
      </div>
    );
  }
);
InteractiveCard.displayName = "InteractiveCard";
```

### 3. Resmi 21st MCP Kurulumu ve Ajan Entegrasyonu
Kurulum (CLI, HTTP MCP sunucusu, `API_KEY_21ST`, stdio alternatifi) ve iş akışı: `bilgi/self-hosted-ve-mcp-servisler.md` M. Eski `@21st-dev/magic-mcp` paketi kullanılmaz.

---

## B. Boşluk, Grid ve Görsel Hiyerarşi

Arayüzün profesyonelliğini belirleyen temel unsur bileşenlerin süsü değil; negatif alanın (whitespace) kalitesi ve matematiksel ritmidir.

### 1. 8pt / 4pt Boşluk Sistemi
- Tüm padding, margin ve gap değerleri 4px/8px katları (`4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px`) olmalıdır.
- Tailwind sınıfları: `p-1 (4px)`, `p-2 (8px)`, `p-3 (12px)`, `p-4 (16px)`, `p-6 (24px)`, `p-8 (32px)`, `p-12 (48px)`.
- İç içe elemanlarda "Dış Boşluk > İç Boşluk" kuralı katıdır (ör. Card padding 24px ise içindeki buton-başlık arası gap 12px veya 16px olmalıdır).

### 2. Bento Grid ve Asimetrik Denge
- Tekdüze, monoton 3 eşit sütunlu yerleşimler yerine içeriğin önemine göre boyutlanan **Bento Grid** mimarisi kullanılır.
- Ana odak bileşeni (Primary value prop) 2 sütun veya 2 satır kaplarken, destekleyici veriler tek hücrede toplanır.
- Görsel ağırlık merkezi tek bir köşeye yığılmaz; karşıt köşede kontrast bir elemanla (ör. metin yoğunluğu karşısında görsel doku) dengelenir.

```html
<!-- Bento Grid Örneği: Asimetrik ve Fonksiyonel -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[280px]">
  <!-- Öne Çıkan Ana Hücre: 2 Sütun -->
  <div class="md:col-span-2 rounded-2xl p-8 bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between">
    <div>
      <span class="text-xs uppercase tracking-wider font-semibold text-[var(--accent)]">Öne Çıkan</span>
      <h3 class="text-2xl font-bold mt-2">Canlı Performans Metrikleri</h3>
    </div>
    <div class="h-32 w-full bg-[var(--bg-muted)] rounded-xl flex items-center justify-center">
      <!-- Veri Görselleştirme -->
    </div>
  </div>

  <!-- Yan Hücre: 1 Sütun -->
  <div class="rounded-2xl p-6 bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between">
    <h4 class="text-lg font-semibold">Hızlı İşlemler</h4>
    <p class="text-sm text-[var(--text-secondary)]">Tek tıkla dağıtım ve anlık log izleme.</p>
  </div>
</div>
```

### 3. Z-Index Ölçeği ve Katman Disiplini
Rastgele `z-[9999]` gibi değerler kesinlikle yasaktır. Proje genelinde şu skala tanımlanmalıdır:
- `z-0`: Temel zemin
- `z-10`: Kart üzeri hafif çıkıntılar / sticky başlıklar
- `z-20`: Dropdown menüler, popover'lar
- `z-30`: Sticky navigasyon barı (Header)
- `z-40`: Modal / Drawer backdrop (arka plan karartması)
- `z-50`: Modal / Drawer gövdesi
- `z-60`: Toast / Notification bildirimleri

---

## K. Klişe Yasağı (Anti-AI Slop UI)

Kedihane arayüzlerinde yapay zekâ tarafından üretildiği ilk bakışta anlaşılan ezberci ve kalitesiz UI şablonları katı şekilde yasaklanmıştır (Anthropic `frontend-design` standardı).

### 1. Anthropic Belirttiği 5 Yapay Zeka Klişe Kümesi (AI Tells)
1. **Sıcak Krem + Terracotta/Kil Vurgu:** Krem arka plan (`#F4F1EA`), yüksek kontrastlı serif başlık ve terracotta/kil rengi vurgu (`#D97757` — Claude'un kendi arayüz tell'idir).
2. **Koyu Arka Plan + Parlak Asit-Yeşil/Vermilion:** Karanlık zemin üzerine basılan klişe neon/asit yeşili vurgular.
3. **Broadsheet Gazete Mizanpajı:** Sıfır border-radius, hairline çok ince çizgiler ve sıkışık gazete sütunları.
4. **SaaS-Card Kiti:** Bütün içeriğin hiyerarşiden bağımsız olarak aynı yuvarlatılmış kartlara bölünmesi, her şeye aynı hafif gri gölge (`rgba(0,0,0,0.1)`) ve dekoratif gradyan basılması.
5. **Şablon Chrome Öğeleri:** Her başlığın üstünde ALL-CAPS harf aralığı açılmış etiket; orta nokta ile birleştirilmiş meta diziler (`A · B · C`); `WORD — fragment` şeklinde tireli etiketler; siyah yerine sahte koyu tonlar (`#0B0B0B`, `#111`); buton/link sonuna eklenen `→`.

### 2. Tipografik ve Görsel Yapay Zeka Hataları
- **Başlıkta Tek Kelime Vurgulama:** Başlıktaki tek bir kelimeyi italic, bold veya farklı renge boyamak en yaygın yapay zeka göstergesidir.
- **Sahte Sıralama:** İçerik gerçek bir kronoloji veya adım zinciri değilse `01 / 02 / 03` gibi numaralı göstergeler kullanılamaz.
- **Mor/Pembe Neon Gradyan Patlaması:** Koyu arka planda her yere yayılan radyal mor-mavi glow yasaktır.
- **Tekdüze 3'lü İkon Kartları ("Hızlı, Güvenli, Kolay"):** İçeriksiz jenerik pazarlama dolgusu yerine somut ürün verisi sunulur.
- **Sahte Grafikler:** Ekseni, birimi veya reel değeri olmayan yukarı tırmanan süs eğrileri yerine gerçekçi sparkline veya tablolar kullanılır.

---

## M. Mikro Etkileşimler ve MCP Sunucu Geliştirme (MCP Builder)

Arayüz animasyonları "göz boyamak" için değil; kullanıcının yaptığı eylemin sonucunu doğrulamak ve mekânsal devamlılık sağlamak içindir. Aynı zamanda Anthropic MCP standardı (`anthropics/skills/mcp-builder`) ile ajanlar arası iletişim köprüleri tasarlanır.

### 1. Zamanlama ve Easing Standartları
- **Mikro Etkileşim (Hover, Focus, Tıklama):** 150ms – 200ms. Easing: `cubic-bezier(0.4, 0, 0.2, 1)` (ease-out).
- **Orta Ölçekli Geçiş (Dropdown açılma, Accordion, Modal):** 250ms – 300ms. Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (spring-benzeri doğal yumuşama).
- **Büyük Geçiş (Sayfa / Route değişimi):** En fazla 350ms. Asla kullanıcıyı bekleten gereksiz uzun animasyon yapılmaz.

### 2. Erişilebilirlik: `prefers-reduced-motion` Zorunluluğu
Hareket hassasiyeti olan kullanıcılar için animasyonlar otomatik olarak devre dışı bırakılmalı veya anlık opaklık geçişine (fade) dönüştürülmelidir.

```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 3. Yükleme Durumları ve İskelet (Skeleton) Tasarımı
- Dönen spinner'lar yerine içeriğin nihai şeklini taklit eden **Skeleton Loading** blokları kullanılmalıdır.
- Skeleton animasyonunda soluk gri gradyan (`pulse` veya `shimmer`) akışı kullanılır; görsel gürültü yaratmayacak hızda (1.5s - 2s döngü) ayarlanır.

### 4. Anthropic MCP Sunucu Geliştirme Protokolü (MCP Builder)
LLM'lerin dış sistemler ve arayüz servisleriyle konuşması için yüksek kaliteli MCP (Model Context Protocol) sunucuları 4 fazlı protokolle geliştirilir:

1. **Faz 1: Derin Araştırma ve Planlama:**
   - **API Kapsamı vs İş Akışı Araçları:** Kapsamlı API endpoint desteği önceliklidir; ancak sık tekrarlanan karmaşık operasyonlar için birleşik iş akışı araçları da tasarlanmalıdır.
   - **Tutarlı ve Eylem Odaklı Araç İsimlendirme:** Araç isimleri net, açıklayıcı ve tutarlı öneklerle adlandırılmalıdır (ör. `github_create_issue`, `github_list_repos`).
   - **Bağlam ve Karakter Sınırı Yönetimi:** LLM'in bağlam penceresini tıkamamak için araç açıklamaları öz olmalı; büyük çıktılarda filtreleme ve sayfalama zorunlu tutulmalıdır.
   - **Eyleme Dönük Hata Mesajları:** Bir hata fırlatıldığında yalnızca "hata oluştu" denilmez; ajanın bir sonraki adımda ne yapması gerektiğini bildiren yönlendirici mesajlar verilir.

2. **Faz 2: Uygulama (TypeScript SDK v2 & FastMCP):**
   - **Önerilen Yığın:** TypeScript SDK v2 (`@modelcontextprotocol/server`) veya Python tarafında `mcp` / `fastmcp`.
   - **Şema Doğrulama:** Giriş parametreleri TypeScript'te Zod, Python'da Pydantic ile sıkı doğrulanmalıdır.
   - **Yapılandırılmış Çıktı:** Araç dönüşlerinde serbest metin yerine `structuredContent` ve `outputSchema` tanımlanmalıdır.
   - **Açıklama İpuçları (Tool Annotations):** Güvenlik için `readOnlyHint`, `destructiveHint`, `idempotentHint` ve `openWorldHint` bayrakları belirtilmelidir.
   - **Sayfalama (Pagination):** 20'den fazla öğe döndürebilecek listelerde `limit` (varsayılan 20, maks 100) ve `cursor` parametresi uygulanmalıdır.

3. **Faz 3: Kod İncelemesi ve Test:**
   - DRY kuralına tam uyum ve merkezi hata yönetimi.
   - `npx @modelcontextprotocol/inspector` ile stdio ve HTTP taşıyıcıları üzerinden canlı test.

4. **Faz 4: Kapsamlı Değerlendirmeler (Evaluations):**
   - MCP sunucusunun kalitesini ölçmek için 10 adet bağımsız, salt okunur (read-only), karmaşık ve doğrulanabilir XML QA değerlendirme senaryosu hazırlanır:
   ```xml
   <evaluation>
     <qa_pair>
       <question>Sistemdeki en yüksek öncelikli açık bildiriminin ID'si nedir?</question>
       <answer>SEC-409</answer>
     </qa_pair>
   </evaluation>
   ```

---

## R. Renk, Kontrast ve Tema Sistemi

Gelişigüzel hex kodları (`#3b82f6` vb.) bileşen içine yazılamaz. Renkler anlamsal (semantic) CSS değişkenleri üzerinden yönetilmelidir.

### 1. 60-30-10 Renk Dengesi Kuralı
- **%60 Hakim Renk:** Zemin ve genel alanlar (Canvas, Card background, nötr tonlar).
- **%30 Destekleyici Renk:** Tipografi, kenarlıklar, ikincil butonlar, yüzey kartları.
- **%10 Vurgu (Accent) Rengi:** Birincil CTA butonları, aktif bildirim göstergeleri, kritik başarı durumları.

### 2. Gerçek Koyu Tema (OLED Siyahı Tuzağına Düşmeme)
- Zemin asla tam saf siyah (`#000000`) yapılmamalıdır; derin kömür / grafit tonları (`#09090b`, `#0d1117`, `#121214`) tercih edilir. Saf siyah sert kontrast yaratır ve gözü yorar.
- Katman yükseldikçe (Elevation) yüzey rengi hafifçe açılmalıdır:
  - Zemin (Base): `#0a0a0c`
  - Kart / Panel (Surface): `#141418`
  - Hover Kart (Surface Hover): `#1c1c22`
  - Popover / Dialog: `#22222a`

### 3. WCAG AA / AAA Kontrast Kuralı
- Gövde metinleri ile arka plan arasında en az **4.5:1** (WCAG AA), tercihen **7:1** (WCAG AAA) kontrast oranı zorunludur.
- Pasif / ikincil metinlerde kontrast asla **3:1** altına düşemez.
- Renk körlüğü için durum bildirimlerinde (Hata, Başarı, Uyarı) yalnızca renk değil, ikon ve açıklayıcı metin birlikte kullanılmalıdır.

```css
:root {
  --bg-base: #f8fafc;
  --bg-surface: #ffffff;
  --bg-muted: #f1f5f9;
  --border-subtle: #e2e8f0;
  --border-strong: #cbd5e1;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --accent: #2563eb;
  --accent-foreground: #ffffff;
}

[data-theme="dark"] {
  --bg-base: #090a0f;
  --bg-surface: #12131a;
  --bg-muted: #1a1c26;
  --border-subtle: #232634;
  --border-strong: #363a4f;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #3b82f6;
  --accent-foreground: #ffffff;
}
```

---

## T. Tipografi, İki Aşamalı Süreç (2-Pass) ve Tasarımda Metin

Tipografi ve metin arayüzün ruhudur. Karakterli bir font ve eylem odaklı metin dili, projeyi amatör bir prototipten profesyonel bir ürüne dönüştürür.

### 1. İki Aşamalı Tasarım Süreci (2-Pass Design Workflow)
1. **1. Aşama — Tasarım Planı (Brainstorm & Plan):**
   - **Renk:** 4–6 isimli hex token'dan oluşan çekirdek palet.
   - **Tipografi:** Seçilen font ailesi ve hiyerarşik rolleri.
   - **Mizanpaj & ASCII Wireframe:** Sayfa akışını tek cümlelik açıklamalar ve ASCII şemalarla planlama.
   - **İlkeler:** Sayfayı akılda kalıcı ve özgün kılan tek bir ana görsel odak (Chanel kuralı: Aynaya bak ve gereksiz bir aksesuarı çıkar).
2. **2. Aşama — Brife Göre Doğrulama ve Kodlama:**
   - Tasarım planının jenerik bir yapay zeka şablonuna düşüp düşmediği denetlenir. Yalnızca özgünlük doğrulandıktan sonra kod yazımına geçilir.

### 2. Arayüzde Metin Yazarlığı (Writing in Design)
- **Kelimeler Tasarımdır:** Kelimeler dekoratif dolgu değildir; yön bulmayı kolaylaştırır.
- **Kullanıcı Perspektifi:** Sistem terimleri değil kullanıcının günlük dili kullanılır (ör. "Webhook konfigürasyonu" yerine "Bildirim yönetimi").
- **Aktif Eylem Dili:** Butonlar ne yapacağını söyler ("Submit" yerine "Değişiklikleri kaydet"). Buton "Yayınla" ise işlem sonrası toast bildirimi "Yayınlandı" olmalıdır.
- **Hatalar ve Boş Durumlar:** Hata mesajları yapay bir dille özür dilemez; neyin ters gittiğini ve nasıl düzeltileceğini söyler. Boş ekranlar (empty state) bir sonraki eyleme davettir.

### 3. Akıcı Tipografi ve Font Eşleştirmesi
- **Display / Başlık Fontları:** Syne, Clash Display, Cal Sans, Space Grotesk, Cabinet Grotesk veya Instrument Serif.
- **Arayüz & Gövde Fontları:** Plus Jakarta Sans, General Sans, Satoshi, Geist Sans, Inter.
- **Akıcı Boyutlandırma:** `font-size: clamp(2.25rem, 5vw + 1rem, 4.5rem)` ile responsive breakpoint karmaşasından kaçınılır.
- **Satır Sınırı:** Gövde paragraflarında satır uzunluğu **45 ile 75 karakter** (`max-w-[65ch]`) arasında tutulur.

---

## W. Web Uygulaması Testi ve Doğrulama (Playwright & Webapp-Testing)

Anthropic `webapp-testing` araç seti ve Playwright kullanarak yerel veya uzak web uygulamalarının arayüz işlevselliği, regresyon testleri ve görsel doğrulaması gerçekleştirilir.

### 1. Karar Ağacı: Doğru Test Yaklaşımını Seçme
```
Kullanıcı görevi → Statik HTML mi?
    ├─ EVET → HTML dosyasını doğrudan oku ve seçicileri (selectors) belirle
    │         ├─ Başarılı → Doğrudan Playwright ile file:// URL betiği yaz
    │         └─ Yetersiz/Dinamik → Aşağıdaki dinamik webapp yolunu izle
    │
    └─ HAYIR (Dinamik Web Uygulaması) → Test sunucusu zaten çalışıyor mu?
        ├─ HAYIR → python tools/webapp_testing/with_server.py komutuyla sunucu yaşam döngüsünü bağla
        │          (Örnek: --server "npm run dev" --port 5173 -- python test.py)
        │
        └─ EVET → Keşif Sonrası Eylem (Reconnaissance-Then-Action) Protokolü:
            1. Sayfaya git ve MUTLAKA page.wait_for_load_state('networkidle') bekle!
            2. Ekran görüntüsü al veya render edilmiş DOM içeriğini incele
            3. Ekrana basılmış gerçek duruma göre seçicileri (button, input, role) tespit et
            4. Keşfedilen seçicilerle etkileşimi yürüt (click, fill, evaluate)
```

### 2. Sunucu Yaşam Döngüsü Yönetimi (`with_server.py`)
Frontend ve backend sunucularını test çalışırken arka planda ayağa kaldırıp test bitince temiz kapatmak için:

```bash
# Tekil sunucu yönetimi
python tools/webapp_testing/with_server.py --server "npm run dev" --port 5173 -- python otomasyon_testi.py

# Çoklu sunucu yönetimi (Backend API + Frontend Vite)
python tools/webapp_testing/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python otomasyon_testi.py
```

### 3. Keşif ve Doğrulama Python Şablonu
Dinamik uygulamalarda en kritik hata `networkidle` beklenmeden DOM'un taranmasıdır. Aşağıdaki şablon standarttır:

```python
from playwright.sync_api import sync_playwright

def test_web_uygulamasi():
    with sync_playwright() as p:
        # Her zaman headless modda başlat
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Konsol loglarını ve hatalarını yakala
        page.on("console", lambda msg: print(f"[Tarayıcı Logu] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Sayfa Hatası] {err}"))

        # Sayfaya git ve JS / ağ isteklerinin bitmesini bekle
        page.goto('http://localhost:5173')
        page.wait_for_load_state('networkidle')

        # 1. Aşama: Görsel Kanıt ve Keşif (Reconnaissance)
        page.screenshot(path='cikti/sayfa_kesif.png', full_page=True)

        # 2. Aşama: Etkileşim ve Doğrulama (Action & Verify)
        page.wait_for_selector('input[name="email"]')
        page.fill('input[name="email"]', 'test@kedihane.app')
        page.click('button[type="submit"]')

        # Sonuç bekleme ve başarı kanıtı
        page.wait_for_selector('.dashboard-loaded')
        page.screenshot(path='cikti/giris_basarili.png')

        browser.close()

if __name__ == '__main__':
    test_web_uygulamasi()
```

### 4. Temel Test İlkeleri ve Hata Önleme
- **networkidle Bekleme Kuralı:** Dinamik React/Vue/Svelte uygulamalarında ağ trafiği dinlenmeden yapılan assertion'lar sahte hatalara (flaky tests) yol açar.
- **Seçici Önceliği:** Sırasıyla `role=` (ör. `page.get_by_role("button", name="Gönder")`), `text=`, `data-testid` ve stabil CSS sınıfları tercih edilir; kırılgan derin XPath'lerden kaçınılır.
- **Kaynak Temizliği:** Tarayıcı oturumu her koşulda (`try...finally` veya `with` bloğu) kapatılarak açık process sızıntısı önlenmelidir.
