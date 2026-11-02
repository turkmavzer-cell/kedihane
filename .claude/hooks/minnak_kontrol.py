#!/usr/bin/env python3
"""Stop hook: raporlarda `Ders:` satırı var ama Minnak Tekir çağrılmadıysa oturumun bitmesini durdurur.

Girdi (stdin, Claude Code hook JSON'u): transcript_path, stop_hook_active.
Çıktı: engellenecekse stdout'a {"decision": "block", "reason": "..."}; aksi halde hiçbir şey.
Her durumda çıkış kodu 0'dır; okuma hatası oturumu engellemez (CLAUDE.md Bölüm 14).
"""
import json
import re
import sys

DERS = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Ders:(?:\*\*)?[ \t]*(\S.*)$", re.M)
BOS = re.compile(r"^(?:yok|\[|`?\"?yok)", re.I)


def metinler(icerik):
    """Mesaj içeriğinden (str veya parça listesi) düz metinleri çıkarır."""
    if isinstance(icerik, str):
        yield icerik
        return
    for parca in icerik or []:
        if not isinstance(parca, dict):
            continue
        if parca.get("type") == "text":
            yield parca.get("text", "")
        elif parca.get("type") == "tool_result":
            yield from metinler(parca.get("content"))


def minnak_cagrisi(icerik):
    if not isinstance(icerik, list):
        return False
    for parca in icerik:
        if isinstance(parca, dict) and parca.get("type") == "tool_use":
            girdi = parca.get("input") or {}
            if str(girdi.get("subagent_type", "")).lower() == "minnak-tekir":
                return True
    return False


def gercek_kullanici_mesaji(kayit):
    if kayit.get("type") != "user":
        return False
    icerik = (kayit.get("message") or {}).get("content")
    if isinstance(icerik, str):
        return True
    return isinstance(icerik, list) and not any(
        isinstance(p, dict) and p.get("type") == "tool_result" for p in icerik)


def karar(kayitlar):
    """Engelleme gerekiyorsa gerekçeyi, gerekmiyorsa None döndürür."""
    son_kullanici = max((i for i, k in enumerate(kayitlar) if gercek_kullanici_mesaji(k)), default=-1)
    son_ders, son_minnak = -1, -1
    for i, k in enumerate(kayitlar[son_kullanici + 1:], son_kullanici + 1):
        icerik = (k.get("message") or {}).get("content")
        if minnak_cagrisi(icerik):
            son_minnak = i
        for metin in metinler(icerik):
            if any(not BOS.match(m.group(1).strip()) for m in DERS.finditer(metin)):
                son_ders = i
    if son_ders > son_minnak:
        return ("Raporlarda `Ders:` satırı var ama Minnak Tekir çağrılmadı. Dersleri arındırıp "
                "minnak-tekir alt ajanına ver, fişi Sarman'a denetlet (CLAUDE.md Bölüm 14).")
    return None


def main():
    try:
        girdi = json.load(sys.stdin)
        if girdi.get("stop_hook_active"):
            return
        kayitlar = []
        with open(girdi["transcript_path"], encoding="utf-8") as fp:
            for satir in fp:
                satir = satir.strip()
                if satir:
                    try:
                        kayitlar.append(json.loads(satir))
                    except ValueError:
                        continue
        gerekce = karar(kayitlar)
        if gerekce:
            print(json.dumps({"decision": "block", "reason": gerekce}, ensure_ascii=False))
    except Exception as hata:  # oturumu asla kilitleme
        print(f"[minnak_kontrol] atlandı: {hata}", file=sys.stderr)


if __name__ == "__main__":
    main()
