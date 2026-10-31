"""Hibrit emprime ayrimi v5 (acik tisort): once duz arka plandan SEFFAF kesim (alfa + renk temizligi),
sonra yazi/rozet/yildiz = tramsiz spot; fotografik obje = dagitik tram (FM) indeks ayrimi, gercek koyu mürekkep,
parlama (specular) korumasi ve yerel kontrast artirma.
Kullanim: python3 tools/hibrit2.py girdi.png cikti_klasoru [nokta_px=3] [obje_murekkep_sayisi=6]
"""
import sys, os, time, json, ctypes
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src_path, out_dir = sys.argv[1], sys.argv[2]
DOT = int(sys.argv[3]) if len(sys.argv) > 3 else 3
NK = int(sys.argv[4]) if len(sys.argv) > 4 else 8
PPI, WCM = int(os.environ.get("PPI","508")), 38.5   # atolye PSD cozunurlugu 508 PPI (kullanici istegi 2026-10-14)
K = 1.0                                                   # kaynak cozunurluk carpani (1024 genislik = 1); sw bilinince ayarlanir
SPEC_L = float(os.environ.get('SPEC_L', 96.5))           # bu parlakligin ustu = mürekkep yok (parlama)
SHARP = float(os.environ.get('SHARP', 0.25))             # yerel kontrast miktari
TEX_G = float(os.environ.get('TEX_G', 3.0))              # doku esitleme en yuksek kazanc (1 = kapali)
TEX_P = float(os.environ.get('TEX_P', 70))               # hedef detay = obje detay enerjisinin bu yuzdeligi
DITH_N = float(os.environ.get('DITH_N', 0.0))              # tram oncesi mavi-gurultu (algi uzayinda std): duz lekeleri bozar
BLK_C = float(os.environ.get('BLK_C', 9))                  # notr siyah icin en yuksek Lab kroma
PAL_A = float(os.environ.get('PAL_A', 0.6))              # palet orneklemesinde ton dengeleme (0=yok, 1=tam esit)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
os.makedirs(os.path.join(out_dir, "Acik_Tisort"), exist_ok=True); os.makedirs(os.path.join(out_dir, "kesim"), exist_ok=True)
NAVY = ("Lacivert", (10,45,90))
PAPER = (252,252,252)
def rgb2lab(a): return cv2.cvtColor(a.astype(np.float32)/255.0 if a.dtype==np.uint8 else a.astype(np.float32), cv2.COLOR_RGB2Lab)

# ---------- 1) seffaf kesim ----------
src = np.asarray(Image.open(src_path).convert('RGB')); sh, sw = src.shape[:2]
W = int(round(WCM/2.54*PPI)); s = W/sw; H = int(round(sh*s)); K = sw/1024.0
odd = lambda v: 2*int(round(v))+1
f32 = src.astype(np.float32)/255
border = np.concatenate([f32[0], f32[-1], f32[:,0], f32[:,-1]]); bgc = np.median(border, 0)
lab = rgb2lab(src); bgl = rgb2lab(np.uint8(bgc*255)[None,None,:])[0,0]
near = (np.sqrt(((lab-bgl)**2).sum(2)) < 3.5).astype(np.uint8)
n, cc = cv2.connectedComponents(near, connectivity=4)
bl = np.unique(np.concatenate([cc[0],cc[-1],cc[:,0],cc[:,-1]])); bl = bl[bl>0]
bg = np.isin(cc, bl)                                     # kenara bagli beyaz = arka plan (icerideki beyazlar kalir)
fg = ~bg
band = fg & (cv2.dilate(bg.astype(np.uint8), np.ones((5,5),np.uint8)) > 0)   # arka plana 2 px icindeki kenar kusagi
# color-to-alpha (beyaz arka plan icin): p = a*F + (1-a)*B, en kucuk gecerli a
d_dark = np.where(f32 < bgc, (bgc-f32)/np.maximum(bgc,1e-3), 0).max(2)
d_light = np.where(f32 > bgc, (f32-bgc)/np.maximum(1-bgc,1e-3), 0).max(2)
a_band = np.clip(np.maximum(d_dark, d_light), 0.0, 1.0)
alpha = np.where(bg, 0.0, np.where(band, np.maximum(a_band, 0.25), 1.0)).astype(np.float32)
Fc = np.where(band[...,None], np.clip(bgc + (f32-bgc)/np.maximum(alpha,1e-3)[...,None], 0, 1), f32)
# arka plan pikselleri icin en yakin on plan rengi (kübik buyutmede sizmasin) - vektorlu
ys0, xs0 = np.where(~bg)
_, lab2 = cv2.distanceTransformWithLabels(bg.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
_ly = np.zeros(int(lab2.max())+1, np.int32); _lx = np.zeros_like(_ly)
_ly[lab2[~bg]] = ys0; _lx[lab2[~bg]] = xs0
Fc = Fc.copy(); Fc[bg] = Fc[_ly[lab2[bg]], _lx[lab2[bg]]]
del lab2, _ly, _lx
log('kesim: on plan %', round(100*fg.mean(),1), 'kusak px', int(band.sum()))

# bilesenler: obje / yazi-rozet
lab = rgb2lab((Fc*255).astype(np.uint8))
navy = (lab[...,2] < -8) & fg
navy = cv2.morphologyEx(navy.astype(np.uint8), cv2.MORPH_OPEN, np.ones((odd(0.5*K),)*2, np.uint8)) > 0   # ince mavi kenar halesi (buyutme artefakti) lacivert sayilmaz
nav_reg = cv2.dilate(navy.astype(np.uint8), np.ones((odd(3*K),)*2,np.uint8)) > 0
rest = cv2.morphologyEx((fg & ~nav_reg).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((odd(K),)*2,np.uint8))
n, ccr, st, _ = cv2.connectedComponentsWithStats(rest, connectivity=8)
order = [i for i in np.argsort(-st[1:,4])+1 if st[i,4] > 1500*K*K and min(st[i,2], st[i,3]) > 40*K]
big = np.where(np.isin(ccr, order), ccr, 0).astype(np.int32)
# kucuk parcalar (kopuk tuyler) en yakin buyuk bilesene baglanir; yakin kenarlar birlesmez
dist_big, nearest = cv2.distanceTransformWithLabels((big == 0).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
lab_to_comp = np.zeros(nearest.max()+1, np.int32); lab_to_comp[nearest[big > 0]] = big[big > 0]
assign = np.where((rest > 0) & (dist_big <= 30*K), lab_to_comp[nearest], 0)
bear_id = order[0]; badge_ids = order[1:]
log('bilesenler', [(int(st[i,4]), [int(v) for v in st[i,:4]]) for i in order])
bear_core = assign == bear_id; badge_core = np.isin(assign, badge_ids)
bear_m = (cv2.dilate(bear_core.astype(np.uint8), np.ones((odd(2*K),)*2,np.uint8)) > 0) & ~badge_core
badge_m = (cv2.dilate(badge_core.astype(np.uint8), np.ones((odd(2*K),)*2,np.uint8)) > 0) & ~bear_core
text_m = fg & ~bear_m
def save_rgba(mask, path):
    a = (alpha*mask*255).round().astype(np.uint8)
    Image.fromarray(np.dstack([(Fc*255).round().astype(np.uint8), a]), 'RGBA').save(path)
save_rgba(bear_m, os.path.join(out_dir,'kesim','ayicik_seffaf.png')); save_rgba(text_m, os.path.join(out_dir,'kesim','yazi_rozet_seffaf.png'))
log('seffaf PNG kaydedildi')

# ---------- 2) duz kisimlar: lacivert + rozet (600 PPI) ----------
wL = rgb2lab(np.array([[PAPER]], np.uint8))[0,0]
navy_L = rgb2lab(np.array([[NAVY[1]]], np.uint8))[0,0]
badge_rgb = np.median((Fc[badge_m & (lab[...,0] < 40)]*255), 0)
badge_L = rgb2lab(badge_rgb.astype(np.uint8)[None,None,:])[0,0]
Fc8 = (Fc*255).round().astype(np.uint8)
Fo8 = (f32*255).round().astype(np.uint8)   # kaynagin ham rengi: kenar kusaginda color-to-alpha (bölme) gurultuyu buyutur, duz rozet maskesi bunu kullanmaz (cikinti/capak nedeni, 2026-10-14)
navy_f = np.zeros((H,W), bool); badge_f = np.zeros((H,W), bool)
for y0 in range(0, H, 256):
    h = min(256, H-y0)
    M = np.float32([[1/s,0,0.5/s-0.5],[0,1/s,(y0+0.5)/s-0.5]])
    kw = dict(flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    tl = rgb2lab(np.clip(cv2.warpAffine(Fc8, M, (W,h), **kw), 0, 255)).reshape(-1,3) - wL
    al = cv2.warpAffine(alpha, M, (W,h), **kw)
    def cover(tgt): ab = tgt-wL; return ((tl@ab)/float(ab@ab)).reshape(h,W)
    nn = dict(flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    rn = cv2.warpAffine(nav_reg.astype(np.uint8), M, (W,h), **nn) > 0
    rb = cv2.warpAffine(badge_m.astype(np.uint8), M, (W,h), **nn) > 0
    navy_f[y0:y0+h] = (cover(navy_L) >= 0.5) & rn & (al >= 0.5)
    tl_o = rgb2lab(np.clip(cv2.warpAffine(Fo8, M, (W,h), **kw), 0, 255)).reshape(-1,3) - wL          # ham renk (alfa bolmesiz)
    ab_b = badge_L-wL; cov_b = ((tl_o@ab_b)/float(ab_b@ab_b)).reshape(h,W)
    badge_f[y0:y0+h] = (cov_b >= 0.5) & rb & (al >= 0.5)                                              # alfa kapisi lacivertle ayni
# duz rozet kenarini duzelt: ince cikinti/capak (<5 px) ac, kucuk basamaklari medyanla yumusat (nokta/tram degil, duz alan)
FLAT_R = float(os.environ.get('FLAT_R', 1.0))
if FLAT_R > 0 and badge_f.any():
    _r = max(1, int(round(FLAT_R*s))); _k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*_r+1, 2*_r+1))
    _b = cv2.morphologyEx(badge_f.astype(np.uint8), cv2.MORPH_OPEN, _k)
    badge_f = cv2.medianBlur(_b*255, 2*int(round(2.25*_r))+1) > 127
    del _b
log('duz kisimlar tamam')

# ---------- 3) obje: palet + dagitik tram ----------
ys, xs = np.where(bear_m); pad = 6
x0, x1 = max(xs.min()-pad,0), min(xs.max()+pad+1, sw); y0_, y1 = max(ys.min()-pad,0), min(ys.max()+pad+1, sh)
Cc = Fc[y0_:y1, x0:x1]; Ac = (alpha*bear_m)[y0_:y1, x0:x1]
dw, dh = int(round((x1-x0)*s/DOT)), int(round((y1-y0_)*s/DOT))
cu = np.clip(cv2.resize(Cc, (dw,dh), interpolation=cv2.INTER_CUBIC), 0, 1)
au = np.clip(cv2.resize(Ac, (dw,dh), interpolation=cv2.INTER_CUBIC), 0, 1)[...,None]
pap = np.array(PAPER, np.float32)/255
comp = cu*au + pap*(1-au)
# yerel kontrast (tuy detayi): sadece obje icinde
blur = cv2.GaussianBlur(comp, (0,0), 5.0)
comp = np.clip(comp + SHARP*(comp-blur), 0, 1)*au + pap*(1-au)
# doku esitleme: detay enerjisi dusuk bolgelerde (kulak, karin) yerel kontrast kazanci artar -> her yerde yuz kadar homojen detay
if TEX_G > 1:
    lum_ = comp @ np.array([0.2126,0.7152,0.0722], np.float32)
    det_ = lum_ - cv2.GaussianBlur(lum_, (0,0), 5.0)
    sd_ = np.sqrt(cv2.GaussianBlur(det_**2, (0,0), 20.0))
    inobj = au[...,0] > 0.9
    tgt_ = float(np.percentile(sd_[inobj], TEX_P))
    gain_ = np.clip(tgt_/(sd_+1e-3), 1.0, TEX_G)[...,None]
    bl2 = cv2.GaussianBlur(comp, (0,0), 5.0)
    comp = np.clip(bl2 + (comp-bl2)*gain_, 0, 1)*au + pap*(1-au)
    log('doku esitleme hedef sd', round(tgt_,4), 'ort kazanc', round(float(gain_[inobj].mean()),2))
labc = rgb2lab(comp)
spec = (labc[...,0] > SPEC_L) & (au[...,0] > 0.5)           # parlama: mürekkep yok
# kucuk beyaz benekleri at (gercek parlama buyuk bilesendir): <SPEC_MIN nokta
_n, _cl, _st, _ = cv2.connectedComponentsWithStats(spec.astype(np.uint8), connectivity=8)
_keep = np.zeros(_n, bool); _keep[1:] = _st[1:,4] >= int(os.environ.get('SPEC_MIN', 20))
spec = _keep[_cl]
comp[spec] = pap
# palet adaylari: tonlari dengeli ornekleyen k-means, birkac tohum/dengeleme; her adayi GERCEKTEN tramlayip puanla
sel = (au[...,0] > 0.9) & ~spec
px_all = labc[sel].astype(np.float32)
lin = lambda v: np.where(v <= 0.04045, v/12.92, ((v+0.055)/1.055)**2.4).astype(np.float32)
bear_names = (["Siyah","Siyah Kahve","Koyu Kahve","Kahve","Orta Kahve","Karamel","Acik Karamel","Krem","Ekstra"])[:NK]
bear_names = bear_names if NK >= 4 else [f"Ton {i+1}" for i in range(NK)]
def make_pal(seed, pal_a, band=(10, 28)):
    rs = np.random.RandomState(seed); bins = np.clip((px_all[:,0]/4).astype(int), 0, 24); cnt = np.bincount(bins, minlength=25).astype(np.float64)
    w = 1.0/np.maximum(cnt[bins], 1)**pal_a; w /= w.sum()
    px = px_all[rs.choice(len(px_all), min(len(px_all), 300000), replace=len(px_all) < 300000, p=w)]
    cv2.setRNGSeed(seed)
    c = cv2.kmeans(px, NK-1, None, (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,60,0.1), 3, cv2.KMEANS_PP_CENTERS)[2]
    c = c[np.argsort(c[:,0])]
    _lo, _hi = np.percentile(px_all[:,0], list(band)); c[0] = px_all[(px_all[:,0] >= _lo) & (px_all[:,0] <= _hi)].mean(0)   # koyu sicak ton (siyah kahve); en uc koyu = ayri siyah
    # NOTR SIYAH: koyu golgeler notr (R~G~B); kahve-siyah murekkep onlara uymaz -> dusuk kromali en koyu piksellerden ayri siyah
    ch = np.hypot(px_all[:,1], px_all[:,2]); nd = px_all[(ch < BLK_C)]
    blk = nd[nd[:,0] <= np.percentile(nd[:,0], 8)].mean(0) if len(nd) > 500 else c[0]*0.8
    blk[0] = min(blk[0], c[0][0]-4)
    return np.vstack([blk[None], c])
here = os.path.dirname(os.path.abspath(__file__))
lib_name = 'fs_dither.dll' if os.name == 'nt' else 'fs_dither.so'
lib_path = os.path.join(here, lib_name)
c_src = os.path.join(here, 'fs_dither.c')
lib = None
if not os.path.exists(lib_path):
    try:
        cmd = f'gcc -O2 -shared -fPIC -o "{lib_path}" "{c_src}"' if os.name != 'nt' else f'gcc -O2 -shared -o "{lib_path}" "{c_src}"'
        os.system(cmd)
    except Exception:
        pass
if os.path.exists(lib_path):
    try:
        lib = ctypes.CDLL(lib_path)
    except Exception:
        lib = None

if lib is None:
    import math
    class FallbackLib:
        def fs_dither(self, img_in, h, w, pal_in, m, out_in, gam=1):
            if isinstance(img_in, (ctypes.c_void_p, int)):
                img_arr = np.ctypeslib.as_array(ctypes.cast(img_in, ctypes.POINTER(ctypes.c_float)), shape=(h, w, 3))
            elif hasattr(img_in, 'contents'):
                img_arr = np.ctypeslib.as_array(img_in, shape=(h, w, 3))
            else:
                img_arr = np.asarray(img_in).reshape((h, w, 3))

            if isinstance(pal_in, (ctypes.c_void_p, int)):
                pal_arr = np.ctypeslib.as_array(ctypes.cast(pal_in, ctypes.POINTER(ctypes.c_float)), shape=(m, 3))
            elif hasattr(pal_in, 'contents'):
                pal_arr = np.ctypeslib.as_array(pal_in, shape=(m, 3))
            else:
                pal_arr = np.asarray(pal_in).reshape((m, 3))

            if isinstance(out_in, (ctypes.c_void_p, int)):
                out_arr = np.ctypeslib.as_array(ctypes.cast(out_in, ctypes.POINTER(ctypes.c_uint8)), shape=(h, w))
            elif hasattr(out_in, 'contents'):
                out_arr = np.ctypeslib.as_array(out_in, shape=(h, w))
            else:
                out_arr = np.asarray(out_in).reshape((h, w))

            pal_list = pal_arr.tolist()
            pal_calc = [[math.sqrt(max(c, 0.0)) for c in row] for row in pal_list] if gam else pal_list

            for y in range(h):
                ltr = (y % 2 == 0)
                xs = range(w) if ltr else range(w - 1, -1, -1)
                dx = 1 if ltr else -1
                for x in xs:
                    p0, p1, p2 = img_arr[y, x]
                    if gam:
                        s0, s1, s2 = math.sqrt(max(p0, 0.0)), math.sqrt(max(p1, 0.0)), math.sqrt(max(p2, 0.0))
                    else:
                        s0, s1, s2 = p0, p1, p2
                    best = 0
                    bd = 1e30
                    for i in range(m):
                        c0, c1, c2 = pal_calc[i]
                        d0, d1, d2 = s0 - c0, s1 - c1, s2 - c2
                        d = d0 * d0 + d1 * d1 + d2 * d2
                        if d < bd:
                            bd = d
                            best = i
                    out_arr[y, x] = best
                    bp0, bp1, bp2 = pal_list[best]
                    e0, e1, e2 = p0 - bp0, p1 - bp1, p2 - bp2
                    if 0 <= x + dx < w:
                        img_arr[y, x + dx, 0] += e0 * 0.4375
                        img_arr[y, x + dx, 1] += e1 * 0.4375
                        img_arr[y, x + dx, 2] += e2 * 0.4375
                    if y + 1 < h:
                        if 0 <= x - dx < w:
                            img_arr[y + 1, x - dx, 0] += e0 * 0.1875
                            img_arr[y + 1, x - dx, 1] += e1 * 0.1875
                            img_arr[y + 1, x - dx, 2] += e2 * 0.1875
                        img_arr[y + 1, x, 0] += e0 * 0.3125
                        img_arr[y + 1, x, 1] += e1 * 0.3125
                        img_arr[y + 1, x, 2] += e2 * 0.3125
                        if 0 <= x + dx < w:
                            img_arr[y + 1, x + dx, 0] += e0 * 0.0625
                            img_arr[y + 1, x + dx, 1] += e1 * 0.0625
                            img_arr[y + 1, x + dx, 2] += e2 * 0.0625

    lib = FallbackLib()

GAM = int(os.environ.get('GAM', 1))
if DITH_N > 0:
    _nz = cv2.GaussianBlur(np.random.RandomState(1).randn(dh, dw).astype(np.float32), (0,0), 0.8); _nz /= _nz.std()
    comp_d = np.where(au > 0.5, np.clip(np.sqrt(np.clip(comp,0,1)) + DITH_N*_nz[...,None], 0, 1)**2, comp)
else: comp_d = comp
img = np.ascontiguousarray(lin(comp_d))
objm = (au[...,0] > 0.5) & ~spec
comp_s = cv2.resize(comp, (dw//2, dh//2), interpolation=cv2.INTER_AREA); lab_s = rgb2lab(comp_s)
FLAT_W = float(os.environ.get('FLAT_W', 0.5))
def run_pal(cen):
    rg = np.clip(cv2.cvtColor(cen.reshape(1,-1,3), cv2.COLOR_Lab2RGB).reshape(-1,3), 0, 1)
    pl = np.ascontiguousarray(lin(np.vstack([pap[None], rg]).astype(np.float32)))
    ix = np.zeros((dh,dw), np.uint8)
    _im = img.copy(); lib.fs_dither(_im.ctypes.data_as(ctypes.c_void_p), dh, dw, pl.ctypes.data_as(ctypes.c_void_p), len(pl), ix.ctypes.data_as(ctypes.c_void_p), GAM)
    ix[spec] = 0
    return rg, pl, ix
def score(rg, ix):
    col = np.vstack([pap[None], rg]).astype(np.float32)[ix]
    de = np.sqrt(((rgb2lab(cv2.resize(col, (dw//2, dh//2), interpolation=cv2.INTER_AREA)) - lab_s)**2).sum(2))
    om = cv2.resize(objm.astype(np.uint8), (dw//2, dh//2), interpolation=cv2.INTER_AREA) > 0
    ixf = ix.astype(np.int16); K = 15
    flat = (cv2.dilate(ixf, np.ones((K,K))) == cv2.erode(ixf, np.ones((K,K)))) & objm
    dk = objm & (labc[...,0] < 42)                                                  # koyu kutleler (kulak, karin, cene alti)
    fl = 100*(flat & dk).sum()/max(dk.sum(),1)
    return de[om].mean(), fl
AM = os.environ.get('AM', '0') == '1'                                           # AM tram (atolye yontemi): yuvarlak nokta, sabit lpi/aci
if AM:
    LPI = float(os.environ.get('LPI', 45)); ANG = float(os.environ.get('ANG', 15)); DMIN = float(os.environ.get('DMIN', 0.03))
    cen = make_pal(int(os.environ.get('PAL_SEED', 0)), 0.0, (3, 8))
    rgbp = np.clip(cv2.cvtColor(cen.reshape(1,-1,3), cv2.COLOR_Lab2RGB).reshape(-1,3), 0, 1)
    BEAR = {nm: tuple(int(round(v*255)) for v in c) for nm, c in zip(bear_names, rgbp)}
    bdist = [np.linalg.norm(cen[i]-badge_L) for i in range(NK)]; BADGE_INK = bear_names[int(np.argmin(bdist))]
    log('AM palet', BEAR, 'rozet:', BADGE_INK, 'lpi', LPI, 'aci', ANG)
    # ton zinciri: kagit -> en acik murekkep -> ... -> en koyu (Lab'da poligon); her piksel zincire izdusurulur
    paper_lab = rgb2lab(np.uint8(np.array(PAPER))[None,None,:])[0,0]
    nodes = np.vstack([paper_lab[None], cen[::-1]]).astype(np.float32)          # dugum j (1..NK) = murekkep no NK-j+1
    nid = np.array([0] + [NK-j+1 for j in range(1, NK+1)], np.uint8)
    labd = rgb2lab(comp); objd = au[...,0] > 0.5
    u = np.zeros((dh, dw), np.float32)
    for r0 in range(0, dh, 256):
        P = labd[r0:r0+256]; bd = np.full(P.shape[:2], 1e18, np.float32); bu = np.zeros(P.shape[:2], np.float32)
        for sg in range(NK):
            A_, B_ = nodes[sg], nodes[sg+1]; AB = B_-A_
            tt = np.clip(((P-A_)@AB)/float(AB@AB), 0, 1); dd = ((P-(A_+tt[...,None]*AB))**2).sum(2)
            m = dd < bd; bd[m] = dd[m]; bu[m] = sg + tt[m]
        u[r0:r0+256] = bu
    u[~objd | spec] = 0
    # ekran esigi: yuvarlak nokta (kosinus spot), alan-dogrusal olacak sekilde CDF ile duzlestirilmis
    cell = PPI/LPI; ca, sa = np.cos(np.radians(ANG)), np.sin(np.radians(ANG))
    sm_ = np.random.RandomState(3).rand(2, 1000000)
    Ssamp = np.sort(1 - ((np.cos(2*np.pi*sm_[0]) + np.cos(2*np.pi*sm_[1]))/4 + 0.5)); qs = np.linspace(0, 1, Ssamp.size)
    uu = cv2.resize(u, (dw*DOT, dh*DOT), interpolation=cv2.INTER_LINEAR)
    oy, ox = int(round(y0_*s)), int(round(x0*s)); hh, ww = min(uu.shape[0], H-oy), min(uu.shape[1], W-ox)
    bear_idx = np.zeros((H,W), np.uint8)
    for r0 in range(0, hh, 512):
        ur = uu[r0:min(r0+512, hh), :ww]; k = np.minimum(np.floor(ur).astype(np.int32), NK-1); f = ur - k
        yy = (oy + r0 + np.arange(ur.shape[0]))[:,None].astype(np.float32); xx = (ox + np.arange(ww))[None,:].astype(np.float32)
        X = (xx*ca + yy*sa)/cell; Y = (-xx*sa + yy*ca)/cell
        Sv = 1 - ((np.cos(2*np.pi*X) + np.cos(2*np.pi*Y))/4 + 0.5)
        T = np.interp(Sv, Ssamp, qs).astype(np.float32)
        f = np.where(f < DMIN, 0, np.where(f > 1-DMIN, 1, f))
        bear_idx[oy+r0:oy+r0+ur.shape[0], ox:ox+ww] = nid[np.where(f > T, k+1, k)]
    del uu, u, labd
    big = None
    log('AM tram bitti')
else:
    cands = []
    for seed in range(int(os.environ.get('PAL_N', 3))):
        for pa in (0.0, 0.3):
            for band in ((3, 8), (10, 28), (18, 40)):
                c = make_pal(seed, pa, band); rg, pl, ix = run_pal(c); de, fl = score(rg, ix)
                cands.append((de + FLAT_W*fl, de, fl, seed, (pa, band), c, rg, pl, ix))
                log(f'  palet adayi tohum{seed} dengeleme{pa} bant{band}: dE {de:.2f} koyu-duz-leke %{fl:.1f} puan {de+FLAT_W*fl:.2f}')
        cands = sorted(cands, key=lambda r: r[0])[:4]                                    # bellek: en iyi 4 aday kalir
    best = min(cands, key=lambda r: r[0]); _, _, _, bseed, bpa, cen, rgbp, pal, idx = best
    log('SECILEN palet: tohum', bseed, 'dengeleme/bant', bpa)
    BEAR = {nm: tuple(int(round(v*255)) for v in c) for nm, c in zip(bear_names, rgbp)}
    bdist = [np.linalg.norm(cen[i]-badge_L) for i in range(NK)]; BADGE_INK = bear_names[int(np.argmin(bdist))]
    log('palet', BEAR, 'rozet:', BADGE_INK)
    idx[spec] = 0
    # koyu/orta bolgelerdeki izole kagit (beyaz) noktalari en yakin murekkebe cevir
    lum2 = comp @ np.array([0.2126,0.7152,0.0722], np.float32)
    bl_l = cv2.GaussianBlur(lum2, (0,0), 3.0)
    ppx = ((idx == 0) & (au[...,0] > 0.5) & ~spec).astype(np.uint8)
    nb = cv2.boxFilter(ppx.astype(np.float32), -1, (5,5), normalize=False) - ppx
    fix = (ppx > 0) & ((bl_l < 0.55) | ((nb < 3) & (bl_l < 0.85)))
    if fix.any():
        pg = np.sqrt(pal[1:]); cg = np.sqrt(np.clip(lin(comp[fix]), 0, 1))
        idx[fix] = 1 + np.argmin(((cg[:,None,:]-pg[None,:,:])**2).sum(2), axis=1)
    log('hata yayilimi bitti', idx.shape, 'temizlenen beyaz nokta', int(fix.sum()))
    big = np.repeat(np.repeat(idx, DOT, 0), DOT, 1)
    oy, ox = int(round(y0_*s)), int(round(x0*s)); hh, ww = min(big.shape[0], H-oy), min(big.shape[1], W-ox)
    bear_idx = np.zeros((H,W), np.uint8); bear_idx[oy:oy+hh, ox:ox+ww] = big[:hh,:ww]
del big, img, comp, cu, au

# ---------- 4) filmler ----------
inks = dict(BEAR); inks[NAVY[0]] = NAVY[1]
masks = {nm: (bear_idx == i+1) for i, nm in enumerate(bear_names)}
masks[NAVY[0]] = navy_f
# duz rozet rengi: palette en yakin murekkep kaynak rozet renginden cok farkliysa uyar (2026-10-14: kahve rozet siyaha gitti).
# BADGE_INK_OWN=1: rozete kendi murekkebi (ek film/kafa) verilir; yoksa en yakin murekkebi paylasir.
_bde = float(np.linalg.norm(rgb2lab(np.array([[inks[BADGE_INK]]], np.uint8))[0,0] - badge_L))
UYARI = []
if os.environ.get('BADGE_INK_OWN', '0') == '1' and _bde > 6:
    inks['Rozet'] = tuple(int(v) for v in badge_rgb); masks['Rozet'] = badge_f
    log('rozet kendi murekkebi (ek film): rgb', inks['Rozet'], '| en yakin palet murekkebi dE', round(_bde,1))
else:
    masks[BADGE_INK] |= badge_f
    log('rozet murekkebi', BADGE_INK, 'dE (kaynak rozet rengine)', round(_bde,1))
    if _bde > 12:
        UYARI.append(f'rozet rengi {BADGE_INK} murekkebine atandi ama kaynak renkten dE {_bde:.0f} uzak: BADGE_INK_OWN=1 ile ayri murekkep ver ya da paleti elle duzelt')
        log('UYARI:', UYARI[-1])
DUZ = [{'ad': 'rozet', 'film': None, 'bbox': None, 'kaynak_rgb': [int(v) for v in badge_rgb]}] if badge_f.any() else []
if DUZ:
    _ys, _xs = np.where(badge_f); DUZ[0]['bbox'] = [int(_xs.min()), int(_ys.min()), int(_xs.max()-_xs.min()+1), int(_ys.max()-_ys.min()+1)]
del bear_idx
lum = lambda c: rgb2lab(np.array([[c]], np.uint8))[0,0,0]
order = sorted(inks, key=lambda k: -lum(inks[k]))
def save(mask, path): Image.frombytes('1',(W,H),np.packbits(~mask,axis=1).tobytes()).save(path, dpi=(PPI,PPI), compress_level=6)
sets = []
for n_, k in enumerate(order):
    fn = f"{n_+1:02d}_{k.replace(' ','_')}.png"; save(masks[k], os.path.join(out_dir,"Acik_Tisort",fn)); sets.append([f"{n_+1:02d} {k}", fn, list(inks[k])])
    log('kaydedildi', fn, 'kapsama %', round(100*masks[k].mean(),2))
_fn_of = {k: sets[i][1] for i, k in enumerate(order)}
if DUZ: DUZ[0]['film'] = _fn_of['Rozet' if 'Rozet' in inks else BADGE_INK]
if navy_f.any():
    _ys, _xs = np.where(navy_f); DUZ.append({'ad': 'lacivert', 'film': _fn_of[NAVY[0]], 'bbox': [int(_xs.min()), int(_ys.min()), int(_xs.max()-_xs.min()+1), int(_ys.max()-_ys.min()+1)], 'kaynak_rgb': list(NAVY[1])})
json.dump({'W':W,'H':H,'ppi':PPI,'dot_px':DOT,'sets':{'Acik_Tisort':sets}, 'duz_bolgeler': DUZ, 'uyarilar': UYARI}, open(os.path.join(out_dir,'kanallar_hibrit.json'),'w'), ensure_ascii=False, indent=1)
canvas = np.zeros((H,W,3), np.uint8); canvas[:] = (250,250,250)
for k in order: canvas[masks[k]] = inks[k]
Image.fromarray(cv2.resize(canvas,(W//8,H//8),interpolation=cv2.INTER_AREA)).save(os.path.join(out_dir,'onizleme_acik.png'))
Image.fromarray(canvas).crop((0,0,W,H)).save(os.path.join(out_dir,'_tam_onizleme.png')) if False else None
np.save(os.path.join(out_dir,'_scale.npy'), np.array([s]))
# yuz kirpmalari (kaynak koordinati, 600 PPI)
def cropsrc(x0_, y0__, x1_, y1__):
    x0_, y0__, x1_, y1__ = [int(round(v*K)) for v in (x0_, y0__, x1_, y1__)]
    return canvas[int(y0__*s):int(y1__*s), int(x0_*s):int(x1_*s)]
import re as _re
cx=[int(v) for v in os.environ.get('CROP','390,770,500,890').split(',')]; Image.fromarray(cropsrc(*cx)).save(os.path.join(out_dir,'_kirp.png'))
Image.fromarray(cropsrc(440,700,540,780)).save(os.path.join(out_dir,'_goz.png')); Image.fromarray(cropsrc(480,820,600,900)).save(os.path.join(out_dir,'_cene.png'))
for item in os.environ.get('CROPS','').split(';'):
    if ':' in item:
        nm, bx = item.split(':'); bx = [int(v) for v in bx.split(',')]; Image.fromarray(cropsrc(*bx)).save(os.path.join(out_dir, f'_{nm}.png'))
# ---------- 5) bolge testi: her calismada tum bolgelerde ton hatasi + doku orani ----------
REG = {'yuz':(432,722,612,847),'cene':(425,837,622,902),'kol':(487,902,632,992),'ayak':(252,1137,387,1217),
       'kulak':(622,522,722,632),'karin':(397,1020,632,1137)}   # 1024 genislik birimi; K ile olceklenir (bu gorsel dizilimi icin)
for item in os.environ.get('REGIONS','').split(';'):
    if ':' in item: nm, bx = item.split(':'); REG[nm] = tuple(int(v) for v in bx.split(','))
log('BOLGE TESTI (dE ort / dE p95 / doku orani sonuc/kaynak; hedef: dE<8, doku 0.6-1.2)')
for nm, (a0,b0,a1,b1) in REG.items():
    a0,b0,a1,b1 = [int(round(v*K)) for v in (a0,b0,a1,b1)]
    if a1 > sw or b1 > sh: continue
    res = cv2.resize(canvas[int(b0*s):int(b1*s), int(a0*s):int(a1*s)], (a1-a0, b1-b0), interpolation=cv2.INTER_AREA)
    ref = src[b0:b1, a0:a1]
    La, Lb = rgb2lab(res), rgb2lab(ref); de = np.sqrt(((La-Lb)**2).sum(2))
    hp = lambda L: (L[...,0]-cv2.GaussianBlur(L[...,0], (0,0), 2.0*K)).std()
    cr = canvas[int(b0*s):int(b1*s), int(a0*s):int(a1*s)].astype(np.int16); ob = (np.abs(cr-250).sum(2) > 12)
    sm = cr.sum(2).astype(np.float32); KW = 15
    flat = (cv2.dilate(sm, np.ones((KW,KW))) - cv2.erode(sm, np.ones((KW,KW))) == 0) & ob
    FL = 100*flat.sum()/max(ob.sum(),1)
    log(f'  {nm:6s} duz-leke %{FL:4.1f}  dE {de.mean():5.1f} / {np.percentile(de,95):5.1f}   doku {hp(La)/max(hp(Lb),1e-6):.2f}')
log('BITTI')
