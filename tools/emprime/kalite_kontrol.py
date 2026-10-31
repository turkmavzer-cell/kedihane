#!/usr/bin/env python3
"""Film ciktisi icin otomatik kalite kontrol. Karar rehberi bolum 7: bilgi/emprime-kanal-ayirma.md
Kullanim: python3 tools/kalite_kontrol.py cikti_klasoru [kaynak.png] [PPI=508]
cikti_klasoru: Acik_Tisort/*.png (1-bit, siyah=murekkep) + kanallar_hibrit.json
kaynak.png (istege bagli): ayni boyutta kaynak; varsa zit renk beneği (murekkep tonu kaynak tonundan >110 derece farkli) olculur, her renk cifti icin.
Cikis kodu 1 = uyari var. Esikler [yorum]; atolye testiyle ayarlanmali. Gozle dogrulamanin yerini TUTMAZ.
"""
import sys, os, json
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

d = sys.argv[1]; srcp = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].isdigit() else None
PPI_EXP = int(os.environ.get('PPI', 508))
J = json.load(open(os.path.join(d, 'kanallar_hibrit.json')))
SETN = os.environ.get('SET') or list(J['sets'])[0]; setn = SETN; sets = J['sets'][setn]
warn = []; info = []
films = []
for nm, fn, rgb in sets:
    im = Image.open(os.path.join(d, setn, fn))
    if im.mode != '1': warn.append(f'{fn}: 1-bit degil ({im.mode})')
    dp = im.info.get('dpi', (None,))[0]
    if dp is None or abs(dp-PPI_EXP) > 1: warn.append(f'{fn}: PPI meta {dp}, beklenen {PPI_EXP}')
    a = ~np.array(im.convert('1'))                         # True = murekkep
    films.append((nm, fn, rgb, a))
H, W = films[0][3].shape
for nm, fn, rgb, a in films:
    if a.shape != (H, W): warn.append(f'{fn}: boyut farkli {a.shape}')
info.append(f'boyut {W}x{H} px, {len(films)} film')

# kapsama
tot = H*W
for nm, fn, rgb, a in films:
    c = a.sum()/tot*100
    info.append(f'  {nm:<18} kapsama %{c:.2f}')
    if c < 0.5 and 'Fon' not in nm: warn.append(f'{nm}: kapsama %{c:.2f} <0,5 — neredeyse kullanilmayan murekkep (birlestir ya da atilacak kafa)')

# cakisma (indeks ayriminda 0 olmali)
for i in range(len(films)):
    for j in range(i+1, len(films)):
        ov = (films[i][3] & films[j][3]).sum()
        if 'Fon' in films[i][0] or 'Fon' in films[j][0] or J.get('lap_altlik'): continue   # lap_altlik: taban noktalarin altina bilerek uzanir   # fon (altlik) renklerin altinda olmali
        if ov > 0.001*min(films[i][3].sum(), films[j][3].sum()):
            warn.append(f'{films[i][0]} ile {films[j][0]} cakisiyor: {ov} px')

# izole kucuk noktalar
cell = PPI_EXP/45.0
tiny_area = max(3, int(0.03*cell*cell))                    # %3 nokta alani ~ 4 px (508 PPI, 45 lpi)
for nm, fn, rgb, a in films:
    nlab, lab, st, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8), connectivity=8)
    areas = st[1:, 4]
    tn = int((areas <= tiny_area).sum()); tot_n = len(areas)
    frac = tn/max(tot_n, 1)
    info.append(f'  {nm:<18} bilesen {tot_n}, <= {tiny_area}px olan {tn} (%{frac*100:.1f})')
    if frac > 0.10 and tn > 2000: warn.append(f'{nm}: %{frac*100:.0f} bilesen <= {tiny_area}px (elekte tutunmayacak mikro nokta)')

# duz (tramsiz) bolgeler: kenar pürüzlülügü + film rengi kaynak renge uyuyor mu (kanallar_hibrit.json 'duz_bolgeler', hibrit2.py yazar)
# Olcu (ayi, 2026-10-14): cikintili rozet 0,070, temiz lacivert yazi 0,006 px/px; esik 0,03. Acma (5 px elips) ile silinen piksel / acilmis kenar uzunlugu.
for w_ in J.get('uyarilar', []): warn.append(w_)
for dz in J.get('duz_bolgeler', []):
    fa = [f for f in films if f[1] == dz.get('film')]
    if not fa or not dz.get('bbox'): continue
    nm, fn, rgb, a = fa[0]; bx, by, bw, bh = dz['bbox']
    m = a[by:by+bh, bx:bx+bw].astype(np.uint8)
    mo = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cs, _ = cv2.findContours(mo, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); per = max(sum(len(c) for c in cs), 1)
    rough = float((m.sum()-mo.sum())/per)
    sl = cv2.cvtColor(np.array([[dz['kaynak_rgb']]], np.float32)/255, cv2.COLOR_RGB2Lab)[0, 0]
    il = cv2.cvtColor(np.array([[rgb]], np.float32)/255, cv2.COLOR_RGB2Lab)[0, 0]; de = float(np.linalg.norm(sl-il))
    info.append(f'  duz bolge {dz["ad"]:<10} film {nm}: kenar puruzlulugu {rough:.3f}, renk dE {de:.1f}')
    if rough > 0.03: warn.append(f'duz bolge {dz["ad"]} ({nm}): kenar cikinti/capakli (puruzluluk {rough:.3f} > 0,03); FLAT_R ile yumusat ya da kaynagi kontrol et')
    if de > 12: warn.append(f'duz bolge {dz["ad"]}: film rengi {nm} kaynak renkten dE {de:.0f} uzak (rozet/logo yanlis murekkebe gitmis olabilir)')

# zit renk beneği: murekkebin tonu, kaynak pikselin tonundan >110 derece farkliysa (genel kural, her renk cifti)
if srcp:
    src = np.array(Image.open(srcp).convert('RGB'))
    if src.shape[:2] != (H, W): warn.append('kaynak boyutu film boyutuyla ayni degil, zit renk kontrolu atlandi')
    else:
        f4 = 4; h4, w4 = H//f4, W//f4
        sl = cv2.cvtColor(cv2.GaussianBlur(cv2.resize(src, (w4, h4), interpolation=cv2.INTER_AREA), (0, 0), 3).astype(np.float32)/255, cv2.COLOR_RGB2Lab)
        sch = np.hypot(sl[..., 1], sl[..., 2]); shu = np.degrees(np.arctan2(sl[..., 2], sl[..., 1]))
        del src
        for nm, fn, rgb, a in films:
            il = cv2.cvtColor(np.array([[rgb]], np.float32)/255, cv2.COLOR_RGB2Lab)[0, 0]
            ch = float(np.hypot(il[1], il[2])); hu = float(np.degrees(np.arctan2(il[2], il[1])))
            if ch <= 5: continue                                # notr murekkep: tonu yok (soluk renkler DAHIL)
            cov = cv2.resize(a.astype(np.float32), (w4, h4), interpolation=cv2.INTER_AREA)
            dh = np.abs((shu-hu+180) % 360-180)
            bad = (sch > 8) & (dh > 90)
            if il[0] < 35: bad &= (sl[..., 0] > 55)             # en koyu: cizgide degil, acik/orta alanda ton koyulastirma
            frac = float((cov*bad).sum()/max(cov.sum(), 1e-6))
            info.append(f'  {nm:<18} kaynak tonuyla uyumsuz (>90 derece) murekkep payi %{frac*100:.2f}')
            esik = 0.03 if il[0] < 35 else 0.015                # en koyu: kontur payi dogal
            if frac > esik: warn.append(f'{nm}: murekkep payinin %{frac*100:.1f}i tonu uyumsuz kaynak alanda (zit renk beneği: orn. bej/kahve icinde mavi)')

print('\n'.join(info))
print()
if warn:
    print('UYARILAR:'); [print(' -', w) for w in warn]
    sys.exit(1)
print('Otomatik kontrol temiz. Yine de %100 kesit ve onizlemeyle gozle dogrula.')
