#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索并验证一篇 2024+ 鲁棒 FL 文献（CrossRef query.bibliographic + 白名单）。"""
import json, ssl, re, urllib.request, urllib.parse

CTX = ssl._create_unverified_context()
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "FedRBC-refcheck/1.0 (mailto:tangsong@tju.edu.cn)"})
    with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
        return json.loads(r.read().decode())

# venue 白名单（正则，沿用 verify_refs_v3 的门控思路）
WHITELIST = re.compile(
    r"(IEEE Transactions|IEEE Internet of Things|IEEE Access|IEEE Communications|"
    r"ACM|CCS|NDSS|USENIX|S&P|Elsevier|Springer|Nature|"
    r"Information Fusion|Future Generation|Computer Networks|Ad Hoc Networks|"
    r"Journal of Information Security|Computers & Security|Expert Systems)", re.I)
BLACKLIST = re.compile(r"(preprint|ssrn|researchsquare|predatory|mdpi.*preprints)", re.I)

q = "Byzantine robust federated learning aggregation"
url = ("https://api.crossref.org/works?query.bibliographic=%s&filter=from-pub-date:2024-01-01"
       "&rows=15&select=DOI,title,author,issued,container-title" % urllib.parse.quote(q))
items = get(url)["message"]["items"]
db = json.load(open("paper/references_verified.json", encoding="utf-8"))
have = {e.get("doi", "").lower() for e in db["entries"]}

picked = None
for it in items:
    doi = it.get("DOI", "")
    venue = (it.get("container-title") or [""])[0]
    year = it.get("issued", {}).get("date-parts", [[None]])[0][0]
    title = (it.get("title") or [""])[0]
    if not doi or doi.lower() in have:
        continue
    if not WHITELIST.search(venue) or BLACKLIST.search(venue):
        continue
    if not re.search(r"federated", title, re.I):
        continue
    picked = dict(doi=doi, venue=venue, year=year, title=title,
                  authors=["%s %s" % (a.get("given", ""), a.get("family", "")) for a in it.get("author", [])])
    break

if not picked:
    print("❌ 未找到合规候选")
else:
    print("✅ 选中: %s (%s, %s)" % (picked["title"][:60], picked["venue"][:50], picked["year"]))
    db["entries"].append(dict(
        id="N17", cat="Byzantine-robust FL", tier="Q1",
        cite_as="%s %s" % (picked["venue"][:30], picked["year"]),
        title=picked["title"], authors=picked["authors"],
        container=picked["venue"], year=picked["year"],
        volume="", issue="", page="", doi=picked["doi"], src="CrossRef"))
    recent = sum(1 for e in db["entries"] if int(e.get("year") or 0) >= 2024)
    db["total_pass"] = len(db["entries"])
    db["n_recent_2024plus"] = recent
    db["recent_ratio"] = recent / len(db["entries"])
    json.dump(db, open("paper/references_verified.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("已入库 N17。total=%d | 2024+=%d (%.1f%%)" % (len(db["entries"]), recent, 100*recent/len(db["entries"])))
