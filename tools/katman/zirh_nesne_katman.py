#!/usr/bin/env python3
"""[ÖRNEK BETİK: Tekil zırh görseli tohum koordinatlarıyla çalışır]
Zirh illustrasyonunu NESNE katmanlarina (bilgi/katman-ayirma.md SOP) ayirir.

Kullanim: python tools/katman/zirh_nesne_katman.py girdi.jpg cikti_klasoru
Yontem: tohum noktalari (gosterim koordinati 1568 genislik) + gradyan uzerinde watershed
(dikdortgen/duz poligon kesim yok; sinirlar tasarimin dikis/kontur cizgilerini izler).
Zemin = alfa ile ayrilir; katmanlar ust uste binince orijinal cikar (olcum yazilir).
Katman adlari ASCII.
"""
import sys, os
import numpy as np, cv2
from PIL import Image
from skimage.segmentation import watershed

SC = 1696 / 1568.0  # tohum koordinatlari 1568 genislikli gorunume gore yazildi

# Katman sirasi: asagidan yukariya. Her katman: tohum listesi (x, y, yaricap)
LAYERS = [
    ("Gogus_Zirhi_ve_Boyunluk", [
        (780, 300, 14), (630, 420, 12), (940, 420, 12), (780, 520, 12), (590, 520, 12), (990, 520, 12),
        (430, 800, 14), (450, 960, 14), (1130, 800, 14), (1130, 960, 14),
        (400, 1180, 12), (1180, 1180, 12), (380, 1060, 10), (1200, 1060, 10),
        (560, 680, 10), (1020, 680, 10), (340, 420, 10), (1240, 420, 10), (520, 1050, 10), (1060, 1050, 10),
        (800, 1080, 8), (330, 1300, 10), (1250, 1300, 10)]),
    ("Karin_Zirhi_Plakalari", [
        (780, 1450, 16), (780, 1570, 12), (560, 1330, 10), (1000, 1330, 10),
        (400, 1410, 8), (400, 1520, 8), (1170, 1410, 8), (1170, 1520, 8),
        (655, 1250, 8), (905, 1260, 8), (410, 1612, 4), (1170, 1612, 4), (560, 1230, 8), (1020, 1230, 8), (520, 1480, 8), (1060, 1480, 8)]),
    ("Kemer", [
        (370, 1790, 14), (1190, 1790, 14), (420, 1655, 6), (1130, 1655, 6), (330, 1880, 6), (1230, 1900, 6)]),
    ("Kemer_Tokasi", [
        (780, 2000, 14), (780, 1870, 10), (650, 1750, 6), (910, 1750, 6), (640, 1940, 6), (930, 1940, 6),
        (780, 2120, 6), (610, 1900, 8), (960, 1900, 8)]),
    ("Omuzluklar", [
        (160, 640, 14), (250, 540, 8), (150, 430, 6), (360, 420, 10), (170, 880, 10), (400, 520, 8),
        (1410, 640, 14), (1320, 540, 8), (1420, 430, 6), (1210, 420, 10), (1410, 880, 10), (1170, 520, 8),
        (130, 740, 6), (1440, 740, 6)]),
    ("Zincir_ve_Yildizlar", [
        (700, 1000, 5), (960, 960, 5), (790, 1110, 4), (580, 840, 5), (1010, 840, 5), (565, 925, 4),
        (1015, 930, 4), (640, 1130, 5)]),
    ("Iskelet_Kafalari", [
        (790, 780, 14), (790, 880, 10), (540, 640, 8), (1050, 650, 8), (790, 610, 4),
        (790, 1290, 10), (690, 1165, 3), (895, 1165, 3), (790, 1060, 5), (790, 1900, 12), (780, 1770, 10)]),
    ("Goz_Isiklari", []),  # kirmizi parlak piksellerden
]


def main(src, out):
    os.makedirs(out, exist_ok=True)
    im = np.array(Image.open(src).convert("RGB"))
    H, W = im.shape[:2]
    f = im.astype(np.float32)
    lum = f.max(2)

    # on plan: siyah arka plandan ayir (alfa, yumusak kenar)
    fg = (lum > 28).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    keep = np.zeros_like(fg)
    for i in range(1, n):
        if st[i, 4] > 1500:
            keep[lab == i] = 1
    # ic bosluklar (agiz ici vb.) on plana dahil
    cnt, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    body = np.zeros_like(keep)
    cv2.drawContours(body, cnt, -1, 1, -1)
    body = body.astype(bool)

    # goz isigi: parlak doygun kirmizi
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    eye = (r > 200) & (g < 90) & (b < 90)
    eye = cv2.morphologyEx(eye.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(eye)
    eyem = np.zeros_like(eye)
    for i in range(1, n):
        if st[i, 4] > 400 and st[i, 1] < 1000 * SC:
            eyem[lab == i] = 1
    eyem = cv2.dilate(eyem, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)

    # yükseklik haritasi: gradyan + koyu konturlar
    sm = cv2.GaussianBlur(f, (0, 0), 1.5)
    gx = cv2.Sobel(sm, cv2.CV_32F, 1, 0); gy = cv2.Sobel(sm, cv2.CV_32F, 0, 1)
    grad = np.sqrt((gx ** 2 + gy ** 2).sum(2))
    dark = np.clip(60 - cv2.GaussianBlur(lum, (0, 0), 1.2), 0, None) * 4  # koyu cizgiler = yuksek
    elev = grad + dark

    markers = np.zeros((H, W), np.int32)
    for li, (name, seeds) in enumerate(LAYERS, start=1):
        for (x, y, rr) in seeds:
            cv2.circle(markers, (int(x * SC), int(y * SC)), int(rr * SC), li, -1)
    markers[eyem] = len(LAYERS)
    markers[~body] = 0
    seg = watershed(elev, markers, mask=body)
    seg[eyem] = len(LAYERS)
    np.save(os.path.join(out, "seg.npy"), seg.astype(np.uint8))

    pal = np.array([[0, 0, 0], [200, 160, 40], [40, 160, 220], [60, 200, 60], [230, 60, 200],
                    [240, 130, 30], [255, 255, 255], [160, 60, 255], [255, 0, 0]], np.uint8)
    prev = (0.5 * im + 0.5 * pal[seg]).astype(np.uint8)
    Image.fromarray(prev).save(os.path.join(out, "onizleme_segment.jpg"), quality=88)

    # --- PSD: Zemin (orijinal) + nesne katmanlari (alt -> ust) ---
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    psd = PSDImage.new("RGB", (W, H))
    psd.append(PixelLayer.frompil(Image.fromarray(im).convert("RGBA"), psd, "Zemin", 0, 0))
    acc = im.astype(np.float32).copy(); cov = np.zeros((H, W), np.float32)
    for li, (name, _) in enumerate(LAYERS, start=1):
        m = (seg == li)
        if name == "Iskelet_Kafalari":
            m = m | eyem  # kafatasi tam olsun (SOP: ici delik birakma)
        a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.7)
        a = np.where(m, np.maximum(a, 0.5), a)
        a = np.clip(a * 1.0, 0, 1)
        a[~body] = 0
        rgba = np.dstack([im, (a * 255).astype(np.uint8)])
        Image.fromarray(rgba, "RGBA").save(os.path.join(out, f"{li:02d}_{name}.png"))
        psd.append(PixelLayer.frompil(Image.fromarray(rgba, "RGBA"), psd, name, 0, 0))
        acc = acc * (1 - a[..., None]) + im * a[..., None]
        cov = cov + a - cov * a
    comp = acc  # alttan: Zemin katmani (orijinal)
    err = np.abs(comp - im.astype(np.float32)).mean() / 255
    print("Birlesim hatasi (ort, 0-1): %.5f" % err)
    psd.save(os.path.join(out, "armor_katmanli.psd"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])



