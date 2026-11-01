#!/usr/bin/env python3
"""Kedihane Repo Denetim Aracı (Sarman Otomatik Kalite Kapısı)

Bu betik git reposundaki izlenen dosyaları 6 kritik kontrolden geçirir:
1. Gizlilik, Marka, Sosyal Hesap ve Sabit Yol Kontrolü
2. Kırık Referans Kontrolü
3. UTF-8 BOM ve İkili (.so/.dll) Kontrolü
4. Fihrist Satır Aralığı (Lxx-Lyy) ve Başlık Eşleşmesi Kontrolü
5. Ajan Hafıza (MEMORY.md) Boyut ve Alfabetik Sıra Kontrolü
6. Sözdizimi Derleme Kontrolü (py_compile & node --check)

Kullanım:
    python tools/denetim.py
"""
import glob
import os
import py_compile
import re
import subprocess
import sys

# Windows konsolunda UTF-8 çıktı desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_tracked_files():
    """git ls-files (izlenen + çalışma ağacındaki izlenmeyen dosyalar) çıktısını alır."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            text=True,
            encoding="utf-8",
        )
        files = sorted(set(f.strip() for f in out.splitlines() if f.strip()))
    except Exception as e:
        print(f"Hata: git ls-files çalıştırılamadı: {e}")
        return []

    filtered = []
    for f in files:
        norm = f.replace("\\", "/")
        if norm.endswith(".ttf") or norm.endswith("package-lock.json"):
            continue
        filtered.append(norm)
    return filtered


def _yerel_yasakli_desenler():
    """Repo dışı tutulan `.denetim_yasakli.txt` dosyasından (satır başına bir regex) yasaklı desenleri okur."""
    yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".denetim_yasakli.txt")
    if not os.path.isfile(yol):
        return []
    with open(yol, "r", encoding="utf-8") as fp:
        return [s.strip() for s in fp if s.strip() and not s.startswith("#")]


def kontrol_1_gizlilik_ve_sabit_yol(files):
    """Gizlilik, Marka, Sosyal Hesap ve Sabit Yol Kontrolü."""
    p_yasakli = re.compile(
        r"|".join(_yerel_yasakli_desenler()) or r"(?!x)x",
        re.IGNORECASE,
    )
    p_telefon = re.compile(
        r"\+[1-9]\d{0,2}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{2,4}|\+20\s*\d|\+90\s*\d|wa\.me/\d+"
    )
    p_sabit_yol = re.compile(
        r"\b[A-Z]:[/\\]Users[/\\][^/\\\s]+|/sessions/[\w-]+/|/mnt/user-data|\bE:[/\\]",
        re.IGNORECASE,
    )

    hatalar = []
    for f in files:
        if f == "tools/denetim.py":
            continue
        if not os.path.isfile(f):
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    m1 = p_yasakli.search(line)
                    if m1:
                        hatalar.append(f"{f}:{line_no} -> Yasaklı desen: '{m1.group()}'")
                    m2 = p_telefon.search(line)
                    if m2:
                        hatalar.append(f"{f}:{line_no} -> Gerçek telefon / wa.me: '{m2.group()}'")
                    m3 = p_sabit_yol.search(line)
                    if m3:
                        hatalar.append(f"{f}:{line_no} -> Sabit sistem yolu: '{m3.group()}'")
        except Exception as err:
            hatalar.append(f"{f} okunamadı: {err}")

    if hatalar:
        print(f"[HATA] Kontrol 1: Gizlilik, Marka, Sosyal Hesap ve Sabit Yol ({len(hatalar)} ihlal)")
        for h in hatalar[:10]:
            print(f"  - {h}")
        if len(hatalar) > 10:
            print(f"  ... ve {len(hatalar) - 10} ihlal daha.")
        return False
    print("[GEÇTİ] Kontrol 1: Gizlilik, Marka, Sosyal Hesap ve Sabit Yol Kontrolü")
    return True


def kontrol_2_kirik_referanslar(files):
    """Kırık Referans Kontrolü."""
    broken_refs = [
        "docs/arastirma/",
        "docs/plan-bolge-safligi",
        "docs/is-akisi-",
        "docs/yontem-gunlugu",
        "docs/katman-ayirma-rehberi",
        "scripts/with_server.py",
    ]

    hatalar = []
    for f in files:
        if f == "tools/denetim.py":
            continue
        if not os.path.isfile(f):
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    for ref in broken_refs:
                        if ref in line:
                            hatalar.append(f"{f}:{line_no} -> Kırık referans: '{ref}'")
        except Exception as err:
            hatalar.append(f"{f} okunamadı: {err}")

    # Markdown'da geçen `tools/...` ve `bilgi/...` yolları gerçekten var mı?
    # CHANGELOG geçmiş kaydıdır (silinmiş dosyaları anar), taranmaz.
    yol_deseni = re.compile(r"`((?:tools|bilgi)/[^`\s*<>{}|]+)`")
    for f in files:
        if not f.endswith(".md") or f.endswith("CHANGELOG.md") or not os.path.isfile(f):
            continue
        with open(f, "r", encoding="utf-8", errors="ignore") as fp:
            for line_no, line in enumerate(fp, 1):
                for yol in yol_deseni.findall(line):
                    yol = yol.split("#")[0].rstrip(".,:;)")
                    if not os.path.exists(yol):
                        hatalar.append(f"{f}:{line_no} -> Var olmayan dosya/klasör: '{yol}'")

    if hatalar:
        print(f"[HATA] Kontrol 2: Kırık Referans Kontrolü ({len(hatalar)} hata)")
        for h in hatalar[:10]:
            print(f"  - {h}")
        if len(hatalar) > 10:
            print(f"  ... ve {len(hatalar) - 10} hata daha.")
        return False
    print("[GEÇTİ] Kontrol 2: Kırık Referans Kontrolü")
    return True


def kontrol_3_utf8_bom_ve_ikili(files):
    """UTF-8 BOM ve İkili (.so/.dll) Kontrolü."""
    hatalar = []
    # 1. git ls-files içinde .so veya .dll uzantılı dosya kontrolü
    for f in files:
        if f.endswith(".so") or f.endswith(".dll"):
            hatalar.append(f"İzlenen ikili kütüphane bulundu: {f}")

    # 2. UTF-8 BOM kontrolü (EF BB BF)
    for f in files:
        if not os.path.isfile(f):
            continue
        try:
            with open(f, "rb") as fp:
                bom = fp.read(3)
                if bom == b"\xef\xbb\xbf":
                    hatalar.append(f"UTF-8 BOM baytı tespit edildi: {f}")
        except Exception as err:
            hatalar.append(f"{f} okunamadı: {err}")

    if hatalar:
        print(f"[HATA] Kontrol 3: UTF-8 BOM ve İkili (.so/.dll) Kontrolü ({len(hatalar)} hata)")
        for h in hatalar:
            print(f"  - {h}")
        return False
    print("[GEÇTİ] Kontrol 3: UTF-8 BOM ve İkili (.so/.dll) Kontrolü")
    return True


def kontrol_4_fihrist_ve_baslik_eslesmesi():
    """Fihrist Satır Aralığı (Lxx-Lyy) ve Başlık Eşleşmesi Kontrolü."""
    target_files = sorted(glob.glob("bilgi/*.md") + glob.glob(".agents/skills/*/SKILL.md"))
    hatalar = []

    for filepath in target_files:
        norm_path = filepath.replace("\\", "/")
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\r\n") for line in f]
        except Exception as e:
            hatalar.append(f"{norm_path} okunamadı: {e}")
            continue

        # Gerçek ## başlıkları topla (Fihrist / İçindekiler başlığı hariç)
        real_headings = []
        for idx, line in enumerate(lines, 1):
            if line.startswith("## ") and "Fihrist" not in line and "İçindekiler" not in line:
                real_headings.append((idx, line))

        # Fihrist satırlarını parse et (Lxx-Lyy)
        fihrist_entries = []
        for idx, line in enumerate(lines, 1):
            if "|" in line and re.search(r"L\d+-L\d+", line):
                m = re.search(r"L(\d+)-L(\d+)", line)
                s_line = int(m.group(1))
                e_line = int(m.group(2))

                # Tablodan başlık adını çıkar
                parts = line.split("|")
                title_col = parts[1].strip() if len(parts) > 1 else ""
                tm = re.search(r"\[([^\]]+)\]", title_col)
                if tm:
                    title_text = tm.group(1).strip()
                else:
                    title_text = title_col.replace("*", "").strip()
                fihrist_entries.append((s_line, e_line, title_text, idx))

        if len(real_headings) != len(fihrist_entries):
            hatalar.append(
                f"{norm_path}: Başlık sayısı ({len(real_headings)}) ile fihrist girdi sayısı ({len(fihrist_entries)}) uyuşmuyor!"
            )
            continue

        for i, ((s_line, e_line, f_title, tbl_line), (r_line, r_text)) in enumerate(
            zip(fihrist_entries, real_headings)
        ):
            # 1. Başlangıç satırı tam eşleşmeli
            if s_line != r_line:
                hatalar.append(
                    f"{norm_path}:{tbl_line} -> Fihrist L{s_line} gösteriyor, gerçek başlık L{r_line}'da ('{r_text}')"
                )

            # 2. Dosyadaki satır gerçekten ## ile başlamalı
            if s_line <= len(lines) and not lines[s_line - 1].startswith("## "):
                hatalar.append(
                    f"{norm_path}:{s_line} -> Satır '## ' ile başlamıyor: '{lines[s_line - 1]}'"
                )

            # 3. e_line s_line'dan büyük olmalı
            if e_line <= s_line:
                hatalar.append(
                    f"{norm_path}:{tbl_line} -> Geçersiz aralık L{s_line}-L{e_line}"
                )

            # 4. Bitiş satırı sonraki başlıktan önce olmalı
            is_last = (i == len(fihrist_entries) - 1)
            next_start = real_headings[i + 1][0] if not is_last else len(lines) + 1
            if not is_last and e_line >= next_start:
                hatalar.append(
                    f"{norm_path}:{tbl_line} -> Bitiş satırı L{e_line}, sonraki başlık L{next_start}'da başlıyor"
                )
            elif is_last and e_line > len(lines):
                hatalar.append(
                    f"{norm_path}:{tbl_line} -> Son bitiş satırı L{e_line} dosya satır sayısını ({len(lines)}) aşıyor"
                )

    if hatalar:
        print(f"[HATA] Kontrol 4: Fihrist Satır Aralığı ve Başlık Eşleşmesi ({len(hatalar)} hata)")
        for h in hatalar[:10]:
            print(f"  - {h}")
        if len(hatalar) > 10:
            print(f"  ... ve {len(hatalar) - 10} hata daha.")
        return False
    print("[GEÇTİ] Kontrol 4: Fihrist Satır Aralığı (Lxx-Lyy) ve Başlık Eşleşmesi Kontrolü")
    return True


def kontrol_5_ajan_hafiza():
    """Ajan Hafıza (MEMORY.md) Boyut ve Alfabetik Sıra Kontrolü."""
    mem_files = sorted(glob.glob(".claude/agent-memory/*/MEMORY.md"))
    hatalar = []

    TR_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz0123456789 -_"
    tr_map = {c: i for i, c in enumerate(TR_ALPHABET)}

    def tr_sort_key(s):
        res = []
        for ch in s:
            if ch == "I":
                c = "ı"
            elif ch == "İ":
                c = "i"
            else:
                c = ch.lower()
            res.append(tr_map.get(c, 999))
        return res

    for mf in mem_files:
        norm_path = mf.replace("\\", "/")
        try:
            with open(mf, "r", encoding="utf-8") as f:
                lines = [l.rstrip("\r\n") for l in f]
        except Exception as e:
            hatalar.append(f"{norm_path} okunamadı: {e}")
            continue

        # 1. Boyut kontrolü (<= 100 satır)
        if len(lines) > 100:
            hatalar.append(f"{norm_path}: Satır sayısı 100 sınırını aşıyor ({len(lines)} satır)!")

        # 2. ### başlıkları alfabetik sıra kontrolü
        h3_list = [l[4:].strip() for l in lines if l.startswith("### ")]
        sorted_h3 = sorted(h3_list, key=tr_sort_key)
        if h3_list != sorted_h3:
            hatalar.append(
                f"{norm_path}: '### ' alt başlıkları alfabetik sırada değil! Mevcut: {h3_list}, Beklenen: {sorted_h3}"
            )

    if hatalar:
        print(f"[HATA] Kontrol 5: Ajan Hafıza (MEMORY.md) Boyut ve Alfabetik Sıra ({len(hatalar)} hata)")
        for h in hatalar:
            print(f"  - {h}")
        return False
    print("[GEÇTİ] Kontrol 5: Ajan Hafıza (MEMORY.md) Boyut ve Alfabetik Sıra Kontrolü")
    return True


def kontrol_6_sozdizimi_derleme():
    """Sözdizimi Derleme Kontrolü (py_compile & node --check)."""
    hatalar = []

    # 1. tools/**/*.py için py_compile
    py_files = sorted(glob.glob("tools/**/*.py", recursive=True))
    for pf in py_files:
        try:
            py_compile.compile(pf, doraise=True)
        except Exception as e:
            hatalar.append(f"Python sözdizimi derleme hatası ({pf}): {e}")

    # 2. tools/psd_worker/*.js için node --check
    js_files = sorted(glob.glob("tools/psd_worker/*.js"))
    for jf in js_files:
        try:
            res = subprocess.run(
                ["node", "--check", jf],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            if res.returncode != 0:
                hatalar.append(f"Node.js sözdizimi derleme hatası ({jf}): {res.stderr.strip()}")
        except Exception as e:
            hatalar.append(f"node --check çalıştırılamadı ({jf}): {e}")

    if hatalar:
        print(f"[HATA] Kontrol 6: Sözdizimi Derleme Kontrolü ({len(hatalar)} hata)")
        for h in hatalar:
            print(f"  - {h}")
        return False
    print("[GEÇTİ] Kontrol 6: Sözdizimi Derleme Kontrolü (py_compile & node --check)")
    return True


def main():
    print("=" * 60)
    print(" Kedihane Otomatik Repo Denetimi (Sarman Kalite Kapısı)")
    print("=" * 60)

    files = get_tracked_files()
    if not files:
        print("[HATA] Taranacak dosya bulunamadı!")
        sys.exit(1)

    sonuclar = [
        kontrol_1_gizlilik_ve_sabit_yol(files),
        kontrol_2_kirik_referanslar(files),
        kontrol_3_utf8_bom_ve_ikili(files),
        kontrol_4_fihrist_ve_baslik_eslesmesi(),
        kontrol_5_ajan_hafiza(),
        kontrol_6_sozdizimi_derleme(),
    ]

    print("=" * 60)
    if all(sonuclar):
        print("SONUÇ: TÜM KONTROLLER BAŞARIYLA GEÇTİ [GEÇTİ]")
        print("=" * 60)
        sys.exit(0)
    else:
        print("SONUÇ: BAZI KONTROLLER BAŞARISIZ OLDU [HATA]")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
