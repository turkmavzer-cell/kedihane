#!/usr/bin/env python3
"""Kedihane Video, Görsel ve Müzik Ön Analiz Aracı (`tools/video/analiz.py`)

Bu betik kurgu öncesinde kaynak klasördeki videoları, görselleri ve müziği tarar:
- Videoların gerçek görünür boyutunu (`displaymatrix` döndürme etiketi dahil),
  kare hızını, süresini, parlaklık ve netlik (Laplacian) skorlarını ölçer.
- Görsellerin en-boy oranını (`3:4`, `9:16`, `1:1`), netliğini ve alfa kanalını inceler.
- Müziğin enerji tepelerinden (peak/onset) gerçek BPM ve vuruş saniyelerini (`vuruslar_sn`) çıkarır.
- Zaman damgalı `_kontak_videolar.jpg`, `_kontak_gorseller.jpg` ve `analiz.json` üretir.

Kullanım:
    python tools/video/analiz.py <kaynak_klasor> [--muzik <muzik_yolu>] [--cikti <cikti_klasoru>]
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def get_ffmpeg_exe() -> str:
    """Sistemdeki veya imageio_ffmpeg içindeki ffmpeg yürütülebilir dosyasını bulur."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if found:
            return found
        raise RuntimeError("ffmpeg bulunamadı. Lütfen imageio-ffmpeg kurun veya ffmpeg'i PATH'e ekleyin.")


def get_ffprobe_exe() -> str:
    """Varsa ffprobe yolunu döner, yoksa boş string döner."""
    return shutil.which("ffprobe") or ""


def laplacian_sharpness(gray_arr: np.ndarray) -> float:
    """2B ayrık Laplacian varyansı ile görüntü netliğini (keskinliğini) ölçer."""
    g = gray_arr.astype(np.float32)
    if g.shape[0] < 4 or g.shape[1] < 4:
        return 0.0
    lap = (
        -4.0 * g[1:-1, 1:-1]
        + g[:-2, 1:-1]
        + g[2:, 1:-1]
        + g[1:-1, :-2]
        + g[1:-1, 2:]
    )
    return float(np.var(lap))


def classify_aspect(w: int, h: int) -> str:
    """Genişlik ve yüksekliğe göre standart en-boy oranı etiketini döner."""
    if w <= 0 or h <= 0:
        return "bilinmiyor"
    r = w / h
    candidates = [
        ("9:16", 9.0 / 16.0),
        ("3:4", 3.0 / 4.0),
        ("4:5", 4.0 / 5.0),
        ("1:1", 1.0),
        ("4:3", 4.0 / 3.0),
        ("16:9", 16.0 / 9.0),
    ]
    best_name, best_diff = "ozel", 999.0
    for name, val in candidates:
        diff = abs(r - val)
        if diff < best_diff:
            best_name, best_diff = name, diff
    return best_name if best_diff <= 0.06 else f"{w}:{h}"


def probe_video_info(filepath: str, ffmpeg_exe: str) -> dict:
    """Videonun çözünürlük, döndürme (displaymatrix), süre, fps ve ses bilgilerini çıkarır."""
    cmd = [ffmpeg_exe, "-hide_banner", "-i", filepath]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    stderr = res.stderr

    dur = 0.0
    m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if m_dur:
        dur = int(m_dur.group(1)) * 3600 + int(m_dur.group(2)) * 60 + float(m_dur.group(3))

    w, h, fps, codec = 0, 0, 30.0, "unknown"
    for line in stderr.splitlines():
        if "Video:" in line:
            m_c = re.search(r"Video:\s*([a-zA-Z0-9_]+)", line)
            if m_c:
                codec = m_c.group(1)
            m_wh = re.search(r",\s*(\d{2,5})x(\d{2,5})(?:[\s,\[])", line)
            if m_wh:
                w, h = int(m_wh.group(1)), int(m_wh.group(2))
            m_fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", line)
            if m_fps:
                fps = float(m_fps.group(1))
            break

    rotation = 0
    m_rot = re.search(r"rotation of\s*([+-]?\d+(?:\.\d+)?)\s*degrees", stderr)
    if m_rot:
        rotation = int(round(float(m_rot.group(1))))
    else:
        m_tag = re.search(r"rotate\s*:\s*(\d+)", stderr)
        if m_tag:
            rotation = int(m_tag.group(1))

    has_audio = "Audio:" in stderr
    eff_w, eff_h = (h, w) if abs(rotation) in (90, 270) else (w, h)

    return {
        "dosya": os.path.basename(filepath),
        "yol": str(Path(filepath).resolve()),
        "kodek": codec,
        "ham_genislik": w,
        "ham_yukseklik": h,
        "donus_derecesi": rotation,
        "gorunen_genislik": eff_w,
        "gorunen_yukseklik": eff_h,
        "en_boy_orani": classify_aspect(eff_w, eff_h),
        "fps": round(fps, 3),
        "sure_sn": round(dur, 3),
        "ses_var_mi": has_audio,
    }


def extract_video_samples(filepath: str, info: dict, ffmpeg_exe: str) -> tuple[list[Image.Image], dict]:
    """Videodan 4 örnek kare çıkarır; netlik, parlaklık ve en iyi zaman aralığını hesaplar."""
    dur = max(info["sure_sn"], 0.5)
    ratios = [0.15, 0.40, 0.65, 0.85]
    timestamps = [round(min(max(0.05, dur * r), max(0.05, dur - 0.1)), 2) for r in ratios]

    frames = []
    metrics = []
    for ts in timestamps:
        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{ts:.2f}", "-i", filepath,
            "-frames:v", "1", "-vf", "scale=360:-2",
            "-f", "image2pipe", "-vcodec", "png", "-"
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0 and proc.stdout:
            from io import BytesIO
            img = Image.open(BytesIO(proc.stdout)).convert("RGB")
            gray = np.array(img.convert("L"))
            bri = float(np.mean(gray))
            shp = laplacian_sharpness(gray)
            frames.append(img)
            metrics.append({
                "saniye": ts,
                "parlaklik": round(bri, 1),
                "netlik": round(shp, 1),
                "siyah_mi": bri < 14.0,
            })
        else:
            img = Image.new("RGB", (270, 480), (20, 20, 20))
            frames.append(img)
            metrics.append({"saniye": ts, "parlaklik": 0.0, "netlik": 0.0, "siyah_mi": True})

    valid = [m for m in metrics if not m["siyah_mi"]]
    best_ts = max(valid or metrics, key=lambda x: x["netlik"])["saniye"]
    rec_start = round(max(0.0, min(best_ts - 1.2, max(0.0, dur - 3.0))), 2)
    rec_dur = round(min(3.5, dur - rec_start), 2)

    summary = {
        "ornek_kareler": metrics,
        "ortalama_parlaklik": round(float(np.mean([m["parlaklik"] for m in metrics])), 1),
        "ortalama_netlik": round(float(np.mean([m["netlik"] for m in metrics])), 1),
        "siyah_kare_uyarisi": any(m["siyah_mi"] for m in metrics),
        "onerilen_baslangic_sn": rec_start,
        "onerilen_sure_sn": rec_dur,
    }
    return frames, summary


def analyze_image(filepath: str) -> tuple[Image.Image, dict]:
    """Görselin boyut, en-boy oranı, alfa kanalı ve netlik bilgilerini analiz eder."""
    img_raw = Image.open(filepath)
    img = ImageOps.exif_transpose(img_raw)
    has_alpha = "A" in img.getbands()
    w, h = img.size
    gray = np.array(img.convert("L").resize((min(w, 540), min(h, 960)), Image.Resampling.BILINEAR))
    shp = laplacian_sharpness(gray)
    bri = float(np.mean(gray))

    aspect = classify_aspect(w, h)
    thumb = img.convert("RGB")
    thumb.thumbnail((320, 480), Image.Resampling.LANCZOS)

    info = {
        "dosya": os.path.basename(filepath),
        "yol": str(Path(filepath).resolve()),
        "genislik": w,
        "yukseklik": h,
        "en_boy_orani": aspect,
        "alfa_var_mi": has_alpha,
        "parlaklik": round(bri, 1),
        "netlik": round(shp, 1),
        "onerilen_mod": "kirp_9_16" if aspect in ("3:4", "4:5", "1:1", "9:16") else "sigdir_bulanik_arka",
    }
    return thumb, info


def analyze_audio_beats(filepath: str, ffmpeg_exe: str, max_sec: float = 95.0) -> dict:
    """Müziğin enerji zarfı ve onset tepelerinden gerçek BPM ve vuruş saniyelerini çıkarır."""
    sr = 22050
    cmd = [
        ffmpeg_exe, "-hide_banner", "-loglevel", "error",
        "-i", filepath, "-t", str(max_sec),
        "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        return {"dosya": os.path.basename(filepath), "hata": "Ses okunamadı", "bpm": 120.0, "vuruslar_sn": []}

    samples = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    total_dur = round(len(samples) / sr, 3)
    if len(samples) < sr * 2:
        return {"dosya": os.path.basename(filepath), "sure_sn": total_dur, "bpm": 120.0, "vuruslar_sn": []}

    hop = 220  # 10 ms çözünürlük (100 Hz zarf)
    env_rate = sr / hop
    n_frames = len(samples) // hop
    framed = samples[: n_frames * hop].reshape((n_frames, hop))
    rms = np.sqrt(np.mean(framed ** 2, axis=1) + 1e-9)

    onset = np.maximum(0.0, np.diff(rms, prepend=rms[0]))
    kernel = np.hanning(7)
    kernel /= np.sum(kernel)
    onset_smooth = np.convolve(onset, kernel, mode="same")

    # Otokorelasyon ile 72..160 BPM aralığında tempo tahmini
    ac_norm = onset_smooth - np.mean(onset_smooth)
    corr = np.correlate(ac_norm, ac_norm, mode="full")[len(ac_norm) - 1 :]
    min_lag = int(round(env_rate * 60.0 / 160.0))
    max_lag = min(len(corr) - 1, int(round(env_rate * 60.0 / 72.0)))

    if max_lag > min_lag:
        best_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        bpm = round(float(60.0 * env_rate / best_lag), 1)
    else:
        bpm = 120.0
        best_lag = int(round(env_rate * 0.5))

    # Gerçek enerji tepelerinden (peak-picking) vuruş zamanlarını çıkar (kaymayı önler)
    min_dist = max(int(best_lag * 0.72), 25)
    thresh = float(np.percentile(onset_smooth, 64))
    peaks = []
    last_idx = -min_dist
    for i in range(2, len(onset_smooth) - 2):
        val = onset_smooth[i]
        if val >= thresh and val >= np.max(onset_smooth[max(0, i - 3) : min(len(onset_smooth), i + 4)]):
            if i - last_idx >= min_dist:
                peaks.append(round(i / env_rate, 3))
                last_idx = i
            elif peaks and val > onset_smooth[last_idx]:
                peaks[-1] = round(i / env_rate, 3)
                last_idx = i

    return {
        "dosya": os.path.basename(filepath),
        "yol": str(Path(filepath).resolve()),
        "sure_sn": total_dur,
        "bpm": bpm,
        "vurus_sayisi": len(peaks),
        "vuruslar_sn": peaks[:160],
    }


def render_video_contact_sheet(video_items: list[tuple[dict, list[Image.Image]]], out_path: str):
    """Videoların 4'lü örnek karelerini ve teknik metriklerini içeren kontak sayfası üretir."""
    if not video_items:
        return
    row_h = 280
    col_w = 160
    canvas_w = 4 * col_w + 340
    canvas_h = max(1, len(video_items)) * row_h + 60
    sheet = Image.new("RGB", (canvas_w, canvas_h), (18, 18, 22))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    draw.text((20, 18), "KEDIHANE VIDEO KAYNAK KONTAK SAYFASI (analiz.py)", fill=(240, 210, 90), font=font)

    for idx, (vinfo, frames) in enumerate(video_items):
        y0 = 50 + idx * row_h
        draw.rectangle([10, y0, canvas_w - 10, y0 + row_h - 10], outline=(60, 65, 75), width=1)
        meta_lines = [
            f"#{idx + 1:02d} {vinfo['dosya']}",
            f"Boyut: {vinfo['gorunen_genislik']}x{vinfo['gorunen_yukseklik']} ({vinfo['en_boy_orani']})",
            f"Donus: {vinfo['donus_derecesi']} deg | FPS: {vinfo['fps']}",
            f"Sure: {vinfo['sure_sn']} sn | Ses: {'Evet' if vinfo['ses_var_mi'] else 'Hayir'}",
            f"Netlik: {vinfo['ortalama_netlik']} | Parlaklik: {vinfo['ortalama_parlaklik']}",
            f"Oneri: {vinfo['onerilen_baslangic_sn']}s (+{vinfo['onerilen_sure_sn']}s)",
        ]
        for li, mline in enumerate(meta_lines):
            color = (255, 110, 110) if (li == 4 and vinfo.get("siyah_kare_uyarisi")) else (220, 225, 230)
            draw.text((22, y0 + 18 + li * 26), mline, fill=color, font=font)

        for fi, frm in enumerate(frames[:4]):
            fx = 330 + fi * col_w
            thumb = frm.copy()
            thumb.thumbnail((col_w - 12, row_h - 45), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (fx, y0 + 12))
            m_fr = vinfo["ornek_kareler"][fi]
            lbl = f"{m_fr['saniye']}s | N:{int(m_fr['netlik'])}"
            draw.text((fx, y0 + row_h - 28), lbl, fill=(180, 230, 180), font=font)

    sheet.save(out_path, quality=88)


def render_image_contact_sheet(img_items: list[tuple[dict, Image.Image]], out_path: str):
    """Görsellerin numaralı, boyut ve oran etiketli kontak sayfasını üretir."""
    if not img_items:
        return
    cols = min(4, max(1, len(img_items)))
    rows = math.ceil(len(img_items) / cols)
    cell_w, cell_h = 260, 360
    sheet = Image.new("RGB", (cols * cell_w + 20, rows * cell_h + 60), (22, 22, 26))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    draw.text((20, 18), "KEDIHANE GORSEL KAYNAK KONTAK SAYFASI (analiz.py)", fill=(120, 215, 250), font=font)

    for idx, (info, thumb) in enumerate(img_items):
        r, c = divmod(idx, cols)
        x0 = 10 + c * cell_w
        y0 = 50 + r * cell_h
        draw.rectangle([x0 + 4, y0 + 4, x0 + cell_w - 4, y0 + cell_h - 4], outline=(70, 75, 85), width=1)
        t_copy = thumb.copy()
        t_copy.thumbnail((cell_w - 20, cell_h - 80), Image.Resampling.LANCZOS)
        ox = x0 + (cell_w - t_copy.width) // 2
        sheet.paste(t_copy, (ox, y0 + 12))
        draw.text((x0 + 12, y0 + cell_h - 60), f"#{idx + 1:02d} {info['dosya'][:24]}", fill=(240, 240, 240), font=font)
        draw.text(
            (x0 + 12, y0 + cell_h - 40),
            f"{info['genislik']}x{info['yukseklik']} ({info['en_boy_orani']}) N:{int(info['netlik'])}",
            fill=(200, 220, 160),
            font=font,
        )
        draw.text((x0 + 12, y0 + cell_h - 22), f"Mod: {info['onerilen_mod']}", fill=(170, 195, 255), font=font)

    sheet.save(out_path, quality=88)


def main():
    parser = argparse.ArgumentParser(description="Kedihane Video/Görsel/Müzik Ön Analiz Aracı")
    parser.add_argument("kaynak_klasor", help="Video ve görsellerin bulunduğu kaynak klasör")
    parser.add_argument("--muzik", default="", help="Müzik dosyası veya müzik klasörü yolu")
    parser.add_argument("--cikti", default="", help="Çıktı klasörü (varsayılan: <kaynak_klasor>/_calisma)")
    args = parser.parse_args()

    src_dir = Path(args.kaynak_klasor).resolve()
    if not src_dir.is_dir():
        print(f"[HATA] Kaynak klasör bulunamadı: {src_dir}")
        sys.exit(1)

    out_dir = Path(args.cikti).resolve() if args.cikti else (src_dir / "_calisma")
    out_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = get_ffmpeg_exe()
    videos, images, audios = [], [], []

    for entry in sorted(src_dir.iterdir()):
        if not entry.is_file() or entry.name.startswith("."):
            continue
        ext = entry.suffix.lower()
        if ext in VIDEO_EXTS:
            videos.append(entry)
        elif ext in IMAGE_EXTS:
            images.append(entry)
        elif ext in AUDIO_EXTS:
            audios.append(entry)

    if args.muzik:
        m_path = Path(args.muzik).resolve()
        if m_path.is_file():
            audios.append(m_path)
        elif m_path.is_dir():
            for entry in sorted(m_path.iterdir()):
                if entry.is_file() and entry.suffix.lower() in AUDIO_EXTS:
                    audios.append(entry)

    video_results = []
    video_sheet_items = []
    for vp in videos:
        vinfo = probe_video_info(str(vp), ffmpeg_exe)
        frames, vmetrics = extract_video_samples(str(vp), vinfo, ffmpeg_exe)
        vinfo.update(vmetrics)
        video_results.append(vinfo)
        video_sheet_items.append((vinfo, frames))

    image_results = []
    image_sheet_items = []
    for ip in images:
        thumb, iinfo = analyze_image(str(ip))
        image_results.append(iinfo)
        image_sheet_items.append((iinfo, thumb))

    audio_results = []
    for ap in audios[:5]:
        ainfo = analyze_audio_beats(str(ap), ffmpeg_exe)
        audio_results.append(ainfo)

    kontak_video_path = str(out_dir / "_kontak_videolar.jpg") if video_sheet_items else ""
    kontak_gorsel_path = str(out_dir / "_kontak_gorseller.jpg") if image_sheet_items else ""

    if video_sheet_items:
        render_video_contact_sheet(video_sheet_items, kontak_video_path)
    if image_sheet_items:
        render_image_contact_sheet(image_sheet_items, kontak_gorsel_path)

    report = {
        "kaynak_klasor": str(src_dir),
        "cikti_klasoru": str(out_dir),
        "kontak_videolar_jpg": kontak_video_path,
        "kontak_gorseller_jpg": kontak_gorsel_path,
        "ozet": {
            "video_sayisi": len(video_results),
            "gorsel_sayisi": len(image_results),
            "muzik_sayisi": len(audio_results),
        },
        "videolar": video_results,
        "gorseller": image_results,
        "muzikler": audio_results,
    }

    json_path = out_dir / "analiz.json"
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)

    print(f"[TAMAM] Analiz tamamlandı: {json_path}")
    print(f"  - Videolar : {len(video_results)} ({kontak_video_path or 'yok'})")
    print(f"  - Görseller: {len(image_results)} ({kontak_gorsel_path or 'yok'})")
    print(f"  - Müzikler : {len(audio_results)}")


if __name__ == "__main__":
    main()
