#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 EIFFeL (CCS 2022) DOI 并合并进文献库。"""
import json, ssl, urllib.request, urllib.parse

def crossref_get(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "FedRBC-refcheck/1.0 (mailto:tangsong@tju.edu.cn)"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode())

DOI = "10.1145/3548606.3560611"
try:
    d = crossref_get(DOI)["message"]
    title = d.get("title", [""])[0]
    authors = ["%s %s" % (a.get("given", ""), a.get("family", "")) for a in d.get("author", [])]
    year = d.get("issued", {}).get("date-parts", [[None]])[0][0]
    venue = (d.get("container-title") or [""])[0]
    print("✅ 验证通过")
    print("  title :", title)
    print("  venue :", venue)
    print("  year  :", year)
    print("  author:", "; ".join(authors[:4]), "et al." if len(authors) > 4 else "")
    # 合并进 references_verified.json
    db = json.load(open("paper/references_verified.json", encoding="utf-8"))
    if not any(e.get("doi", "").lower() == DOI for e in db["entries"]):
        db["entries"].append(dict(
            id="B5", title=title, authors=authors, year=year, venue=venue,
            doi=DOI, type="conference", verified="crossref",
            venue_type="top", note="EIFFeL: Ensuring Integrity for Federated Learning, CCS 2022 (基线3, 5年内)"))
        # 重算指标
        n = len(db["entries"])
        db["n_recent_2024plus"] = sum(1 for e in db["entries"] if int(e.get("year") or 0) >= 2024)
        db["n_top_tier"] = sum(1 for e in db["entries"] if e.get("venue_type") == "top")
        json.dump(db, open("paper/references_verified.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("已合并入库：B5。当前总数 %d，2024+ %d，top %d" % (n, db["n_recent_2024plus"], db["n_top_tier"]))
    else:
        print("DOI 已在库中")
except Exception as e:
    print("❌ 验证失败:", e)
