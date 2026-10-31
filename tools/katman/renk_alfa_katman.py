#!/usr/bin/env python3
"""Açık zeminli sulu boya/leke desenini katmanlara ayırır (renk-alfa): Zemin + Bej yikama + Gri-siyah leke.

Kullanım: python3 tools/katman/renk_alfa_katman.py girdi.tif cikti_klasoru [--sicak 20]

Yöntem:
 1) Zemin rengi = her kanalın yüksek yüzdelik değeri (kâğıt rengi), düz katman.
 2) Color-to-alpha: a = max_c (zemin_c - p_c)/zemin_c ; renk C = (p - zemin(1-a))/a  (piksel = zemin(1-a)+C·a).
 3) Aile: (R-B) sıcaklığı yerelde yumuşatılıp eşiklenir (>eşik = bej, değilse gri-siyah); her piksel tek aileye gider,
    bu yüzden katmanlar üst üste binince orijinal çıkar (fark raporlanır).
Çıktı: cikti_klasoru/Katmanli.psd + her katman PNG (ASCII adlar).
"""
import argparse, os
import numpy as np, cv2
from PIL import Image
from psd_tools import PSDImage
from psd_tools.constants import Compression


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('girdi'); ap.add_argument('cikti')
    ap.add_argument('--sicak', type=float, default=20.0)
    ap.add_argument('--yuzdelik', type=float, default=96.0)
    o = ap.parse_args()
    os.makedirs(o.cikti, exist_ok=True)
    im = Image.open(o.girdi).convert('RGB'); p = np.array(im).astype(np.float32); H, W = p.shape[:2]
    bg = np.array([np.percentile(p[..., c], o.yuzdelik) for c in range(3)], np.float32)
    a = np.clip(((bg - p) / bg).max(2), 0, 1)
    a[a < 0.01] = 0
    a3 = a[..., None]
    C = np.where(a3 > 0, np.clip((p - bg * (1 - a3)) / np.maximum(a3, 0.01), 0, 255), 0)
    warm = cv2.GaussianBlur(p[..., 0] - p[..., 2], (0, 0), 1.5)
    bej = warm > o.sicak
    # düşük alfalı pikseller komşu aileyi alır (gürültüye karşı yumuşatma)
    m = cv2.GaussianBlur(bej.astype(np.float32), (0, 0), 2.0) > 0.5
    fam_bej = m & (a > 0)
    fam_ink = (~m) & (a > 0)
    layers = [('Zemin', np.dstack([np.tile(np.round(bg).astype(np.uint8), (H, W, 1)), np.full((H, W), 255, np.uint8)]))]
    comp = np.tile(bg, (H, W, 1))
    st = []
    for ad, mk in (('Bej yikama', fam_bej), ('Gri-siyah leke', fam_ink)):
        A = np.where(mk, a, 0)
        img = np.dstack([np.round(C).astype(np.uint8), np.round(A * 255).astype(np.uint8)])
        layers.append((ad, img))
        comp = comp * (1 - A[..., None]) + C * A[..., None]
        st.append((ad, round(float(mk.mean()), 3)))
    err = np.abs(comp - p).max(2)
    print('zemin', np.round(bg).astype(int).tolist(), 'pay', st)
    print(f'birlesik-orijinal fark: ort {err.mean():.2f}, max {err.max():.0f}, >6: %{100*(err>6).mean():.2f}')
    psd = PSDImage.new('RGB', (W, H), color=(255, 255, 255))
    for i, (ad, img) in enumerate(layers):
        Image.fromarray(img, 'RGBA').save(os.path.join(o.cikti, f'{i:02d}_{ad.replace(" ", "_")}.png'))
        psd.create_pixel_layer(Image.fromarray(img, 'RGBA'), name=ad, top=0, left=0, compression=Compression.ZIP)
    out = os.path.join(o.cikti, 'Katmanli.psd'); psd.save(out)
    print('yazildi', out, [l.name for l in PSDImage.open(out)])
    Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(os.path.join(o.cikti, '_birlesik_kontrol.png'))


if __name__ == '__main__':
    main()
