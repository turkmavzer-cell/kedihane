---
name: veri-ve-finans
description: Bombay, Siyam ve Van için anti-bot web veri kazıma (Scrapling), otonom tarayıcı (browser-use), finansal veri ve algoritmik ticaret (OpenBB, Freqtrade, Lean), paketleme ve fiyatlandırma (pricing) ile kitap/belge derleme (Book-to-Skill, MarkItDown) rehberi.
---

# Veri, Finans, Web Kazıma ve Bilgi Derleme Rehberi

> [!IMPORTANT]
> **Kedihane Token Tasarrufu Kuralı:** Bu rehberin tamamı tek seferde okunmaz. Yapacağınız işleme göre aşağıdaki alfabetik fihristten ilgili satır aralığını tespit edip yalnızca o aralığı okuyun.

### Alfabetik Fihrist (A-Z)
| Başlık | Kapsam ve Odak | Satır Aralığı |
| :--- | :--- | :--- |
| [F. Finansal Veri ve Algoritmik Ticaret (OpenBB, Freqtrade & Lean)](#f-finansal-veri-ve-algoritmik-ticaret-openbb-freqtrade--lean) | OpenBB v4, Freqtrade IStrategy/backtest/FreqAI ve QuantConnect Lean Forex algoritmaları | L22-L223 |
| [K. Kariyer ve İş Başvuru Otomasyonu (AI Job Search)](#k-kariyer-ve-iş-başvuru-otomasyonu-ai-job-search) | İş ilanı ayrıştırma, ATS skorlama, anahtar kelime optimizasyonu ve mülakat hazırlığı | L227-L241 |
| [P. Paketleme ve Fiyatlandırma Stratejisi (Pricing Strategy)](#p-paketleme-ve-fiyatlandırma-stratejisi-pricing-strategy) | Değer metriği seçimi, Van Westendorp 4 fiyat sorusu, 3 katmanlı Good-Better-Best ve freemium/deneme | L245-L308 |
| [R. Rehber, Belge (MarkItDown) ve Kitap Derleme (Book-to-Skill)](#r-rehber-belge-markitdown-ve-kitap-derleme-book-to-skill) | virgiliojr94/book-to-skill ile kitap derleme ve Microsoft MarkItDown CLI/Python dönüştürücü | L312-L384 |
| [V. Web Veri Kazıma (Scrapling) ve Otonom Tarayıcı (Browser-Use)](#v-web-veri-kazıma-scrapling-ve-otonom-tarayıcı-browser-use) | Scrapling anti-bot/stealth kazıma ve browser-use Python asenkron tarayıcı ajanı | L388-L511 |

---

## F. Finansal Veri ve Algoritmik Ticaret (OpenBB, Freqtrade & Lean)

Kedihane ekibinde finansal analizler, forex parite takipleri, algoritmik ticaret ve yatırım simülasyonları açık kaynak `OpenBB` Platformu, `Freqtrade` ve `QuantConnect LEAN` motorları üzerinden yürütülür.

### 1. OpenBB Kurulumu ve Ortam Hazırlığı
```bash
pip install openbb
# Temel veri ve teknik analiz eklentileri (OpenBB Platform)
pip install openbb-yfinance openbb-fmp openbb-technical openbb-crypto
```

### 2. Python SDK ile Forex, Hisse, Kripto ve Teknik Analiz
```python
from openbb import obb

# 1. Forex parite verisi (EUR/USD saatlik)
forex_data = obb.currency.price.historical(
    symbol="EURUSD",
    provider="yfinance",
    start_date="2026-01-01",
    interval="1h"
)
df_forex = forex_data.to_dataframe()

# 2. Hisse senedi geçmiş fiyat verisi
stock_price = obb.equity.price.historical(symbol="AAPL", provider="yfinance")
df_stock = stock_price.to_dataframe()

# 3. Kripto para geçmiş verisi (BTC/USD)
crypto_price = obb.crypto.price.historical(symbol="BTCUSD", provider="yfinance")
df_crypto = crypto_price.to_dataframe()

# 4. Teknik Göstergeler ve Volatilite Hesaplama
df_stock['SMA_20'] = df_stock['close'].rolling(window=20).mean()
df_stock['SMA_50'] = df_stock['close'].rolling(window=50).mean()
volatilite = df_stock['close'].pct_change().std() * (252 ** 0.5)
```

### 3. Open Data Platform (ODP) API ve MCP Entegrasyonu
OpenBB Platform'u yerel API sunucusu veya MCP sunucusu olarak çalıştırıp AI ajanlarına ve OpenBB Workspace arayüzüne bağlamak için:

```bash
# ODP API ve resmi MCP sunucu eklentilerini yükleme
pip install openbb-platform-api openbb-mcp-server

# Yerel FastAPI API sunucusunu 127.0.0.1:6900 portunda başlatma
openbb-api

# Antigravity ve Claude ajanları için OpenBB MCP sunucusunu başlatma
openbb-mcp
```
- **Ajan Erişimi:** `openbb-mcp` CLI komutu ile başlatılan MCP sunucusu üzerinden Antigravity veya Claude ajanları doğrudan finansal veri sorgulayabilir.
- **Enterprise Workspace:** `pro.openbb.co` arayüzündeki "Connect Backend" adımından `http://127.0.0.1:6900` adresi eklenerek özel paneller oluşturulabilir.

### 4. Freqtrade ile Algoritmik Ticaret, Backtesting ve FreqAI
Freqtrade (`freqtrade/freqtrade`), kripto ve parite piyasalarında kurallı alım-satım stratejilerini geriye dönük test eden (backtest), makine öğrenimiyle optimize eden ve otonom çalıştıran açık kaynaklı bir alım-satım botudur.

> [!WARNING]
> **GNU GPLv3 Copyleft Lisans Uyarısı:** Freqtrade GNU GPLv3 lisansına tabidir. Kedihane veya Cihan bünyesinde dahili araştırma, backtesting ve kendi hesaplarımızda canlı alım-satım için kullanımı tamamen serbesttir. Ancak Freqtrade kodu değiştirilerek üçüncü taraflara kapalı kaynak ticari bir yazılım/SaaS ürünü olarak dağıtılırsa veya satılırsa, yapılan tüm değişikliklerin ve entegre kodların GPLv3 uyarınca açık kaynak olarak yayınlanması yasal zorunluluk haline gelir.

- **Temel CLI Komutları:**
```bash
# Kullanıcı çalışma dizini ve şablon strateji oluşturma
freqtrade create-userdir --userdir user_data
freqtrade new-strategy --strategy MyStrategy

# Geçmiş mum verisi indirme (Binance 5m/1h)
freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT -t 5m 1h --timerange 20260101-20260301

# Geriye dönük test (Backtesting)
freqtrade backtesting --config user_data/config.json --strategy MyStrategy -i 5m --timerange 20260101-20260301

# Hiperparametre Optimizasyonu (Hyperopt)
freqtrade hyperopt --config user_data/config.json --strategy MyStrategy --hyperopt-loss SharpeHyperOptLoss -e 100 --spaces buy sell roi stoploss

# Canlı veya Simüle (Dry-run) Bot Çalıştırma
freqtrade trade --config user_data/config.json --strategy MyStrategy
```

- **`IStrategy` Sınıf Mimarisi (Python):**
```python
import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter
import talib.abstract as ta
from technical import qtpylib

class MyTrendStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '5m'
    can_short: bool = False

    # Dinamik veya sabit ROI tablosu
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Stoploss kuralı (-%10) ve Trailing Stoploss
    stoploss = -0.10
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    # Hyperopt edilebilir parametreler
    buy_rsi = IntParameter(low=15, high=40, default=30, space="buy", optimize=True)
    sell_rsi = IntParameter(low=60, high=85, default=70, space="sell", optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Teknik Göstergeler (RSI, EMA, Bollinger Bantları)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=20, stds=2)
        dataframe['bb_lower'] = bollinger['lower']
        dataframe['bb_upper'] = bollinger['upper']
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['rsi'], self.buy_rsi.value)) &
                (dataframe['close'] > dataframe['ema_fast']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['rsi'], self.sell_rsi.value)) |
                (dataframe['close'] > dataframe['bb_upper'])
            ),
            'exit_long'
        ] = 1
        return dataframe
```

- **FreqAI ile Adaptif Makine Öğrenimi:**
FreqAI, piyasa rejim değişikliklerine uyum sağlayan LightGBM, XGBoost veya PyTorch modelleri ile kendi kendine eğitilen (adaptive training) tahmin sinyalleri üretir:
```bash
freqtrade trade --config config_freqai.json --strategy FreqaiStrategy --freqaimodel LightGBMRegressor
```

### 5. QuantConnect Lean ile Çoklu Varlık ve Forex Algoritması (`QCAlgorithm`)
QuantConnect LEAN (`QuantConnect/Lean`), hisse senetleri, opsiyonlar, vadeli işlemler ve özellikle Forex piyasalarında kurumsal düzeyde olay güdümlü (event-driven) simülasyon ve canlı işlem motorudur.

- **Yerel CLI Kullanımı:**
```bash
pip install lean
lean init
lean backtest "MyForexProject"
```

- **Python ile Forex Stratejisi (`QCAlgorithm`):**
```python
from AlgorithmImports import *

class ForexMomentumStrategy(QCAlgorithm):

    def initialize(self):
        self.set_cash(100000)  # $100.000 başlangıç sermayesi
        self.set_start_date(2025, 1, 1)
        self.set_end_date(2026, 1, 1)

        # Forex paritesi tanımlama (EUR/USD saatlik çözünürlük)
        self.eurusd = self.add_forex("EURUSD", Resolution.HOUR).symbol

        # Üstel Hareketli Ortalamalar (EMA)
        self.fast_ema = self.ema(self.eurusd, 12, Resolution.HOUR)
        self.slow_ema = self.ema(self.eurusd, 26, Resolution.HOUR)

        # Isınma periyodu (göstergelerin dolması için)
        self.set_warm_up(30, Resolution.DAILY)

    def on_data(self, data: Slice):
        # Göstergeler hazır olana kadar bekle
        if self.is_warming_up or not self.slow_ema.is_ready:
            return

        # Trend kesişimi kontrolü
        holdings = self.portfolio[self.eurusd].quantity

        if self.fast_ema.current.value > self.slow_ema.current.value:
            if holdings <= 0:
                self.log("EURUSD Alış Sinyali: Hızlı EMA yavaşı yukarı kesti.")
                self.set_holdings(self.eurusd, 1.0)
        elif self.fast_ema.current.value < self.slow_ema.current.value:
            if holdings > 0:
                self.log("EURUSD Satış Sinyali: Hızlı EMA yavaşı aşağı kesti.")
                self.liquidate(self.eurusd)
```

### 6. Risk ve Doğrulama Protokolü (Van & Sarman)
- Canlı emir iletimi yapılmadan önce geriye dönük test (Backtesting) verileri Sharpe Oranı, Maksimum Düşüş (Max Drawdown) ve Kâr Faktörü (Profit Factor) kriterlerine göre incelenir.
- Gerçek para ile işlem yapılmadan önce mutlaka Cihan'dan açık yazılı onay alınır (`GEMINI.md` Güvenlik Kuralı).
- [doğrulanmadı] Forex botunu canlıya bağlama talebinde önce backtest ve demo raporu (işlem sayısı, en büyük düşüş, kâr faktörü) istenir; canlı test küçük sermaye ve otomatik durdurma sınırlarıyla başlar; Türkiye'de lisanslı kurumda asgari teminat şartı bu küçük testi engelleyebilir.

---

## K. Kariyer ve İş Başvuru Otomasyonu (AI Job Search)

Aday takip sistemleri (ATS - Applicant Tracking Systems) ve iş arama süreçlerinde veriye dayalı optimizasyon rehberi.

### 1. İş İlanı Ayrıştırma ve Anahtar Kelime Çıkarımı
1. İlan metnini ham olarak alın ve 3 kategoriye ayırın:
   - **Zorunlu Beceriler (Hard Skills):** Diller, frameworkler, araçlar (ör. TypeScript, Docker, PostgreSQL).
   - **Metodolojiler:** Agile, CI/CD, TDD, mikroservis mimarisi.
   - **Yumuşak Beceriler (Soft Skills):** Çapraz ekip iletişimi, liderlik, problem çözme.
2. ATS puanını maksimize etmek için adayın özgeçmişinde bu anahtar kelimelerin birebir (aynı harf biçimiyle) ve deneyim bağlamı içinde geçmesi sağlanır.

### 2. Özelleştirilmiş CV ve Kapak Mektubu Standardı
- Jenerik tek bir CV asla tüm pozisyonlara gönderilmez.
- Her başvuru için ilanın öncelik sırasına göre deneyim maddeleri yeniden sıralanır; kanıtlanabilir başarı metrikleri (rakamlar, yüzdeler, ölçek büyüklükleri) öne çıkarılır.
- Kapak mektubu şirketin mevcut teknik problemlerine doğrudan çözüm öneren kısa, net ve iddiasız profesyonel tonda hazırlanır.

---

## P. Paketleme ve Fiyatlandırma Stratejisi (Pricing Strategy)

SaaS, dijital ürün ve danışmanlık hizmetlerinde fiyatlandırma, maliyetin üzerine kâr koymak (cost-plus) veya rakipleri körü körüne kopyalamak değildir. `coreyhaines31/marketingskills` (pricing) çerçevesine göre fiyat, sunulan algılanan değere (perceived value) ve müşterinin ödeme istekliliğine (willingness to pay) göre belirlenir.

### 1. Değer Metriği (Value Metric) Seçimi
Fiyatın hangi birim üzerinden ölçekleneceği (pricing metric), ürünün başarısını doğrudan belirler.
- **Altın Kural:** "Müşteri bu metriği daha fazla tükettiğinde daha fazla değer elde ediyor mu?"
  - *Evet:* İdeal değer metriğidir (ör. e-posta listesi büyüklüğü, işlenen ödeme hacmi, oluşturulan video dakikası).
  - *Hayır:* Fiyat değeri yansıtmaz ve büyümeyi cezalandırır.
- **Yaygın Metrikler:**
  - *Kullanıcı / Koltuk Başına (Per seat):* İş birliği araçları için uygundur (Slack, Notion). Ancak tek kullanıcılı araçlarda büyümeyi kısıtlar.
  - *Kullanım Başına (Usage-based):* Değişken tüketim (AWS, Twilio, Stripe). Tüketim arttıkça gelir doğal olarak artar.
  - *Sonuç Odaklı (Outcome-based):* Başarılan iş veya çözülen bilet başına (Intercom Fin).
  - *Düz Ücret (Flat-rate):* Sade ürünler, tek persona, sıfır fiyat sürtünmesi (Basecamp).

### 2. Van Westendorp 4 Fiyat Sorusu (Fiyat Araştırması)
Aday veya mevcut müşterilere yöneltilen 4 soru ile fiyat kabul edilebilirlik aralığı (Range of Acceptable Prices) bulunur:
1. **Hangi fiyatta bu ürün o kadar ucuzdur ki kalitesinden şüphe edersiniz?** (Too cheap)
2. **Hangi fiyatta bu ürünün bir fırsat/kelepir olduğunu düşünürsünüz?** (Bargain)
3. **Hangi fiyatta bu ürün pahalı gelmeye başlar ama yine de almayı düşünürsünüz?** (Expensive)
4. **Hangi fiyatta bu ürün aşırı pahalıdır ve kesinlikle almayı düşünmezsiniz?** (Too expensive)

*Analiz Çıktısı:* Bu eğrilerin kesişim noktaları, ürün için pazarda kabul gören taban ve tavan fiyat bantlarını verir. İlk fiyat belirlerken "$9 tuzağına" (aşırı düşük fiyat verip sahte çekim gücü yaratma ve destek yükü altında ezilme) düşülmemeli; $10 (bireysel), $100 (SMB / SaaS standardı), $1.000 (orta ölçek / kurumsal) büyüklük kuralı gözetilmelidir.

### 3. İyi-Daha İyi-En İyi (Good-Better-Best) 3 Katmanlı Paket Mimarisi
En etkili endüstri standardı 3 katmanlı paket yapısıdır:
- **İyi Katmanı (Good / Starter - Giriş):**
  - *Amaç:* Giriş bariyerlerini kaldırmak, hızlı aktivasyon.
  - *Kapsam:* Çekirdek özellikler, sınırlı kullanım kotaları.
  - *Fiyat:* Erişilebilir, düşük taban fiyat.
- **Daha İyi Katmanı (Better / Pro - Önerilen / Çapa):**
  - *Amaç:* Müşterilerin %60-70'inin tercih edeceği tatlı nokta; ana gelir motoru.
  - *Kapsam:* Tam özellik seti, cömert limitler, öncelikli destek.
  - *Fiyat:* Şirketin ana çapa fiyatı.
- **En İyi Katmanı (Best / Business / Enterprise - Premium):**
  - *Amaç:* Yüksek bütçeli güç kullanıcılarını ve şirketleri yakalamak.
  - *Kapsam:* Tüm özellikler, SSO/SAML, gelişmiş denetim günlükleri, özel entegrasyonlar, SLA ve birebir müşteri temsilcisi.
  - *Fiyat:* Pro katmanının 2-3 katı veya satış ekibiyle görüşme (Contact Sales).

### 4. Freemium vs. Ücretsiz Deneme (Free Trial) Karar Matrisi
- **Ne Zaman Freemium Seçilmeli?**
  - Üründe güçlü viral döngü veya ağ etkisi (network effects) varsa.
  - Ücretsiz kullanıcılar ekosisteme değer katıyorsa (içerik, veri, referans).
  - Ücretsiz kullanıcıya hizmet etmenin marjinal maliyeti (sunucu/token) sıfıra yakınsa.
  - Ücretsizden ücretliye geçişi tetikleyen net kullanım/özellik sınırları varsa.
- **Ne Zaman Ücretsiz Deneme (Free Trial) Seçilmeli?**
  - Ürünün değerini kanıtlaması kurulum, onboarding veya veri aktarımı gerektiriyorsa.
  - Satın alma kararı bir ekip/komite tarafından veriliyorsa (B2B SaaS).
  - Fiyat noktası yüksekse ($50+/ay).
  - *Deneme Süresi Standardı:* Basit ürünler için 7-14 gün, karmaşık entegrasyonlar için 14-30 gün.
- **Hibrit & Reverse Trial Modeli:** Kullanıcıya ilk 14 gün tüm Pro özellikler açık olarak başlatılır; deneme süresi bittiğinde hesap kilitlenmek yerine kısıtlı ücretsiz (Free) katmana düşürülür (Reverse Trial).

### 5. Fiyat Artışı İletişimi ve Dağıtım Metodolojisi
Fiyat artışı ani bir düğme değişimi değil, riskleri yönetilen bir süreçtir:
1. **Önce Yeni Müşterilerde Test Edin:** Fiyat artışını ilk olarak yalnızca yeni kayıt olan kullanıcılara uygulayın ve dönüşüm oranını izleyin. Yeni müşterilerin geçmiş fiyat çapası olmadığı için pazarın tepkisi temiz ölçülür.
2. **Sonsuz Grandfathering Tuzağına Düşmeyin:** Eski müşterileri sonsuza dek eski fiyatta tutmak şirket gelirini eritir. Eski müşterilere 3-6 aylık koruma (grace period) tanıyın; geçişi zamana yayın.
3. **Kademeli Geçiş:** Mevcut kullanıcıların ilk %5-10'luk grubunu yeni fiyata taşıyıp destek hacmini ve churn oranını gözlemleyin.
4. **Gerekçeyi Şeffafça Açıklayın:** Müşteriye fiyatın neden arttığını (eklenen onlarca yeni özellik, artan altyapı hızı, yeni AI yetenekleri) aylar öncesinden bildirin. "Yıllık plana geçerek eski fiyatı 1 yıl sabitleyin" teklifiyle kızgınlığı sadakate dönüştürün.

### 6. Pazarlama ve Büyüme (CRO) Çapraz Referansı
Fiyatlandırma sayfasının (Pricing page) dönüşüm oranı optimizasyonu (CRO), değer önerisi netliği, metin yazarlığı ve lansman stratejileri için `.agents/skills/pazarlama-ve-buyume/SKILL.md` rehberine başvurun. Van (finansal model ve katmanlar) ile Ankara (sayfa tasarımı, kancalar ve metin) fiyatlandırma projelerinde ortaklaşa çalışır.

### 7. Satış Üzerinden Kâr Marjı Formülü
- Satış fiyatı üzerinden marj isteniyorsa: fiyat = maliyet / (1 − marj). Maliyet × (1 + marj) düşük fiyat verir (%35 hedefte gerçek marj %25,9).

---

## R. Rehber, Belge (MarkItDown) ve Kitap Derleme (Book-to-Skill)

Kitapları, dokümanları ve rehberleri otonom ajan yeteneklerine ve token-tasarruflu başvuru kaynaklarına dönüştürme mimarisi `virgiliojr94/book-to-skill` ve Microsoft `markitdown` araçları üzerine kuruludur.

### 1. Çerçeve ve İlke Çıkarma Protokolü
1. **İçindekiler ve Yapı Haritası:** Kitabın/belgenin ana omurgası tespit edilir; temel modüller fihriste bağlanır.
2. **Çekirdek Çerçeveler (Frameworks):** Yazarın önerdiği karar mekanizmaları, formüller ve adım adım süreçler soyutlanır.
3. **Uygulanabilir İlkeler (Actionable Principles):** "Ne yapılmalı" ve "Ne yapılmamalı" kuralları net emir kipleriyle çıkarılır.
4. **Tuzaklar ve Anti-Kalıplar (Pitfalls):** En sık yapılan hatalar, kaçınılması gereken kalıplar ve nedenleri listelenir.
5. **Ses Kalibrasyonu (Voice Calibration):** Yazarın düşünme, değerlendirme ve iletişim tonu korunur.

### 2. Dört Çalışma Modu (Modes of Operation)
1. **Full Conversion (Varsayılan):** Kaynaktan tam bir ajan yeteneği paketi üretir (`SKILL.md`, `references/`, terimler sözlüğü, kalıplar ve hızlı başvuru kılavuzu).
2. **Analyze Only:** Kod/dosya üretmeden önce yapısal analiz raporu sunar (keşfedilen çerçeve, ilke ve teknikler).
3. **Generate from Prior Analysis:** Önceden hazırlanmış analiz raporunu girdi alarak skill dosyalarını üretir.
4. **Update / Fold-in:** Mevcut bir skill üzerine yeni dokümanları veya bölümleri birleştirir; dizin ve sözlükleri günceller.

### 3. Kedihane Uyarlaması
- Kedihane'de derlenen kitaplar ya doğrudan `.agents/skills/<skill-adi>/SKILL.md` olarak otonom yetenek haline getirilir ya da `bilgi/<alan>.md` altında katı alfabetik (`A-Z`) fihristli rehber dokümanına dönüştürülür.
- Teorik dolgu metinler ayıklanır; geliştiricinin kitaba tekrar bakmasına gerek bırakmayacak derinlikte ve doğrudan uygulanabilir kurallar korunur.

### 4. Microsoft MarkItDown ile Belgeleri Markdown'a Dönüştürme (`microsoft/markitdown`)
Kitaplar, araştırma raporları, finansal tablolar ve kurumsal dokümanlar genellikle PDF, DOCX, XLSX veya ses formatında gelir. Microsoft `markitdown` kütüphanesi, bu belgeleri LLM'lerin ve Book-to-Skill iş akışlarının doğrudan tüketebileceği token-tasarruflu Markdown formatına çevirir.

- **Kurulum:**
```bash
# Tüm dönüştürücüler ile kurulum
pip install 'markitdown[all]'

# Veya dosya türüne göre minimal kurulum:
pip install 'markitdown[pdf, docx, pptx, xlsx]'
```

- **CLI ile Tek Komutla Dönüştürme:**
```bash
# PDF dosyasını Markdown'a çevir
markitdown rapor.pdf -o rapor.md

# Excel tablosunu doğrudan Markdown çıktısı olarak al
markitdown bilanzo.xlsx > tablo.md

# Word (docx) veya PowerPoint (pptx) slaytlarını çevirme
markitdown sunum.pptx -o slaytlar.md

# Pipeline üzerinden standart girdi (stdin) ile çalıştırma
cat sozlesme.pdf | markitdown > ozet.md
```

- **Python SDK Kullanımı:**
```python
from markitdown import MarkItDown

# Standart dönüştürücü
md = MarkItDown(enable_plugins=False)
result = md.convert("finansal_tablo.xlsx")
print(result.markdown)

# Ses ve YouTube Transkripsiyonu
result_audio = md.convert("toplanti_kaydi.mp3")
print(result_audio.markdown)

# Vision LLM Destekli OCR (PDF/Görsel içindeki grafikleri ve metinleri okuma)
from openai import OpenAI

client = OpenAI()
md_ocr = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="gpt-4o"
)
result_scan = md_ocr.convert("taranmis_belge.pdf")
print(result_scan.markdown)
```

---

## V. Web Veri Kazıma (Scrapling) ve Otonom Tarayıcı (Browser-Use)

Klasik kazıma kütüphaneleri (Requests, BeautifulSoup) modern bot korumaları (Cloudflare Turnstile/Interstitial, DataDome, Akamai) karşısında engellenir. Kedihane standardı veri çekiminde **Scrapling** (`D4Vinci/Scrapling`), otonom kullanıcı gezinimi ve karmaşık web etkileşimlerinde ise **Browser-Use** (`browser-use/browser-use`) kütüphanesidir.

### 1. Fetcher Mimarisi ve Gerçek Sınıf Kullanımları (Scrapling)
Scrapling istekleri için iki temel sınıf ailesi kullanılır:
- **`Fetcher`:** Hızlı HTTP istekleri. TLS parmak izi taklidi (impersonate), HTTP/3 ve özel başlıklar sunar.
- **`StealthyFetcher` / `StealthySession`:** Gelişmiş bot korumalarını (Cloudflare vb.) aşmak için gizlenmiş Chromium/Chrome tarayıcı otomasyonu.

```python
from scrapling.fetchers import Fetcher, FetcherSession, StealthyFetcher, StealthySession

# 1. Hızlı HTTP İsteği (Tekil)
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()

# 2. Kalıcı HTTP Oturumu (Browser TLS Fingerprint Taklidi)
with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text').getall()

# 3. Anti-Bot ve Cloudflare Aşma (StealthyFetcher - Sınıf Metodu .fetch)
page = StealthyFetcher.fetch('https://target-site.com/protected', solve_cloudflare=True)
data = page.css('.content-item::text').getall()

# 4. Çok Adımlı Kalıcı Tarayıcı Oturumu (StealthySession)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://target-site.com/dashboard')
    results = page.css('.result-row::text').getall()
```

### 2. Parsel / Scrapy Uyumlu Seçiciler ve Gezinme API'si
Scrapling, Parsel/Scrapy sözdizimi ile zengin DOM gezinimini birleştirir:
- **CSS / XPath Çıkarımı:** `.css('h1::text').get()` (ilk eşleşen metin), `.getall()` (tüm liste), `.attrib['href']`.
- **BeautifulSoup Tarzı:** `page.find_all('div', class_='product')` veya `page.find_by_text('Fiyat')`.
- **İlişkisel DOM Gezinimi:** `first_item.next`, `first_item.parent`, `first_item.find_similar()`, `first_item.below_elements`.

### 3. LLM ve Ajanlar İçin Temiz Markdown Çıktısı
Scrapling sayfayı doğrudan LLM'e beslemeye hazır, temiz ve sterilize edilmiş Markdown'a dönüştürür:
```python
# Tek satırda LLM-ready temiz Markdown
markdown_text = page.markdown()
```

### 4. Ölçeklenebilir Spiders Mimarisi ve Duraklat/Devam Et (`crawldir`)
Büyük çaplı kazımalarda eşzamanlı `Spider` mimarisi kullanılır:
```python
from scrapling.spiders import Spider, Response

class ProductSpider(Spider):
    name = "products"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 5
    robots_txt_obey = True

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
            }
        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page)

# Pause & Resume: Ctrl+C ile güvenli durur, aynı crawldir ile kaldığı yerden devam eder
result = ProductSpider(crawldir="./crawl_checkpoint").start()
result.items.to_json("output.json")
```

### 5. Etik ve Güvenli Kazıma Kuralları
- `robots_txt_obey=True` ve `AutoThrottle` mekanizması kullanılarak hedef sunucu aşırı yüklenmemelidir.
- Proxy rotasyonu gerektiğinde `ProxyRotator` sınıfı oturumlara bağlanmalıdır.
- Kişisel veriler, şifreler veya gizli müşteri alanları asla taranmaz.

### 6. Browser-Use ile Otonom AI Tarayıcı Ajanı (`browser-use/browser-use`)
Statik kazımanın yetersiz kaldığı, karmaşık kullanıcı etkileşimleri (form doldurma, çok adımlı oturum açma, dinamik SPA siteleri, uçak/otel arama, sepet tamamlama) gerektiren senaryolarda `browser-use` Python kütüphanesi kullanılır.

- **Kurulum:**
```bash
pip install browser-use
# veya uv ile:
uv add browser-use
```

- **Python Asenkron Tarayıcı Ajanı Kodu:**
```python
import asyncio
from dotenv import load_dotenv
from browser_use import Agent, Browser
from browser_use import ChatOpenAI  # veya ChatBrowserUse

load_dotenv()

async def main():
    # LLM modeli seçimi (GPT-4o, Claude Sonnet 3.5 veya yerel model)
    llm = ChatOpenAI(model='gpt-4o')

    # Ajanı başlatma: Görev, model ve tarayıcı örneği
    agent = Agent(
        task="Trendyol veya Hepsiburada üzerinde 'mekanik klavye' ara, en yüksek puanlı ilk 3 ürünün adını ve fiyatını listele.",
        llm=llm,
        browser=Browser(headless=False)  # Görsel izleme için headless=False; sunucuda True
    )

    # Ajanı çalıştır ve sonucu al
    history = await agent.run()
    sonuc = history.final_result()
    print("Ajan Görev Sonucu:
", sonuc)

if __name__ == "__main__":
    asyncio.run(main())
```

- **Bulut ve Docker Desteği (Cloud Browser):**
Chrome kurulumu bulunmayan sunucularda veya CI/CD ortamlarında güncel `BrowserProfile` API'siyle `BROWSER_USE_API_KEY` üzerinden uzaktan yönetilen stealth bulut tarayıcıları devreye alınabilir:

```python
from browser_use import Browser, BrowserProfile

# Güncel browser-use Cloud Browser API'si
browser = Browser(browser_profile=BrowserProfile(use_cloud=True))
```
