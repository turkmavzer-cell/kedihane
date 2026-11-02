#!/usr/bin/env python3
"""Kedihane Repo Denetim Aracı (Sarman Otomatik Kalite Kapısı)

Bu betik git reposundaki izlenen dosyaları 10 kontrolden geçirir:
1. Gizlilik, Marka, Sosyal Hesap ve Sabit Yol Kontrolü
2. Kırık Referans Kontrolü
3. UTF-8 BOM ve İkili (.so/.dll) Kontrolü
4. Fihrist Satır Aralığı (Lxx-Lyy) ve Başlık Eşleşmesi Kontrolü
5. Ajan Hafıza (MEMORY.md) Boyut ve Alfabetik Sıra Kontrolü
6. Sözdizimi Derleme Kontrolü (py_compile & node --check)
7. Tekrar ve Sayısal Standart Kontrolü (bilgi/HARITA.md "Sayısal Standartlar")
8. Bilgi Haritası Kontrolü (bilgi/HARITA.md "Konu Haritası")
9. Ekip Tutarlılığı (CLAUDE.md §2 ↔ .claude/agents ↔ GEMINI.md §3; Minnak Tekir hafızasız)
10. Yetki Sınırı Uyarısı (commit'e giren CLAUDE.md, GEMINI.md, AGENTS.md, ajan dosyası; engellemez)

Kullanım:
    python tools/denetim.py                  # tüm kontroller
    python tools/denetim.py --fihrist-duzelt # fihrist Lxx-Lyy aralıklarını yeniden yazar, sonra denetler
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
    target_files = sorted(f for f in glob.glob("bilgi/*.md") + glob.glob(".agents/skills/*/SKILL.md")
                          if f.replace("\\", "/") != "bilgi/HARITA.md")
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
            # 0. Fihrist satırı ile başlık aynı bölüm etiketini taşımalı (sıra kontrolü)
            if _etiket(f_title) != _etiket(r_text[3:]):
                hatalar.append(
                    f"{norm_path}:{tbl_line} -> Fihrist '{f_title[:40]}' ile sıradaki başlık '{r_text[:40]}' uyuşmuyor (sıra hatası)"
                )

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

        # 2. ### altındaki her ders tarihli tek satır olmalı: "- YYYY-AA-GG: ders"
        alt = False
        for i, l in enumerate(lines, 1):
            if l.startswith("### "):
                alt = True
            elif l.startswith("## ") or l.startswith("# "):
                alt = False
            elif alt and l.startswith("- ") and not re.match(r"- \d{4}-\d{2}-\d{2}: \S", l):
                hatalar.append(f"{norm_path}:{i}: Ders satırı '- YYYY-AA-GG: ders' biçiminde değil")

        # 3. ### başlıkları alfabetik sıra kontrolü
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


# ---------------------------------------------------------------------------
# Bilgi Haritası, tekrar ve fihrist yardımcıları
# ---------------------------------------------------------------------------
HARITA = "bilgi/HARITA.md"
ISTISNA = "tools/denetim_istisna.txt"


def _rehber_dosyalari():
    yollar = glob.glob("bilgi/*.md") + glob.glob(".agents/skills/*/SKILL.md")
    return sorted(y.replace("\\", "/") for y in yollar if y.replace("\\", "/") != HARITA)


def _bilgi_dosyalari():
    """Tekrar kontrolünün kapsadığı bilgi dosyaları (CHANGELOG ve HARITA hariç)."""
    adaylar = _rehber_dosyalari() + glob.glob(".claude/agents/*.md") + glob.glob(".claude/agent-memory/*/MEMORY.md")
    adaylar += ["CLAUDE.md", "GEMINI.md", "AGENTS.md", ".agents/learnings/PROJECT.md"]
    return sorted(set(f.replace("\\", "/") for f in adaylar if os.path.isfile(f) and f.replace("\\", "/") != HARITA))


def _oku(yol):
    with open(yol, "r", encoding="utf-8") as fp:
        return [l.rstrip("\r\n") for l in fp]


def _tablo(lines, baslik):
    """`## <baslik>` altındaki ilk markdown tablosunu satır listesi (hücre listesi) olarak döndürür."""
    satirlar, icinde, tablo_basladi = [], False, False
    for l in lines:
        if l.startswith("## "):
            if icinde:
                break
            icinde = baslik.lower() in l.lower()
            continue
        if not icinde:
            continue
        if l.strip().startswith("|"):
            tablo_basladi = True
            hucre = [h.strip().replace("\\|", "|") for h in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
            if all(re.fullmatch(r":?-{3,}:?", h) for h in hucre if h):
                continue
            satirlar.append(hucre)
        elif tablo_basladi:
            break
    return satirlar[1:] if satirlar else []  # başlık satırı atlanır


def _harita():
    if not os.path.isfile(HARITA):
        return None, None
    lines = _oku(HARITA)
    return _tablo(lines, "Konu Haritası"), _tablo(lines, "Sayısal Standartlar")


def _normalize(l):
    l = re.sub(r"^\s*(?:[-*>]|\d+\.)\s*", "", l.strip())
    l = re.sub(r"[*_`#|]", "", l)
    return re.sub(r"\s+", " ", l).strip().lower().replace("i\u0307", "i")


def _istisnalar():
    if not os.path.isfile(ISTISNA):
        return []
    return [re.compile(s.strip(), re.I) for s in _oku(ISTISNA) if s.strip() and not s.startswith("#")]


def _etiket(metin):
    """Başlık veya fihrist hücresindeki bölüm etiketi ("A", "Ç", "10")."""
    m = re.match(r"[\s*\[`]*(?:#+\s*)?([A-ZÇĞİÖŞÜ]|\d+)\.", metin)
    return m.group(1) if m else None


def _fihrist_basligi(satir):
    parts = satir.split("|")
    return parts[1].strip() if len(parts) > 1 else ""


def fihrist_duzelt():
    """Rehber ve skill fihristlerindeki Lxx-Lyy aralıklarını gerçek `## ` başlıklarına göre yeniden yazar."""
    degisen = []
    for yol in _rehber_dosyalari():
        lines = _oku(yol)
        basliklar = [i for i, l in enumerate(lines, 1)
                     if l.startswith("## ") and "Fihrist" not in l and "İçindekiler" not in l]
        satirlar = [i for i, l in enumerate(lines) if "|" in l and re.search(r"L\d+-L\d+", l)]
        if len(basliklar) != len(satirlar):
            print(f"[UYARI] {yol}: başlık ({len(basliklar)}) ve fihrist ({len(satirlar)}) sayısı farklı; elle düzeltin.")
            continue
        uyusmayan = [(lines[b - 1], _fihrist_basligi(lines[t])) for b, t in zip(basliklar, satirlar)
                     if _etiket(lines[b - 1][3:]) != _etiket(_fihrist_basligi(lines[t]))]
        if uyusmayan:
            print(f"[UYARI] {yol}: fihrist sırası başlık sırasıyla uyuşmuyor (ör. '{uyusmayan[0][1][:40]}' ↔ "
                  f"'{uyusmayan[0][0][:40]}'); fihrist satırlarını başlık sırasına dizin, dosyaya dokunulmadı.")
            continue
        yeni = list(lines)
        for k, (bas, ti) in enumerate(zip(basliklar, satirlar)):
            son_sinir = basliklar[k + 1] - 1 if k + 1 < len(basliklar) else len(lines)
            bit = son_sinir
            while bit > bas and lines[bit - 1].strip() in ("", "---"):
                bit -= 1
            yeni[ti] = re.sub(r"L\d+-L\d+", f"L{bas}-L{bit}", lines[ti], count=1)
        if yeni != lines:
            with open(yol, "w", encoding="utf-8", newline="\n") as fp:
                fp.write("\n".join(yeni) + "\n")
            degisen.append(yol)
    print(f"[FİHRİST] {len(degisen)} dosyada aralık güncellendi" + (": " + ", ".join(degisen) if degisen else ""))


def kontrol_7_tekrar_ve_standart():
    """Aynı uzun satırın iki dosyada geçmesi ve sayısal standartların asıl yer dışında farklı değerle yazılması."""
    hatalar, uyarilar = [], []
    istisna = _istisnalar()
    dosyalar = _bilgi_dosyalari()
    gorulen = {}
    for yol in dosyalar:
        kod = False
        for i, l in enumerate(_oku(yol), 1):
            if l.strip().startswith("```"):
                kod = not kod
                continue
            if kod:
                continue
            n = _normalize(l)
            if len(n) < 60 or any(r.search(n) for r in istisna):
                continue
            gorulen.setdefault(n, []).append(f"{yol}:{i}")
    for n, yerler in gorulen.items():
        if len({y.rsplit(":", 1)[0] for y in yerler}) > 1:
            hatalar.append(f"Tekrar: {', '.join(yerler)} -> '{n[:70]}...' (tek yerde tut, ötekine atıf koy)")

    _, standartlar = _harita()
    birimler = {
        "çözünürlük": (r"(\d{3,4})\s*[x×]\s*(\d{3,4})", lambda m: f"{m.group(1)}x{m.group(2)}"),
        "lufs": (r"([−-]?\d+(?:[.,]\d+)?)\s*LUFS", lambda m: m.group(1).replace("−", "-").replace(",", ".")),
        "lpi": (r"(\d+(?:[.,]\d+)?)\s*LPI", lambda m: m.group(1).replace(",", ".")),
        "ppi": (r"(\d+(?:[.,]\d+)?)\s*PPI", lambda m: m.group(1).replace(",", ".")),
        "fps": (r"(\d+(?:[.,]\d+)?)\s*fps\b", lambda m: m.group(1).replace(",", ".")),
        "mbps": (r"(\d+(?:[.,]\d+)?)\s*Mbps\b", lambda m: m.group(1).replace(",", ".")),
    }
    for satir in standartlar or []:
        if len(satir) < 5:
            continue
        ad, birim, deger, baglam, asil = (h.strip("` ") for h in satir[:5])
        if birim.lower() not in birimler:
            hatalar.append(f"HARITA: '{ad}' için bilinmeyen birim '{birim}'")
            continue
        desen, cevir = birimler[birim.lower()]
        try:
            baglam_re = re.compile(baglam, re.I)
        except re.error as e:
            hatalar.append(f"HARITA: '{ad}' bağlam deseni geçersiz: {e}")
            continue
        for yol in dosyalar:
            if yol == asil:
                continue
            for i, l in enumerate(_oku(yol), 1):
                if not baglam_re.search(l):
                    continue
                for m in re.finditer(desen, l, re.I):
                    v = cevir(m)
                    if v != deger:
                        hatalar.append(f"Standart '{ad}': {yol}:{i} '{v}' yazıyor, asıl değer '{deger}' ({asil})")
    for u in uyarilar:
        print(f"  [UYARI] {u}")
    if hatalar:
        print(f"[HATA] Kontrol 7: Tekrar ve Sayısal Standart ({len(hatalar)} hata)")
        for h in hatalar[:15]:
            print(f"  - {h}")
        if len(hatalar) > 15:
            print(f"  ... ve {len(hatalar) - 15} hata daha.")
        return False
    print("[GEÇTİ] Kontrol 7: Tekrar ve Sayısal Standart Kontrolü")
    return True


def kontrol_8_harita():
    """bilgi/HARITA.md: her satırın dosyası ve başlığı var mı, her rehber haritada mı; anahtar sözcük başka başlıkta mı (uyarı)."""
    konular, _ = _harita()
    if konular is None:
        print(f"[HATA] Kontrol 8: {HARITA} bulunamadı")
        return False
    hatalar, uyarilar, haritadaki = [], [], set()
    istisna = _istisnalar()
    basliklar = {}
    for yol in _bilgi_dosyalari():
        basliklar[yol] = [(i, l) for i, l in enumerate(_oku(yol), 1) if re.match(r"#{2,3} ", l)]
    for satir in konular:
        if len(satir) < 5:
            hatalar.append(f"HARITA satırı eksik sütunlu: {satir}")
            continue
        konu, sozcukler, asil, bolum = satir[0], satir[1], satir[2].strip("` "), satir[3]
        haritadaki.add(asil)
        if not os.path.isfile(asil):
            hatalar.append(f"'{konu}': asıl dosya yok: {asil}")
            continue
        heads = [l for _, l in basliklar.get(asil, [])] or [l for l in _oku(asil) if l.startswith("## ")]
        for b in re.findall(r"§?([A-ZÇĞİÖŞÜ]|\d+)(?=[\s,.;]|$)", bolum):
            if not any(re.match(rf"## {re.escape(b)}\.", h) for h in heads):
                hatalar.append(f"'{konu}': {asil} içinde '## {b}.' başlığı yok")
        for s in [x.strip().lower() for x in sozcukler.split(",") if x.strip()]:
            s_re = re.compile(rf"(?<!\w){re.escape(s)}(?!\w)", re.I)
            for yol, hs in basliklar.items():
                if yol == asil or yol.endswith("/MEMORY.md"):
                    continue
                for i, h in hs:
                    if s_re.search(h) and not any(r.search(f"{yol}: {h}") for r in istisna):
                        uyarilar.append(f"'{s}' ({konu}) asıl yer dışında başlıkta: {yol}:{i} -> asıl {asil}")
    for yol in _rehber_dosyalari():
        if yol.replace("\\", "/") not in haritadaki and yol != HARITA:
            hatalar.append(f"{yol} haritada yok; bilgi/HARITA.md'ye satır ekleyin")
    for u in uyarilar[:15]:
        print(f"  [UYARI] {u}")
    if len(uyarilar) > 15:
        print(f"  [UYARI] ... ve {len(uyarilar) - 15} uyarı daha.")
    if hatalar:
        print(f"[HATA] Kontrol 8: Bilgi Haritası ({len(hatalar)} hata)")
        for h in hatalar[:15]:
            print(f"  - {h}")
        return False
    print(f"[GEÇTİ] Kontrol 8: Bilgi Haritası Kontrolü ({len(konular)} konu, {len(uyarilar)} uyarı)")
    return True


def _ilk_sutun(lines, baslik_deseni):
    """`## ` başlığı desene uyan bölümdeki ilk tablonun ilk sütunu (küçük harf, işaretsiz)."""
    sonuc, icinde = [], False
    for l in lines:
        if l.startswith("## "):
            icinde = bool(re.search(baslik_deseni, l))
            continue
        if icinde and l.strip().startswith("|"):
            h = re.sub(r"[*`]", "", l.strip().strip("|").split("|")[0]).strip().lower()
            if h and not re.fullmatch(r":?-{3,}:?", h) and h not in ("kod adı",):
                sonuc.append(h)
    return sonuc


def kontrol_9_ekip_tutarliligi():
    """CLAUDE.md §2, .claude/agents/*.md ve GEMINI.md §3 aynı ekibi gösteriyor mu; Minnak Tekir hafızasız mı;
    HARITA "Sahip" sütunundaki ajanın dosyası asıl rehberi anıyor mu (uyarı)."""
    hatalar, uyarilar = [], []
    dosyalar = {os.path.basename(f)[:-3] for f in glob.glob(".claude/agents/*.md")}
    claude = set(_ilk_sutun(_oku("CLAUDE.md"), r"^## 2\. ")) if os.path.isfile("CLAUDE.md") else set()
    gemini = set(_ilk_sutun(_oku("GEMINI.md"), r"^## 3\. ")) if os.path.isfile("GEMINI.md") else set()
    for ad in sorted(dosyalar - claude):
        hatalar.append(f".claude/agents/{ad}.md CLAUDE.md §2 tablosunda yok")
    for ad in sorted(claude - dosyalar):
        hatalar.append(f"CLAUDE.md §2'deki '{ad}' için .claude/agents/{ad}.md yok")
    for ad in sorted(dosyalar - gemini):
        hatalar.append(f".claude/agents/{ad}.md GEMINI.md §3 tablosunda yok")
    minnak = ".claude/agents/minnak-tekir.md"
    if os.path.isfile(minnak):
        on = "\n".join(_oku(minnak)[:8])
        if re.search(r"^memory:", on, re.M):
            hatalar.append(f"{minnak}: Minnak Tekir hafızasızdır; 'memory:' satırı olmamalı")
    if os.path.isdir(".claude/agent-memory/minnak-tekir"):
        hatalar.append(".claude/agent-memory/minnak-tekir/ olmamalı (Minnak Tekir hafızasız)")

    konular, _ = _harita()
    for satir in konular or []:
        if len(satir) < 5:
            continue
        asil = satir[2].strip("` ")
        if not (asil.startswith("bilgi/") or asil.startswith(".agents/skills/")) or asil == HARITA:
            continue
        anilan = asil if asil.startswith("bilgi/") else os.path.dirname(asil)
        for sahip in [x.strip().lower() for x in satir[4].split(",")]:
            yol = f".claude/agents/{sahip}.md"
            if os.path.isfile(yol) and anilan not in "\n".join(_oku(yol)):
                uyarilar.append(f"{yol} HARITA'da sahibi olduğu '{anilan}' dosyasını anmıyor")
    for u in sorted(set(uyarilar))[:15]:
        print(f"  [UYARI] {u}")
    if hatalar:
        print(f"[HATA] Kontrol 9: Ekip Tutarlılığı ({len(hatalar)} hata)")
        for h in hatalar:
            print(f"  - {h}")
        return False
    print(f"[GEÇTİ] Kontrol 9: Ekip Tutarlılığı ({len(dosyalar)} ajan, {len(set(uyarilar))} uyarı)")
    return True


def kontrol_10_yetki_uyarisi():
    """Commit'e giren kural/ajan dosyaları için uyarı (engellemez): bunları Minnak Tekir değil Tekir, Cihan onayıyla değiştirir."""
    try:
        cikti = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True).stdout
    except Exception:
        cikti = ""
    kural = [f for f in cikti.split() if f in ("CLAUDE.md", "GEMINI.md", "AGENTS.md") or f.startswith(".claude/agents/")]
    for f in kural:
        print(f"  [UYARI] Kontrol 10: {f} commit'e giriyor; Cihan onayı ve Sarman denetimi gerekir (Minnak yazamaz).")
    print(f"[GEÇTİ] Kontrol 10: Yetki Sınırı Uyarısı ({len(kural)} uyarı)")
    return True


def main():
    print("=" * 60)
    print(" Kedihane Otomatik Repo Denetimi (Sarman Kalite Kapısı)")
    print("=" * 60)

    if "--fihrist-duzelt" in sys.argv:
        fihrist_duzelt()

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
        kontrol_7_tekrar_ve_standart(),
        kontrol_8_harita(),
        kontrol_9_ekip_tutarliligi(),
        kontrol_10_yetki_uyarisi(),
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
