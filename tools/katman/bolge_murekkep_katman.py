#!/usr/bin/env python3
"""Az murekkepli baski gorselini BOLGE GRUBU x MUREKKEP KATMANI olarak PSD'ye ayirir.

Kullanim: python3 tools/katman/bolge_murekkep_katman.py girdi.jpg bolgeler.npz cikti.psd [--ceza bolge1:Siyah=8,bolge2:Kirmizi=8]

bolgeler.npz: her anahtar bir bolge adi, deger = HxW bool maske. Maskeler ayrik olmali
(ortusme 0, bosluk 0); yoksa betik durur. Anahtar sirasi = grup sirasi (ilk anahtar en altta).
Maskeler bolgenin yapi piksellerinden uretilir, dikdortgenden degil (bilgi/katman-ayirma.md B).

Yontem (bilgi/katman-ayirma.md 2026-10-20):
 1) Her bolgede murekkep renkleri ayri kestirilir: Krem (parlak %20 medyani), Siyah (koyu %20 medyani),
    Kirmizi (en koyu %2 kirmizi medyani) + Acik Kirmizi (en doygun/parlak %10) - kirmizi piksel varsa.
 2) piksel = w_krem*Krem + w_kirmizi*Kirmizi + ... ; w>=0, toplam 1 (kisitli en kucuk kareler),
    murekkep basina sizinti cezasi (--ceza, seviye).
 3) Ust uste alfa: a_k = w_k, a_r = w_r/(w_krem+w_r) (Krem opak, bolge icinde); alfa<0,02 -> 0.
 4) PSD: RGBA; her bolge bir grup; en altta gizli Orijinal_referans. KATMAN ADLARI ASCII (proje kurali).
Cikti: yeniden birlestirme hatasini (ort / %99 / max) bolge basina yazar.
"""
import argparse, itertools, os
import numpy as np
from PIL import Image
from psd_tools import PSDImage

def simplex_ls(px,E,penalty=None):
    """px Nx3, E kx3. min ||px - w@E||, w>=0, sum w=1, yuz numaralandirma.
    penalty: murekkep basina ceza (seviye); secim = hata + kullanilan murekkeplerin cezasi.
    Boylece rengi aciklamaya katkisi cezadan kucuk olan murekkep kullanilmaz (sizinti azalir)."""
    N=len(px); k=len(E); pen=np.zeros(k) if penalty is None else np.asarray(penalty,float)
    best=np.full(N,np.inf); W=np.zeros((N,k)); RES=np.full(N,np.inf)
    for s in range(1,k+1):
        for sub in itertools.combinations(range(k),s):
            sub=list(sub); e0=E[sub[0]]
            if s==1: w=np.ones((N,1))
            else:
                D=(E[sub[1:]]-e0); G=D@D.T
                if abs(np.linalg.det(G))<1e-6: continue
                u=((px-e0)@D.T)@np.linalg.inv(G); w=np.c_[1-u.sum(1),u]
            ok=(w>=-1e-9).all(1)
            r=np.sqrt(((px-np.clip(w,0,None)@E[sub])**2).sum(1))
            sc=np.where(ok,r+pen[sub].sum(),np.inf)
            upd=sc<best
            Wf=np.zeros((N,k)); Wf[:,sub]=np.clip(w,0,None)
            best[upd]=sc[upd]; W[upd]=Wf[upd]; RES[upd]=r[upd]
    return W,RES


THR = 0.02


def inks_for(px, siyah_yedek=None):
    L = px.mean(1); rg = px[:, 0] - px[:, 1]; neu = rg < 45
    c = px[neu & (L > 180)]
    krem = np.median(c[c.mean(1) >= np.percentile(c.mean(1), 80)], 0)
    dk = px[neu & (L < 90)]
    if len(dk) >= 200 and siyah_yedek is None:
        siyah = np.median(dk[dk.mean(1) <= np.percentile(dk.mean(1), 20)], 0)
    else:
        siyah = siyah_yedek
    R = px[rg > 100]; out = {'Krem': krem}
    if len(R) >= 200:
        out['Kirmizi'] = np.median(R[R[:, 0] <= np.percentile(R[:, 0], 2)], 0)
        hi = R[R[:, 0] >= np.percentile(R[:, 0], 90)]
        out['Acik_Kirmizi'] = np.median(hi[hi[:, 1] <= np.percentile(hi[:, 1], 30)], 0)
    if siyah is not None:
        out['Siyah'] = siyah
    return {k: np.round(v) for k, v in out.items()}


def layer_alphas(Wt):
    cs = np.cumsum(Wt, 1); A = np.where(cs > 1e-9, Wt / np.maximum(cs, 1e-9), 0.0); A[:, 0] = 1.0
    return A


def composite(E, A):
    out = np.repeat(E[0][None], len(A), 0)
    for i in range(1, len(E)):
        out = out * (1 - A[:, i:i + 1]) + E[i] * A[:, i:i + 1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('girdi'); ap.add_argument('maskeler'); ap.add_argument('cikti')
    ap.add_argument('--ceza', default='', help='bolge:Murekkep=seviye,... (sizinti cezasi; verilmeyen 0)')
    o = ap.parse_args()
    CEZA = {}
    for t in filter(None, o.ceza.split(',')):
        a, v = t.split('='); b, n = a.split(':'); CEZA[(b, n)] = float(v)
    src = Image.open(o.girdi).convert('RGB'); im = np.asarray(src).astype(np.float64); H, W = im.shape[:2]
    M = np.load(o.maskeler); keys = list(M.keys())
    tot = sum(M[k].astype(int) for k in keys)
    assert tot.shape == (H, W) and tot.min() == 1 and tot.max() == 1, \
        f'Maskeler ayrik degil: bosluk {(tot == 0).sum()}, ortusme {(tot > 1).sum()}'
    ref = max(keys, key=lambda k: M[k].sum()); ref_ink = inks_for(im[M[ref]])
    psd = PSDImage.new('RGBA', (W, H), color=(0, 0, 0, 0))
    ro = psd.create_pixel_layer(src.convert('RGBA'), name='Orijinal_referans', top=0, left=0); ro.visible = False
    for k in keys:
        m = M[k]; px = im[m]
        inks = inks_for(px, siyah_yedek=ref_ink.get('Siyah') if k != ref else None)
        names = list(inks.keys()); E = np.array([inks[n] for n in names])
        pen = [CEZA.get((k, n), 0) for n in names]
        Wt, _ = simplex_ls(px, E, pen); A = layer_alphas(Wt)
        A[:, 1:] = np.where(A[:, 1:] < THR, 0, A[:, 1:]); A = np.round(A * 255) / 255
        e = np.abs(np.round(composite(E, A)) - px).max(1)
        print(f'{k}: piksel {int(m.sum())}, murekkepler {names}, hata ort {e.mean():.2f} %99 {np.percentile(e, 99):.0f} max {e.max():.0f}')
        g = psd.create_group(name=k, open_folder=True)
        for i, n in enumerate(names):
            arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = E[i].astype(np.uint8)
            a = np.zeros((H, W)); a[m] = A[:, i]; arr[..., 3] = np.round(a * 255).astype(np.uint8)
            g.create_pixel_layer(Image.fromarray(arr, 'RGBA'), name=n, top=0, left=0)
    os.makedirs(os.path.dirname(os.path.abspath(o.cikti)), exist_ok=True)
    psd.save(o.cikti); print('yazildi', o.cikti, os.path.getsize(o.cikti))


if __name__ == '__main__':
    main()
