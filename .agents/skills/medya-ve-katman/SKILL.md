---
name: medya-ve-katman
description: Kaliko için Photoshop katman ayırma (psd_worker), emprime renk ayrımı, görsel düzeltme, ffmpeg video/ses analizi ve OpenVoice ses klonlama rehberi.
---

# Medya, Katman Ayırma ve Ses/Video İşleme Rehberi

> [!IMPORTANT]
> **Kedihane Token Tasarrufu Kuralı:** Bu rehberin tamamı tek seferde okunmaz. Yapacağınız işleme göre aşağıdaki alfabetik fihristten ilgili satır aralığını tespit edip yalnızca o aralığı okuyun. Ayrıca `bilgi/*.md` dosyalarının tamamını asla okumayın, sadece fihristten tespit edilen ilgili satır aralıklarını çekin.

### Alfabetik Fihrist (A-Z)
| Başlık | Kapsam ve Odak | Satır Aralığı |
| :--- | :--- | :--- |
| [E. Emprime ve Tekstil Kanal Ayırma](#e-emprime-ve-tekstil-kanal-ayırma) | tools/emprime/, tools/photoshop/ ve bilgi/emprime-kanal-ayirma.md | L24-L44 |
| [G. Görsel Düzeltme, Rötuş ve Otomatik Dekupe (Rembg)](#g-görsel-düzeltme-rötuş-ve-otomatik-dekupe-rembg) | Non-destructive rötuş, danielgatis/rembg CLI/Python BiRefNet/ISNet otomatik dekupe | L48-L113 |
| [K. Katman Ayırma ve PSD Worker Aracı](#k-katman-ayırma-ve-psd-worker-aracı) | tools/psd_worker/, tools/katman/ Python/JSX, bilgi/katman-ayirma.md | L117-L140 |
| [R. React ile Programatik Video Üretimi (Remotion)](#r-react-ile-programatik-video-üretimi-remotion) | remotion-dev/remotion mimarisi, Composition, spring/interpolate, CLI render komutları | L144-L222 |
| [S. Ses Klonlama ve Dublaj (OpenVoice V2 & MeloTTS)](#s-ses-klonlama-ve-dublaj-openvoice-v2--melotts) | myshell-ai/OpenVoice V2 ve MeloTTS ile çok dilli ve duygusal ses klonlama | L226-L282 |
| [T. Tasarım, Sinematik Kamera ve Reasoning Brief Mimarisi (Ankara & Kaliko)](#t-tasarım-sinematik-kamera-ve-reasoning-brief-mimarisi-ankara--kaliko) | Reasoning Brief, sinematik optik/lens, katman-dostu prompt, Kling/Veo stabilite ve TEXT_INTEGRATION | L286-L322 |
| [V. Video/Ses Analizi (FFmpeg) ve Vektörleştirme (VTracer)](#v-videoses-analizi-ffmpeg-ve-vektörleştirme-vtracer) | ffprobe, ebur128 LUFS ve visioncortex/vtracer | L326-L402 |

---

## E. Emprime ve Tekstil Kanal Ayırma

Tekstil ve serigrafi baskı süreçlerinde görsel doğrudan CMYK basılamaz; kumaş rengine ve tram limitlerine göre spot kanallara ayrıştırılmalıdır.

### 1. Detaylı Metot Yönlendirmesi
Bu konunun tam teknik detayları, Photoshop Curves değerleri ve film çıkış açıları için `bilgi/emprime-kanal-ayirma.md` dosyasına başvurun.
- **Kural:** Dosyanın tamamını okumayın! `bilgi/emprime-kanal-ayirma.md` başındaki fihrist tablosundan sadece ilgili yöntemin satır aralığını okuyun.

### 2. Temel Ayrım İlkeleri ve Kontrol Listesi
- **Beyaz Altlık (Underbase):** Koyu kumaşlarda tüm renklerin altına %100 beyaz astar atılmalı, kenarlardan 5 piksel boğma (choke), ince çizgilerde 1 px choke (veya 2 px spread) yapılmalıdır.
- **Tram Açıları (Moiré Önleme):** 45 LPI, 508 PPI, 15° veya 22.5° elips nokta standardı korunmalı; 0°, 45° ve 90° moiré yarattığı için asla kullanılmamalıdır.
- **Simüle Proses ve Bölge Saflığı:** 6 kafa makine sınırı gözetilmeli; Lab ton farkı > 110° olan zıt renklerin karışımı engellenmelidir.

### 3. Çalıştırılabilir Ayrım Araçları (`tools/emprime/` ve `tools/photoshop/`)
- **Bölge Saflıklı AM Tramlama (`bolge_am.py`):**
  - Tek aşamalı: `python tools/emprime/bolge_am.py girdi.png cikti_klasoru 6 5`
  - İki aşamalı önizleme: `ASAMA=onizleme python tools/emprime/bolge_am.py girdi.png cikti_klasoru 6 5`
- **Önizlemeden Film Ayrımı (`onizlemeden_ayir.py`):** `python tools/emprime/onizlemeden_ayir.py onayli_onizleme.png cikti_klasoru acik cikti/onizleme_palet.json`
- **Tramsız Düz Spot Ayrım (`tramsiz.py`):** `python tools/emprime/tramsiz.py girdi.jpg cikti_klasoru`
- **Ayrım Kalite Kontrolü (`kalite_kontrol.py`):** `python tools/emprime/kalite_kontrol.py cikti_klasoru kaynak.png` (dE <= 12, pürüzlülük <= 0.03)
- **Photoshop Multichannel PSD Üretimi (`tools/photoshop/`):** `psd_olustur_tek_adim.jsx` ile `kanallar_hibrit.json`'dan otomatik PSD üretimi.

---

## G. Görsel Düzeltme, Rötuş ve Otomatik Dekupe (Rembg)

Kaliko tarafından yürütülen görsel işleme süreçlerinde yıkıcı (destructive) düzenlemeler kesinlikle yasaktır. Ayrıca `danielgatis/rembg` motoru ile yüksek kaliteli otomatik dekupe uygulanır.

### 1. Detaylı Metot Yönlendirmesi (MeChi 3.3 — Nano Banana Pro)
Bozuk kumaş desenlerinin adli referans mantığıyla idealize düz tuvalde yeniden yaratılması, 7 parametreli mikro analiz, modüler master prompt ve desen ihya protokolleri için `bilgi/gorsel-duzeltme.md` rehberine başvurun.
- **Kural:** Dosyanın tamamını okumayın; fihrist tablosundan yalnızca ilgili satır aralığını çekin.

### 2. Temel İlkeler ve Kaynak Beyanı
1. **Tahribatsız (Non-Destructive) İş Akışı:**
   - Orijinal arka plan katmanı asla doğrudan düzenlenmez, kilitli tutulur.
   - Tüm rötuşlar yeni boş katmanlar veya akıllı nesneler (Smart Objects) üzerinde yapılır.
   - Renk ve ton ayarları maskelenmiş Ayar Katmanları (Adjustment Layers) ile yönetilir.
2. **Renk Uzayı ve Profil Disiplini:**
   - Web ve ekran çıktıları için: `sRGB IEC61966-2.1`.
   - Profesyonel arşiv ve baskı için: `Adobe RGB (1998)` veya `ProPhoto RGB`.
3. **Telif ve Kaynak Beyanı Zorunluluğu (📌 Kaynak Beyanı):**
   - Dışarıdan temin edilen her görsel için stok lisansı veya açık kaynak kullanım hakkı doğrulanmalıdır.
   - Teslimat notunda görselin kaynağı (unsplash, pexels, yapay zeka promptu veya müşteri materyali) açıkça belirtilmelidir.

### 3. Otomatik Dekupe ve Arka Plan Temizleme (`rembg`)
`danielgatis/rembg`, hem CLI hem de Python kütüphanesi olarak çalışan, gelişmiş derin öğrenme modelleriyle görsellerin arka planını dekupe eden standart aracımızdır.

#### CLI Kullanımı:
```bash
# Tekil dosya arka planını kaldırma
rembg i girdi.png cikti.png

# Renk halosu temizleme (-dc / Decontaminate: çimen, gökyüzü gibi renk yansımalarını temizler)
rembg i -dc urun.jpg urun_temiz.png

# Alfa matting ile tüy/saç kenarlarını hassas ayırma (-a)
rembg i -a portre.jpg portre_alpha.png

# ViTMatte ile en yüksek kaliteli kenar detayı (-vm)
rembg i -vm model.jpg model_vitmatte.png

# Klasördeki tüm görselleri toplu işleme (Batch)
rembg p girdi_klasor/ cikti_klasor/

# İzleme modu (Klasöre yeni düşen görselleri otomatik dekupe eder)
rembg p -w girdi_klasor/ cikti_klasor/
```

#### Önerilen Modeller ve Lisans Uyarısı:
- **`birefnet-general` / `birefnet-portrait` (Varsayılan Ticari Öneri):** Genel ve portre dekupe için açık lisanslı ikili referans modeli. Saç, tüy ve kumaş kıvrımlarında üstün ayrım gücü; tekstil ve e-ticaret işlerinde varsayılan önerimizdir.
- **`isnet-general-use` (Yedek Ticari Model):** Genel kullanım için açık lisanslı, hızlı, dengeli ve keskin kenarlı model.
- **`u2net` / `u2netp`:** Düşük kaynak tüketen, hızlı ve hafif açık alternatifler.
- ⚠️ **`bria-rmbg` (RMBG-2.0) Ticari Lisans Uyarısı:** En keskin kenar kalitesini sunsa da **BRIA AI ticari lisansına** tabidir. Ticari projelerde doğrudan kullanılamaz; ticari kullanım için BRIA AI ile ticari lisans anlaşması zorunludur. Açık ticari işlerde daima `birefnet-general` veya `isnet-general-use` tercih edilir.

#### Python Entegrasyonu:
```python
from rembg import remove, new_session
from PIL import Image

# 1. Hızlı PIL nesnesi dekupe
girdi = Image.open('urun.png')
cikti = remove(girdi, decontaminate=True)
cikti.save('urun_temiz.png')

# 2. BiRefNet modeli ile kalıcı oturum üzerinden toplu işleme
session = new_session('birefnet-general')
with open('portre.jpg', 'rb') as i:
    with open('portre_dekupe.png', 'wb') as o:
        o.write(remove(i.read(), session=session))
```

---

## K. Katman Ayırma ve PSD Worker Aracı

Kedihane çalışma alanında `tools/psd_worker/` dizini altında görselleri ve Photoshop PSD dosyalarını otomasyonla katmanlarına ayıran Node.js araçları hazır bulunmaktadır.

### 1. PSD Worker Aracı
`tools/psd_worker/make_thumbs.js` katman veya görsel klasöründen hızlı küçük resim (thumbnail) üretir (`canvas`):

```bash
cd tools/psd_worker
node make_thumbs.js --input "../../cikti/katmanlar/" --size 300
```

Görsele özel katman ayırma betiği yazılırsa repoya eklenmez (`CLAUDE.md` Bölüm 14, Görsel işleri).

### 2. İleri Düzey Matematiksel Katman Ayırma Araçları (`tools/katman/`)
Kedihane bünyesine eklenen Python ve ExtendScript (JSX) araçları:
- `bolge_murekkep_katman.py`: Bölge bazlı mürekkep katman ayrımı (simplex_ls).
- `katman_birlestir.jsx`: Photoshop ExtendScript ile ayrılmış katmanları kurallı birleştirme betiği.
- `renk_alfa_katman.py` & `uc_renk_katman.py`: Yumuşak alfa geçişli 3 katmanlı ayırma.
- `zemin_desen_katman.py`: Zemin ve tek renk desen ayrımı.

### 3. `bilgi/katman-ayirma.md` Yönlendirmesi
Yumuşak alfa matematiksel formülasyonu (`C = αF + (1−α)B`), Color-to-Alpha farkları, kısıtlı en küçük kareler (`simplex_ls`) bölge grupları ve az mürekkepli baskı katmanları için `bilgi/katman-ayirma.md` rehberine başvurun.
- **Kural:** Dosyanın tamamını okumayın; fihrist tablosundan ilgili bölümün satır aralığını tespit edip okuyun.

---

## R. React ile Programatik Video Üretimi (Remotion)

`remotion-dev/remotion`, React bileşenleri, CSS, SVG ve canvas teknolojilerini kullanarak deterministik, kare bazlı (frame-by-frame) video üretimi sağlayan modern programatik video motorudur. Kedihane tanıtımları, Reels, Shorts ve dinamik veri videoları bu standartla oluşturulur.

> [!WARNING]
> **Remotion Company License Lisans Uyarısı:** Remotion MIT lisanslı değildir; özel bir şirket lisansına (Remotion Company License) sahiptir. Bireysel geliştiriciler ve en fazla 3 çalışanı/yüklenicisi olan küçük ekipler için kullanımı tamamen ücretsizdir. Ancak 4 veya daha fazla çalışanı bulunan kâr amaçlı ticari şirketlerde ticari lisans satın alınması yasal olarak zorunludur.

### 1. Remotion Çekirdek Bileşenleri ve Hook Mimarisi
- `Composition`: Videonun kare hızı (`fps`), süresi (`durationInFrames`), çözünürlüğü (`width`, `height`) ve bileşenini (`component`) tanımlayan giriş noktasıdır.
- `useCurrentFrame()`: Oynatılan o anki karenin tam sayı indeksini (0, 1, 2...) döndürür.
- `useVideoConfig()`: Videonun `fps`, `width`, `height` ve toplam süre bilgilerini sağlayan reaktif hook'tur.
- `spring`: Fizik kurallarına dayalı deterministik yay animasyonu üretir (`damping`, `mass`, `stiffness`).
- `interpolate`: Kare aralıklarını değer aralıklarına eşler (ör. 0-20. kareler arasında opaklığı 0'dan 1'e çıkarma).
- `Sequence`: Belirli bir karede başlayıp süren katmanları (`from`, `durationInFrames`) zaman çizelgesine yerleştirir.
- `AbsoluteFill`: Video tuvalini tam oturan (`position: absolute; inset: 0`) kapsayıcı bileşendir.

### 2. Örnek Reels / Tanıtım Videosu Şablonu

```tsx
// src/KedihaneVideo.tsx
import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';

interface KedihaneVideoProps {
  title: string;
  subtitle: string;
}

export const KedihaneVideo: React.FC<KedihaneVideoProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fizik tabanlı yay animasyonu ile ölçekleme
  const scale = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.5 }
  });

  // 0-20. kareler arasında yumuşak belirme
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: 'clamp'
  });

  // Metin yukarı kayma geçişi
  const translateY = interpolate(frame, [30, 50], [40, 0], {
    extrapolateRight: 'clamp'
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#090a0f', justifyContent: 'center', alignItems: 'center' }}>
      <Sequence from={0} durationInFrames={120}>
        <div style={{ opacity, transform: `scale(${scale})`, textAlign: 'center' }}>
          <h1 style={{ color: '#ffffff', fontSize: 68, fontFamily: 'system-ui, sans-serif' }}>{title}</h1>
        </div>
      </Sequence>
      <Sequence from={35}>
        <div style={{ transform: `translateY(${translateY}px)`, color: '#38bdf8', fontSize: 34, marginTop: 20 }}>
          {subtitle}
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
```

### 3. CLI Render ve Önizleme Komutları
Remotion projelerinde render işlemi doğrudan Node.js CLI üzerinden headless Chrome/Chromium ile yürütülür:

```bash
# 1. Canlı Geliştirme ve Önizleme Stüdyosu
npx remotion preview

# 2. Deterministik MP4 Render Alma
npx remotion render src/index.ts KedihaneVideo cikti/video.mp4 --codec=h264 --crf=18

# 3. Yalnızca belirli bir kareden durağan görüntü (Still Image) alma
npx remotion still src/index.ts KedihaneVideo cikti/thumbnail.png --frame=45
```

---

## S. Ses Klonlama ve Dublaj (OpenVoice V2 & MeloTTS)

`myshell-ai/OpenVoice` V2 mimarisi, referans konuşmacının ses rengini (timbre) sıfır vuruşlu (zero-shot) olarak klonlarken tonlama, ritim, aksan ve duyguyu bağımsız olarak kontrol etmeyi sağlar. OpenVoice V2 ve MeloTTS MIT lisansı ile tamamen açık kaynak ve ticari kullanıma uygundur.

### 1. Çalışma Mantığı ve V2 İki Aşamalı Akış
1. **Baz TTS (MeloTTS):** Metin, hedef dilde ve belirlenen hız/aksan parametreleriyle MeloTTS (`melo.api.TTS`) baz modeli tarafından üretilir. V2'de İngilizce (Amerikan, İngiliz, Hint, Avustralya), İspanyolca, Fransızca, Çince, Japonca ve Korece dilleri yerel olarak desteklenir.
2. **Ton Dönüştürücü (ToneColorConverter):** Referans ses örneğinden (10-30 saniyelik temiz ses) çıkarılan ses rengi embedding vektörü, baz ses çıktısının üzerine giydirilir. `vad=True` parametresi ile sessiz bölümler otomatik filtrelenir.

### 2. OpenVoice V2 Python İş Akışı Şablonu

```python
import os
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

# 1. Ortam ve Model Başlatma (V2 Kontrol Noktaları)
ckpt_converter = 'checkpoints_v2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'cikti/dublaj_v2'
os.makedirs(output_dir, exist_ok=True)

tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# 2. Referans Sesten Hedef Ses Rengi Embedding'i Çıkarma
reference_audio = 'girdi/referans_ses.mp3'  # Klonlanacak konuşmacının temiz sesi
target_se, audio_name = se_extractor.get_se(reference_audio, tone_color_converter, vad=True)

# 3. MeloTTS ile Baz Ses Üretimi
lang = 'EN_NEWEST'  # Desteklenenler: EN, EN_NEWEST, ES, FR, ZH, JP, KR
text = "Kedihane multi-agent framework delivers high-performance digital automation."
base_model = TTS(language=lang, device=device)
speaker_ids = base_model.hps.data.spk2id

# Varsayılan veya seçilen konuşmacı profili
speaker_key = list(speaker_ids.keys())[0]  # ör. 'en-default' veya 'en-us'
speaker_id = speaker_ids[speaker_key]
speaker_key_formatted = speaker_key.lower().replace('_', '-')

# Ara baz ses dosyasını oluşturma
temp_base_wav = os.path.join(output_dir, 'temp_base.wav')
base_model.tts_to_file(text, speaker_id, temp_base_wav, speed=1.0)

# 4. Kaynak Ses Tonu ile Hedef Ses Rengini Birleştirme (Klonlama)
source_se = torch.load(f'checkpoints_v2/base_speakers/ses/{speaker_key_formatted}.pth', map_location=device)
final_output_path = os.path.join(output_dir, 'kedihane_klonlanmis_cikti.wav')

tone_color_converter.convert(
    audio_src_path=temp_base_wav,
    src_se=source_se,
    tgt_se=target_se,
    output_path=final_output_path,
    message="@kedihane"
)
```

---

## T. Tasarım, Sinematik Kamera ve Reasoning Brief Mimarisi (Ankara & Kaliko)

Üretken yapay zekâ (görsel ve video) süreçlerinde rastgele anahtar kelimeler yerine sinematik optik parametreler, fiziksel ışık ve katman ayrımına elverişli yapılandırılmış brifing mimarisi kullanılır. Bu bölüm Ankara (Yaratıcı Yönetmen) ve Kaliko (Medya Operatörü) ortak üretim standardıdır.

### 1. Reasoning Brief Formülü (Kelime Çorbası Yasağı)
Modeli yanıltan ve kaliteyi düşüren `masterpiece, 8k, ultra realistic, trending on artstation` gibi anlamsız kelime çorbası etiketleri kesinlikle yasaktır. Bunların yerine 6 katmanlı fiziksel brifing mimarisi uygulanır:

1. **SUBJECT (Özne ve Malzeme Dokusu):** Öznin anatomik detayları, giysi/malzeme dokusu (ör. `brushed aluminum with micro-scratches`, `heavyweight 320 GSM ring-spun cotton`).
2. **ACTION (Fiziksel Eylem):** Fizik kurallarıyla uyumlu, durağan veya net tanımlanmış hareket (ör. `standing motionless with hands resting on a wooden drafting table`).
3. **ENVIRONMENT (Mekân ve Derinlik):** Sahne derinliği, zemin, ufuk ve mekân geometrisi (ör. `minimalist brutalist concrete studio, deep linear vanishing point`).
4. **LIGHTING (Işık Yönü ve Kelvin Sıcaklığı):** Işığın yönü, sertliği, Kelvin renk sıcaklığı ve kontur (ör. `key light from 45-degree camera left at 3200K warm tungsten, sharp cyan rim light separating subject from background`).
5. **CAMERA & LENS (Optik ve Hareket):** Odak uzaklığı (`24mm / 35mm / 50mm / 85mm`), diyafram değeri (`f/1.4 - f/8`) ve kamera hareketi (`static, dolly-in, horizontal tracking`).
6. **TEXT_INTEGRATION (Tipografi Uyumu):** Görsel içine gömülecek metin, font stili ve yüzey fiziği entegrasyonu (ör. `"KEDIHANE" screen-printed in bold geometric sans-serif across the chest`).

### 2. Emprime ve PSD Katman Ayrımına Hazır Görsel Üretim Standardı
Görsel üretiminin amacı tek başına dijital sergileme değil; `tools/katman/` veya `tools/emprime/` araçlarıyla baskıya veya katmanlara dönüştürmektir:
- **Net Kontrast ve Rim-Light İzolasyonu:** Özne ile arka plan arasında en az 2 durak (EV) kontrast farkı ve kenar ayırıcı kontur ışığı (`strong edge backlighting`) verilerek dekupe motorlarının (`rembg`, BiRefNet) pürüzsüz maske üretmesi sağlanır.
- **Emprime/Serigrafi için Bölge Saflığı:** Tekstil baskısı hedefleniyorsa atmosferik sis, duman ve parazit gradyanlar yasaktır (`no atmospheric haze, no volumetric smoke, clean sharp edges, isolated subject, solid flat background`).
- **Antigravity Yerleşik Üretim Akışı:** Görsel üretimi için pahalı harici API'ler yerine Antigravity'nin yerleşik `image-generator` alt ajanı devreye sokulur; üretilen PNG doğrudan Kaliko'ya iletilerek `tools/emprime/bolge_am.py` veya `tools/photoshop/psd_olustur_tek_adim.jsx` akışına verilir.

### 3. Video Üretiminde (Kling / Sora / Veo / Runway) Kamera ve Hareket Kararlılığı
Video modellerinde uzuv erimesi (morphing), mekân bükülmesi ve titremeyi önleyen katı stabilite kuralları:
- **Tek Sahne - Tek Hareket Kuralı (`Single Continuous Motion`):** Bir sahnede birden fazla kamera ekseni veya çelişkili özne hareketi verilmez. Yalnızca 1 ana kamera hareketi ve 1 fiziksel özne eylemi tanımlanır.
- **Sinematik Lens ve Diyafram Eşleşmesi:**
  | Plan Türü | Lens | Diyafram | Kamera Hareketi | Kullanım Amacı |
  | :--- | :--- | :--- | :--- | :--- |
  | **Geniş / Çevre (Establishing)** | 24mm | f/8.0 | Yavaş ileri kaydırma (`slow dolly-in`) | Mekânı ve derinliği tanıtma |
  | **Orta Plan (Medium)** | 35mm - 50mm | f/4.0 | Yatay takip (`lateral tracking`) | Karakter ve eylem odaklı |
  | **Portre / Detay (Close-up)** | 85mm | f/1.8 | Sabit (`static`) veya mikro pan | Duygu, doku, bokeh ve özne izolasyonu |

### 4. Görsel İçi Tipografi ve Ambalaj/Baskı Yazısı (`TEXT_INTEGRATION`)
Yapay zekâ modellerinin harf atlama, hece karıştırma veya garip glifler üretmesini önlemek için:
- **Çift Tırnak Kuralı:** Yazılacak metin istisnasız çift tırnak içinde (`"METİN"`) belirtilir.
- **Font Ailesi ve Tipografi Tarifi:** Fontun türü açıkça tanımlanır (`bold geometric sans-serif`, `distressed vintage serif`, `minimal mono typography`).
- **Yüzey Fiziği ile Bütünleştirme:** Metnin görselde havada uçuşan yapay bir katman olmaması için baskı/yüzey dokusuyla birlikte tarif edilir:
  - *Örnek (Kumaş):* `the text "BRAND" screen-printed in high-density puff ink across the chest of the hoodie, subtle fabric weave visible through the letters`.
  - *Örnek (Ambalaj/Etiket):* `the word "KEDIHANE" hot-stamped in matte gold foil onto the dark textured cardboard box`.

---

## V. Video/Ses Analizi (FFmpeg) ve Vektörleştirme (VTracer)

Medya dosyalarının teknik analizi (kare kontrolü, LUFS ölçümü) **Gemini 3.8 Flash** modeli ve FFmpeg ile yürütülürken; raster desenlerin vektörel SVG formatına dönüştürülmesi `visioncortex/vtracer` motoru ile sağlanır.

### 1. `ffprobe` ile Hızlı Akış ve Kodek Analizi
Medya dosyasının çözünürlük, kare hızı (FPS), kodek ve süre bilgilerini JSON formatında çekmek için:

```bash
# Video ve ses akışlarını ayrıştırma
ffprobe -v quiet -print_format json -show_format -show_streams -i "girdi/video.mp4" > "cikti/medya_analizi.json"
```

İncelenmesi gereken kritik alanlar:
- `streams[0].codec_name`: Video kodeği (`h264`, `hevc`, `prores`).
- `streams[0].r_frame_rate`: Kare hızı (24/1, 30/1, 60/1).
- `streams[0].pix_fmt`: Renk alt örneklemesi (`yuv420p`, `yuv422p10le`).
- `streams[1].sample_rate`: Ses örnekleme hızı (44100Hz veya 48000Hz standardı).

### 2. `ebur128` Filtresi ile Ses Seviyesi ve LUFS Ölçümü
YouTube, Spotify ve televizyon standartlarında sesin patlamasını veya kısık kalmasını önlemek için EBU R128 standardında entegre ses seviyesi (Integrated Loudness) ölçülür:

```bash
# EBU R128 entegre ses ölçümü
ffmpeg -i "girdi/audio.wav" -af ebur128=framelog=verbose -f null - 2>&1 | grep -A 10 "Summary:"
```

Hedef LUFS Standartları:
- **YouTube / Web Video:** `-14 LUFS` (True Peak: `-1.0 dBFS`)
- **Spotify / Apple Music:** `-14 LUFS` (True Peak: `-1.0 dBFS`)
- **Podcast / Konuşma:** `-16 LUFS` (Stereo) / `-19 LUFS` (Mono)
- **Televizyon / Yayın:** `-23 LUFS` (EBU R128 Avrupa standardı)

### 3. Dikey Video Kurgu Standartları
- **İşlev:** Ses dosyasının RMS sessizlik analizine göre altyazı ve video kesimlerini senkronize etmek; RTL altyazıda harf şekillendirme ve LTR bloklama.
- **Standartlar ve Araçlar:** `tools/video/analiz.py` (ön analiz + kontak sayfası) ve `tools/video/plan_render.py` (`--dogrula`, `--onizleme`, `--master`; kilit ve denetim) kullanılır; ayrıntılar için `bilgi/video-kurgu.md`, `bilgi/sosyal-medya-ve-video-operasyonu.md` ve `bilgi/tekstil-ve-sim-gorsel-promptlari.md` fihristini okuyun.

### 4. `visioncortex/vtracer` ile Raster Görüntüleri Vektöre (SVG) Dönüştürme
`visioncortex/vtracer`, raster görüntüleri (PNG, JPG) katmanlı, temiz SVG vektör grafiklerine dönüştüren yüksek hızlı açık kaynak motorumuzdur. Potrace'e göre renkli ve degradeli görselleri başarıyla işler; Adobe Illustrator'ın Image Trace aracına kıyasla delikli şekiller yerine boşluksuz üst üste yığma (stacking) stratejisiyle çok daha kompakt ve hafif SVG üretir.

#### VTracer CLI Komutları:
```bash
# 1. En temel dönüştürme
vtracer girdi.png cikti.svg

# 2. Siyah-beyaz çizim ve logo önayarı (preset)
vtracer scan.png cizim.svg --preset bw

# 3. Boşluksuz mozaik ve dikişsiz kesim (--hierarchical cutout)
vtracer desen.jpg desen.svg --hierarchical cutout

# 4. Eğri sadeleştirme (--simplify: dosya boyutunu yarıya indirirken pürüzsüzleştirir)
vtracer desen.jpg desen.svg --simplify 1.5

# 5. Sabit renk paletine bağlama ve renk sınırlandırma
vtracer logo.png logo.svg --palette '#1b1b1b,#e0c088,#5a7d3c,#8fb0d0' --max-colors 16

# 6. Düzensiz aydınlatmalı taramalarda adaptif eşikleme (Bradley-Roth)
vtracer scan.jpg cizim.svg --clustering bw --adaptive
```

#### VTracer Python Entegrasyonu:
```python
import vtracer

# 1. Hızlı dosya dönüştürme
vtracer.convert_file("logo.png", "logo.svg")

# 2. Emprime ve tekstil baskı için gelişmiş konfigürasyon
cfg = vtracer.Config(
    mode="spline",            # Eğri uyumu: pixel, polygon, spline
    hierarchical="cutout",    # Boşluksuz mozaik (seam-free cutout)
    filter_speckle=4,         # 4 pikselden küçük parazit/noktaları temizle
    color_precision=6,        # RGB kanalı başına anlamlı bit sayısı (1-8)
    simplify=1.5              # paper.js tarzı pürüzsüzleştirme
)
cfg.convert_file("baski_deseni.png", "cikti/vektor_desen.svg")
```
