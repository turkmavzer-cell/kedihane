#!/usr/bin/env python3
"""Düz zeminli, çok renkli (sulu boya/illüstrasyon) motif desenini katmanlı PSD'ye ayırır.

Katmanlar (alttan üste): Zemin, renk aileleri (Pembe-Kirmizi, Turuncu-Sari, Yesil, Mavi-Turkuaz), Kontur (ince koyu çizgiler).
Kullanım: python3 tools/katman/motif_aile_katman.py girdi.png cikti.psd [--kontur 0|1]

Yöntem:
 1) Kontur: yerel medyandan (9 px) belirgin koyu ince çizgi -> alfa; kontur rengi Kp = (p - U(1-a))/a, U = konturun altındaki renk (medyan).
 2) Zemin ayrımı: zemin rengi = en sık renk; ön plan maskesi, kenar bandında (3 px) renk en yakın iç pikselden alınıp alfa en küçük kareyle hesaplanır.
 3) Aileler: ton (HSV hue) ile; düşük doygunluk ve kenar pikselleri en yakın güvenilir piksele; one-hot Gauss bulanıklığı + argmax ile lekesiz.
Katmanlar üst üste binince orijinal çıkar; fark raporlanır. Katman adları ASCII (psd-tools MacRoman).
"""
import argparse
from collections import Counter
import numpy as np, cv2
from PIL import Image
from psd_tools import PSDImage
from psd_tools.constants import Compression

AILE = ['Pembe-Kirmizi', 'Turuncu-Sari', 'Yesil', 'Mavi-Turkuaz']


def nearest_fill(val, valid):
    """valid olmayan piksellere en yakın valid pikselin değerini ver."""
    inv = (~valid).astype(np.uint8)
    _, lab = cv2.distanceTransformWithLabels(inv, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.where(valid)
    tab = np.zeros((lab.max() + 1,) + val.shape[2:], val.dtype)
    tab[lab[ys, xs]] = val[ys, xs]
    return tab[lab]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('girdi'); ap.add_argument('cikti'); ap.add_argument('--kontur', type=int, default=1)
    o = ap.parse_args()
    p8 = np.array(Image.open(o.girdi).convert('RGB'))
    H, W = p8.shape[:2]
    p = p8.astype(np.float32)
    # zemin
    cnt = Counter(map(tuple, (p8 // 4 * 4).reshape(-1, 3)))
    k0 = np.array(cnt.most_common(1)[0][0])
    bg = np.median(p8[np.abs(p8.astype(int) - k0).max(2) < 10].reshape(-1, 3), axis=0).astype(np.float32)
    # --- kontur
    L = cv2.cvtColor(p8, cv2.COLOR_RGB2GRAY).astype(np.float32)
    med = cv2.medianBlur(p8, 9).astype(np.float32)
    Lmed = cv2.cvtColor(med.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    dark = Lmed - L
    a_c = np.zeros((H, W), np.float32)
    if o.kontur:
        a_c = np.clip((dark - 14) / 40.0, 0, 1)
        a_c[np.abs(p - bg).max(2) < 8] = 0
        a_c = cv2.GaussianBlur(a_c, (0, 0), 0.6)
        a_c[a_c < 0.25] = 0           # düşük alfada bölme gürültüyü büyütür
    U = p.copy()
    cm = a_c > 0.02
    U[cm] = med[cm]
    ac3 = a_c[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        Kp = np.where(ac3 > 0.02, (p - U * (1 - ac3)) / np.maximum(ac3, 1e-3), 0)
    Kp = np.clip(Kp, 0, 255)
    # kırpılan kontur renginde alttaki rengi yeniden çöz: U = (p - Kp*a)/(1-a)
    re = (ac3 > 0) & (ac3 < 0.95)
    U2 = np.clip((p - Kp * ac3) / np.maximum(1 - ac3, 0.05), 0, 255)
    U = np.where(re, U2, U)
    # --- zemin ayrımı (U üzerinden)
    d = np.abs(U - bg).max(2)
    F = (d > 5).astype(np.uint8)
    interior = cv2.erode(F, np.ones((7, 7), np.uint8)).astype(bool)
    C = nearest_fill(U, interior)                          # ön plan rengi (kenarda iç renk)
    Cint = np.where(interior[..., None], U, C)
    dd = Cint - bg
    alpha = np.clip(((U - bg) * dd).sum(2) / np.maximum((dd * dd).sum(2), 1.0), 0, 1)
    alpha[interior] = 1.0
    alpha[(F == 0)] = 0
    alpha[alpha < 0.03] = 0
    # kenar pikselinde rengi kesin çöz: C = (U - bg(1-a))/a
    Cx = np.clip((U - bg * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 0.03), 0, 255)
    Cl = np.where(alpha[..., None] > 0, np.where(interior[..., None], U, Cx), 0)
    # --- aile sınıflama (Cl üzerinden)
    hsv = cv2.cvtColor(np.clip(Cl, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    h = hsv[..., 0] * 2.0; s = hsv[..., 1] / 255.0; v = hsv[..., 2] / 255.0
    fam = np.full((H, W), -1, np.int8)
    fam[(h >= 330) | (h < 14)] = 0
    fam[(h >= 14) & (h < 50)] = 1
    fam[(h >= 50) & (h < 165)] = 2
    fam[(h >= 165) & (h < 270)] = 3
    fam[(h >= 270) & (h < 330)] = 0
    conf = (alpha > 0.9) & (s > 0.28) & (v > 0.2)
    fam[~conf] = -1
    ok = fam >= 0
    famf = nearest_fill(fam.astype(np.int16)[..., None], ok)[..., 0].astype(np.int8)
    oh = np.stack([cv2.GaussianBlur((famf == k).astype(np.float32), (0, 0), 2.5) for k in range(4)], 0)
    fam = oh.argmax(0).astype(np.int8)
    # --- katmanlar
    layers = [('Zemin', np.dstack([np.tile(np.round(bg).astype(np.uint8), (H, W, 1)), np.full((H, W), 255, np.uint8)]))]
    comp = np.tile(bg, (H, W, 1)).astype(np.float32)
    stats = []
    for k, ad in enumerate(AILE):
        m = (fam == k) & (alpha > 0)
        A = np.where(m, alpha, 0)
        img = np.dstack([np.clip(np.round(Cl), 0, 255).astype(np.uint8), np.round(A * 255).astype(np.uint8)])
        layers.append((ad, img))
        comp = comp * (1 - A[..., None]) + Cl * A[..., None]
        stats.append((ad, float(m.mean())))
    if o.kontur:
        img = np.dstack([np.clip(np.round(Kp), 0, 255).astype(np.uint8), np.round(a_c * 255).astype(np.uint8)])
        layers.append(('Kontur', img))
        comp = comp * (1 - ac3) + Kp * ac3
    err = np.abs(comp - p).max(2)
    print('zemin', np.round(bg).astype(int).tolist(), 'aile payi', [(a, round(b, 3)) for a, b in stats])
    print(f'birlesik-orijinal fark: ort {err.mean():.2f}, max {err.max():.0f}, >6: %{100*(err>6).mean():.2f}, >20: %{100*(err>20).mean():.3f}')
    Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(o.cikti.replace('.psd', '_birlesik.png'))
    psd = PSDImage.new('RGB', (W, H), color=(255, 255, 255))
    for ad, im in layers:
        psd.create_pixel_layer(Image.fromarray(im, 'RGBA'), name=ad, top=0, left=0, compression=Compression.ZIP)
    psd.save(o.cikti)
    print('yazildi', o.cikti, [l.name for l in PSDImage.open(o.cikti)])


if __name__ == '__main__':
    main()
