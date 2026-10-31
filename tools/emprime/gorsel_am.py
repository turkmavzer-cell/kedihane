#!/usr/bin/env python3
"""Genel AM tram ayrimi (acik tisort, N murekkep, tek ekran, murekkepler cakismaz).
Kullanim: python3 tools/gorsel_am.py girdi.png maske.png cikti_klasoru [N=6]
Env: TQMIN(0.30) PPI(508) LPI(45) ANG(15) DMIN(0.03) MINC(0.10) SEED(0) NSEED(4) WP_GAIN(1)
Yontem: piksel basina en iyi (murekkep a, murekkep b, kagit) karisimi (dogrusal RGB, alan orani); a ve b ayni
yuvarlak nokta ekraninda arka arkaya dolar (koyu olan nokta cekirdegi, acik olan halka). Yani cakisma yok.
Kagit (tisort) beyaz sayilir: kagit rengi tum goruntude beyaza normalize edilir.
"""
import sys, os, json, time
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

inp, mskp, out_dir = sys.argv[1:4]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 6
PPI = int(os.environ.get('PPI', 508)); LPI = float(os.environ.get('LPI', 45)); ANG = float(os.environ.get('ANG', 15))
DMIN = float(os.environ.get('DMIN', 0.03)); NAMES = [x for x in os.environ.get('NAMES', '').split(',') if x]; NSEED = int(os.environ.get('NSEED', 4))
os.makedirs(os.path.join(out_dir, 'Acik_Tisort'), exist_ok=True)

src = np.array(Image.open(inp).convert('RGB')); H, W = src.shape[:2]
msk = cv2.resize(cv2.imread(mskp, 0), (W, H), interpolation=cv2.INTER_LINEAR)
msk = cv2.GaussianBlur(msk, (0, 0), 1.5) > 127
log('girdi', W, H, 'maske %', round(100*msk.mean(), 1))

lin = lambda c: np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
dlin = lambda c: np.where(c <= 0.0031308, c*12.92, 1.055*np.clip(c, 0, None)**(1/2.4)-0.055)
# beyaz noktasi: figur disindaki kagit
bgpix = src[~cv2.dilate(msk.astype(np.uint8), np.ones((61, 61), np.uint8)).astype(bool)][::50].astype(np.float32)/255
if len(bgpix) <= 1000:                                        # maske tum goruntuyu kapsiyor: kenar seridini kagit say
    e = max(8, min(H, W)//50); bgpix = np.concatenate([src[:e].reshape(-1, 3), src[-e:].reshape(-1, 3), src[:, :e].reshape(-1, 3), src[:, -e:].reshape(-1, 3)])[::50].astype(np.float32)/255
wp = np.percentile(bgpix, 60, axis=0)
log('kagit beyaz noktasi', np.round(wp*255).astype(int))

# yarim cozunurlukte coz (katsayi hesabi)
h2, w2 = H//2, W//2
small = cv2.resize(src, (w2, h2), interpolation=cv2.INTER_AREA).astype(np.float32)/255
small = np.clip(small/wp, 0, 1)
sm = cv2.resize(msk.astype(np.uint8), (w2, h2), interpolation=cv2.INTER_NEAREST).astype(bool)
L = lin(small)                                               # dogrusal RGB, kagit = 1
rgb2lab = lambda x: cv2.cvtColor(x.astype(np.float32).reshape(-1, 1, 3), cv2.COLOR_RGB2Lab).reshape(-1, 3)
fig = L[sm]; samp = fig[np.random.RandomState(0).permutation(len(fig))[:400000]]
labs = rgb2lab(dlin(samp))
nonp = labs[:, 0] < 93                                       # kagit benzeri olmayanlar
S, Ls = samp[nonp], labs[nonp]
wgt = np.clip((100-Ls[:, 0])/40, 0.3, 2.0).astype(np.float32)  # koyu/doygun ayrintilar agirlik alir
log('murekkep adayi piksel', len(S))

def fit(inks, chunk=300):
    """her piksel icin en iyi (a,b,ca,cb); inks: (N,3) dogrusal RGB"""
    n = len(inks); ia = np.zeros((h2, w2), np.uint8); ib = np.zeros((h2, w2), np.uint8)
    ca = np.zeros((h2, w2), np.float32); cb = np.zeros((h2, w2), np.float32); er = np.zeros((h2, w2), np.float32)
    D = 1.0 - inks                                            # kagitten fark vektorleri (kagit = 1)
    pairs = [(a, b) for a in range(n) for b in range(a+1, n)]
    for r0 in range(0, h2, chunk):
        P = (1.0 - L[r0:r0+chunk])                            # (h,w,3) hedef fark
        best = np.full(P.shape[:2], 1e9, np.float32)
        bi = np.zeros(P.shape[:2], np.uint8); bj = np.zeros(P.shape[:2], np.uint8)
        bca = np.zeros(P.shape[:2], np.float32); bcb = np.zeros(P.shape[:2], np.float32)
        cands = [(a, a) for a in range(n)] + pairs
        for a, b in cands:
            if a == b:
                x = np.clip((P@D[a])/float(D[a]@D[a]), 0, 1); y = np.zeros_like(x)
            else:
                A = np.stack([D[a], D[b]], 1)                  # 3x2
                M = np.linalg.pinv(A)                         # 2x3
                xy = P@M.T; x = np.clip(xy[..., 0], 0, 1); y = np.clip(xy[..., 1], 0, 1)
                s = x+y; ov = s > 1; x = np.where(ov, x/np.maximum(s, 1e-6), x); y = np.where(ov, y/np.maximum(s, 1e-6), y)
            E = ((x[..., None]*D[a]+y[..., None]*D[b]-P)**2).sum(-1)
            if a != b and OPP[a, b]:             # zit renkli murekkepler (ton farki > 110 derece) az miktarda karistirilmaz: benek yapar
                E = np.where(np.minimum(x, y) < TQMIN, 1e9, E)
            m = E < best; best[m] = E[m]; bi[m] = a; bj[m] = b; bca[m] = x[m]; bcb[m] = y[m]
        ia[r0:r0+chunk] = bi; ib[r0:r0+chunk] = bj; ca[r0:r0+chunk] = bca; cb[r0:r0+chunk] = bcb; er[r0:r0+chunk] = best
    return ia, ib, ca, cb, er

def score(inks):
    """ornek piksellerde hizli hata (Lab dE)"""
    D = 1.0 - inks; n = len(inks); P = 1.0 - S
    best = np.full(len(S), 1e9, np.float32)
    for a in range(n):
        for b in range(a, n):
            if a == b:
                x = np.clip((P@D[a])/float(D[a]@D[a]), 0, 1); y = 0*x
            else:
                M = np.linalg.pinv(np.stack([D[a], D[b]], 1)); xy = P@M.T; x = np.clip(xy[:, 0], 0, 1); y = np.clip(xy[:, 1], 0, 1)
                s = x+y; ov = s > 1; x = np.where(ov, x/np.maximum(s, 1e-6), x); y = np.where(ov, y/np.maximum(s, 1e-6), y)
            R = 1.0 - (x[:, None]*D[a]+y[:, None]*D[b])
            best = np.minimum(best, np.linalg.norm(rgb2lab(dlin(np.clip(R, 0, 1)))-Ls, axis=1))
    return float((best*wgt).sum()/wgt.sum())

# palet: en koyu (notr siyah/koyu kahve) + N-1 k-means merkezi
darkest = S[np.argsort(Ls[:, 0])[:max(50, len(S)//300)]].mean(0)
cands = []
for sd in range(NSEED):
    crit = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5)
    rest = Ls[Ls[:, 0] > 35]; wrest = wgt[Ls[:, 0] > 35]
    idx = np.random.RandomState(sd).choice(len(rest), min(len(rest), 60000), replace=False, p=wrest[:]/wrest.sum())
    cv2.setRNGSeed(sd)
    _, _, cen = cv2.kmeans(rest[idx].astype(np.float32), N-1, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cl = lin(np.clip(cv2.cvtColor(cen.reshape(1, -1, 3), cv2.COLOR_Lab2RGB).reshape(-1, 3), 0, 1))
    inks = np.vstack([darkest[None], cl]).astype(np.float32)
    sc = score(inks); cands.append((sc, sd, inks)); log(f' palet tohum {sd}: agirlikli dE {sc:.2f}')
sc, sd, inks = min(cands, key=lambda r: r[0])
log('secilen tohum', sd, 'dE', round(sc, 2))
order = np.argsort(-rgb2lab(dlin(inks))[:, 0])                # acik -> koyu
inks = inks[order]
rgb_ink = np.clip(np.round(dlin(inks)*255), 0, 255).astype(int)
log('murekkepler (acik->koyu):', rgb_ink.tolist())

TQMIN = float(os.environ.get('TQMIN', 0.30))
_il = rgb2lab(dlin(inks)); _ch = np.hypot(_il[:, 1], _il[:, 2]); _hu = np.degrees(np.arctan2(_il[:, 2], _il[:, 1]))
OPP = np.zeros((N, N), bool)
for _a in range(N):
    for _b in range(N):
        if _a != _b and _ch[_a] > 12 and _ch[_b] > 12 and _il[_a, 0] > 30 and _il[_b, 0] > 30:   # cok koyu murekkep (ince detay) muaf
            _dh = abs((_hu[_a]-_hu[_b]+180) % 360-180); OPP[_a, _b] = _dh > 110
log('zit renk ciftleri (ton farki >110, ancak >=%30 karisabilir):', [(int(a), int(b)) for a in range(N) for b in range(a+1, N) if OPP[a, b]])
ia, ib, ca, cb, er = fit(inks)
log('katsayilar bitti')
# koyu olan nokta cekirdegi: indeks buyuk = koyu; cekirdek = koyu
swap = ia < ib                                               # (a acik, b koyu) -> koyu once
c1 = np.where(swap, cb, ca); c2 = np.where(swap, ca, cb); i1 = np.where(swap, ib, ia); i2 = np.where(swap, ia, ib)
c1[~sm] = 0; c2[~sm] = 0
# kucuk ikincil bilesenler (ozellikle zit renkli: sicak alanda turkuaz benekleri) basilamaz/istenmez -> at.
# en koyu murekkep ince detay icin DMIN'de kalir, digerleri MINC'e kadar atilir
MINC = float(os.environ.get('MINC', 0.10))
c1 = np.where(c1 < np.where(i1 == N-1, DMIN, MINC), 0, c1); c2 = np.where(c2 < np.where(i2 == N-1, DMIN, MINC), 0, c2)
tot = c1+c2; full = tot > 1-DMIN; sc_ = np.where(full, 1/np.maximum(tot, 1e-6), 1)
c1 = c1*sc_; c2 = c2*sc_
del ca, cb, er, ia, ib

# ekran esigi (yuvarlak nokta, alan-dogrusal)
cell = PPI/LPI; cs, sn = np.cos(np.radians(ANG)), np.sin(np.radians(ANG))
rs = np.random.RandomState(3).rand(2, 1000000)
Ss = np.sort(1-((np.cos(2*np.pi*rs[0])+np.cos(2*np.pi*rs[1]))/4+0.5)); qs = np.linspace(0, 1, Ss.size)
idxmap = np.zeros((H, W), np.uint8)                          # 0 = kagit, 1..N murekkep
for r0 in range(0, H, 512):
    r1 = min(r0+512, H)
    rr = np.arange(r0, r1)
    yh = np.minimum((rr/2).astype(np.float32), h2-1.001); xh = np.minimum((np.arange(W)/2).astype(np.float32), w2-1.001)
    # dogrusal buyutme
    def up(a):
        y0 = yh.astype(int); fy = (yh-y0)[:, None]; x0 = xh.astype(int); fx = (xh-x0)[None, :]
        return (a[y0][:, x0]*(1-fy)*(1-fx)+a[y0+1][:, x0]*fy*(1-fx)+a[y0][:, x0+1]*(1-fy)*fx+a[y0+1][:, x0+1]*fy*fx)
    C1 = up(c1); C2 = up(c2)
    Y0 = np.minimum((rr//2), h2-1); X0 = np.minimum(np.arange(W)//2, w2-1)
    I1 = i1[Y0][:, X0]; I2 = i2[Y0][:, X0]
    xx = np.arange(W)[None, :].astype(np.float32); yy = rr[:, None].astype(np.float32)
    X = (xx*cs+yy*sn)/cell; Y = (-xx*sn+yy*cs)/cell
    Sv = 1-((np.cos(2*np.pi*X)+np.cos(2*np.pi*Y))/4+0.5)
    T = np.interp(Sv, Ss, qs).astype(np.float32)
    res = np.where(T < C1, I1+1, np.where(T < C1+C2, I2+1, 0))
    res[~msk[r0:r1]] = 0
    idxmap[r0:r1] = res
log('tram bitti')

names = ['Acik_Mavi', 'Krem_Bej', 'Kahve', 'Koyu']  # yedek; gercek adlar renkten uretilir
def nm(rgb, i):
    r, g, b = rgb
    return f'Renk{i+1}'

def auto_ad(rgb, i):
    """renkten kaba ad (Lab ton/aydinlik); ayni ad cakisirsa sira eklenir"""
    l, a_, b_ = cv2.cvtColor(np.array([[np.array(rgb, np.float32)/255]], np.float32), cv2.COLOR_RGB2Lab)[0, 0]
    ch = float(np.hypot(a_, b_)); hu = float(np.degrees(np.arctan2(b_, a_))) % 360
    if ch < 7: ad = 'Acik_Gri' if l > 70 else ('Gri' if l > 35 else 'Siyah')
    elif hu < 40: ad = 'Somon' if l > 75 else 'Kirmizi_Kahve'
    elif hu < 80: ad = 'Bej' if (ch < 25 and l > 65) else 'Sari' if l > 68 else 'Karamel' if l > 55 else 'Kahve' if l > 30 else 'Koyu_Kahve'
    elif hu < 150: ad = 'Yesil'
    elif hu < 260: ad = 'Acik_Mavi' if l > 72 else 'Turkuaz' if l > 40 else 'Koyu_Mavi'
    else: ad = 'Mor'
    if ad in _kullanilan: ad = f'{ad}{i+1}'
    _kullanilan.add(ad); return ad
_kullanilan = set()
sets = []; films = {}
for k in range(N):
    m = idxmap == (k+1)
    lab = rgb2lab(np.array([[rgb_ink[k]/255.0]], np.float32).reshape(1, 3))[0]
    films[k] = (m, lab)
# elekte tutunmayacak mikro parcalari (<= MINPX px) temizle: maske kenari ve nokta kesisiminde olusur
MINPX = int(os.environ.get('MINPX', 4))
for k in range(N):
    m = films[k][0]
    nl, lb, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    small = np.zeros(nl, bool); small[1:] = st[1:, 4] < MINPX
    nrem = int(small[1:].sum())
    if nrem: m[small[lb]] = False
    log(f'mikro parca temizligi film {k+1}: {nrem} parca silindi')
    del lb
# baski sirasi: acik -> koyu (altta acik)
for n_, k in enumerate(range(N)):
    m = films[k][0]
    nmk = NAMES[n_] if n_ < len(NAMES) else auto_ad(rgb_ink[k], n_)
    fn = f'{n_+1:02d}_{nmk}.png'
    Image.frombytes('1', (W, H), np.packbits(~m, axis=1).tobytes()).save(os.path.join(out_dir, 'Acik_Tisort', fn), dpi=(PPI, PPI), compress_level=6)
    sets.append([f'{n_+1:02d} {nmk}', fn, rgb_ink[k].tolist()])
    log('kaydedildi', fn, 'kapsama %', round(100*m.mean(), 2))
json.dump({'W': W, 'H': H, 'ppi': PPI, 'dot_px': 0, 'sets': {'Acik_Tisort': sets}}, open(os.path.join(out_dir, 'kanallar_hibrit.json'), 'w'), ensure_ascii=False, indent=1)
# onizleme: dogrusal karisim degil, murekkep ustte boyanmis (cakisma yok) beyaz kagit
prev = np.full((H, W, 3), 255, np.uint8)
for k in range(N): prev[films[k][0]] = rgb_ink[k]
Image.fromarray(prev).save(os.path.join(out_dir, 'onizleme_acik.png'), dpi=(PPI, PPI))
log('bitti')
