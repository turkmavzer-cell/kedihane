#!/usr/bin/env python3
"""Kurgu planını (plan.json) doğrular, render eder ve çıktıyı denetler.

Kullanım:
  python tools/video/plan_render.py plan.json --dogrula  [--analiz analiz.json]
  python tools/video/plan_render.py plan.json --onizleme [--analiz analiz.json]
  python tools/video/plan_render.py plan.json --master   [--analiz analiz.json]

- --analiz verilirse kesimler ±0,15 sn içindeki müzik vuruşuna otomatik hizalanır.
- --onizleme iki kontrol sayfası üretir: <ad>_kareler.jpg (her planın orta karesi) ve
  varsa <ad>_yazilar.jpg (yazı PNG'leri gri zeminde, güvenli alan çizgili). Her
  sayfanın üst bandında bir kod vardır; kod terminale yazılmaz.
- --master yalnız plan.json'daki onay_kareler (ve yazı varsa onay_yazilar) kodları
  son önizlemeyle eşleşirse ve plan önizlemeden sonra değişmediyse çalışır.
- Her renderdan sonra çıktı otomatik denetlenir; master'da FAIL varsa teslim yasaktır.
- --master ayrıca <ad>_premiere.xml (FCP7) üretir: kaynaklara bağlı kesim listesi.
- ffmpeg: önce imageio-ffmpeg, yoksa PATH. ffprobe yoksa bilgiler ffmpeg -i çıktısından okunur.
Plan şeması: bilgi/video-kurgu.md, "C. plan.json Şeması".
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import numpy as np
from PIL import Image, ImageDraw, ImageFont

IMZA = "kedihane-plan_render v2"
GORSEL = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
GECISLER = {"kesme", "fade", "fadeblack"}
KADRAJLAR = {"orta": 0.5, "ust": 0.0, "alt": 1.0}
SIGDIR = {"sigdir": "siyah", "bulanik": "bulanik", "sigdir_bulanik_arka": "bulanik"}


def _bul_ffmpeg():
    """Önce imageio-ffmpeg (tam libx264), yoksa PATH'teki ffmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        yol = shutil.which("ffmpeg")
        if yol:
            return yol
    sys.exit("[HATA] ffmpeg bulunamadı: pip install imageio-ffmpeg ya da ffmpeg'i PATH'e ekle.")


FFMPEG = _bul_ffmpeg()
FFPROBE = shutil.which("ffprobe")
TEMPO = {  # varsayılan geçiş, geçiş süresi aralığı, en uzun plan
    "hareketli": {"gecis": "kesme", "sure": 0.25, "aralik": (0.15, 0.35), "en_uzun": 4.0},
    "yavas": {"gecis": "fade", "sure": 0.45, "aralik": (0.35, 0.8), "en_uzun": 7.0},
}
GUVENLI = (0.055, 0.078, 0.87, 0.83)  # x0, y0, x1, y1 (oran): platform düğmeleri dışı
HIZALA = 0.15


def font(boyut=13):
    for ad in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arialbd.ttf", "arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(ad, boyut)
        except OSError:
            continue
    return ImageFont.load_default()


def _akis_suresi(yol, secici, fps=None):
    """ffprobe yoksa: video = kare sayısı / fps, ses = çözülmüş son zaman damgası."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", yol, "-map", secici, "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    if fps:
        kare = re.findall(r"frame=\s*(\d+)", r.stderr)
        return int(kare[-1]) / fps if kare else 0.0
    t = re.findall(r"time=(\d+):(\d+):([\d.]+)", r.stderr)
    return int(t[-1][0]) * 3600 + int(t[-1][1]) * 60 + float(t[-1][2]) if t else 0.0


def probe(yol):
    """Video bilgisi. ffprobe varsa onu, yoksa (imageio-ffmpeg) ffmpeg -i çıktısını kullanır."""
    b = {"sure": None, "w": None, "h": None, "sar": "1:1", "fps_r": None, "fps_avg": None,
         "rot": 0, "comment": "", "ses": False, "v_sure": 0.0, "a_sure": 0.0}
    if FFPROBE:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", yol],
                           capture_output=True, text=True)
        j = json.loads(r.stdout or "{}")
        f = j.get("format", {})
        b["sure"] = float(f["duration"]) if f.get("duration") else None
        b["comment"] = f.get("tags", {}).get("comment", "")
        for st in j.get("streams", []):
            if st["codec_type"] == "video" and b["w"] is None:
                b.update(w=st.get("width"), h=st.get("height"), sar=st.get("sample_aspect_ratio", "1:1"),
                         fps_r=st.get("r_frame_rate"), fps_avg=st.get("avg_frame_rate"),
                         v_sure=float(st.get("duration", 0) or 0))
                rots = [sd.get("rotation", 0) for sd in st.get("side_data_list", []) if "rotation" in sd]
                b["rot"] = int(float(rots[0])) if rots else int(st.get("tags", {}).get("rotate", 0))
            elif st["codec_type"] == "audio" and not b["ses"]:
                b.update(ses=True, a_sure=float(st.get("duration", 0) or 0))
        return b
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", yol], capture_output=True, text=True, errors="replace")
    e = r.stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e)
    if m:
        b["sure"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    m = re.search(r"Video: .*?, (\d{2,5})x(\d{2,5})(?: \[SAR (\d+:\d+))?", e)
    if m:
        b.update(w=int(m[1]), h=int(m[2]), sar=m[3] or "1:1")
    m = re.search(r"([\d.]+) fps", e)
    if m:
        fps = float(m[1])
        b["fps_r"] = b["fps_avg"] = f"{round(fps)}/1" if abs(fps - round(fps)) < 0.01 else m[1]
    m = re.search(r"rotation of (-?[\d.]+) degrees", e)
    b["rot"] = int(float(m[1])) if m else 0
    m = re.search(r"comment\s*:\s*(.*)", e)
    b["comment"] = m[1].strip() if m else ""
    b["ses"] = "Audio:" in e
    if b["w"] and b["fps_r"]:
        pay, _, payda = b["fps_r"].partition("/")
        b["v_sure"] = _akis_suresi(yol, "0:v:0", float(pay) / float(payda or 1))
    if b["ses"]:
        b["a_sure"] = _akis_suresi(yol, "0:a:0")
    return b


def kaynak_suresi(yol):
    return probe(yol)["sure"]


def ses_var_mi(yol):
    return probe(yol)["ses"]


def coz(klasor, yol):
    return yol if os.path.isabs(yol) else os.path.normpath(os.path.join(klasor, yol))


def gorsel_mi(yol):
    return os.path.splitext(yol)[1].lower() in GORSEL


def plan_ozeti(plan):
    temiz = {k: v for k, v in plan.items() if not k.startswith("onay_")}
    return hashlib.sha256(json.dumps(temiz, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def kod_ozeti(kod, tuz):
    return hashlib.pbkdf2_hmac("sha256", kod.encode(), bytes.fromhex(tuz), 200_000).hex()


# ---------------------------------------------------------------- plan hazırlama

def hazirla(plan, klasor):
    """Planı iç biçime çevirir: her plana tempo, gecis, D, sure, giris/cikis yazar."""
    varsayilan_tempo = plan.get("tempo", "hareketli")
    for i, p in enumerate(plan["planlar"]):
        p["_yol"] = coz(klasor, p["kaynak"])
        p["_gorsel"] = gorsel_mi(p["kaynak"])
        p["_tempo"] = p.get("tempo", varsayilan_tempo)
        t = TEMPO.get(p["_tempo"], TEMPO["hareketli"])
        p["_gecis"] = "kesme" if i == 0 else p.get("gecis", t["gecis"])
        p["_D"] = 0.0 if p["_gecis"] == "kesme" else p.get("gecis_sure", t["sure"])
        if p["_gorsel"]:
            p["_giris"], p["_cikis"], p["_hiz"] = 0.0, float(p.get("sure", 0)), 1.0
        else:
            p["_giris"], p["_cikis"], p["_hiz"] = p.get("giris", 0), p.get("cikis", 0), p.get("hiz", 1.0)


def zaman_cizelgesi(planlar):
    L, sonuc = 0.0, []
    for p in planlar:
        d = (p["_cikis"] - p["_giris"]) / p["_hiz"]
        bas = L - p["_D"]
        sonuc.append({"bas": bas, "sure": d, "D": p["_D"], "kesim": bas + p["_D"] / 2})
        L = bas + d
    return sonuc, L


def vurus_listesi(plan, analiz):
    if not analiz:
        return []
    m = analiz.get("muzik") or (analiz.get("muzikler") or [{}])[0]
    vur = m.get("vuruslar") or m.get("vuruslar_sn") or []
    bas = plan.get("muzik", {}).get("baslangic", 0)
    return [t - bas for t in vur if t >= bas]


def vurusa_hizala(plan, vuruslar, sureler):
    """Her kesimi ±HIZALA içindeki en yakın vuruşa, önceki planın sonunu oynatarak taşır."""
    notlar = []
    if not vuruslar or plan.get("vurusa_hizala", True) is False:
        return notlar
    planlar = plan["planlar"]
    for i in range(1, len(planlar)):
        cizelge, _ = zaman_cizelgesi(planlar)
        k = cizelge[i]["kesim"]
        b = min(vuruslar, key=lambda v: abs(v - k))
        fark = b - k
        if abs(fark) < 0.01 or abs(fark) > HIZALA:
            continue
        onceki = planlar[i - 1]
        yeni = onceki["_cikis"] + fark * onceki["_hiz"]
        ust = sureler.get(onceki["_yol"]) if not onceki["_gorsel"] else None
        if (yeni - onceki["_giris"]) / onceki["_hiz"] < 0.4 or (ust and yeni > ust):
            continue
        onceki["_cikis"] = yeni
        notlar.append(f"plan {i}: bitiş {fark:+.2f} sn → kesim {b:.2f} sn vuruşuna")
    return notlar


# ---------------------------------------------------------------- doğrulama

def guvenli_alan_disi(png):
    try:
        a = np.asarray(Image.open(png).convert("RGBA"))[:, :, 3] > 32
    except OSError:
        return None
    h, w = a.shape
    x0, y0, x1, y1 = (int(GUVENLI[0] * w), int(GUVENLI[1] * h), int(GUVENLI[2] * w), int(GUVENLI[3] * h))
    toplam = a.sum()
    if not toplam:
        return 0.0
    ic = a[y0:y1, x0:x1].sum()
    return (toplam - ic) / toplam


def yuva_kontrol(png, yuvalar):
    """Dairesel bayrak/amblem yuvası tamamen opak mı? (cx, cy, r: PNG pikseli)"""
    if not yuvalar:
        return []
    a = np.asarray(Image.open(png).convert("RGBA"))[:, :, 3]
    h, w = a.shape
    yy, xx = np.ogrid[:h, :w]
    hatalar = []
    for k, y in enumerate(yuvalar, 1):
        cx, cy, r = int(y.get("cx", 0)), int(y.get("cy", 0)), int(y.get("r", 0))
        maske = (xx - cx) ** 2 + (yy - cy) ** 2 <= max(r - 2, 1) ** 2
        if r <= 0 or not maske.any():
            hatalar.append(f"yuva {k} ({cx},{cy},r={r}) görüntü dışında")
            continue
        bos = float(np.mean(a[maske] < 250))
        if bos > 0.005:
            hatalar.append(f"yuva {k} tam dolmamış (%{bos * 100:.1f} boşluk); görseli büyüt, boyama yapma")
    return hatalar


def dogrula(plan, analiz):
    hatalar, uyarilar = [], []
    if len(plan.get("cikti", {}).get("boyut", [])) != 2:
        hatalar.append("cikti.boyut [genişlik, yükseklik] olmalı")
    planlar = plan.get("planlar", [])
    if not planlar:
        return ["planlar listesi boş"], [], {}
    sureler = {}
    for i, p in enumerate(planlar):
        e = f"plan {i + 1}"
        for alan in ("kaynak", "neden") + (("sure",) if p["_gorsel"] else ("giris", "cikis")):
            if alan not in p or (alan == "neden" and not str(p.get("neden", "")).strip()):
                hatalar.append(f"{e}: '{alan}' eksik veya boş")
        if not os.path.isfile(p["_yol"]):
            hatalar.append(f"{e}: kaynak yok: {p['kaynak']}")
            continue
        if p["_tempo"] not in TEMPO:
            hatalar.append(f"{e}: tempo {sorted(TEMPO)} içinden olmalı")
        if p["_gecis"] not in GECISLER:
            hatalar.append(f"{e}: gecis {sorted(GECISLER)} içinden olmalı ('{p['_gecis']}' yok)")
        kj = p.get("kadraj", "orta")
        if not (kj in SIGDIR or kj in KADRAJLAR or (isinstance(kj, (int, float)) and 0 <= kj <= 1)):
            hatalar.append(f"{e}: kadraj orta/ust/alt/sigdir/bulanik veya 0–1 arası sayı olmalı")
        if p["_gorsel"]:
            if p["_cikis"] <= 0:
                hatalar.append(f"{e}: görselde 'sure' > 0 olmalı")
            continue
        sureler.setdefault(p["_yol"], kaynak_suresi(p["_yol"]))
        ks = sureler[p["_yol"]]
        if not 0 <= p["_giris"] < p["_cikis"]:
            hatalar.append(f"{e}: giris < cikis olmalı")
        if ks is not None and p["_cikis"] > ks + 0.05:
            hatalar.append(f"{e}: cikis {p['_cikis']} kaynak süresini ({ks:.2f}) aşıyor")
        if not 0.25 <= p["_hiz"] <= 4:
            hatalar.append(f"{e}: hiz 0,25–4 arasında olmalı")
    for j, y in enumerate(plan.get("yazilar", [])):
        yol = coz(plan["_klasor"], y.get("png", ""))
        if not os.path.isfile(yol):
            hatalar.append(f"yazı {j + 1}: PNG yok: {y.get('png')}")
            continue
        for h in yuva_kontrol(yol, y.get("yuva_kontrol", [])):
            hatalar.append(f"yazı {j + 1}: {h}")
        oran = guvenli_alan_disi(yol)
        if oran and oran > 0.01:
            uyarilar.append(f"yazı {j + 1}: opak piksellerin %{oran * 100:.0f}'i güvenli alan dışında")
    if hatalar:
        return hatalar, uyarilar, sureler

    vuruslar = vurus_listesi(plan, analiz)
    for n in vurusa_hizala(plan, vuruslar, sureler):
        print(f"[HIZALA] {n}")
    cizelge, toplam = zaman_cizelgesi(planlar)
    for i, (p, z) in enumerate(zip(planlar, cizelge)):
        e, t = f"plan {i + 1}", TEMPO[p["_tempo"]]
        if z["sure"] < 0.4:
            uyarilar.append(f"{e}: {z['sure']:.2f} sn, çok kısa")
        if z["sure"] > plan.get("en_uzun_plan", t["en_uzun"]):
            uyarilar.append(f"{e}: {z['sure']:.2f} sn, {p['_tempo']} tempo için uzun; gerekçesi var mı?")
        if i and z["D"]:
            lo, hi = t["aralik"]
            if not lo <= z["D"] <= hi:
                hatalar.append(f"{e}: gecis_sure {z['D']} sn, {p['_tempo']} tempoda {lo}–{hi} olmalı")
            if z["D"] >= min(z["sure"], cizelge[i - 1]["sure"]):
                hatalar.append(f"{e}: gecis_sure plan süresinden uzun")
        if i and vuruslar:
            fark = min(abs(z["kesim"] - v) for v in vuruslar)
            if fark > 0.12:
                uyarilar.append(f"{e}: kesim {z['kesim']:.2f} sn, en yakın vuruşa {fark:.2f} sn uzak")
    hareketli = [z for p, z in zip(planlar[1:], cizelge[1:]) if p["_tempo"] == "hareketli"]
    efektli = sum(1 for z in hareketli if z["D"])
    if len(hareketli) > 2 and efektli > len(hareketli) / 3:
        uyarilar.append(f"hareketli bölümde {efektli}/{len(hareketli)} geçiş efektli; çoğu kesme olmalı")
    hedef = plan.get("hedef_sure")
    if hedef and abs(toplam - hedef) > 1.0:
        uyarilar.append(f"toplam {toplam:.2f} sn, hedef {hedef} sn")
    plan["_cizelge"], plan["_toplam"] = cizelge, toplam
    return hatalar, uyarilar, sureler


# ---------------------------------------------------------------- ffmpeg komutu

def kadraj_filtresi(kj, W, H):
    if SIGDIR.get(kj) == "siyah":
        return (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black")
    oran = KADRAJLAR.get(kj, kj if isinstance(kj, (int, float)) else 0.5)
    return (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H}:(iw-ow)/2:(ih-oh)*{oran}")


def atempo_zinciri(hiz):
    parcalar = []
    while hiz > 2.0:
        parcalar.append("atempo=2.0")
        hiz /= 2.0
    while hiz < 0.5:
        parcalar.append("atempo=0.5")
        hiz /= 0.5
    return ",".join(parcalar + [f"atempo={hiz:.4f}"])


def boyut(plan, onizleme):
    W, H = plan["cikti"]["boyut"]
    if onizleme:
        W, H = 540, int(round(540 * H / W / 2)) * 2
    return W, H


def komut_kur(plan, cikti_yolu, onizleme):
    W, H = boyut(plan, onizleme)
    F = plan["cikti"].get("fps", 30)
    planlar, cizelge, toplam = plan["planlar"], plan["_cizelge"], plan["_toplam"]
    orj_ses = plan.get("orijinal_ses", False)
    keskin = plan.get("keskinlestir", False)
    girdiler, filtre = [], []

    for i, p in enumerate(planlar):
        d = cizelge[i]["sure"]
        if p["_gorsel"]:
            girdiler += ["-loop", "1", "-framerate", str(F), "-t", f"{d:.3f}", "-i", p["_yol"]]
        else:
            girdiler += ["-ss", f"{p['_giris']:.3f}", "-t", f"{p['_cikis'] - p['_giris']:.3f}", "-i", p["_yol"]]
        ks = ",unsharp=5:5:0.6:5:5:0.0" if (keskin or p.get("keskinlestir")) else ""
        son = f"{ks},fps={F},trim=duration={d:.3f},setpts=PTS-STARTPTS,settb=1/{F},format=yuv420p,setsar=1[v{i}]"
        if SIGDIR.get(p.get("kadraj")) == "bulanik":
            filtre.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{p['_hiz']},split[ba{i}][on{i}]")
            filtre.append(f"[ba{i}]scale={W // 4}:{H // 4}:force_original_aspect_ratio=increase,"
                          f"crop={W // 4}:{H // 4},boxblur=10:2,scale={W}:{H}[bb{i}]")
            filtre.append(f"[on{i}]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[of{i}]")
            filtre.append(f"[bb{i}][of{i}]overlay=(W-w)/2:(H-h)/2{son}")
        else:
            filtre.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{p['_hiz']},"
                          f"{kadraj_filtresi(p.get('kadraj', 'orta'), W, H)}{son}")
        if orj_ses:
            if not p["_gorsel"] and ses_var_mi(p["_yol"]):
                filtre.append(f"[{i}:a]asetpts=PTS-STARTPTS,{atempo_zinciri(p['_hiz'])},aresample=48000,"
                              f"aformat=channel_layouts=stereo,atrim=duration={d:.3f}[a{i}]")
            else:
                filtre.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={d:.3f}[a{i}]")

    v, a = "v0", "a0"
    for i in range(1, len(planlar)):
        z, g = cizelge[i], planlar[i]["_gecis"]
        if g == "kesme":
            filtre.append(f"[{v}][v{i}]concat=n=2:v=1:a=0,settb=1/{F}[vx{i}]")
            if orj_ses:
                filtre.append(f"[{a}][a{i}]concat=n=2:v=0:a=1[ax{i}]")
        else:
            filtre.append(f"[{v}][v{i}]xfade=transition={g}:duration={z['D']:.3f}:"
                          f"offset={z['bas']:.3f},settb=1/{F}[vx{i}]")
            if orj_ses:
                filtre.append(f"[{a}][a{i}]acrossfade=d={z['D']:.3f}[ax{i}]")
        v, a = f"vx{i}", f"ax{i}"

    n = len(planlar)
    for j, y in enumerate(plan.get("yazilar", [])):
        girdiler += ["-i", coz(plan["_klasor"], y["png"])]
        filtre.append(f"[{n}:v]scale={W}:{H}[p{j}]")
        filtre.append(f"[{v}][p{j}]overlay=0:0:enable='between(t,{y['bas']},{y['bit']})'[vy{j}]")
        v, n = f"vy{j}", n + 1

    kf = plan["cikti"].get("kapanis_fade", 0)
    if kf:
        filtre.append(f"[{v}]fade=t=out:st={toplam - kf:.3f}:d={kf}[vson]")
        v = "vson"

    m, ses_cikis = plan.get("muzik"), None
    if m:
        girdiler += ["-i", coz(plan["_klasor"], m["dosya"])]
        mf = m.get("fade_out", 1.5)
        filtre.append(f"[{n}:a]atrim=start={m.get('baslangic', 0)},asetpts=PTS-STARTPTS,aresample=48000,"
                      f"aformat=channel_layouts=stereo,volume={m.get('ses_db', 0)}dB,"
                      f"atrim=duration={toplam:.3f},afade=t=out:st={max(0, toplam - mf):.3f}:d={mf}[mz]")
        if orj_ses:
            filtre.append(f"[{a}]volume={plan.get('orijinal_ses_db', -6)}dB[ao]")
            filtre.append("[ao][mz]amix=inputs=2:duration=first:normalize=0[amx]")
            ses_cikis = "amx"
        else:
            ses_cikis = "mz"
    elif orj_ses:
        ses_cikis = a
    if ses_cikis:
        filtre.append(f"[{ses_cikis}]loudnorm=I={plan.get('hedef_lufs', -14)}:TP=-1:LRA=11,"
                      f"aresample=48000,apad,atrim=duration={toplam:.3f}[ason]")

    komut = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *girdiler,
             "-filter_complex", ";".join(filtre), "-map", f"[{v}]"]
    if ses_cikis:
        komut += ["-map", "[ason]"]
    if onizleme:
        komut += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28"]
        komut += ["-c:a", "aac", "-b:a", "128k"] if ses_cikis else []
    else:
        komut += ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-maxrate", "80M",
                  "-bufsize", "160M", "-profile:v", "high", "-level", "5.2"]
        komut += ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"] if ses_cikis else []
    komut += ["-r", str(F), "-fps_mode", "cfr", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              "-metadata", f"comment={IMZA} plan:{plan_ozeti(plan['_ham'])[:12]}", cikti_yolu]
    return komut


# ---------------------------------------------------------------- Premiere XML

def _pathurl(yol):
    return "file://localhost/" + quote(Path(yol).resolve().as_posix().lstrip("/"), safe="/:")


def premiere_xml(plan, hedef):
    """FCP7 xmeml: kaynak dosyalara bağlı kesim listesi. Geçişler kesme, hız 1x olarak gelir."""
    W, H = plan["cikti"]["boyut"]
    F = plan["cikti"].get("fps", 30)

    def oran(el):
        r = ET.SubElement(el, "rate")
        ET.SubElement(r, "timebase").text = str(F)
        ET.SubElement(r, "ntsc").text = "FALSE"

    kok = ET.Element("xmeml", version="4")
    seq = ET.SubElement(kok, "sequence")
    ET.SubElement(seq, "name").text = Path(hedef).stem
    oran(seq)
    medya = ET.SubElement(seq, "media")
    video = ET.SubElement(medya, "video")
    sc = ET.SubElement(ET.SubElement(video, "format"), "samplecharacteristics")
    ET.SubElement(sc, "width").text = str(W)
    ET.SubElement(sc, "height").text = str(H)
    ET.SubElement(sc, "pixelaspectratio").text = "square"
    iz = ET.SubElement(video, "track")
    kesimler = [z["kesim"] for z in plan["_cizelge"]] + [plan["_toplam"]]
    kesimler[0] = 0.0
    for i, p in enumerate(plan["planlar"]):
        bas_f, bit_f = round(kesimler[i] * F), round(kesimler[i + 1] * F)
        ci = ET.SubElement(iz, "clipitem", id=f"clipitem-{i + 1}")
        ET.SubElement(ci, "name").text = f"{i + 1:02d} {p.get('neden', '')[:40]}"
        oran(ci)
        ET.SubElement(ci, "start").text = str(bas_f)
        ET.SubElement(ci, "end").text = str(bit_f)
        giris_f = round(p["_giris"] * F)
        ET.SubElement(ci, "in").text = str(giris_f)
        ET.SubElement(ci, "out").text = str(giris_f + bit_f - bas_f)
        fe = ET.SubElement(ci, "file", id=f"file-{i + 1}")
        ET.SubElement(fe, "name").text = Path(p["_yol"]).name
        ET.SubElement(fe, "pathurl").text = _pathurl(p["_yol"])
    m = plan.get("muzik")
    if m:
        ses = ET.SubElement(ET.SubElement(medya, "audio"), "track")
        ci = ET.SubElement(ses, "clipitem", id="clipitem-muzik")
        ET.SubElement(ci, "name").text = Path(m["dosya"]).name
        oran(ci)
        ET.SubElement(ci, "start").text = "0"
        ET.SubElement(ci, "end").text = str(round(plan["_toplam"] * F))
        ET.SubElement(ci, "in").text = str(round(m.get("baslangic", 0) * F))
        ET.SubElement(ci, "out").text = str(round((m.get("baslangic", 0) + plan["_toplam"]) * F))
        fe = ET.SubElement(ci, "file", id="file-muzik")
        ET.SubElement(fe, "name").text = Path(m["dosya"]).name
        ET.SubElement(fe, "pathurl").text = _pathurl(coz(plan["_klasor"], m["dosya"]))
    ET.SubElement(seq, "duration").text = str(round(plan["_toplam"] * F))
    agac = ET.ElementTree(kok)
    ET.indent(agac, space=" ")
    agac.write(hedef, encoding="utf-8", xml_declaration=True)


# ---------------------------------------------------------------- kontrol sayfaları

def kare_al(video, t, genislik=None):
    vf = ["-vf", f"scale={genislik}:-2"] if genislik else []
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", *vf,
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert("RGB") if r.returncode == 0 and r.stdout else None


def kod_bandi(sayfa, kod):
    band = Image.new("RGB", (sayfa.width, 44), (20, 20, 20))
    ImageDraw.Draw(band).text((10, 6), f"KOD: {kod}" if kod else "MASTER", fill="yellow", font=font(28))
    yeni = Image.new("RGB", (sayfa.width, sayfa.height + 44))
    yeni.paste(band, (0, 0))
    yeni.paste(sayfa, (0, 44))
    return yeni


def kareler_sayfasi(video, plan, hedef, kod, sutun=4):
    kareler = []
    for i, (p, z) in enumerate(zip(plan["planlar"], plan["_cizelge"])):
        k = kare_al(video, z["bas"] + z["sure"] / 2, 200)
        if k:
            kareler.append((i + 1, p.get("neden", ""), k))
    if not kareler:
        return
    kw, kh = kareler[0][2].size
    satir = -(-len(kareler) // sutun)
    sayfa = Image.new("RGB", (sutun * kw, satir * (kh + 30)), "black")
    ciz, yf = ImageDraw.Draw(sayfa), font(13)
    for j, (no, neden, k) in enumerate(kareler):
        x, y = (j % sutun) * kw, (j // sutun) * (kh + 30)
        sayfa.paste(k, (x, y))
        ciz.text((x + 3, y + kh + 2), f"#{no}", fill="yellow", font=yf)
        ciz.text((x + 3, y + kh + 15), str(neden)[:30], fill="white", font=yf)
    kod_bandi(sayfa, kod).save(hedef, quality=85)


def yazilar_sayfasi(plan, hedef, kod, W=270, H=480):
    yazilar = plan.get("yazilar", [])
    sayfa = Image.new("RGB", (W * len(yazilar), H + 22), "black")
    ciz, yf = ImageDraw.Draw(sayfa), font(13)
    for j, y in enumerate(yazilar):
        zemin = Image.new("RGBA", (W, H), (128, 128, 128, 255))
        png = Image.open(coz(plan["_klasor"], y["png"])).convert("RGBA").resize((W, H), Image.LANCZOS)
        zemin.alpha_composite(png)
        z = ImageDraw.Draw(zemin)
        z.rectangle([GUVENLI[0] * W, GUVENLI[1] * H, GUVENLI[2] * W, GUVENLI[3] * H], outline=(255, 0, 0, 255))
        sayfa.paste(zemin.convert("RGB"), (j * W, 0))
        ciz.text((j * W + 3, H + 4), f"yazı {j + 1}: {y['bas']}–{y['bit']} sn", fill="white", font=yf)
    kod_bandi(sayfa, kod).save(hedef, quality=85)


# ---------------------------------------------------------------- render sonrası denetim

def denetle(video, plan, W, H):
    F = plan["cikti"].get("fps", 30)
    sonuc, uyarilar = [], []
    b = probe(video)

    def kayit(ad, ok, ayrinti=""):
        sonuc.append((ad, ok, ayrinti))

    kayit("çözünürlük", (b["w"], b["h"]) == (W, H), f"{b['w']}x{b['h']}")
    kayit("SAR 1:1", b["sar"] in ("1:1", "0:1", "N/A"), b["sar"])
    kayit(f"{F} fps sabit", b["fps_r"] == b["fps_avg"] == f"{F}/1", f"{b['fps_r']} / {b['fps_avg']}")
    kayit("döndürme kalıntısı yok", not b["rot"], str(b["rot"]))
    kayit("motor imzası", IMZA in b["comment"], "")
    with open(video, "rb") as f:
        bas = f.read(1 << 20)
    kayit("faststart", 0 <= bas.find(b"moov") < (bas.find(b"mdat") if b"mdat" in bas else 1 << 30), "")
    vsure = b["v_sure"]
    kayit("süre planla eşit", abs(vsure - plan["_toplam"]) < 0.1, f"{vsure:.2f} / plan {plan['_toplam']:.2f}")
    if plan.get("muzik") or plan.get("orijinal_ses"):
        kayit("ses/görüntü süresi", b["ses"] and abs(b["a_sure"] - vsure) < 0.1, f"{b['a_sure']:.2f} / {vsure:.2f}")
    # siyah kare: kapanış fade'i ve fadeblack geçişleri dışında 0,5 sn+ siyah = FAIL
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", video, "-an", "-vf", "blackdetect=d=0.5:pix_th=0.08",
                        "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    serbest = [(plan["_toplam"] - plan["cikti"].get("kapanis_fade", 0) - 0.2, plan["_toplam"] + 1)]
    serbest += [(z["bas"] - 0.2, z["bas"] + z["D"] + 0.2) for p, z in zip(plan["planlar"], plan["_cizelge"])
                if p["_gecis"] == "fadeblack"]
    siyah = [(float(b), float(e)) for b, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    kacak = [s for s in siyah if not any(a <= s[0] and s[1] <= b for a, b in serbest)]
    kayit("istenmeyen siyah kare yok", not kacak, str(kacak) if kacak else "")
    # donuk kare: yalnız video kaynaklı planlarda uyarı
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", video, "-an", "-vf", "freezedetect=n=0.002:d=1.0",
                        "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    donuk = [float(t) for t in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    for t in donuk:
        for i, (p, z) in enumerate(zip(plan["planlar"], plan["_cizelge"])):
            if not p["_gorsel"] and z["bas"] <= t < z["bas"] + z["sure"] - 0.5:
                uyarilar.append(f"plan {i + 1}: {t:.2f} sn'de donuk görüntü (≥1 sn)")
    # netlik: plan ortası karede Laplacian varyansı (yalnız uyarı)
    for i, z in enumerate(plan["_cizelge"]):
        k = kare_al(video, z["bas"] + z["sure"] / 2)
        if k is None:
            continue
        g = np.asarray(k.convert("L"), dtype=np.float32)
        lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
        if lap.var() < plan.get("netlik_esigi", 30):
            uyarilar.append(f"plan {i + 1}: netlik düşük (Laplacian {lap.var():.0f}); bulanık olabilir")
    gecen = sum(1 for _, ok, _ in sonuc if ok)
    for ad, ok, ayr in sonuc:
        print(f"  [{'PASS' if ok else 'FAIL'}] {ad} {ayr}".rstrip())
    for u in uyarilar:
        print(f"  [UYARI] {u}")
    return gecen == len(sonuc), f"{gecen}/{len(sonuc)}"


# ---------------------------------------------------------------- ana akış

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("plan")
    kip = p.add_mutually_exclusive_group(required=True)
    kip.add_argument("--dogrula", action="store_true")
    kip.add_argument("--onizleme", action="store_true")
    kip.add_argument("--master", action="store_true")
    p.add_argument("--analiz", help="analiz.json; verilirse kesimler müzik vuruşuna hizalanır ve denetlenir")
    a = p.parse_args()

    with open(a.plan, encoding="utf-8") as f:
        ham = json.load(f)
    plan = json.loads(json.dumps(ham))
    plan["_ham"], plan["_klasor"] = ham, os.path.dirname(os.path.abspath(a.plan))
    analiz = None
    if a.analiz:
        with open(a.analiz, encoding="utf-8") as f:
            analiz = json.load(f)
    if not plan.get("planlar"):
        sys.exit("[HATA] 'planlar' yok. 'sahneler' eski şemadır; bilgi/video-kurgu.md C bölümüne göre yaz."
                 if plan.get("sahneler") else "[HATA] planlar listesi boş")
    hazirla(plan, plan["_klasor"])

    hatalar, uyarilar, _ = dogrula(plan, analiz)
    for h in hatalar:
        print(f"[HATA] {h}")
    for u in uyarilar:
        print(f"[UYARI] {u}")
    if hatalar:
        sys.exit(1)
    print(f"[TAMAM] {len(plan['planlar'])} plan, toplam {plan['_toplam']:.2f} sn")
    if a.dogrula:
        return

    kilit_yolu = os.path.splitext(os.path.abspath(a.plan))[0] + ".kilit.json"
    if a.master:
        try:
            with open(kilit_yolu, encoding="utf-8") as f:
                kilit = json.load(f)
        except OSError:
            sys.exit("[KİLİT] Önce --onizleme çalıştır ve kontrol sayfalarına bak.")
        if kilit["plan"] != plan_ozeti(ham):
            sys.exit("[KİLİT] Plan son önizlemeden sonra değişmiş. Yeniden --onizleme al ve sayfalara bak.")
        for alan in ("kareler", "yazilar"):
            if kilit.get(alan) and kod_ozeti(str(ham.get(f"onay_{alan}", "")).strip().upper(),
                                            kilit["tuz"]) != kilit[alan]:
                sys.exit(f"[KİLİT] onay_{alan} kodu yanlış veya eksik. Kodu _{alan}.jpg sayfasının "
                         f"üst bandından oku ve plan.json'a yaz.")

    ad = plan["cikti"].get("ad", "kurgu_v1.mp4")
    if a.onizleme:
        ad = os.path.splitext(ad)[0] + "_onizleme.mp4"
    cikti_yolu = coz(plan["_klasor"], ad)
    r = subprocess.run(komut_kur(plan, cikti_yolu, a.onizleme), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-1500:])
        sys.exit("[HATA] ffmpeg başarısız")
    print(f"[TAMAM] {cikti_yolu}")

    kok = os.path.splitext(cikti_yolu)[0]
    if a.onizleme:
        alfabe = "ABCDEFGHJKLMNPRSTUVYZ23456789"
        tuz = secrets.token_hex(16)
        kilit = {"plan": plan_ozeti(ham), "tuz": tuz}
        kod = "".join(secrets.choice(alfabe) for _ in range(6))
        kareler_sayfasi(cikti_yolu, plan, kok + "_kareler.jpg", kod)
        kilit["kareler"] = kod_ozeti(kod, tuz)
        print(f"[TAMAM] Kontrol sayfası: {kok}_kareler.jpg (kodu sayfadan oku)")
        if plan.get("yazilar"):
            kod2 = "".join(secrets.choice(alfabe) for _ in range(6))
            yazilar_sayfasi(plan, kok + "_yazilar.jpg", kod2)
            kilit["yazilar"] = kod_ozeti(kod2, tuz)
            print(f"[TAMAM] Yazı sayfası: {kok}_yazilar.jpg (kodu sayfadan oku)")
        with open(kilit_yolu, "w", encoding="utf-8") as f:
            json.dump(kilit, f)
    else:
        kareler_sayfasi(cikti_yolu, plan, kok + "_kareler.jpg", None)
        premiere_xml(plan, kok + "_premiere.xml")
        print(f"[TAMAM] Premiere XML: {kok}_premiere.xml (geçişler kesme olarak gelir)")

    print("[DENETİM]")
    ok, skor = denetle(cikti_yolu, plan, *boyut(plan, a.onizleme))
    if ok:
        print(f"[DENETİM] PASS ({skor})")
    else:
        print(f"[DENETİM] FAIL ({skor})" + ("; teslim yasak" if a.master else ""))
        if a.master:
            sys.exit(2)


if __name__ == "__main__":
    main()
