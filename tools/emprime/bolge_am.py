#!/usr/bin/env python3
"""Bolge saflikli AM tram ayrimi. Plan: bilgi/emprime-kanal-ayirma.md
Kullanim: python3 tools/bolge_am.py girdi.png cikti_klasoru N_acik [N_koyu_renk]
  N_acik: acik tisort renk sayisi; N_koyu_renk: koyu tisortte fon HARIC renk sayisi (verilmezse koyu set uretilmez)
Env: ASAMA=tek|onizleme (onizleme = iki asamali yontem 1. asama; bkz. bilgi/emprime-kanal-ayirma.md)
     FIGUR=figur_maske.png (koyu tiste kagit beyazi ile figur beyazini ayirir; yoksa figur = kagit olmayan her yer)
     LAP=1 (tramli renklerin altinda tam kaplayan duz taban 'lap'; LAP_TOL=0,25 LAP_ABS=0,0004; yalniz 1. asama onizleme/tek asama gorunumu, film ust uste basimi henuz yok)
     PPI(508) LPI(45) ANG(15) DMIN(0.03) MINC(0.10) MINPX(4) CHOKE_PX(4) SHIRT(30,30,30 onizleme)
Ilke: her pikselin renk ailesi (ton) yumusatilmis kaynaktan bulunur; piksel yalniz kendi ailesinin murekkepleriyle
karisir. En koyu murekkep baska ailede yalniz cizgi/kontur maskesinde kullanilir. Duz bolgeler sabit tonda tutulur.
Murekkepler cakismaz (indeks), tek ekran; koyu tiste fon (beyaz altlik) ayni ekranda renklerin altinda.
"""
import sys, os, json, time
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

inp, out_dir = sys.argv[1], sys.argv[2]
N_ACIK = int(sys.argv[3]) if len(sys.argv) > 3 else 6
N_KOYU = int(sys.argv[4]) if len(sys.argv) > 4 else 0
E = os.environ.get
PPI = int(E('PPI', 508)); LPI = float(E('LPI', 45)); ANG = float(E('ANG', 15))
DMIN = float(E('DMIN', 0.03)); MINC = float(E('MINC', 0.10)); MINPX = int(E('MINPX', 4)); CHOKE = int(E('CHOKE_PX', 4))
SHIRT = np.array([int(x) for x in E('SHIRT', '30,30,30').split(',')], np.uint8)
FIGUR = E('FIGUR'); os.makedirs(out_dir, exist_ok=True)
ASAMA = E('ASAMA', 'tek')   # 'tek': filmleri dogrudan uret; 'onizleme': iki asamali yontemin 1. asamasi, yalniz indeksli onizleme PNG (film yok)
PAIR_PEN = float(E('PAIR_PEN', 0.0)); IDX_MED = int(E('IDX_MED', 41)); REV_E = float(E('REV_E', 0.003)); REFINE = int(E('REFINE', 2)); MINW = int(E('MINW', 3))
LAP = int(E('LAP', 0)); LAP_TOL = float(E('LAP_TOL', 1.0)); LAP_ABS = float(E('LAP_ABS', 0.003)); LAP_MINB = float(E('LAP_MINB', 0.85))   # LAP=1: 'lap' (tam kaplayan duz taban) - atolye, 2026-10-14: tramli renklerin altinda duz taban renk

lin = lambda c: np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
dlin = lambda c: np.where(c <= 0.0031308, c*12.92, 1.055*np.clip(c, 0, None)**(1/2.4)-0.055)
def tolab(rgb01):
    sh = rgb01.shape; return cv2.cvtColor(rgb01.reshape(-1, 1, 3).astype(np.float32), cv2.COLOR_RGB2Lab).reshape(sh)

# ---------------- 1) girdi, beyaz noktasi, yarim cozunurluk ----------------
src = np.array(Image.open(inp).convert('RGB')); H, W = src.shape[:2]
e = max(8, min(H, W)//50)
bord = np.concatenate([src[:e].reshape(-1, 3), src[-e:].reshape(-1, 3), src[:, :e].reshape(-1, 3), src[:, -e:].reshape(-1, 3)])[::50].astype(np.float32)/255
wp = np.percentile(bord, 60, axis=0); log('girdi', W, H, 'kagit beyaz noktasi', np.round(wp*255).astype(int))
h2, w2 = H//2, W//2
small = np.clip(cv2.resize(src, (w2, h2), interpolation=cv2.INTER_AREA).astype(np.float32)/255/wp, 0, 1)
del src
# ---------------- 2) on temizlik: kenar koruyan yumusatma ----------------
labr = tolab(small); mur = cv2.blur(labr, (5, 5))
sd_raw = np.sqrt(np.maximum(cv2.blur(labr*labr, (5, 5))-mur*mur, 0).sum(2)); del labr, mur   # ayrinti (cil, kirpik) olcusu: yumusatma ONCESI
s8 = (small*255+0.5).astype(np.uint8)
for _ in range(2): s8 = cv2.bilateralFilter(s8, 9, 14, 5)
sm = s8.astype(np.float32)/255; del s8
lab = tolab(sm); Lc, ac, bc = lab[..., 0], lab[..., 1], lab[..., 2]
C = np.hypot(ac, bc); HU = np.degrees(np.arctan2(bc, ac)) % 360
paper = (Lc > 93) & (C < 5)
log('yumusatma bitti; kagit %', round(100*paper.mean(), 1))
# cizgi/kontur maskesi: ince koyu yapi (black-hat) ya da cok koyu
L8 = np.clip(Lc*2.55, 0, 255).astype(np.uint8)
bh = cv2.morphologyEx(L8, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
LINE_L = float(E('LINE_L', 38))
line = (Lc < LINE_L) & (C < 25)          # yalniz gercek koyu cizgi/dolu sekil; renkli seklin koyu kenar seridi (L 45-60) cizgi DEGIL -> ip/solucan capak olusmaz
line = cv2.dilate(line.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
log('cizgi maskesi %', round(100*line.mean(), 2))
# duz bolge: yerel std kucuk
mu = cv2.blur(lab, (7, 7)); sd = np.sqrt(np.maximum(cv2.blur(lab*lab, (7, 7))-mu*mu, 0).sum(2))
flat = (sd < 1.5) & (sd_raw < 4) & ~paper & ~line
log('duz bolge %', round(100*flat.mean(), 1))

# ---------------- 3) renk aileleri (ton tepeleri) ----------------
FAM_C = float(E('FAM_C', 6))
chrom = (C >= FAM_C) & ~paper
hist, _ = np.histogram(HU[chrom], bins=72, range=(0, 360), weights=C[chrom])
hs = np.convolve(np.concatenate([hist[-3:], hist, hist[:3]]), np.ones(5)/5, 'same')[3:-3]
peaks = [i for i in range(72) if hs[i] >= hs[i-1] and hs[i] >= hs[(i+1) % 72] and hs[i] > 0]
def mass(i): return sum(hs[(i+k) % 72] for k in range(-6, 7))
tot = max(sum(hs), 1e-6)
peaks = sorted([p for p in peaks if mass(p)/tot > 0.05], key=lambda p: -mass(p))
cent = []
for p in peaks:                                            # birbirine 50 dereceden yakin tepeleri birlestir
    hdeg = p*5+2.5
    if all(abs((hdeg-c+180) % 360-180) > 50 for c in cent): cent.append(hdeg)
cent = np.array(cent if cent else [0.0])
NF = len(cent); log('renk aileleri (ton merkezleri):', np.round(cent).tolist())
def hdist(h, c): return np.abs((h-c+180) % 360-180)
fam = np.full((h2, w2), -1, np.int16)                      # -1 kagit
dmat = np.stack([hdist(HU, c) for c in cent], -1)
fam[chrom] = np.argmin(dmat, -1)[chrom]
# dusuk kromali (gri/kenar ara tonu) kagit-disi pikseller: en yakin etiketli komsunun ailesi
unl = (~chrom) & ~paper
if unl.any() and chrom.any():
    srcm = np.where(chrom, 0, 255).astype(np.uint8)
    _, lbl = cv2.distanceTransformWithLabels(srcm, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    zi = np.flatnonzero(srcm.ravel() == 0)
    famflat = fam.ravel()
    fam_unl = famflat[zi][lbl.ravel()[unl.ravel()]-1]
    famflat[np.flatnonzero(unl.ravel())] = fam_unl
    fam = famflat.reshape(h2, w2)
for f in range(NF): log(f'  aile {f} ({cent[f]:.0f} derece): alan %', round(100*(fam == f).mean(), 1))

# ---------------- 4) palet: en koyu (cizgi) + ailelere acgozlu dagitim ----------------
Lsm = lin(sm)
detail = cv2.dilate((sd_raw >= 6).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~paper
Lsm[detail] = lin(small)[detail]                           # ayrintida (cil, kirpik) yumusatilmamis kaynak: kucuk koyu noktalar kaybolmasin
log('ayrinti (yumusatma uygulanmayan) %', round(100*detail.mean(), 1))
def palette(ncol, region):
    """region: piksel maskesi (basilacak alan). donus: inks (dogrusal RGB), ink_fam"""
    rs = np.random.RandomState(0)
    lp = region & line & ~paper
    dk = Lsm[lp] if lp.sum() > 100 else Lsm[region & ~paper]
    dkl = tolab(dlin(dk))
    darkest = dk[np.argsort(dkl[:, 0])[:max(30, len(dk)//200)]].mean(0)
    samples = {}
    for f in range(NF):
        m = region & (fam == f) & ~line & ~paper
        px = Lsm[m]
        if len(px) < 200: continue
        px = px[rs.permutation(len(px))[:40000]]
        samples[f] = (tolab(dlin(px)), m.sum())
    def sse(f, k):
        X, n = samples[f]
        k = min(k, len(X))
        cv2.setRNGSeed(0)
        comp, _, cen = cv2.kmeans(X.astype(np.float32), k, None, (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 2, cv2.KMEANS_PP_CENTERS)
        return comp/len(X)*n, cen
    alloc = {f: 1 for f in samples}
    budget = ncol-1-len(alloc)
    if budget < 0:                                         # aile sayisi renk sayisindan fazla: en buyukleri tut
        keep = sorted(samples, key=lambda f: -samples[f][1])[:ncol-1]; alloc = {f: 1 for f in keep}; budget = 0
    cur = {f: sse(f, alloc[f])[0] for f in alloc}
    for _ in range(budget):
        gains = {f: cur[f]-sse(f, alloc[f]+1)[0] for f in alloc}
        fb = max(gains, key=gains.get); alloc[fb] += 1; cur[fb] = sse(fb, alloc[fb])[0]
    inks = [darkest]; ifam = [-2]                           # -2 = en koyu (cizgi) murekkebi
    for f in alloc:
        _, cen = sse(f, alloc[f])
        cl = lin(np.clip(cv2.cvtColor(cen.reshape(1, -1, 3).astype(np.float32), cv2.COLOR_Lab2RGB).reshape(-1, 3), 0, 1))
        for c in cl: inks.append(c); ifam.append(f)
    inks = np.array(inks, np.float32); ifam = np.array(ifam)
    # en koyunun tonu bir aileye yakinsa o ailede ton icin de kullanilabilir
    dl = tolab(dlin(inks[:1]))[0]; dch = np.hypot(dl[1], dl[2]); dhu = np.degrees(np.arctan2(dl[2], dl[1])) % 360
    dark_fam = int(np.argmin(hdist(dhu, cent))) if dch >= 6 and hdist(dhu, cent).min() < 40 else -1
    log('  dagitim (aile: murekkep):', alloc, '| en koyu ailesi:', dark_fam)
    return inks, ifam, dark_fam

# ---------------- 5) kisitli karisim ----------------
def fit(inks, ifam, dark_fam, region, chunk=256):
    n = len(inks); D = 1.0-inks
    i1 = np.zeros((h2, w2), np.uint8); i2 = np.zeros((h2, w2), np.uint8)
    c1 = np.zeros((h2, w2), np.float32); c2 = np.zeros((h2, w2), np.float32)
    cands = [(a, a) for a in range(n)] + [(a, b) for a in range(n) for b in range(a+1, n)]
    for r0 in range(0, h2, chunk):
        P = 1.0-Lsm[r0:r0+chunk]; fm = fam[r0:r0+chunk]; ln = line[r0:r0+chunk]
        def allowed(k):
            if ifam[k] == -2: return ln | (fm == dark_fam) if dark_fam >= 0 else ln
            return fm == ifam[k]
        al = [allowed(k) for k in range(n)]
        best = np.full(P.shape[:2], 1e9, np.float32)
        bi = np.zeros(P.shape[:2], np.uint8); bj = np.zeros(P.shape[:2], np.uint8)
        bx = np.zeros(P.shape[:2], np.float32); by = np.zeros(P.shape[:2], np.float32)
        Ez = (P**2).sum(-1)                                     # yalniz kagit
        m0 = Ez < best; best[m0] = Ez[m0]
        for a, b in cands:
            ok = al[a] & al[b]
            if not ok.any(): continue
            if a == b:
                x = np.clip((P@D[a])/float(D[a]@D[a]), 0, 1); y = np.zeros_like(x)
            else:
                M = np.linalg.pinv(np.stack([D[a], D[b]], 1)); xy = P@M.T
                x = np.clip(xy[..., 0], 0, 1); y = np.clip(xy[..., 1], 0, 1)
                s = x+y; ov = s > 1; x = np.where(ov, x/np.maximum(s, 1e-6), x); y = np.where(ov, y/np.maximum(s, 1e-6), y)
            Er = ((x[..., None]*D[a]+y[..., None]*D[b]-P)**2).sum(-1)
            Er = np.where(ok, Er, 1e9)
            if a != b: Er = Er + PAIR_PEN                     # sadelik: tek murekkep tonu tercih (ten/gok gibi yumusak alanda benekli gecis olmaz)
            m = Er < best; best[m] = Er[m]; bi[m] = a; bj[m] = b; bx[m] = x[m]; by[m] = y[m]
        if LAP:                                                  # lap: kagit gorunmez; taban murekkep %100 (duz), ustte koyu murekkep nokta (x+y=1)
            bf = np.full(P.shape[:2], 1e9, np.float32)
            fi = np.zeros(P.shape[:2], np.uint8); fj = np.zeros(P.shape[:2], np.uint8)
            fx = np.zeros(P.shape[:2], np.float32); fy = np.zeros(P.shape[:2], np.float32)
            nrm = (D**2).sum(1)
            for a in range(n):                                   # tek murekkep %100 (duz): piksel o murekkepten en az LAP_MINB kadar koyu olmali
                prj = (P@D[a])/max(float(nrm[a]), 1e-9)
                Er = np.where(al[a] & (prj >= LAP_MINB), ((D[a]-P)**2).sum(-1), 1e9)
                m = Er < bf; bf[m] = Er[m]; fi[m] = a; fj[m] = a; fx[m] = 1.0; fy[m] = 0.0
            for a in range(n):
                for b in range(a+1, n):
                    ok = al[a] & al[b]
                    if not ok.any(): continue
                    dk, lt = (a, b) if nrm[a] >= nrm[b] else (b, a)   # dk: koyu (nokta), lt: acik (duz taban)
                    prj = (P@D[lt])/max(float(nrm[lt]), 1e-9)
                    ok = ok & (prj >= LAP_MINB)                       # taban murekkepten daha acik pikselde lap yok (kagit kalir)
                    if not ok.any(): continue
                    dd = D[dk]-D[lt]; xl = np.clip(((P-D[lt])@dd)/max(float(dd@dd), 1e-9), 0, 1)
                    Er = ((xl[..., None]*D[dk]+(1-xl)[..., None]*D[lt]-P)**2).sum(-1) + PAIR_PEN
                    Er = np.where(ok, Er, 1e9)
                    m = Er < bf; bf[m] = Er[m]; fi[m] = dk; fj[m] = lt; fx[m] = xl[m]; fy[m] = 1-xl[m]
            use = bf <= best*(1+LAP_TOL)+LAP_ABS                  # lap neredeyse ayni hatayla cozuyorsa lap tercih edilir
            bi = np.where(use, fi, bi); bj = np.where(use, fj, bj); bx = np.where(use, fx, bx); by = np.where(use, fy, by)
        i1[r0:r0+chunk] = bi; i2[r0:r0+chunk] = bj; c1[r0:r0+chunk] = bx; c2[r0:r0+chunk] = by
    rg = region
    c1[~rg] = 0; c2[~rg] = 0
    if LAP: log('  lap (fit): kagitsiz piksel % (bolge ici)', round(100*float((((c1+c2) >= 0.999) & rg).sum()/max(rg.sum(), 1)), 1))
    return i1, i2, c1, c2


def refine(inks, ifam, dfam, region, i1, i2, c1, c2, iters):
    """en az kullanilan (en koyu olmayan) murekkebi, en kotu temsil edilen piksellerin rengiyle degistir; hata dusuyorsa kabul et.
    Ornek: ten rengi palette yoksa ten sari+bej noktasiyla turuncu cikar -> ten murekkebi eklenir."""
    D = 1.0-inks; Psr = dlin(Lsm)
    def err(i1, i2, c1, c2, D):                              # algisal (sRGB) hata: koyu/acik tonlar dengeli agirlik alir
        rec = dlin(np.clip(1.0-(c1[..., None]*D[i1]+c2[..., None]*D[i2]), 0, 1))
        Ee = ((rec-Psr)**2).sum(-1); Ee[~region] = 0; return Ee
    Ecur = err(i1, i2, c1, c2, D); base = float(Ecur[region].mean()); korunan = set()
    for it in range(iters):
        use = np.array([c1[i1 == k].sum()+c2[i2 == k].sum() for k in range(len(inks))])
        cand = [k for k in range(len(inks)) if ifam[k] != -2 and k not in korunan]
        if not cand: break
        kmin = min(cand, key=lambda k: use[k])
        bad = region & ~line & ~paper
        thr = np.percentile(Ecur[bad], 97)
        sel = bad & (Ecur >= thr)
        if sel.sum() < 500: break
        fsel = fam[sel]; fsel = fsel[fsel >= 0]
        if len(fsel) == 0: break
        fnew = int(np.bincount(fsel).argmax())
        sel &= (fam == fnew)
        # yuksek hatali pikseller tisort/kagida cok yakin degilse: renklerinin ortalamasi yeni murekkep
        newc = Lsm[sel].mean(0)
        nl_ = tolab(dlin(newc[None]))[0]; el = tolab(dlin(inks))
        if np.min(np.linalg.norm(el-nl_, axis=1)) < 12:   # mevcut murekkebe cok yakin: yeni renk kazandirmaz
            log('  palet iyilestirme: yeni renk mevcut murekkebe cok yakin, durduruldu'); break
        inks2 = inks.copy(); inks2[kmin] = newc; ifam2 = ifam.copy(); ifam2[kmin] = fnew
        j1, j2, d1, d2 = fit(inks2, ifam2, dfam, region)
        E2 = err(j1, j2, d1, d2, 1.0-inks2); e2 = float(E2[region].mean())
        log(f'  palet iyilestirme {it+1}: {kmin}. murekkep (kullanim {use[kmin]/use.sum()*100:.1f}%) -> aile {fnew} renk {np.round(dlin(newc)*255).astype(int).tolist()}; hata {base:.5f} -> {e2:.5f}')
        if e2 < base*0.97:
            inks, ifam, i1, i2, c1, c2, Ecur, base = inks2, ifam2, j1, j2, d1, d2, E2, e2; korunan.add(kmin)
        else: break
    return inks, ifam, i1, i2, c1, c2

def finalize(inks, i1, i2, c1, c2, region):
    """yumusak ton alaninda murekkep ciftini bolge capinda sabitle (cogunluk oyu), kaplamayi o cift icin yeniden coz.
    Boylece ten/gok gibi yumusak gecislerde cift degisiminden dogan yamali (leke) gorunum olusmaz."""
    lum = tolab(dlin(inks))[:, 0]; n = len(inks); D = 1.0-inks
    a_ = np.minimum(i1, i2).astype(np.int16); b_ = np.maximum(i1, i2).astype(np.int16)
    code = a_*16+b_; code[(c1+c2) < 1e-4] = 255
    lapm0 = ((c1+c2) >= 0.999) & region if LAP else np.zeros(code.shape, bool)    # kagitsiz (lap) pikseller
    fe = np.zeros(fam.shape, np.uint8)                      # aile sinirlari: oylama disi
    fe[:, 1:] |= (fam[:, 1:] != fam[:, :-1]); fe[1:, :] |= (fam[1:, :] != fam[:-1, :])
    fe = cv2.dilate(fe, np.ones((IDX_MED, IDX_MED), np.uint8)).astype(bool)
    tone = region & ~line & (sd < 4.0) & (cv2.dilate((sd_raw >= 6).astype(np.uint8), np.ones((5, 5), np.uint8)) == 0) & ~fe                # ayrinti (cil, kirpik) ve kenar disi yumusak alan
    best = np.full(code.shape, -1.0, np.float32); mode = code.copy()
    for k in np.unique(code[tone]):
        cnt = cv2.boxFilter((code == k).astype(np.float32), -1, (IDX_MED, IDX_MED))
        m = cnt > best; best[m] = cnt[m]; mode[m] = k
    code0 = code.copy(); code = np.where(tone, mode, code)
    # ozgun cozumun hatasi (oylamayla ayrinti kaybolursa geri donmek icin)
    P0 = 1.0-Lsm
    E0 = ((c1[..., None]*D[i1]+c2[..., None]*D[i2]-P0)**2).sum(-1)
    I1 = np.zeros(code.shape, np.uint8); I2 = np.zeros(code.shape, np.uint8)
    C1 = np.zeros(code.shape, np.float32); C2 = np.zeros(code.shape, np.float32)
    for k in np.unique(code):
        if k == 255: continue
        a, b = int(k)//16, int(k) % 16
        m = (code == k) & region
        if not m.any(): continue
        P = 1.0-Lsm[m]
        if a == b:
            x = np.clip((P@D[a])/float(D[a]@D[a]), 0, 1); y = np.zeros_like(x)
        else:
            M = np.linalg.pinv(np.stack([D[a], D[b]], 1)); xy = P@M.T
            x = np.clip(xy[:, 0], 0, 1); y = np.clip(xy[:, 1], 0, 1)
            ssum = x+y; ov = ssum > 1; x = np.where(ov, x/np.maximum(ssum, 1e-6), x); y = np.where(ov, y/np.maximum(ssum, 1e-6), y)
        if LAP:
            lp = lapm0[m]
            if lp.any():                                        # lap pikselde cift degisse bile x+y=1 kisitiyla coz
                if a == b: x = np.where(lp, 1.0, x); y = np.where(lp, 0.0, y)
                else:
                    dd = D[a]-D[b]; xl = np.clip(((P-D[b])@dd)/max(float(dd@dd), 1e-9), 0, 1)
                    x = np.where(lp, xl, x); y = np.where(lp, 1-xl, y)
        # koyu olan nokta cekirdegi
        if lum[a] <= lum[b]: I1[m], I2[m], C1[m], C2[m] = a, b, x, y
        else: I1[m], I2[m], C1[m], C2[m] = b, a, y, x
    E1 = ((C1[..., None]*D[I1]+C2[..., None]*D[I2]-P0)**2).sum(-1)
    rev = (code != code0) & (E1 > E0+REV_E)                 # cil/ince ayrinti: oylama bozduysa ozgun cifte don
    sw = lum[i1] > lum[i2]
    I1[rev] = np.where(sw, i2, i1)[rev]; I2[rev] = np.where(sw, i1, i2)[rev]
    C1[rev] = np.where(sw, c2, c1)[rev]; C2[rev] = np.where(sw, c1, c2)[rev]
    tone = tone & ~rev
    log('  ton oylamasi: degisen %', round(100*((code != code0) & ~rev).mean(), 1), '| ayrinti icin geri donen %', round(100*rev.mean(), 2))
    del P0, E0, E1
    darkest = int(np.argmin(lum))
    C1 = np.where(C1 < np.where(I1 == darkest, DMIN, MINC), 0, C1); C2 = np.where(C2 < np.where(I2 == darkest, DMIN, MINC), 0, C2)
    for arr, sg, msk in ((C1, 3, flat), (C2, 3, flat), (C1, 2, tone), (C2, 2, tone)):   # duz ve yumusak alanda gurultusuz ton
        wgt = msk.astype(np.float32)
        num = cv2.GaussianBlur(arr*wgt, (0, 0), sg); den = cv2.GaussianBlur(wgt, (0, 0), sg)
        sm_ = np.where(den > 1e-3, num/np.maximum(den, 1e-3), arr); arr[msk] = sm_[msk]
    # dolu (tramsiz) yapma: yalniz yumusak ton alani DISINDA; ten gibi alanda kati yama ile noktali alan yan yana gelmez
    tt = C1+C2; full = (tt > 1-DMIN) & ~tone; k = np.where(full, 1/np.maximum(tt, 1e-6), 1); C1 *= k; C2 *= k
    C1 = np.minimum(C1, np.where(tone, 0.96, 1.0)); C2 = np.minimum(C2, np.where(tone, np.maximum(0.96-C1, 0), 1.0))
    if LAP: log('  lap (finalize): kagitsiz piksel % (bolge ici)', round(100*float(lapm0.sum()/max(region.sum(), 1)), 1))
    if LAP: C2 = np.where(lapm0, 1.0-C1, C2)                # lap: taban tam kaplar (tonda %96 sinirini asar; kagit benegi olmaz)
    return I1, I2, C1, C2

# ---------------- 6) ekran ----------------
cell = PPI/LPI; cs, sn = np.cos(np.radians(ANG)), np.sin(np.radians(ANG))
rsd = np.random.RandomState(3).rand(2, 1000000)
Ss = np.sort(1-((np.cos(2*np.pi*rsd[0])+np.cos(2*np.pi*rsd[1]))/4+0.5)); qs = np.linspace(0, 1, Ss.size)
def screen(I1, I2, C1, C2, n, U=None):
    """tam cozunurluk indeks haritasi (0 kagit, 1..n murekkep) ve istege bagli fon (U kaplama) haritasi"""
    idx = np.zeros((H, W), np.uint8); fon = np.zeros((H, W), bool) if U is not None else None
    for r0 in range(0, H, 512):
        r1 = min(r0+512, H); rr = np.arange(r0, r1)
        yh = np.minimum(rr/2, h2-1.001).astype(np.float32); xh = np.minimum(np.arange(W)/2, w2-1.001).astype(np.float32)
        y0 = yh.astype(int); fy = (yh-y0)[:, None]; x0 = xh.astype(int); fx = (xh-x0)[None, :]
        up = lambda a: a[y0][:, x0]*(1-fy)*(1-fx)+a[y0+1][:, x0]*fy*(1-fx)+a[y0][:, x0+1]*(1-fy)*fx+a[y0+1][:, x0+1]*fy*fx
        Y0 = np.minimum(rr//2, h2-1); X0 = np.minimum(np.arange(W)//2, w2-1)
        xx = np.arange(W)[None, :].astype(np.float32); yy = rr[:, None].astype(np.float32)
        X = (xx*cs+yy*sn)/cell; Y = (-xx*sn+yy*cs)/cell
        T = np.interp(1-((np.cos(2*np.pi*X)+np.cos(2*np.pi*Y))/4+0.5), Ss, qs).astype(np.float32)
        a1 = up(C1); a2 = up(C2)
        if U is not None:
            u = up(U); a1 = a1*u; a2 = a2*u
            fon[r0:r1] = T < u
        tt_ = a1+a2; tt_ = tt_+(tt_ > 0.999)*0.01 if LAP else tt_
        idx[r0:r1] = np.where(T < a1, I1[Y0][:, X0]+1, np.where(T < tt_, I2[Y0][:, X0]+1, 0))
    return idx, fon

def auto_ad(rgb, used):
    l, a_, b_ = cv2.cvtColor(np.array([[np.array(rgb, np.float32)/255]], np.float32), cv2.COLOR_RGB2Lab)[0, 0]
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

def clean(m):
    if MINW > 1:                                           # ip/solucan gibi ince capaklar: MINW px'ten ince her yapi silinir
        op = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((MINW, MINW), np.uint8)).astype(bool)
        m = m & op
    nl, lb, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    small_ = np.zeros(nl, bool); small_[1:] = st[1:, 4] < MINPX
    if small_[1:].any(): m[small_[lb]] = False
    return m

def save_p(pidx, pal, path):
    im = Image.fromarray(pidx, 'P'); flat_ = [v for c in pal for v in c]; im.putpalette(flat_+[0]*(768-len(flat_)))
    im.save(path, dpi=(PPI, PPI), compress_level=6)
def save(mask, path):
    if ASAMA == 'onizleme': return                         # 1. asamada film yazilmaz
    Image.frombytes('1', (W, H), np.packbits(~mask, axis=1).tobytes()).save(path, dpi=(PPI, PPI), compress_level=6)

meta = {'W': W, 'H': H, 'ppi': PPI, 'lpi': LPI, 'aci': ANG, 'sets': {}}
used = set()

# ---------------- ACIK TISORT ----------------
region_acik = ~paper
inks, ifam, dfam = palette(N_ACIK, region_acik)
i1, i2, c1, c2 = fit(inks, ifam, dfam, region_acik); log('acik: karisim bitti')
inks, ifam, i1, i2, c1, c2 = refine(inks, ifam, dfam, region_acik, i1, i2, c1, c2, REFINE)
I1, I2, C1, C2 = finalize(inks, i1, i2, c1, c2, region_acik); del i1, i2, c1, c2
idx, _ = screen(I1, I2, C1, C2, len(inks)); log('acik: tram bitti')
rgbi = np.clip(np.round(dlin(inks)*255), 0, 255).astype(int)
order = np.argsort(-tolab(dlin(inks))[:, 0])               # baski sirasi: acik -> koyu
d = os.path.join(out_dir, 'Acik_Tisort'); (os.makedirs(d, exist_ok=True) if ASAMA != 'onizleme' else None)
sets = []; prev = np.full((H, W, 3), 255, np.uint8); pidx = np.zeros((H, W), np.uint8); ppal = [[255, 255, 255]]
for n_, k in enumerate(order):
    m = clean(idx == k+1); ad = auto_ad(rgbi[k], used)
    fn = f'{n_+1:02d}_{ad}.png'; save(m, os.path.join(d, fn)); sets.append([f'{n_+1:02d} {ad}', fn, rgbi[k].tolist()])
    prev[m] = rgbi[k]; pidx[m] = n_+1; ppal.append(rgbi[k].tolist()); log('  acik', fn, 'kapsama %', round(100*m.mean(), 2))
meta['sets']['Acik_Tisort'] = sets
if ASAMA == 'onizleme':
    save_p(pidx, ppal, os.path.join(out_dir, 'Onizleme_Acik_Tisort.png'))
    meta.setdefault('onizleme', {})['Acik_Tisort'] = {'dosya': 'Onizleme_Acik_Tisort.png', 'tisort_rgb': [255, 255, 255], 'murekkepler': sets}
del pidx
Image.fromarray(prev).save(os.path.join(out_dir, 'onizleme_acik_indeks.png'))
np.save(os.path.join(out_dir, '_aile.npy'), fam.astype(np.int8)); np.save(os.path.join(out_dir, '_cizgi.npy'), line)
del idx, prev

# ---------------- KOYU TISORT ----------------
if N_KOYU:
    if FIGUR:
        fg = cv2.resize(cv2.imread(FIGUR, 0), (w2, h2), interpolation=cv2.INTER_LINEAR) > 127
    else:
        fg = np.zeros((h2, w2), bool)
    # fon kaplamasi (opaklik): figur = 1; firca/zemin = kagittan uzaklik
    # figur maskesine sizan kagit: maske disiyla baglantili kagit bilesenleri figur beyazi sayilmaz
    if fg.any():
        nl, lb, st, _ = cv2.connectedComponentsWithStats(paper.astype(np.uint8), connectivity=4)
        out_cnt = np.bincount(lb[~fg], minlength=nl); tot_cnt = st[:, 4]
        leak = np.zeros(nl, bool); leak[1:] = out_cnt[1:] > 0.2*tot_cnt[1:]
        fg = fg & ~leak[lb]; del lb
        log('koyu: figur beyazi (maske ici, disa baglanmayan kagit) %', round(100*(fg & paper).mean(), 2))
    dE = np.sqrt((Lc-100)**2+ac**2+bc**2)
    U = np.clip((dE-5.0)/5.0, 0, 1).astype(np.float32); U[paper] = 0; U[fg] = 1.0
    U = cv2.GaussianBlur(U, (0, 0), 1.0)
    region_k = U > 0.02
    used_k = set()
    inks_k, ifam_k, dfam_k = palette(N_KOYU, region_k)
    i1, i2, c1, c2 = fit(inks_k, ifam_k, dfam_k, region_k); log('koyu: karisim bitti')
    inks_k, ifam_k, i1, i2, c1, c2 = refine(inks_k, ifam_k, dfam_k, region_k, i1, i2, c1, c2, REFINE)
    I1, I2, C1, C2 = finalize(inks_k, i1, i2, c1, c2, region_k); del i1, i2, c1, c2
    idx, fon = screen(I1, I2, C1, C2, len(inks_k), U)
    lumk = tolab(dlin(inks_k))[:, 0]; dk = int(np.argmin(lumk))
    fon &= ~(idx == dk+1)                                   # en koyu murekkebin altina fon yok
    # disa bakan kenarda choke: kati fon bolgesinin kenar seridinde fon kaldir
    solid = cv2.resize((U > 0.5).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
    er = cv2.erode(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*CHOKE+1, 2*CHOKE+1)))
    band = (solid > 0) & (er == 0); fon[band] = False; del solid, er, band
    fon = clean(fon)
    rgbk = np.clip(np.round(dlin(inks_k)*255), 0, 255).astype(int)
    d = os.path.join(out_dir, 'Koyu_Tisort'); (os.makedirs(d, exist_ok=True) if ASAMA != 'onizleme' else None)
    sets = [['01 Fon_Beyaz', '01_Fon_Beyaz.png', [255, 255, 255]]]; save(fon, os.path.join(d, '01_Fon_Beyaz.png'))
    log('  koyu 01_Fon_Beyaz.png kapsama %', round(100*fon.mean(), 2))
    prev = np.full((H, W, 3), SHIRT, np.uint8); prev[fon] = 255
    pidx = np.zeros((H, W), np.uint8); pidx[fon] = 1; ppal = [SHIRT.tolist(), [255, 255, 255]]
    ordk = np.argsort(-lumk)
    for n_, k in enumerate(ordk):
        m = clean(idx == k+1); ad = auto_ad(rgbk[k], used_k)
        fn = f'{n_+2:02d}_{ad}.png'; save(m, os.path.join(d, fn)); sets.append([f'{n_+2:02d} {ad}', fn, rgbk[k].tolist()])
        prev[m] = rgbk[k]; pidx[m] = n_+2; ppal.append(rgbk[k].tolist()); log('  koyu', fn, 'kapsama %', round(100*m.mean(), 2))
    meta['sets']['Koyu_Tisort'] = sets
    if ASAMA == 'onizleme':
        save_p(pidx, ppal, os.path.join(out_dir, 'Onizleme_Koyu_Tisort.png'))
        meta.setdefault('onizleme', {})['Koyu_Tisort'] = {'dosya': 'Onizleme_Koyu_Tisort.png', 'tisort_rgb': SHIRT.tolist(), 'fon_rgb': [255, 255, 255], 'murekkepler': sets[1:]}
    del pidx
    meta['koyu_tisort_onizleme_rengi'] = SHIRT.tolist()
    Image.fromarray(prev).save(os.path.join(out_dir, 'onizleme_koyu_indeks.png'))
if ASAMA == 'onizleme':
    meta.pop('sets', None)
    json.dump(meta, open(os.path.join(out_dir, 'onizleme_palet.json'), 'w'), ensure_ascii=False, indent=1)
    log('1. ASAMA bitti: Onizleme_*.png dosyalarini Photoshop\'ta duzenleyip onaylayin; 2. asama: tools/onizlemeden_ayir.py')
else:
    json.dump(meta, open(os.path.join(out_dir, 'kanallar_hibrit.json'), 'w'), ensure_ascii=False, indent=1)
log('bitti')
