#!/usr/bin/env python3
"""Düz zemin + tek renkli desen (ör. zigzag/üçgen doku) görselini katmanlı PSD'ye ayırır.

Kullanım:
  python3 tools/katman/zemin_desen_katman.py girdi.png cikti.psd [--mod 2|3] [--zemin R,G,B --desen R,G,B] [--esik 0.98]

Yöntem (katmanlar üst üste binince orijinal çıkar):
  piksel = zemin*(1-a) + desen*a  ->  a = <p-zemin, desen-zemin> / |desen-zemin|^2  (en küçük kareler)
  zemin ve desen rengi verilmezse en sık iki renk alınır (en sık = zemin, en sık ikinci belirgin renk = desen).

Modlar:
  2: Zemin + Desen (alfa kanalı geçişleri saydam taşır)  -> kullanıcının "doğru oldu" dediği düzen
  3: Zemin + Desen (tam opak, a>=esik) + Geçiş (kısmi saydam, 0<a<esik)

Gerekli: numpy, Pillow, psd-tools. Katman adları ASCII olmalı (psd-tools MacRoman).
"""
import argparse
from collections import Counter
import numpy as np
from PIL import Image
from psd_tools import PSDImage


def renk_bul(a):
    c = Counter(map(tuple, (a // 4 * 4).reshape(-1, 3)))  # 4'lük kutular: gürültüyü topla
    top = [k for k, _ in c.most_common(40)]
    zemin = np.array(top[0], float)
    for k in top[1:]:
        if np.linalg.norm(np.array(k, float) - zemin) > 120:
            ks = [p for p in a.reshape(-1, 3)[:: max(1, a.size // 3 // 200000)]
                  if np.linalg.norm(p - np.array(k)) < 8]
            desen = np.mean(ks, axis=0) if ks else np.array(k, float)
            break
    else:
        raise SystemExit('Belirgin ikinci renk bulunamadi')
    # zemin icin de gercek ortalama
    zs = [p for p in a.reshape(-1, 3)[:: max(1, a.size // 3 // 200000)] if np.linalg.norm(p - zemin) < 8]
    return (np.mean(zs, axis=0) if zs else zemin), desen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('girdi'); ap.add_argument('cikti')
    ap.add_argument('--mod', type=int, default=2, choices=[2, 3])
    ap.add_argument('--zemin'); ap.add_argument('--desen')
    ap.add_argument('--esik', type=float, default=0.98)
    o = ap.parse_args()
    im = Image.open(o.girdi).convert('RGB')
    a = np.array(im).astype(float)
    H, W = a.shape[:2]
    if o.zemin and o.desen:
        bg = np.array([float(x) for x in o.zemin.split(',')]); pk = np.array([float(x) for x in o.desen.split(',')])
    else:
        bg, pk = renk_bul(a)
    d = pk - bg
    al = np.clip(((a - bg) @ d) / (d @ d), 0, 1)
    al[al < 0.02] = 0; al[al > 0.98] = 1
    A = np.round(al * 255).astype(np.uint8)
    bgi = np.zeros((H, W, 4), np.uint8); bgi[..., :3] = np.round(bg).astype(np.uint8); bgi[..., 3] = 255

    def desen_katman(alfa):
        L = np.zeros((H, W, 4), np.uint8); L[..., :3] = np.round(pk).astype(np.uint8); L[..., 3] = alfa; return L

    katmanlar = [('Zemin', bgi)]
    if o.mod == 2:
        katmanlar.append(('Desen', desen_katman(A)))
    else:
        t = int(round(o.esik * 255))
        katmanlar.append(('Desen opak', desen_katman(np.where(A >= t, A, 0).astype(np.uint8))))
        katmanlar.append(('Gecis saydam', desen_katman(np.where((A > 0) & (A < t), A, 0).astype(np.uint8))))

    comp = bg.copy()[None, None, :].repeat(H, 0).repeat(W, 1)
    for ad, L in katmanlar[1:]:
        aa = L[..., 3:4] / 255.
        comp = comp * (1 - aa) + L[..., :3] * aa
    err = np.abs(comp - a).max(2)
    print(f'zemin={np.round(bg).astype(int).tolist()} desen={np.round(pk).astype(int).tolist()}')
    print(f'birlesik-orijinal fark: max {err.max():.1f}, ort {err.mean():.2f}, >6 olan piksel %{100*(err>6).mean():.2f}')
    psd = PSDImage.new('RGB', (W, H), color=(255, 255, 255))
    for ad, L in katmanlar:
        psd.create_pixel_layer(Image.fromarray(L), name=ad, top=0, left=0)
    psd.save(o.cikti)
    print('yazildi:', o.cikti, [l.name for l in PSDImage.open(o.cikti)])


if __name__ == '__main__':
    main()
