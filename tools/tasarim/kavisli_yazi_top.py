"""Katmanli tasarim ureticisi: kavisli (U yollu) yazilar + ozgun cizim basketbol/dunya topu.
Her nesne ayri seffaf PNG (bbox'a kirpili) + katmanlar.json uretir; Photoshop'ta katman_pds_olustur.jsx ile PSD yapilir.
Kullanim: python3 kavisli_yazi_top.py cikti_klasoru
Yazi fontu: Orbitron (SIL OFL), klasorde .ttf.
"""
import sys, os, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageChops
Image.MAX_IMAGE_PIXELS = None
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
PPI = 600; W = 7087; H = int(round(738/663*W)); K = W/663          # orijinal oran: 663x738
INNER = "THE LOS ANGELES LAKERS ARE A PROFESSIONAL BASKETBALL TEAM WHO PLAY IN THE NBA"
OUTER = ["LOS ANGELES LAKERS -", "LOS ANGELES LAKERS-", "LOS ANGELES LAKERS"]
BLACK = (17,17,17); GRAY = (95,95,95)
layers = []
def save_layer(name, rgba, file, ox=0, oy=0):
    im = Image.fromarray(rgba, 'RGBA') if isinstance(rgba, np.ndarray) else rgba
    bb = im.getchannel('A').getbbox()
    if bb is None: return
    im.crop(bb).save(os.path.join(out, file), dpi=(PPI,PPI)); layers.append({"name": name, "file": file, "x": bb[0]+ox, "y": bb[1]+oy})
    print('katman', name, bb, flush=True)

# ---------- yol ----------
def make_path(cx, rx, y0, yb, ry):
    pts = [(cx-rx, y) for y in np.arange(y0, yb, 0.25/K)]
    for phi in np.linspace(math.pi, 0, 4000): pts.append((cx+rx*math.cos(phi), yb+ry*math.sin(phi)))
    pts += [(cx+rx, y) for y in np.arange(yb, y0, -0.25/K)]
    P = np.array(pts)*K; d = np.r_[0, np.cumsum(np.hypot(*np.diff(P,axis=0).T))]
    return P, d
def at(P, d, s):
    i = int(np.clip(np.searchsorted(d, s), 1, len(d)-1)); t = P[min(i+3,len(P)-1)] - P[max(i-3,0)]
    return P[i], math.degrees(math.atan2(-t[1], t[0]))
def draw_text_on_path(text, font_path, size, P, d, start, length, outline=0, fill=BLACK, color_mask=None, first_last=None):
    font = ImageFont.truetype(font_path, size); adv = [font.getlength(c) for c in text]
    tot = sum(adv); sc = length/tot if length else 1.0       # harf araligi olcegi (tracking)
    cap = font.getbbox('H'); caph = cap[3]-cap[1]
    D = int(size*2.4)
    mask = Image.new('L', (W, H), 0); s = start; per_char = []
    for c, a in zip(text, adv):
        a2 = a*sc; pos, ang = at(P, d, s + a2/2); s += a2
        if c == ' ': per_char.append((c, None)); continue
        g_f = Image.new('L', (D, D), 0); g_s = Image.new('L', (D, D), 0)
        ox, oy = D/2 - a/2, D/2 + caph/2                        # taban cizgisi; pivot = (adv/2, taban - cap/2)
        ImageDraw.Draw(g_f).text((ox, oy), c, font=font, fill=255, anchor='ls')
        if outline:
            ImageDraw.Draw(g_s).text((ox, oy), c, font=font, fill=255, anchor='ls', stroke_width=outline)
            g = ImageChops.subtract(g_s, g_f)
        else: g = g_f
        g = g.rotate(ang, resample=Image.BICUBIC)
        px, py = int(round(pos[0]-D/2)), int(round(pos[1]-D/2))
        reg = mask.crop((px, py, px+D, py+D)); mask.paste(ImageChops.lighter(reg, g), (px, py))
        per_char.append((c, (px+D//2, py+D//2)))
    return mask, per_char, tot*sc
def to_rgba(mask, color):
    a = np.asarray(mask); rgba = np.zeros(a.shape+(4,), np.uint8); rgba[...,:3] = color; rgba[...,3] = a; return rgba

# ---------- ic cumle ----------
Pi, di = make_path(294, 146, 128, 385, 140)
f_inner = os.path.join(HERE, 'orbitron800.ttf')
adv100 = ImageFont.truetype(f_inner, 100).getlength(INNER)
size_in = int((di[-1]*0.965)/adv100*100)
size_in = min(size_in, int(15.5*K))
m, _, used = draw_text_on_path(INNER, f_inner, size_in, Pi, di, (di[-1]-di[-1]*0.965)/2, di[-1]*0.965)
print('ic yazi boyu', size_in, 'px', round(used/di[-1],3))
save_layer('Yazi - Ic cumle', to_rgba(m, BLACK), 'yazi_ic_cumle.png')

# ---------- dis yazi (kontur) ----------
Po, do = make_path(294, 196, 128, 400, 190)
f_out = os.path.join(HERE, 'orbitron700.ttf'); full = "  ".join(OUTER)
adv100 = ImageFont.truetype(f_out, 100).getlength(full)
size_out = int((do[-1]*0.97)/adv100*100)
sw = max(4, int(size_out*0.04))
mm, per, used = draw_text_on_path(full, f_out, size_out, Po, do, (do[-1]-do[-1]*0.97)/2, do[-1]*0.97, outline=sw)
print('dis yazi boyu', size_out, 'px', 'kontur', sw)
# uc katmana bol: harf konumlarina gore (yol uzerindeki sira)
idx = []; pos = 0
for j, part in enumerate(OUTER):
    seg = list(range(pos, pos+len(part))); idx.append(seg); pos += len(part)+2
# katman: her segment icin tum yazi yeniden cizilir ama yalnizca o segment harfleri (basit yol: segmenti ayri baslangic/uzunlukla ciz)
adv_full = ImageFont.truetype(f_out, size_out).getlength(full); sc = (do[-1]*0.97)/adv_full
start0 = (do[-1]-do[-1]*0.97)/2; fnt = ImageFont.truetype(f_out, size_out)
names = ['Yazi - Dis sol', 'Yazi - Dis alt', 'Yazi - Dis sag']; files = ['yazi_dis_sol.png','yazi_dis_alt.png','yazi_dis_sag.png']
for j, part in enumerate(OUTER):
    pre = "  ".join(OUTER[:j]) + ("  " if j else "")
    s0 = start0 + fnt.getlength(pre)*sc; ln = fnt.getlength(part)*sc
    mk, _, _ = draw_text_on_path(part, f_out, size_out, Po, do, s0, ln, outline=sw)
    save_layer(names[j], to_rgba(mk, GRAY), files[j])

# ---------- top ----------
CX, CY, R = int(294*K), int(392*K), int(100*K)
B = int(R*1.25); x0, y0 = CX-B, CY-B; S = 2*B                      # top kutusu
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); X = (xx-B)/R; Y = (yy-B)/R; r2 = X*X+Y*Y
inside = r2 <= 1.0; Z = np.sqrt(np.clip(1-r2, 0, 1))
def aa_disc(rad): return np.clip((rad - np.sqrt(r2))*R/1.5 + 0.5, 0, 1)
# govde: beyaz disk + siyah halka
disc = aa_disc(1.0); ring = np.clip(disc - aa_disc(0.965), 0, 1)
body = np.zeros((S,S,4), np.uint8); body[...,:3] = 255; body[...,3] = (disc*255).astype(np.uint8)
body[...,:3] = (np.array(BLACK)[None,None,:]*ring[...,None] + 255*(1-ring[...,None])).astype(np.uint8)
save_layer('Top - Govde', body, 'top_govde.png', x0, y0)
# tarama: degisken kalinlikli capraz cizgi (isik ust-sag)
L = np.array([0.55,-0.55,0.63]); L /= np.linalg.norm(L)
dark = np.clip(1.0 - (X*L[0]+Y*L[1]+Z*L[2]), 0, 1)*0.75 + 0.1*(1-Z)
def hatch(angle, pitch, dk, thr):
    a = math.radians(angle); u = (xx*math.cos(a)+yy*math.sin(a))/pitch; dist = np.abs(u-np.round(u))*pitch
    half = np.clip((dk-thr)/(1-thr), 0, 1)**0.9*pitch*0.46
    return np.clip(half - dist + 0.75, 0, 1)
h = np.maximum(hatch(38, 15, dark, 0.18), hatch(-38, 15, dark, 0.58))
h = h*aa_disc(0.955)
tar = np.zeros((S,S,4), np.uint8); tar[...,:3] = BLACK; tar[...,3] = (h*255).astype(np.uint8)
save_layer('Top - Tarama', tar, 'top_tarama.png', x0, y0)
# dunya haritasi: ortografik, kareli (halftone-izgara) dolgu
import geopandas as gpd, shapely
from shapely.ops import unary_union
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')); land = unary_union(world.geometry)
lon0, lat0 = math.radians(-92), math.radians(12)
pitch = int(R*0.085); gx = np.arange(pitch//2, S, pitch); GX, GY = np.meshgrid(gx, gx)
px = (GX-B)/R; py = -(GY-B)/R; rho = np.hypot(px, py); ok = rho <= 0.93
c = np.arcsin(np.clip(rho, 0, 1)); sc_, cc_ = np.sin(c), np.cos(c)
with np.errstate(all='ignore'):
    lat = np.arcsin(np.clip(cc_*math.sin(lat0) + np.where(rho>0, py*sc_*math.cos(lat0)/rho, 0), -1, 1))
    lon = lon0 + np.arctan2(px*sc_, rho*math.cos(lat0)*cc_ - py*math.sin(lat0)*sc_)
lon_d = (np.degrees(lon)+180)%360-180; lat_d = np.degrees(lat)
island = shapely.contains_xy(land, lon_d.ravel(), lat_d.ravel()).reshape(lon_d.shape) & ok
patch = (((GX-B)/R+0.12)/0.95)**2 + (((GY-B)/R-0.22)/0.78)**2 <= 1.0      # sol-alt yama
cells = island & patch
mp = np.zeros((S,S,4), np.uint8); white = np.zeros((S,S), np.uint8); blk = np.zeros((S,S), np.uint8)
for gx_, gy_ in zip(GX[cells], GY[cells]):
    cv2.rectangle(white, (int(gx_-pitch/2), int(gy_-pitch/2)), (int(gx_+pitch/2), int(gy_+pitch/2)), 255, -1)
    q = int(pitch*0.30); cv2.rectangle(blk, (int(gx_-q), int(gy_-q)), (int(gx_+q), int(gy_+q)), 255, -1, cv2.LINE_AA)
mp[...,:3] = 255; mp[...,3] = white
mp[...,:3] = np.where(blk[...,None] > 0, (np.array(BLACK)*blk[...,None]/255 + 255*(1-blk[...,None]/255)).astype(np.uint8), 255)
save_layer('Top - Dunya haritasi', mp, 'top_harita.png', x0, y0)
# dikisler: 3B buyuk/kucuk daireler, on yuz; beyaz hale + siyah
def rot(v, ax, ay, az):
    cx_, sx_, cy_, sy_, cz_, sz_ = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1,0,0],[0,cx_,-sx_],[0,sx_,cx_]]); Ry = np.array([[cy_,0,sy_],[0,1,0],[-sy_,0,cy_]]); Rz = np.array([[cz_,-sz_,0],[sz_,cz_,0],[0,0,1]])
    return v @ (Rz@Ry@Rx).T
def circle3d(normal, offset, n=1400):
    nrm = np.array(normal, float); nrm /= np.linalg.norm(nrm); a = np.cross(nrm, [0,0,1.0]);
    if np.linalg.norm(a) < 1e-6: a = np.cross(nrm, [0,1.0,0])
    a /= np.linalg.norm(a); b = np.cross(nrm, a); rr = math.sqrt(1-offset**2)
    t = np.linspace(0, 2*math.pi, n); return nrm[None]*offset + rr*(np.cos(t)[:,None]*a[None] + np.sin(t)[:,None]*b[None])
seams = [circle3d([1,0,0], 0.0), circle3d([0,1,0], 0.0), circle3d([0,0,1], 0.0)*0, circle3d([1,0,0], 0.62), circle3d([1,0,0], -0.62)]
seams = [circle3d([1,0,0], 0.0), circle3d([0,1,0], 0.0), circle3d([1,0,0], 0.62), circle3d([1,0,0], -0.62)]
halo = np.zeros((S,S), np.uint8); inkm = np.zeros((S,S), np.uint8)
for sm in seams:
    v = rot(sm, math.radians(-18), math.radians(22), math.radians(28)); front = v[:,2] > 0.02
    seg = []
    for i in range(len(v)):
        if front[i]: seg.append((B+v[i,0]*R*0.98, B+v[i,1]*R*0.98))
        elif len(seg) > 1: seg = seg if False else seg; cv2.polylines(halo, [np.array(seg, np.int32)], False, 255, int(R*0.12), cv2.LINE_AA); cv2.polylines(inkm, [np.array(seg, np.int32)], False, 255, int(R*0.058), cv2.LINE_AA); seg = []
        else: seg = []
    if len(seg) > 1: cv2.polylines(halo, [np.array(seg, np.int32)], False, 255, int(R*0.12), cv2.LINE_AA); cv2.polylines(inkm, [np.array(seg, np.int32)], False, 255, int(R*0.058), cv2.LINE_AA)
clip = aa_disc(0.985); halo = (halo*clip).astype(np.uint8); inkm = (inkm*clip).astype(np.uint8)
dk = np.zeros((S,S,4), np.uint8); a_ = np.maximum(halo, inkm)
col = np.where(inkm[...,None] > 128, np.array(BLACK, np.uint8)[None,None,:], 255).astype(np.uint8)
dk[...,:3] = col; dk[...,3] = a_
save_layer('Top - Dikisler', dk, 'top_dikisler.png', x0, y0)
json.dump({'W': W, 'H': H, 'ppi': PPI, 'layers': layers}, open(os.path.join(out, 'katmanlar.json'), 'w'), ensure_ascii=False, indent=1)
# onizleme
prev = Image.new('RGB', (W, H), 'white')
for l in layers:
    im = Image.open(os.path.join(out, l['file'])); prev.paste(im, (l['x'], l['y']), im)
prev.resize((W//7, H//7), Image.LANCZOS).save(os.path.join(out, 'onizleme.png')); print('BITTI')
