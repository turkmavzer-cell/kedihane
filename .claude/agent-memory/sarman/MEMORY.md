# Sarman — Hafıza

> Biçim ve kurallar: `bilgi/HARITA.md` Ekleme Prosedürü.

## Dersler (Alfabetik Sektör / İş Sırası)

### Denetim araçları
- 2026-11-02: Otomatik düzeltici (ör. fihrist aralığı) öğeleri sıraya göre eşleştiriyorsa geçici kopyada sıra hatası enjekte et; sessizce yanlış düzeltip denetimi geçirebilir.

### Git kancaları
- 2026-11-02: Yeni hook dosyasının exec bit'ini kontrol et; 644 ise git kancayı uyarıyla atlar (Linux'ta sınandı). LF satır sonu için `.gitattributes` olup olmadığına bak.
