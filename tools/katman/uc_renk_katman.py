#!/usr/bin/env python3
"""3 renkli (Acik Kahve zemin + Krem + Koyu Kahve) tekstil desenini 3 saf katmanli PSD'ye ayirir.

Kullanim:
  python tools/katman/uc_renk_katman.py girdi.jfif cikti.psd [--klasor cikti_klasoru]

Kurallar (bilgi/katman-ayirma.md):
  1) Her katman yalnizca kendi saf RGB rengini tasir (hicbir katmanda digerinin rengi kalmaz):
     - Acik_Kahve_Zemin: saf acik kahve (tam tuval opak zemin)
     - Krem: saf krem RGB + alt-piksel yumusak alfa (zemin ve koyu kahve bolgelerinde alfa = 0)
     - Koyu_Kahve: saf koyu kahve RGB + alt-piksel yumusak alfa (zemin ve krem bolgelerinde alfa = 0)
  2) Krem ve Koyu_Kahve ic gecislerinde 1px'lik ara sinir kapatilir (farkli zemin rengi denendiginde bosluk sizmaz).
  3) Katman adlari ASCII (psd-tools MacRoman uyumu).
"""
import argparse
import os
import cv2
import numpy as np
from PIL import Image
from psd_tools import PSDImage
from psd_tools.constants import Compression


def ayir_uc_renk(girdi_yolu, cikti_psd, cikti_klasor=None):
    im = Image.open(girdi_yolu).convert('RGB')
    p = np.array(im, dtype=np.float32)
    H, W = p.shape[:2]

    # 1. Saf renklerin (Zemin, Krem, Koyu Kahve) duz ic bolgelerden kestirimi
    gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY).astype(np.float32)
    local_mean = cv2.blur(gray, (7, 7))
    local_std = np.sqrt(np.maximum(cv2.blur(gray ** 2, (7, 7)) - local_mean ** 2, 0))
    L = p.mean(axis=2)
    rb = p[..., 0] - p[..., 2]

    bg_core = (local_std < 1.5) & (L > 95) & (L < 115)
    C_bg = np.median(p[bg_core], axis=0).astype(np.float32)

    cr_erode = cv2.erode((L > 205).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    C_cr = np.median(p[cr_erode], axis=0).astype(np.float32)

    # Koyu kahve ana kontur/govde rengi
    dk_core_px = (L >= 20) & (L <= 42)
    C_dk = np.median(p[dk_core_px], axis=0).astype(np.float32)

    # 2. Gecerli Krem bolgesi (histerezis + cicek mesafesi ile nokta/JPEG halkasi elenir)
    cc_num, cc_lab, cc_stats, _ = cv2.connectedComponentsWithStats((L > 175).astype(np.uint8), connectivity=8)
    big_mask = np.zeros(cc_num, dtype=bool)
    for i in range(1, cc_num):
        x, y, w, h, area = cc_stats[i]
        touch_border = (x == 0) or (y == 0) or (x + w >= W) or (y + h >= H)
        if area >= 18 or (touch_border and area >= 4):
            big_mask[i] = True
    big_cr = big_mask[cc_lab]
    dist_to_big_cr = cv2.distanceTransform((~big_cr).astype(np.uint8), cv2.DIST_L2, 5)

    cand_cr = ((L > 116) & (dist_to_big_cr <= 15)).astype(np.uint8)
    core_cr = ((L > 168) | ((L > 132) & (rb < 42))) & (dist_to_big_cr <= 14)
    num_c, lab_c, stats_c, _ = cv2.connectedComponentsWithStats(cand_cr, connectivity=8)
    keep_c = np.zeros(num_c, dtype=bool)
    np.logical_or.at(keep_c, lab_c[core_cr], True)
    keep_c[0] = False
    for i in range(1, num_c):
        if stats_c[i, cv2.CC_STAT_AREA] < 4:
            keep_c[i] = False
    valid_cr = keep_c[lab_c]
    valid_cr_dil = cv2.dilate(valid_cr.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)

    # 3. Gecerli Koyu Kahve bolgesi (histerezis ile zemin JPEG gurultusu elenir)
    cand_dk = (L < 95).astype(np.uint8)
    core_dk = (L < 75)
    num_d, lab_d, stats_d, _ = cv2.connectedComponentsWithStats(cand_dk, connectivity=8)
    keep_d = np.zeros(num_d, dtype=bool)
    np.logical_or.at(keep_d, lab_d[core_dk], True)
    keep_d[0] = False
    for i in range(1, num_d):
        if stats_d[i, cv2.CC_STAT_AREA] < 2:
            keep_d[i] = False
    valid_dk = keep_d[lab_d]
    valid_dk_dil = cv2.dilate(valid_dk.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)

    d_to_cr = cv2.distanceTransform((~valid_cr).astype(np.uint8), cv2.DIST_L2, 3)
    d_to_dk = cv2.distanceTransform((~valid_dk).astype(np.uint8), cv2.DIST_L2, 3)

    # 4. Renk dogrulari uzerine izdüsüm ve alt-piksel alfa hesabi
    v_bd = C_dk - C_bg
    t_bd = np.clip(((p - C_bg) @ v_bd) / np.dot(v_bd, v_bd), 0.0, 1.0)
    t_bd_solid = np.clip(t_bd / 0.88, 0.0, 1.0)

    v_bc = C_cr - C_bg
    t_bc = np.clip(((p - C_bg) @ v_bc) / np.dot(v_bc, v_bc), 0.0, 1.0)
    t_bc_solid = np.clip(t_bc / 0.94, 0.0, 1.0)

    v_dc = C_cr - C_dk
    t_dc = np.clip(((p - C_dk) @ v_dc) / np.dot(v_dc, v_dc), 0.0, 1.0)
    proj_dc = C_dk + t_dc[..., None] * v_dc
    err_dc = np.linalg.norm(p - proj_dc, axis=2)
    dist_bg = np.linalg.norm(p - C_bg, axis=2)

    a_cr = np.where(valid_cr_dil & (L > C_bg.mean()), t_bc_solid, 0.0)
    a_dk = np.where(valid_dk_dil & (L < C_bg.mean()), t_bd_solid, 0.0)

    # Cicek icindeki 1px'lik Krem <-> Koyu Kahve gecis sinirini kapat
    seam_cd = (
        (d_to_cr <= 2.0) & (d_to_dk <= 2.0) & ((d_to_cr + d_to_dk) <= 3.0) &
        (L >= 70.0) & (L <= 135.0) & (err_dc < dist_bg + 2.0)
    )
    a_cr[seam_cd] = np.maximum(a_cr[seam_cd], np.clip((t_dc[seam_cd] - 0.20) / (0.60 - 0.20), 0.0, 1.0))
    U = C_bg[None, None, :] * (1.0 - a_cr[..., None]) + C_cr[None, None, :] * a_cr[..., None]
    v_ud = C_dk[None, None, :] - U
    t_ud = np.clip(((p - U) * v_ud).sum(axis=2) / np.maximum((v_ud * v_ud).sum(axis=2), 1.0), 0.0, 1.0)
    a_dk[seam_cd] = np.maximum(a_dk[seam_cd], np.clip(t_ud[seam_cd] / 0.90, 0.0, 1.0))

    a_cr[a_cr < 0.05] = 0.0
    a_dk[a_dk < 0.05] = 0.0
    a_cr[a_cr > 0.96] = 1.0
    a_dk[a_dk > 0.96] = 1.0

    A_cr_u8 = np.round(a_cr * 255).astype(np.uint8)
    A_dk_u8 = np.round(a_dk * 255).astype(np.uint8)

    # 5. Katman RGBA goruntulerini olustur (her katmanda yalnizca kendi saf RGB rengi!)
    zemin_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    zemin_rgba[..., :3] = np.round(C_bg).astype(np.uint8)
    zemin_rgba[..., 3] = 255

    krem_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    krem_rgba[..., :3] = np.round(C_cr).astype(np.uint8)
    krem_rgba[..., 3] = A_cr_u8

    koyu_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    koyu_rgba[..., :3] = np.round(C_dk).astype(np.uint8)
    koyu_rgba[..., 3] = A_dk_u8

    katmanlar = [
        ('Acik_Kahve_Zemin', zemin_rgba),
        ('Krem', krem_rgba),
        ('Koyu_Kahve', koyu_rgba),
    ]

    # Birlesik goruntu dogrulamasi
    a_cr_f = A_cr_u8[..., None] / 255.0
    a_dk_f = A_dk_u8[..., None] / 255.0
    comp = np.round(C_bg) * (1.0 - a_cr_f) + np.round(C_cr) * a_cr_f
    comp = comp * (1.0 - a_dk_f) + np.round(C_dk) * a_dk_f
    err_max = np.abs(comp - p).max(axis=2)
    err_mean = np.abs(comp - p).mean()

    print(f'Boyut: {W}x{H}')
    print(f'Renkler (RGB): Acik_Kahve_Zemin={np.round(C_bg).astype(int).tolist()}, '
          f'Krem={np.round(C_cr).astype(int).tolist()}, Koyu_Kahve={np.round(C_dk).astype(int).tolist()}')
    print(f'Kapsama: Krem=%{100*(A_cr_u8>0).mean():.2f}, Koyu_Kahve=%{100*(A_dk_u8>0).mean():.2f}')
    print(f'Birlesik-orijinal fark: kanal ort={err_mean:.2f}, max-kanal ort={err_max.mean():.2f}')

    # PSD olustur
    psd = PSDImage.new('RGBA', (W, H))
    for ad, arr in katmanlar:
        psd.create_pixel_layer(Image.fromarray(arr, 'RGBA'), name=ad, top=0, left=0, compression=Compression.ZIP)

    os.makedirs(os.path.dirname(os.path.abspath(cikti_psd)), exist_ok=True)
    psd.save(cikti_psd)
    print('PSD yazildi:', cikti_psd, [l.name for l in PSDImage.open(cikti_psd)])

    if cikti_klasor:
        os.makedirs(cikti_klasor, exist_ok=True)
        for i, (ad, arr) in enumerate(katmanlar, start=1):
            Image.fromarray(arr, 'RGBA').save(os.path.join(cikti_klasor, f'{i:02d}_{ad}.png'))
        Image.fromarray(np.clip(np.round(comp), 0, 255).astype(np.uint8), 'RGB').save(
            os.path.join(cikti_klasor, '_birlesik_onizleme.png')
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('girdi', help='Girdi gorsel yolu')
    ap.add_argument('cikti_psd', help='Cikti PSD yolu')
    ap.add_argument('--klasor', default=None, help='Tekil PNG katmanlarin kaydedilecegi klasor')
    args = ap.parse_args()
    ayir_uc_renk(args.girdi, args.cikti_psd, args.klasor)


if __name__ == '__main__':
    main()
