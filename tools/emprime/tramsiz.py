import sys, os, time, math, json
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src_path, out_dir = sys.argv[1], sys.argv[2]

PPI = 600; WCM = 38.5
TRAP_PX = 4                       # ~0.17 mm: acik renk, koyu rengin altina tasar
CHOKE_PT = 2.0                    # underbase daraltma (punto)
CHOKE_PX = int(round(CHOKE_PT/72*PPI))
MED = 5                           # leke temizleme (medyan) cekirdegi
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
os.makedirs(out_dir, exist_ok=True)

# gercek murekkepler (onceki otomatik tespit; kenar ara tonlari elenmis)
INKS = {"Siyah": (24,25,47), "Mavi 1": (9,43,121), "Mavi 2": (59,113,158), "Kirmizi": (231,47,15)}

def rgb2lab(a):
    f = a.astype(np.float32)/255.0 if a.dtype == np.uint8 else a.astype(np.float32)
    return cv2.cvtColor(f, cv2.COLOR_RGB2Lab)

names = list(INKS)
rgbs = np.array([INKS[n] for n in names], np.uint8)
labs = rgb2lab(rgbs.reshape(1,-1,3)).reshape(-1,3)
order = np.argsort(-labs[:,0])            # acik -> koyu (baski sirasi)
names = [names[i] for i in order]; rgbs = rgbs[order]; labs = labs[order]
WHITE = rgb2lab(np.array([[[255,255,255]]], np.uint8))[0,0]
pal = np.vstack([WHITE, labs]).astype(np.float32)      # sinif 0 = beyaz/kagit
m = len(pal)
log('baski sirasi', names)

src = np.asarray(Image.open(src_path).convert('RGB'))
sh, sw = src.shape[:2]
W = int(round(WCM/2.54*PPI)); s = W/sw; H = int(round(sh*s))
log('kaynak', sw, sh, 'hedef', W, H, f'{W*H/1e6:.0f} MP', 'choke px', CHOKE_PX)

lab_path = os.path.join(out_dir, '_labels_cache.npy')
if os.path.exists(lab_path):
    L = np.load(lab_path); log('labels.npy yuklendi')
else:
    L = np.zeros((H, W), np.uint8)
    pairs = [(i,j) for i in range(m) for j in range(i+1, m)]
    TH = 256
    for y0 in range(0, H, TH):
        h = min(TH, H-y0); N = h*W
        M = np.float32([[1/s,0,0.5/s-0.5],[0,1/s,(y0+0.5)/s-0.5]])
        tile = cv2.warpAffine(src, M, (W,h), flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        lab = rgb2lab(tile).reshape(-1,3)
        best = np.full(N, 1e9, np.float32); cls = np.zeros(N, np.uint8)
        for i in range(m):                                   # saf renk
            d = lab-pal[i]; e = (d*d).sum(1); mk = e < best; best[mk] = e[mk]; cls[mk] = i
        for (i,j) in pairs:                                  # iki renk karisimi (kenar yumusatma)
            ab = pal[j]-pal[i]; den = float((ab*ab).sum())
            d = lab-pal[i]; t = np.clip((d@ab)/den, 0, 1)
            r = d-t[:,None]*ab; e = (r*r).sum(1)
            mk = e < best; best[mk] = e[mk]; cls[mk] = np.where(t[mk] >= 0.5, j, i)
        L[y0:y0+h] = cls.reshape(h, W)
        if (y0//TH) % 10 == 0: log('tile', y0//TH+1, '/', math.ceil(H/TH))
    np.save(lab_path, L); log('siniflandirma bitti')

# leke / JPEG gurultusu temizligi (siralı etiketlerde medyan: yeni sinif uretmez)
L = cv2.medianBlur(L, MED); log('medyan temizlik')

def dist_in(mask):          # maske icindeki piksellerin disariya uzakligi
    return cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
def dilate_px(mask, r):
    d = cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5)
    return d <= r

# ince (baskiya uygun olmayan) halka/leke temizligi: genisligi < 2*THIN_R+1 px olan mürekkep parcalari komsu sinifa verilir
THIN_R = 3
unknown = np.zeros(L.shape, bool)
for c in range(1, len(names)):          # en koyu mürekkep (Siyah) haric: ince siyah cizgiler korunur
    mk = (L == c)
    op = dilate_px(dist_in(mk) > THIN_R, THIN_R)
    unknown |= mk & ~op
    del mk, op
log('ince parca piksel %', round(100*unknown.mean(), 3))
known = ~unknown
lbl = cv2.distanceTransformWithLabels(unknown.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)[1]
known_vals = L[known]
L[unknown] = known_vals[lbl[unknown]-1]
del lbl, known_vals, known, unknown
log('ince parca temizligi bitti')

# kagit (disarisi) ve tasarim beyazi ayrimi: kenara bagli beyaz = tisort/kagit.
# kucuk anahat bosluklarindan sizmayi onlemek icin beyaz once 3 px asindirilir
white = (L == 0)
core = dist_in(white) > 3
n_cc, cc = cv2.connectedComponents(core.astype(np.uint8), connectivity=4, ltype=cv2.CV_32S)
border = np.unique(np.concatenate([cc[0,:], cc[-1,:], cc[:,0], cc[:,-1]]))
lut = np.zeros(n_cc+1, bool); lut[border] = True; lut[0] = False
outside_core = lut[cc]; del cc, core
outside = dilate_px(outside_core, 4) & white
del outside_core
dwhite = white & ~outside
log('beyaz bilesen', n_cc, 'tasarim beyazi %', round(100*dwhite.mean(),2))

masks = {k: (L == (k+1)) for k in range(len(names))}     # k=0 en acik mürekkep
del white

# trap: acik renk, kendinden koyu renklerin altina TRAP_PX tasar
final = {}
for k in range(len(names)):
    darker = np.zeros((H,W), bool)
    for q in range(k+1, len(names)): darker |= masks[q]
    final[k] = masks[k] | (dilate_px(masks[k], TRAP_PX) & darker) if darker.any() else masks[k]
    log('trap', names[k])

# underbase (koyu tisort): tum mürekkep + tasarim beyazi birlesimi, sadece disa bakan kenarlarda choke
U = np.zeros((H,W), bool)
for k in masks: U |= masks[k]
U |= dwhite
E = dist_in(U) > CHOKE_PX
opened = dilate_px(~E, 0) if False else None
d_out = cv2.distanceTransform((~E).astype(np.uint8), cv2.DIST_L2, 5)
recon = d_out <= CHOKE_PX                                 # acma (opening) sonucu
thin = U & ~recon                                         # choke'ta yok olacak ince detaylar -> korunur
UB = E | thin
black = masks[len(names)-1]                               # en koyu (Siyah): altina beyaz konmaz
UB &= ~(dist_in(black) > TRAP_PX)
log('underbase hazir, kapsama %', round(100*UB.mean(),2))

def save(mask, path):
    im = Image.frombytes('1', (W,H), np.packbits(~mask, axis=1).tobytes())
    im.save(path, dpi=(PPI,PPI), compress_level=6)

sets = {"Acik_Tisort": [], "Koyu_Tisort": []}
koyu_dir = os.path.join(out_dir, "Koyu_Tisort"); acik_dir = os.path.join(out_dir, "Acik_Tisort")
os.makedirs(koyu_dir, exist_ok=True); os.makedirs(acik_dir, exist_ok=True)
save(UB, os.path.join(koyu_dir, "01_Beyaz_Zemin.png")); sets["Koyu_Tisort"].append(["01 Beyaz Zemin (underbase)", "01_Beyaz_Zemin.png", [255,255,255]])
for k in range(len(names)):
    nm = names[k]
    fa = f"{k+1:02d}_{nm.replace(' ','_')}.png"; fk = f"{k+2:02d}_{nm.replace(' ','_')}.png"
    save(final[k], os.path.join(acik_dir, fa)); sets["Acik_Tisort"].append([f"{k+1:02d} {nm}", fa, rgbs[k].tolist()])
    save(final[k], os.path.join(koyu_dir, fk)); sets["Koyu_Tisort"].append([f"{k+2:02d} {nm}", fk, rgbs[k].tolist()])
    log('kaydedildi', nm)
json.dump({'W':W,'H':H,'ppi':PPI,'sets':sets,'trap_px':TRAP_PX,'choke_px':CHOKE_PX}, open(os.path.join(out_dir,'kanallar_tramsiz.json'),'w'), ensure_ascii=False, indent=1)

# onizleme: baski sirasina gore opak katmanlama
def composite(bg, layers, sl=None):
    out = None
    for (mask, col) in layers:
        a = mask if sl is None else mask[sl]
        if out is None: out = np.zeros(a.shape+(3,), np.uint8); out[:] = bg
        out[a] = col
    return out
light_layers = [(final[k], rgbs[k]) for k in range(len(names))]
dark_layers = [(UB, (255,255,255))] + light_layers
for tag, bg, layers in (("acik", (250,250,250), light_layers), ("koyu", (28,28,30), dark_layers)):
    full = composite(bg, layers)
    Image.fromarray(cv2.resize(full, (W//8, H//8), interpolation=cv2.INTER_AREA)).save(os.path.join(out_dir, f"onizleme_{tag}.png"))
    sl = (slice(5400, 5900), slice(3000, 4400))
    Image.fromarray(composite(bg, layers, sl)).save(os.path.join(out_dir, f"onizleme_{tag}_100pct.png"))
    sl2 = (slice(4900, 6000), slice(7900, 9094))
    Image.fromarray(composite(bg, layers, sl2)).save(os.path.join(out_dir, f"onizleme_{tag}_E.png"))
    del full
log('BITTI')
