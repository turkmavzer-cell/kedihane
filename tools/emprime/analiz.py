#!/usr/bin/env python3
"""Ayrima baslamadan once gorsel on analizi. Karar rehberi: bilgi/emprime-kanal-ayirma.md
Kullanim: python3 tools/analiz.py girdi.png [maske.png]   (maske varsa yalnizca figur analiz edilir)
Cikti: terminalde rapor + (varsa) girdi yanina <ad>_analiz.json.
Hicbir sey uretmez, yalnizca olcer. Esikler [yorum]: gercek isle test edilmeli.
"""
import sys, os, json
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

path = sys.argv[1]; mpath = sys.argv[2] if len(sys.argv) > 2 else None
im0 = Image.open(path); dpi = im0.info.get('dpi', (None, None))[0]
W0, H0 = im0.size; mode = im0.mode
rgba = np.array(im0.convert('RGBA')); has_alpha = bool((rgba[..., 3] < 250).mean() > 0.001)
rgb = rgba[..., :3]
S = min(1.0, 2200/max(W0, H0)); sm = cv2.resize(rgb, (int(W0*S), int(H0*S)), interpolation=cv2.INTER_AREA)
h, w = sm.shape[:2]
if mpath:
    m = cv2.resize(cv2.imread(mpath, 0), (w, h), interpolation=cv2.INTER_NEAREST) > 127
else:
    m = np.ones((h, w), bool)
R = {}
R['dosya'] = os.path.basename(path); R['boyut_px'] = [W0, H0]; R['mod'] = mode; R['dpi_meta'] = dpi; R['seffaflik_kullaniliyor'] = has_alpha
ppi = dpi or 508
R['baski_cm'] = [round(W0/ppi*2.54, 1), round(H0/ppi*2.54, 1)]
R['uyari'] = []
if dpi is None: R['uyari'].append('DPI meta yok; 508 varsayildi')
elif abs(dpi-508) > 1: R['uyari'].append(f'DPI {dpi}; proje standardi 508')
if W0/ppi*2.54 < 20: R['uyari'].append('baski genisligi 20 cm altinda mi? kontrol et')

lab = cv2.cvtColor(sm.astype(np.float32)/255, cv2.COLOR_RGB2Lab)
L = lab[..., 0]
# kagit beyaz noktasi: figur disi (maske varsa), yoksa kenar seridi
if mpath:
    bgm = ~cv2.dilate(m.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)
else:
    bgm = np.zeros((h, w), bool); e = max(4, h//50); bgm[:e] = bgm[-e:] = True; bgm[:, :e] = bgm[:, -e:] = True
bgpix = sm[bgm]
wp = np.percentile(bgpix, 60, axis=0) if len(bgpix) > 500 else np.array([255, 255, 255.0])
R['kagit_beyaz_noktasi_rgb'] = [int(x) for x in wp]
if wp.min() < 235: R['uyari'].append('kagit/zemin beyaz degil (%s): beyaza normalize edilmeli' % [int(x) for x in wp])
# zemin tipi: kenar bolgesinde doku
bgL = L[bgm]
if len(bgL) > 500:
    R['zemin_L_std'] = round(float(bgL.std()), 2)
    if bgL.std() > 1.2: R['uyari'].append('zeminde doku/leke var (kagit dokusu ya da firca): basilacaksa tram ister, degilse maskele')

# duz alan / doku orani (yerel Lab std, 5x5)
mu = cv2.blur(lab, (5, 5)); mu2 = cv2.blur(lab*lab, (5, 5)); sd = np.sqrt(np.maximum(mu2-mu*mu, 0).sum(2))
flat = (sd < 2.0)&m; tex = (sd >= 2.0)&(sd < 8.0)&m; edge = (sd >= 8.0)&m
n = max(m.sum(), 1)
R['duz_oran'] = round(float(flat.sum()/n), 3); R['doku_oran'] = round(float(tex.sum()/n), 3); R['kenar_oran'] = round(float(edge.sum()/n), 3)

# palet: k-means 12, kapsama
pix = lab[m].reshape(-1, 3); idx = np.random.RandomState(0).permutation(len(pix))[:80000]
cv2.setRNGSeed(0)
K = 12
_, lb, cen = cv2.kmeans(pix[idx].astype(np.float32), K, None, (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
cnt = np.bincount(lb.ravel(), minlength=K)/len(idx)
order = np.argsort(-cnt)
cols = cv2.cvtColor(cen.reshape(1, -1, 3).astype(np.float32), cv2.COLOR_Lab2RGB).reshape(-1, 3)
R['palet_k12'] = [{'rgb': [int(c*255) for c in cols[i]], 'kapsama_%': round(float(cnt[i]*100), 2)} for i in order]
R['gercek_renk_tahmini(>=1%)'] = int((cnt >= 0.01).sum())
kucuk = [i for i in order if cnt[i] < 0.01]
if kucuk: R['uyari'].append(f'{len(kucuk)} palet rengi <%1 kapsama: birlestirilebilir ya da ince detay (kirpik/gozluk) olabilir')

# ince detay: koyu cizgi kalinligi
dark = ((L < 40)&m).astype(np.uint8)
if dark.sum() > 50:
    dist = cv2.distanceTransform(dark, cv2.DIST_L2, 3)
    skel_w = dist[dist > 0]
    cell_px_full = ppi/45.0                                  # 45 lpi hucre (tam cozunurluk px)
    wid_px_full = (2*np.percentile(skel_w, 50))/S
    R['koyu_detay_medyan_kalinlik_mm'] = round(float(wid_px_full/ppi*25.4), 3)
    R['tram_hucre_mm(45lpi)'] = round(25.4/45, 3)
    if wid_px_full < cell_px_full*0.6: R['uyari'].append('koyu ince detay 45 lpi hucrenin ~%60i altinda: tramli ekranda kopabilir')

# JPEG blokluluk (8x8 sinir sureksizligi)
g = cv2.cvtColor(rgb[:min(H0, 4000), :min(W0, 4000)], cv2.COLOR_RGB2GRAY).astype(np.float32)
dx = np.abs(np.diff(g, axis=1)); b = dx[:, 7::8].mean(); o = dx.mean()
R['jpeg_blok_orani'] = round(float(b/max(o, 1e-6)), 3)
if b/max(o, 1e-6) > 1.08: R['uyari'].append('8x8 blok sinirlari belirgin: JPEG artefakti olabilir (netlestirme/temizleme)')

# kenar halesi (cok kaba): figur kenarinda doygunlugu farkli ince halka
# oneri
oner = []
if R['duz_oran'] > 0.85 and R['doku_oran'] < 0.08: oner.append('Duz renkli: tramsiz spot')
elif R['doku_oran'] > 0.25 or R['kenar_oran'] > 0.25: oner.append('Dokulu/boyama: AM tram + cakismasiz karisim (45 lpi); mürekkep sayisi kafa sayisina gore')
else: oner.append('Karma: duz alanlar tramsiz, gecisler tramli (hibrit)')
if R['gercek_renk_tahmini(>=1%)'] > 8: oner.append('Gercek renk 8den fazla: atolye kafa sayisini sor, birlestirme gerekir')
R['oneri'] = oner
R['sorulacaklar'] = ['Tisort rengi (acik/koyu/ikisi)?', 'Kac murekkep (kafa sayisi)?', 'Zemin/firca darbeleri basilsin mi?']

print(json.dumps(R, ensure_ascii=False, indent=1))
open(os.path.splitext(path)[0]+'_analiz.json', 'w').write(json.dumps(R, ensure_ascii=False, indent=1)) if os.access(os.path.dirname(os.path.abspath(path)), os.W_OK) else None
