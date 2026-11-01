#!/usr/bin/env python3
"""Kedihane Kurgu Doğrulama, Önbellekli Segment Render ve Premiere XML Aracı (`tools/video/plan_render.py`)

Bu betik `plan.json` dosyasını doğrular ve yüksek kaliteli dikey/yatay video kurgusunu üretir:
- `--dogrula`: Sahne sürelerini, boş `neden` alanlarını, vuruş (beat) uyumunu (<= 0.12 sn),
  yasaklı geçişleri ve şablon/bayrak alfa doluluğunu kontrol eder.
- `--onizleme`: 540x960 hızlı kontrol çıktısı ve `_kareler.jpg` kanıt tablosu üretir.
- `--master`: 1080x1920 (veya hedef boyutta) CRF 17 H.264 High + AAC 48kHz master MP4,
  Premiere Pro XML (`_premiere.xml`) ve `_kareler.jpg` kanıt tablosu üretir.
- SHA-256 Segment Önbelleği sayesinde tek sahne düzeltmelerinde yalnızca değişen sahneyi render eder.
- Dikey 4K telefon videolarında `displaymatrix` (-90 derece) yan verisini otomatik temizler.

Kullanım:
    python tools/video/plan_render.py <plan.json> --dogrula
    python tools/video/plan_render.py <plan.json> --onizleme
    python tools/video/plan_render.py <plan.json> --master
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

IZINLI_GECISLER = {"cut", "kesme", "fade", "erime"}
IZINLI_MODLAR = {"kirp_9_16", "sigdir_bulanik_arka"}


def get_ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if found:
            return found
        raise RuntimeError("ffmpeg bulunamadı. Lütfen imageio-ffmpeg kurun veya ffmpeg'i PATH'e ekleyin.")


def probe_duration(filepath: str, ffmpeg_exe: str) -> float:
    cmd = [ffmpeg_exe, "-hide_banner", "-i", filepath]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", res.stderr)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def file_sha256_short(filepath: str) -> str:
    if not filepath or not os.path.isfile(filepath):
        return "none"
    st = os.stat(filepath)
    raw = f"{Path(filepath).resolve()}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]


def check_slot_alpha_fill(png_path: str, slots: list[dict]) -> list[str]:
    """Dairesel/dikdörtgen şablon yuvalarında şeffaf/boş piksel kalıp kalmadığını denetler."""
    errors = []
    if not os.path.isfile(png_path):
        return [f"Şablon dosyası bulunamadı: {png_path}"]
    img = Image.open(png_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]
    h, w = alpha.shape

    for idx, sl in enumerate(slots, 1):
        cx, cy, r = int(sl.get("cx", 0)), int(sl.get("cy", 0)), int(sl.get("r", 0))
        if r <= 0:
            continue
        yy, xx = np.ogrid[:h, :w]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r - 2) ** 2
        if not np.any(mask):
            errors.append(f"Yuva #{idx} ({cx},{cy},r={r}) görüntü sınırları dışında.")
            continue
        transparent_ratio = float(np.mean(alpha[mask] < 250))
        if transparent_ratio > 0.005:
            errors.append(
                f"Yuva #{idx} ({cx},{cy},r={r}) tam doldurulmamış (%{transparent_ratio * 100:.1f} şeffaf boşluk var)!"
            )
    return errors


def validate_plan(plan: dict, plan_dir: Path, ffmpeg_exe: str) -> tuple[list[str], list[str]]:
    """plan.json şemasını, kurgu dilini, geçişleri ve vuruş uyumunu doğrular."""
    errors = []
    warnings = []

    sahneler = plan.get("sahneler", [])
    if not sahneler:
        errors.append("Planda hiçbir sahne ('sahneler') tanımlanmamış.")
        return errors, warnings

    hedef_sure = float(plan.get("hedef_sure_sn", 0.0))
    vuruslar = sorted(float(x) for x in plan.get("vuruslar_sn", []))
    analiz_yolu = plan.get("analiz_json", "")
    if not vuruslar and analiz_yolu:
        ap = (plan_dir / analiz_yolu).resolve() if not os.path.isabs(analiz_yolu) else Path(analiz_yolu)
        if ap.is_file():
            try:
                adata = json.loads(ap.read_text(encoding="utf-8"))
                if adata.get("muzikler"):
                    vuruslar = sorted(float(x) for x in adata["muzikler"][0].get("vuruslar_sn", []))
            except Exception:
                pass

    toplam_sure = 0.0
    gecis_toplam = 0.0

    for i, s in enumerate(sahneler):
        no = i + 1
        kaynak_raw = s.get("kaynak", "")
        kaynak_p = (plan_dir / kaynak_raw).resolve() if not os.path.isabs(kaynak_raw) else Path(kaynak_raw)
        if not kaynak_p.is_file():
            errors.append(f"Sahne #{no}: Kaynak dosya bulunamadı -> '{kaynak_raw}'")
            continue

        ext = kaynak_p.suffix.lower()
        if ext not in VIDEO_EXTS and ext not in IMAGE_EXTS:
            errors.append(f"Sahne #{no}: Desteklenmeyen dosya uzantısı -> '{ext}'")

        neden = str(s.get("neden", "")).strip()
        if len(neden) < 5:
            errors.append(f"Sahne #{no}: 'neden' alanı boş veya çok kısa (kurgu gerekçesi zorunludur).")

        sure = float(s.get("sure", 0.0))
        baslangic = float(s.get("baslangic", 0.0))
        hiz = float(s.get("hiz", 1.0))
        if sure <= 0.2:
            errors.append(f"Sahne #{no}: Geçersiz sahne süresi ({sure} sn).")

        if i == 0 and sure > 3.2:
            warnings.append(f"Sahne #1 (Hook): İlk sahne {sure:.2f} sn (önerilen <= 3.0 sn çarpıcı giriş).")
        elif sure < 1.0:
            warnings.append(f"Sahne #{no}: Çok kısa sahne ({sure:.2f} sn < 1.0 sn).")
        elif sure > 5.5:
            warnings.append(f"Sahne #{no}: Çok uzun sahne ({sure:.2f} sn > 5.5 sn).")

        if ext in VIDEO_EXTS:
            v_dur = probe_duration(str(kaynak_p), ffmpeg_exe)
            gereken = baslangic + (sure * hiz)
            if v_dur > 0 and gereken > v_dur + 0.08:
                errors.append(
                    f"Sahne #{no}: Kaynak süresi aşıldı ({kaynak_p.name}: istenen {gereken:.2f}s > mevcut {v_dur:.2f}s)."
                )

        mod = s.get("mod", "kirp_9_16")
        if mod not in IZINLI_MODLAR:
            errors.append(
                f"Sahne #{no}: Yasaklı veya bilinmeyen görüntüleme modu '{mod}'. İzinli: {sorted(IZINLI_MODLAR)}."
            )

        if s.get("pan_zoom") or s.get("crop_pan"):
            errors.append(
                f"Sahne #{no}: Sabit görselde tam-sayı crop/pan kaydırması yasaktır (1px titreme yaratır)."
            )

        gecis = str(s.get("gecis", "fade")).lower()
        gecis_sure = float(s.get("gecis_sure", 0.40 if gecis in ("fade", "erime") else 0.0))
        if gecis not in IZINLI_GECISLER:
            errors.append(
                f"Sahne #{no}: Göz yoran / yasaklı geçiş '{gecis}'. Yalnızca {sorted(IZINLI_GECISLER)} kullanılabilir."
            )
        if gecis in ("fade", "erime") and not (0.20 <= gecis_sure <= 0.65):
            warnings.append(f"Sahne #{no}: Fade süresi {gecis_sure:.2f} sn (önerilen 0.35 - 0.45 sn).")

        katman_raw = s.get("katman_png", "")
        if katman_raw:
            kp = (plan_dir / katman_raw).resolve() if not os.path.isabs(katman_raw) else Path(katman_raw)
            if not kp.is_file():
                errors.append(f"Sahne #{no}: Yazı/şablon PNG bulunamadı -> '{katman_raw}'")
            elif s.get("yuva_kontrol"):
                slot_errs = check_slot_alpha_fill(str(kp), s["yuva_kontrol"])
                for se in slot_errs:
                    errors.append(f"Sahne #{no} Şablon Hatası: {se}")

        toplam_sure += sure
        if i > 0 and gecis in ("fade", "erime"):
            gecis_toplam += gecis_sure

        net_kesim = toplam_sure - gecis_toplam
        if vuruslar and i < len(sahneler) - 1:
            en_yakin_fark = min(abs(net_kesim - b) for b in vuruslar)
            if en_yakin_fark > 0.12:
                warnings.append(
                    f"Sahne #{no} bitişi ({net_kesim:.2f}s) en yakın müzik vuruşundan {en_yakin_fark:.2f}s uzakta (> 0.12s)."
                )

    net_toplam = toplam_sure - gecis_toplam
    if hedef_sure > 0 and abs(net_toplam - hedef_sure) > 1.5:
        warnings.append(f"Net kurgu süresi ({net_toplam:.2f}s) hedef süreden ({hedef_sure:.2f}s) > 1.5s sapıyor.")

    return errors, warnings


def prepare_still_frame(
    img_path: str,
    target_w: int,
    target_h: int,
    mod: str,
    odak_x: float,
    odak_y: float,
    overlay_paths: list[str],
) -> Image.Image:
    """Görseli sündürmeden 1:1 piksel oranıyla 9:16 kırpar, UnsharpMask ve PNG katmanlarını uygular."""
    raw = Image.open(img_path)
    img = ImageOps.exif_transpose(raw).convert("RGB")
    iw, ih = img.size
    target_ratio = target_w / target_h

    if mod == "kirp_9_16":
        src_ratio = iw / ih
        if src_ratio > target_ratio:
            crop_h = ih
            crop_w = int(round(ih * target_ratio))
            max_dx = max(0, iw - crop_w)
            x0 = int(round(max_dx * max(0.0, min(1.0, odak_x))))
            y0 = 0
        else:
            crop_w = iw
            crop_h = int(round(iw / target_ratio))
            max_dy = max(0, ih - crop_h)
            x0 = 0
            y0 = int(round(max_dy * max(0.0, min(1.0, odak_y))))
        cropped = img.crop((x0, y0, x0 + crop_w, y0 + crop_h))
        canvas = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.4, percent=125, threshold=2))
    else:
        bg = img.resize((target_w, target_h), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius=28))
        bg = Image.eval(bg, lambda p: int(p * 0.45))
        fg = img.copy()
        fg.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        fg = fg.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=2))
        ox = (target_w - fg.width) // 2
        oy = (target_h - fg.height) // 2
        bg.paste(fg, (ox, oy))
        canvas = bg

    rgba = canvas.convert("RGBA")
    for ovp in overlay_paths:
        if ovp and os.path.isfile(ovp):
            ov = Image.open(ovp).convert("RGBA")
            if ov.size != (target_w, target_h):
                ov = ov.resize((target_w, target_h), Image.Resampling.LANCZOS)
            rgba = Image.alpha_composite(rgba, ov)

    return rgba.convert("RGB")


def render_segment(
    idx: int,
    shot: dict,
    plan_dir: Path,
    seg_dir: Path,
    target_w: int,
    target_h: int,
    fps: int,
    crf: int,
    sabit_katman_png: str,
    ffmpeg_exe: str,
) -> Path:
    """Tek bir sahneyi SHA-256 önbellekli olarak seg_XX_<hash>.mp4 dosyasına render eder."""
    kaynak_raw = shot["kaynak"]
    kaynak_p = (plan_dir / kaynak_raw).resolve() if not os.path.isabs(kaynak_raw) else Path(kaynak_raw)
    ext = kaynak_p.suffix.lower()

    sure = float(shot.get("sure", 3.0))
    baslangic = float(shot.get("baslangic", 0.0))
    hiz = float(shot.get("hiz", 1.0))
    mod = shot.get("mod", "kirp_9_16")
    odak_x = float(shot.get("odak_x", 0.5))
    odak_y = float(shot.get("odak_y", 0.35))

    overlays = []
    if sabit_katman_png:
        sp = (plan_dir / sabit_katman_png).resolve() if not os.path.isabs(sabit_katman_png) else Path(sabit_katman_png)
        if sp.is_file():
            overlays.append(str(sp))
    if shot.get("katman_png"):
        kp = (plan_dir / shot["katman_png"]).resolve() if not os.path.isabs(shot["katman_png"]) else Path(shot["katman_png"])
        if kp.is_file():
            overlays.append(str(kp))

    sig_payload = json.dumps(
        {
            "src": file_sha256_short(str(kaynak_p)),
            "ov": [file_sha256_short(o) for o in overlays],
            "sure": round(sure, 3),
            "baslangic": round(baslangic, 3),
            "hiz": round(hiz, 3),
            "mod": mod,
            "ox": round(odak_x, 3),
            "oy": round(odak_y, 3),
            "w": target_w,
            "h": target_h,
            "fps": fps,
            "crf": crf,
        },
        sort_keys=True,
    )
    seg_hash = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()[:10]
    final_seg = seg_dir / f"seg_{idx:02d}_{seg_hash}.mp4"

    if final_seg.is_file() and final_seg.stat().st_size > 1024:
        return final_seg

    # Eski seg_XX_* dosyalarını temizle
    for old_f in seg_dir.glob(f"seg_{idx:02d}_*.mp4"):
        try:
            old_f.unlink()
        except Exception:
            pass

    tmp_seg = seg_dir / f"_tmp_seg_{idx:02d}.mp4"

    if ext in IMAGE_EXTS:
        composed_img = prepare_still_frame(str(kaynak_p), target_w, target_h, mod, odak_x, odak_y, overlays)
        tmp_png = seg_dir / f"_tmp_still_{idx:02d}.png"
        composed_img.save(tmp_png, compress_level=1)
        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", str(fps), "-i", str(tmp_png),
            "-t", f"{sure:.3f}",
            "-vf", f"fps={fps},settb=1/{fps},setsar=1,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-an", str(final_seg)
        ]
        subprocess.run(cmd, check=True)
        try:
            tmp_png.unlink()
        except Exception:
            pass
        return final_seg

    # Video kaynağı: birleşik PNG katmanı varsa tek bir geçici PNG oluştur
    ov_png_path = None
    if overlays:
        base_ov = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        for ovp in overlays:
            ov_img = Image.open(ovp).convert("RGBA")
            if ov_img.size != (target_w, target_h):
                ov_img = ov_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base_ov = Image.alpha_composite(base_ov, ov_img)
        ov_png_path = seg_dir / f"_tmp_ov_{idx:02d}.png"
        base_ov.save(ov_png_path, compress_level=1)

    pts_expr = f"{1.0 / hiz:.4f}*PTS" if abs(hiz - 1.0) > 0.01 else "PTS-STARTPTS"
    scale_crop = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={target_w}:{target_h},unsharp=3:3:0.45:3:3:0.0,"
        f"setpts={pts_expr},fps={fps},settb=1/{fps},setsar=1,format=yuv420p"
    )

    if ov_png_path:
        fc = f"[0:v]{scale_crop}[v0];[v0][1:v]overlay=0:0:shortest=1,fps={fps},settb=1/{fps},setsar=1,format=yuv420p[vout]"
        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{baslangic:.3f}", "-i", str(kaynak_p),
            "-i", str(ov_png_path),
            "-t", f"{sure:.3f}",
            "-filter_complex", fc,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-an", str(tmp_seg)
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{baslangic:.3f}", "-i", str(kaynak_p),
            "-t", f"{sure:.3f}",
            "-vf", scale_crop,
            "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-an", str(tmp_seg)
        ]

    subprocess.run(cmd, check=True)
    if ov_png_path and ov_png_path.is_file():
        try:
            ov_png_path.unlink()
        except Exception:
            pass

    # Kritik koruma: FFmpeg 7.1 dikey 4K videolardan kopyalanan displaymatrix yan verisini sıfırla
    cmd_strip = [
        ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
        "-display_rotation", "0", "-i", str(tmp_seg),
        "-c", "copy", str(final_seg)
    ]
    subprocess.run(cmd_strip, check=True)
    try:
        tmp_seg.unlink()
    except Exception:
        pass

    return final_seg


def join_segments_and_audio(
    segments: list[Path],
    sahneler: list[dict],
    plan: dict,
    plan_dir: Path,
    out_mp4: Path,
    fps: int,
    crf: int,
    ffmpeg_exe: str,
) -> float:
    """Normalize edilmiş segmentleri xfade/concat ile birleştirir ve müziği (-14 LUFS + fade-out) ekler."""
    inputs = []
    for seg in segments:
        inputs.extend(["-i", str(seg)])

    n = len(segments)
    if n == 1:
        total_dur = float(sahneler[0]["sure"])
        v_filter = f"[0:v]fps={fps},settb=1/{fps},setsar=1,format=yuv420p[vout]"
    else:
        fc_parts = []
        for i in range(n):
            fc_parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={fps},settb=1/{fps},setsar=1,format=yuv420p[v{i}]")

        offset = float(sahneler[0]["sure"])
        prev_label = "v0"
        for i in range(1, n):
            gecis = str(sahneler[i - 1].get("gecis", "fade")).lower()
            d_tr = float(sahneler[i - 1].get("gecis_sure", 0.40)) if gecis in ("fade", "erime") else 0.0
            out_label = "vout" if i == n - 1 else f"vx{i}"
            if d_tr > 0.01:
                offset = max(0.05, offset - d_tr)
                fc_parts.append(
                    f"[{prev_label}][v{i}]xfade=transition=fade:duration={d_tr:.3f}:offset={offset:.3f}[{out_label}]"
                )
            else:
                fc_parts.append(
                    f"[{prev_label}][v{i}]xfade=transition=fade:duration=0.040:offset={max(0.05, offset - 0.04):.3f}[{out_label}]"
                )
            offset += float(sahneler[i]["sure"])
            prev_label = out_label

        total_dur = offset
        v_filter = ";".join(fc_parts)

    muzik_raw = plan.get("muzik", "")
    muzik_p = (plan_dir / muzik_raw).resolve() if (muzik_raw and not os.path.isabs(muzik_raw)) else (Path(muzik_raw) if muzik_raw else None)

    cmd = [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error"] + inputs
    if muzik_p and muzik_p.is_file():
        muzik_bas = float(plan.get("muzik_baslangic_sn", 0.0))
        fade_out_st = max(0.5, total_dur - 1.5)
        a_filter = (
            f"[{n}:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_st:.3f}:d=1.5[aout]"
        )
        full_fc = f"{v_filter};{a_filter}"
        cmd += [
            "-ss", f"{muzik_bas:.3f}", "-i", str(muzik_p),
            "-filter_complex", full_fc,
            "-map", "[vout]", "-map", "[aout]",
            "-t", f"{total_dur:.3f}",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-movflags", "+faststart",
            "-metadata", "comment=kedihane-plan-render-v2",
            str(out_mp4),
        ]
    else:
        cmd += [
            "-filter_complex", v_filter,
            "-map", "[vout]",
            "-t", f"{total_dur:.3f}",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-an",
            "-movflags", "+faststart",
            "-metadata", "comment=kedihane-plan-render-v2",
            str(out_mp4),
        ]

    subprocess.run(cmd, check=True)
    return round(total_dur, 3)


def generate_verification_sheet(
    mp4_path: Path, sahneler: list[dict], out_jpg: Path, ffmpeg_exe: str
):
    """Her sahnenin orta karesini çekerek numaralı `_kareler.jpg` kanıt sayfasını oluşturur."""
    mid_times = []
    cursor = 0.0
    for i, s in enumerate(sahneler):
        dur = float(s.get("sure", 3.0))
        gecis = str(s.get("gecis", "fade")).lower()
        d_tr = float(s.get("gecis_sure", 0.40)) if (i > 0 and gecis in ("fade", "erime")) else 0.0
        cursor = max(0.0, cursor - d_tr)
        mid_times.append((i + 1, round(cursor + dur * 0.5, 2), Path(s["kaynak"]).name))
        cursor += dur

    thumbs = []
    for no, ts, name in mid_times:
        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{ts:.2f}", "-i", str(mp4_path),
            "-frames:v", "1", "-vf", "scale=270:-2",
            "-f", "image2pipe", "-vcodec", "png", "-"
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0 and proc.stdout:
            im = Image.open(BytesIO(proc.stdout)).convert("RGB")
        else:
            im = Image.new("RGB", (270, 480), (30, 30, 30))
        thumbs.append((no, ts, name, im))

    cols = min(4, max(1, len(thumbs)))
    rows = math.ceil(len(thumbs) / cols)
    cw, ch = 290, 540
    sheet = Image.new("RGB", (cols * cw + 20, rows * ch + 60), (16, 18, 22))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((20, 18), f"KEDIHANE RENDER KONTROL SAYFASI: {mp4_path.name}", fill=(110, 235, 160), font=font)

    for idx, (no, ts, name, im) in enumerate(thumbs):
        r, c = divmod(idx, cols)
        x0, y0 = 10 + c * cw, 50 + r * ch
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch - 4], outline=(65, 75, 85), width=1)
        im.thumbnail((cw - 20, ch - 60), Image.Resampling.LANCZOS)
        sheet.paste(im, (x0 + (cw - im.width) // 2, y0 + 10))
        draw.text((x0 + 14, y0 + ch - 42), f"Sahne #{no:02d} @ {ts:.2f}s", fill=(245, 220, 100), font=font)
        draw.text((x0 + 14, y0 + ch - 24), name[:28], fill=(210, 215, 220), font=font)

    sheet.save(out_jpg, quality=90)


def write_premiere_xml(
    segments: list[Path], sahneler: list[dict], plan: dict, plan_dir: Path, xml_path: Path, w: int, h: int, fps: int
):
    """Premiere Pro ile tam uyumlu FCP7 XML (xmeml v4) zaman çizelgesi üretir."""
    root = ET.Element("xmeml", version="4")
    seq = ET.SubElement(root, "sequence")
    ET.SubElement(seq, "name").text = xml_path.stem
    rate = ET.SubElement(seq, "rate")
    ET.SubElement(rate, "timebase").text = str(fps)
    ET.SubElement(rate, "ntsc").text = "FALSE"

    media = ET.SubElement(seq, "media")
    video = ET.SubElement(media, "video")
    v_fmt = ET.SubElement(video, "format")
    sc = ET.SubElement(v_fmt, "samplecharacteristics")
    ET.SubElement(sc, "width").text = str(w)
    ET.SubElement(sc, "height").text = str(h)
    ET.SubElement(sc, "pixelaspectratio").text = "square"

    v_track = ET.SubElement(video, "track")
    cursor_f = 0
    for idx, (seg_p, s) in enumerate(zip(segments, sahneler)):
        dur_f = int(round(float(s.get("sure", 3.0)) * fps))
        ci = ET.SubElement(v_track, "clipitem", id=f"clipitem-{idx + 1}")
        ET.SubElement(ci, "name").text = seg_p.name
        ET.SubElement(ci, "duration").text = str(dur_f)
        c_rate = ET.SubElement(ci, "rate")
        ET.SubElement(c_rate, "timebase").text = str(fps)
        ET.SubElement(c_rate, "ntsc").text = "FALSE"
        ET.SubElement(ci, "start").text = str(cursor_f)
        ET.SubElement(ci, "end").text = str(cursor_f + dur_f)
        ET.SubElement(ci, "in").text = "0"
        ET.SubElement(ci, "out").text = str(dur_f)
        f_el = ET.SubElement(ci, "file", id=f"file-{idx + 1}")
        ET.SubElement(f_el, "name").text = seg_p.name
        abs_posix = seg_p.resolve().as_posix()
        ET.SubElement(f_el, "pathurl").text = "file://localhost/" + quote(abs_posix, safe="/:")
        cursor_f += dur_f

    ET.SubElement(seq, "duration").text = str(cursor_f)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description="Kedihane Plan Doğrulama ve Render Aracı")
    parser.add_argument("plan_json", help="Kurgu planı JSON dosyası yolu")
    parser.add_argument("--dogrula", action="store_true", help="Yalnızca planı doğrula, render alma")
    parser.add_argument("--onizleme", action="store_true", help="540x960 hızlı önizleme ve _kareler.jpg üret")
    parser.add_argument("--master", action="store_true", help="1080x1920 master MP4, Premiere XML ve _kareler.jpg üret")
    args = parser.parse_args()

    plan_path = Path(args.plan_json).resolve()
    if not plan_path.is_file():
        print(f"[HATA] Plan dosyası bulunamadı: {plan_path}")
        sys.exit(1)

    plan_dir = plan_path.parent
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    ffmpeg_exe = get_ffmpeg_exe()

    errors, warnings = validate_plan(plan, plan_dir, ffmpeg_exe)
    print("=" * 60)
    print(f" Kedihane Kurgu Planı Doğrulaması: {plan_path.name}")
    print("=" * 60)
    for w_msg in warnings:
        print(f"  [UYARI] {w_msg}")
    for e_msg in errors:
        print(f"  [HATA]  {e_msg}")

    if errors:
        print(f"\n[BAŞARISIZ] Toplam {len(errors)} hata ve {len(warnings)} uyarı bulundu. Render durduruldu.")
        sys.exit(1)

    print(f"[GEÇTİ] Doğrulama başarılı ({len( plan.get('sahneler', []) )} sahne, {len(warnings)} uyarı).")
    if args.dogrula and not (args.onizleme or args.master):
        sys.exit(0)

    is_master = args.master or not args.onizleme
    base_w = int(plan.get("genislik", 1080))
    base_h = int(plan.get("yukseklik", 1920))
    target_w = base_w if is_master else max(360, base_w // 2)
    target_h = base_h if is_master else max(640, base_h // 2)
    fps = int(plan.get("fps", 30))
    crf = int(plan.get("crf", 17 if is_master else 24))

    cikti_raw = plan.get("cikti_mp4", "kurgu_master.mp4" if is_master else "kurgu_onizleme.mp4")
    if not is_master and cikti_raw.endswith(".mp4") and "_onizleme" not in cikti_raw:
        cikti_raw = cikti_raw[:-4] + "_onizleme.mp4"
    out_mp4 = (plan_dir / cikti_raw).resolve() if not os.path.isabs(cikti_raw) else Path(cikti_raw)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    seg_dir = plan_dir / "_segments" / ("master" if is_master else "onizleme")
    seg_dir.mkdir(parents=True, exist_ok=True)

    sahneler = plan["sahneler"]
    sabit_katman = plan.get("sabit_katman_png", "")

    rendered_segs = []
    for idx, shot in enumerate(sahneler):
        seg_p = render_segment(
            idx, shot, plan_dir, seg_dir, target_w, target_h, fps, crf, sabit_katman, ffmpeg_exe
        )
        rendered_segs.append(seg_p)
        print(f"  + Sahne #{idx + 1:02d}/{len(sahneler):02d} hazır: {seg_p.name}")

    total_dur = join_segments_and_audio(
        rendered_segs, sahneler, plan, plan_dir, out_mp4, fps, crf, ffmpeg_exe
    )

    kareler_jpg = out_mp4.with_name(out_mp4.stem + "_kareler.jpg")
    generate_verification_sheet(out_mp4, sahneler, kareler_jpg, ffmpeg_exe)

    xml_path = out_mp4.with_name(out_mp4.stem + "_premiere.xml")
    write_premiere_xml(rendered_segs, sahneler, plan, plan_dir, xml_path, target_w, target_h, fps)

    print("=" * 60)
    print(f"[TAMAM] Video üretildi : {out_mp4} ({total_dur:.2f} sn, {target_w}x{target_h})")
    print(f"[KANIT] Kontrol sayfası: {kareler_jpg}")
    print(f"[XML]   Premiere sekans: {xml_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
