# Bombay — Hafıza

En fazla 100 satır. Dersler sektör/iş başlıklarına göre alfabetik sıralıdır.
Her ders tek satır ve tarihli: `- YYYY-AA-GG: ders`.
Yeni dersler doğrudan ilgili alt başlığın altına eklenir; alt başlık yoksa alfabetik sırayı bozmadan yeni başlık açılır.

## Dersler (Alfabetik Sektör / İş Sırası)

### Algoritmalar ve Optimizasyon
- 2026-10-19: Mürekkep renkleri biliniyorsa alfayı palet izdüşümüyle hesapla (α=⟨c−b,Fk−b⟩/|Fk−b|²); Color to Alpha en küçük alfayı seçtiği için düz mürekkepte α<1 kalır.
- 2026-10-20: Kısıtlı en küçük kareler (w≥0, Σw=1) için alt küme sayımı + ceza yöntemi 3–4 mürekkepte hızlı ve kararlı; kod `bilgi/katman-ayirma.md` B ve H bölümleri.
- 2026-10-20: Kontur oturtma yarıçapını morfolojik konturdan değil geçişin %50 noktalarından ölç.

### Görüntü İşleme ve PSD
- 2026-10-19: Color to Alpha kendi zemininde her zaman hata 0 verir (yanıltıcı); doğruluğu koyu bir zemine bindirerek ölç.
- 2026-10-19: psd-tools 1.25'te RGBA katmanlı PSD için `PSDImage.new("RGBA", ...)` kullan; `"RGB"` ile alfa katman maskesine gider.
- 2026-10-19: Alfalı görseli yalnız premultiplied uzayda ölç/ölçekle/bulanıklaştır; straight alfayla kenarda 49 seviyeye kadar hale oluşur.
- 2026-10-20: Büyük PSD'de kanalları RLE satır tablosundan seyrek oku, tam tuvali belleğe açma; PPI = ham değer/65536.
- 2026-10-20: Tram frekansı/açısı kırpmanın FFT tepe noktasından ölçülür (lpi = PPI × frekans).

### Ortam ve Paket Yönetimi
- 2026-10-19: Sandbox'ta `pip install --break-system-packages <paket>` çalışır; ağ yalnız paket kayıtlarına açık.

### Tarayıcı ve Web Otomasyonu
- 2026-10-21: DOM'da input[type=file] açmayan ataç butonlarında HTMLInputElement.prototype.click metodunu yamalayarak geçici file input'u DOM'a ekle ve işlem öncesi eski input'ları temizle.
- 2026-10-24: Çoklu mesaj/ek otomasyonunda sol listeden konuşmaya tıkladıktan sonra üst başlık (header) adını doğrula; ek kutusunda dosya zaten varsa tekrar ekleme ve Gönder butonu aktif/siyah olmadan tıklama.
