#!/usr/bin/env python3
"""IKI ASAMALI YONTEM - 2. ASAMA: kullanicinin duzenleyip onayladigi onizleme PNG'sinden filmleri cikarir.
Aciklama: bilgi/emprime-kanal-ayirma.md

Kullanim:
  python3 tools/onizlemeden_ayir.py duzenlenmis.png cikti_klasoru acik|koyu [onizleme_palet.json] [tisort_rgb]
    acik : beyaz/acik tisort. Beyaz (tisort rengi) piksel = murekkep yok; diger her renk = bir film.
    koyu : koyu tisort. Tisort rengi = murekkep yok; beyaz = yalniz fon; diger renk = film (+ altinda fon).
           Fon = tisort rengi olmayan her yer, en koyu murekkebin alti haric, disa bakan kenarda CHOKE_PX choke.
    onizleme_palet.json (1. asamanin ciktisi) verilirse tisort rengi oradan alinir; yoksa tisort_rgb (orn. 30,30,30)
    ya da acik icin 255,255,255.
Env: LAP_ALTLIK(0): 1 ise "lap" = tramli koyu noktalarin altina daha acik taban murekkep filmi uzar (ust uste baski). LAP_WIN(9) LAP_MIN(0.15)
     PPI(508) MINW(3) MINPX(4) CHOKE_PX(4) MAXRENK(6, uyari icin) DE_TOL(3: bu kadar yakin renkler ayni murekkep)

Kurallar:
- Her farkli renk bir murekkep/film. Kullanicinin degistirdigi renk (Color Table) yeni murekkep rengi olur.
- Cok az pikselli (toplamin %0,05'inden az) renkler kenar yumusatma artigi sayilir, en yakin renge atanir ve raporlanir.
- Ince capak (MINW) ve mikro parca (MINPX) temizlenir.
- Cikti tek asamali yontemle ayni: <set>/NN_Ad.png (1-bit, siyah = murekkep, 508 PPI) + kanallar_hibrit.json;
  PSD icin tools/photoshop/psd_olustur_tek_adim.jsx ayni klasore kopyalanip Photoshop'ta calistirilir.
"""
import sys, os, json
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

inp, out_dir, tur = sys.argv[1], sys.argv[2], sys.argv[3].lower()
palj = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4].endswith('.json') else None
rgb_arg = [a for a in sys.argv[4:] if ',' in a and not a.endswith('.json')]
E = os.environ.get
PPI = int(E('PPI', 508)); MINW = int(E('MINW', 3)); MINPX = int(E('MINPX', 4)); CHOKE = int(E('CHOKE_PX', 4))
MAXRENK = int(E('MAXRENK', 6)); DE_TOL = float(E('DE_TOL', 3))
assert tur in ('acik', 'koyu'), 'tur: acik ya da koyu'
setn = 'Acik_Tisort' if tur == 'acik' else 'Koyu_Tisort'

shirt = np.array([255, 255, 255]) if tur == 'acik' else np.array([30, 30, 30])
if palj:
    pj = json.load(open(palj)).get('onizleme', {}).get(setn)
    if pj: shirt = np.array(pj['tisort_rgb'])
if rgb_arg: shirt = np.array([int(v) for v in rgb_arg[0].split(',')])

im = Image.open(inp)
dpi = im.info.get('dpi', (None,))[0]
rgb = np.array(im.convert('RGB')); H, W = rgb.shape[:2]
print(f'girdi {W}x{H}, dpi {dpi}, tur {tur}, tisort rengi {shirt.tolist()}')
if dpi is None or abs(dpi-PPI) > 1: print(f'UYARI: dpi {dpi}, beklenen {PPI} (goruntu yeniden boyutlandirilmis olabilir)')

# renkleri say
code = (rgb[..., 0].astype(np.int32) << 16) | (rgb[..., 1].astype(np.int32) << 8) | rgb[..., 2]
u, inv, cnt = np.unique(code.ravel(), return_inverse=True, return_counts=True)
cols = np.stack([(u >> 16) & 255, (u >> 8) & 255, u & 255], 1)
tot = H*W
ana = cnt >= 0.0005*tot
print(f'farkli renk {len(u)}; ana renk {ana.sum()}, artik (kenar yumusatma vb.) renk {(~ana).sum()} / {int(cnt[~ana].sum())} px')
lab = cv2.cvtColor(cols.astype(np.float32).reshape(-1, 1, 3)/255, cv2.COLOR_RGB2Lab).reshape(-1, 3)
# birbirine cok yakin ana renkleri birlestir (Photoshop renk tablosu yuvarlamasi)
ai = list(np.where(ana)[0][np.argsort(-cnt[ana])])
temsil = {}
for i in ai:
    hit = [j for j in temsil.values() if np.linalg.norm(lab[i]-lab[j]) < DE_TOL]
    temsil[i] = hit[0] if hit else i
anaset = sorted(set(temsil.values()), key=lambda j: -cnt[j])
# her renk (artik dahil) -> en yakin ana renk
A = np.array(anaset); dmat = np.linalg.norm(lab[:, None, :]-lab[A][None], axis=2)
map_ = A[np.argmin(dmat, 1)]
for i, j in temsil.items(): map_[i] = j
lbl = map_[inv].reshape(H, W)
# tisort rengi ve (koyu) beyaz fon
sh_lab = cv2.cvtColor((shirt/255).astype(np.float32).reshape(1, 1, 3), cv2.COLOR_RGB2Lab).reshape(3)
sh = A[np.argmin(np.linalg.norm(lab[A]-sh_lab, axis=1))]
if np.linalg.norm(lab[sh]-sh_lab) > 10: print(f'UYARI: tisort rengine yakin renk bulunamadi; en yakin {cols[sh].tolist()} tisort sayildi')
inks = [j for j in anaset if j != sh]
beyaz = None
if tur == 'koyu':
    wl = cv2.cvtColor(np.array([[[1, 1, 1]]], np.float32), cv2.COLOR_RGB2Lab).reshape(3)
    cand = [j for j in inks if np.linalg.norm(lab[j]-wl) < 6]
    if cand: beyaz = cand[0]; inks.remove(beyaz)
print('murekkep sayisi', len(inks) + (1 if tur == 'koyu' else 0), '(koyu: fon dahil)')
if len(inks) + (1 if tur == 'koyu' else 0) > MAXRENK: print(f'UYARI: {MAXRENK} kafadan fazla renk var; renk birlestirmek gerekebilir')

def clean(m):
    if MINW > 1:
        m = m & cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((MINW, MINW), np.uint8)).astype(bool)
    nl, lb, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    sm = np.zeros(nl, bool); sm[1:] = st[1:, 4] < MINPX
    if sm[1:].any(): m[sm[lb]] = False
    return m

def auto_ad(rgb_, used):
    l, a_, b_ = cv2.cvtColor(np.array([[np.array(rgb_, np.float32)/255]], np.float32), cv2.COLOR_RGB2Lab)[0, 0]
    ch = float(np.hypot(a_, b_)); hu = float(np.degrees(np.arctan2(b_, a_))) % 360
    if ch < 5: ad = 'Acik_Gri' if l > 70 else ('Gri' if l > 35 else 'Siyah')
    elif hu < 40: ad = 'Somon' if l > 75 else 'Kirmizi_Kahve'
    elif hu < 80: ad = 'Bej' if (ch < 25 and l > 65) else 'Sari' if l > 68 else 'Karamel' if l > 55 else 'Kahve' if l > 30 else 'Koyu_Kahve'
    elif hu < 150: ad = 'Yesil'
    elif hu < 260: ad = 'Acik_Mavi' if l > 78 else 'Turkuaz' if l > 45 else 'Koyu_Turkuaz' if l > 30 else 'Lacivert'
    else: ad = 'Mor'
    base, i = ad, 2
    while ad in used: ad = f'{base}{i}'; i += 1
    used.add(ad); return ad

def save(mask, path): Image.frombytes('1', (W, H), np.packbits(~mask, axis=1).tobytes()).save(path, dpi=(PPI, PPI), compress_level=6)

LAP_ALT = int(E('LAP_ALTLIK', 0)); LAP_WIN = int(E('LAP_WIN', 9)); LAP_MIN = float(E('LAP_MIN', 0.15))
inks = sorted(inks, key=lambda j: -lab[j][0])              # acik -> koyu
EXT = {}                                                   # lap: murekkep j -> daha koyu noktalarin altina uzanan ek piksel
if LAP_ALT:
    def _box(m): return cv2.boxFilter(m.astype(np.float32), -1, (LAP_WIN, LAP_WIN), normalize=True, borderType=cv2.BORDER_REPLICATE)
    fp = _box(lbl == sh)
    for k, dk in enumerate(inks):
        dm = (lbl == dk)
        if k == 0 or not dm.any(): continue
        best = np.zeros((H, W), np.float32); who = np.full((H, W), -1, np.int16)
        for q in range(k):                                 # daha acik murekkepler
            f = _box(lbl == inks[q]); up = f > best; best[up] = f[up]; who[up] = q
        ok = dm & (best >= LAP_MIN) & (best > 2*fp)
        for q in range(k):
            a_ = ok & (who == q)
            if a_.any(): EXT[inks[q]] = EXT.get(inks[q], np.zeros((H, W), bool)) | a_
        print(f'  lap: {cols[dk].tolist()} noktalarinin %{100*ok.sum()/max(dm.sum(), 1):.1f}i altina taban uzatildi')
        del best, who
    del fp
d = os.path.join(out_dir, setn); os.makedirs(d, exist_ok=True)
sets = []; used = set(); n0 = 1
inks = sorted(inks, key=lambda j: -lab[j][0])              # baski sirasi: acik -> koyu
if tur == 'koyu':
    darkest = inks[-1] if inks else None
    fon = (lbl != sh)
    if darkest is not None: fon &= (lbl != darkest)        # en koyu murekkebin altina fon yok
    solid = (lbl != sh).astype(np.uint8)
    er = cv2.erode(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*CHOKE+1, 2*CHOKE+1)))
    fon &= ~((solid > 0) & (er == 0))                      # disa bakan kenar choke
    fon = clean(fon)
    save(fon, os.path.join(d, '01_Fon_Beyaz.png')); sets.append(['01 Fon_Beyaz', '01_Fon_Beyaz.png', [255, 255, 255]])
    print(f'  01_Fon_Beyaz kapsama %{100*fon.mean():.2f}'); n0 = 2
for n_, j in enumerate(inks):
    m = clean(lbl == j)
    if j in EXT: m |= EXT[j]
    if m.mean() < 0.0001:
        print(f'  UYARI: renk {cols[j].tolist()} temizlikten sonra neredeyse bos (%{100*m.mean():.3f}); kenar yumusatma artigi sayilip film yazilmadi'); continue
    ad = auto_ad(cols[j], used); fn = f'{len(sets)+1:02d}_{ad}.png'
    save(m, os.path.join(d, fn)); sets.append([f'{len(sets)+1:02d} {ad}', fn, cols[j].tolist()])
    print(f'  {fn} renk {cols[j].tolist()} kapsama %{100*m.mean():.2f}')
jp = os.path.join(out_dir, 'kanallar_hibrit.json')
meta = json.load(open(jp)) if os.path.exists(jp) else {'W': W, 'H': H, 'ppi': PPI, 'sets': {}}
meta['sets'][setn] = sets
if LAP_ALT: meta['lap_altlik'] = True
meta.setdefault('kaynak', {})[setn] = os.path.basename(inp)   # acik ve koyu ayni klasorde birlikte durabilir
json.dump(meta, open(jp, 'w'), ensure_ascii=False, indent=1)
print('2. ASAMA bitti. Sonra: tools/kalite_kontrol.py ve PSD (psd_olustur_tek_adim.jsx).')
