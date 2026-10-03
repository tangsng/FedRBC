#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC 参考文献真实性验证 v2
数据源策略：
  - 期刊/会议（有 CrossRef DOI） -> CrossRef 直查复核
  - 顶会论文（PMLR/NeurIPS 无 CrossRef DOI）-> DataCite（arXiv DOI 10.48550/arXiv.XXXX）验证
  - 近年补充（2024-2026）-> CrossRef 检索（from-pub-date 过滤）+ 题名相关性筛选 + 逐条复核
输出：results/refs_validation.md + paper/references_verified.json
"""
import json, time, ssl, urllib.request, urllib.parse, urllib.error

CROSSREF = "https://api.crossref.org/works/"
DATACITE = "https://api.datacite.org/dois/"
UA = {"User-Agent": "FedRBC-RefVerifier/2.0 (mailto:research@example.org)"}
_CTX = ssl._create_unverified_context()

def http_json(url, retries=4, timeout=40):
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2.0 * (k + 1))
        except Exception:
            time.sleep(2.0 * (k + 1))
    return None

def norm(s):
    return "".join(c.lower() for c in (s or "") if c.isalnum())

# ---------------- 种子池：crossref=DOI 直查；arxiv=DataCite；query=CrossRef 题名查 ----------------
SEEDS = [
 # --- A. FL 基础 ---
 dict(id="A1", cat="FL foundations", tier="top", mode="arxiv", arxiv="1602.05629",
      title="Communication-Efficient Learning of Deep Networks from Decentralized Data",
      expect="McMahan", year=2017, cite_as="AISTATS 2017 (PMLR 54)"),
 dict(id="A2", cat="FL foundations", tier="top", mode="crossref", doi="10.1561/2200000083",
      title="Advances and Open Problems in Federated Learning", expect="Kairouz", year=2021),
 dict(id="A3", cat="FL foundations", tier="top", mode="arxiv", arxiv="1812.06127",
      title="Federated Optimization in Heterogeneous Networks", expect="Li", year=2020,
      cite_as="MLSys 2020"),
 dict(id="A5", cat="FL foundations", tier="top", mode="arxiv", arxiv="2003.00295",
      title="Adaptive Federated Optimization", expect="Reddi", year=2021, cite_as="ICLR 2021"),
 # --- B. 鲁棒/Byzantine ---
 dict(id="B1", cat="Byzantine-robust FL", tier="top", mode="arxiv", arxiv="1703.02757",
      title="Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent",
      expect="Blanchard", year=2017, cite_as="NeurIPS 2017"),
 dict(id="B2", cat="Byzantine-robust FL", tier="top", mode="arxiv", arxiv="1803.01498",
      title="Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates",
      expect="Yin", year=2018, cite_as="ICML 2018"),
 dict(id="B3", cat="Byzantine-robust FL", tier="top", mode="crossref", doi="10.14722/ndss.2021.24494",
      title="FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping", expect="Cao", year=2021),
 dict(id="B4", cat="Byzantine-robust FL", tier="top", mode="arxiv", arxiv="1807.00459",
      title="How To Backdoor Federated Learning", expect="Bagdasaryan", year=2020, cite_as="AISTATS 2020"),
 dict(id="B6", cat="Byzantine-robust FL", tier="top", mode="arxiv", arxiv="1902.06156",
      title="A Little Is Enough: Circumventing Defenses for Distributed Learning",
      expect="Baruch", year=2019, cite_as="NeurIPS 2019"),
 # --- C. 区块链+FL ---
 dict(id="C1", cat="blockchain FL", tier="top", mode="crossref", doi="10.1109/TDSC.2019.2952332",
      title="DeepChain: Auditable and Privacy-Preserving Deep Learning with Blockchain-based Incentive",
      expect="Weng", year=2021, year_tol=2),
 dict(id="C2", cat="blockchain FL", tier="top", mode="crossref", doi="10.1109/TII.2019.2942190",
      title="Blockchain and Federated Learning for Privacy-Preserved Data Sharing in Industrial IoT",
      expect="Lu", year=2020, year_tol=2),
 dict(id="C3", cat="blockchain FL", tier="top", mode="crossref", doi="10.1109/TCOMM.2020.2990686",
      title="Federated Learning With Blockchain for Autonomous Vehicles: Analysis and Design Challenges",
      expect="Pokhrel", year=2020),
 dict(id="C4", cat="blockchain FL", tier="", mode="crossref", doi="10.1109/MNET.011.2000263",
      title="A Blockchain-based Decentralized Federated Learning Framework with Committee Consensus",
      expect="Li", year=2021, year_tol=2),
 dict(id="C5", cat="blockchain FL", tier="", mode="crossref", doi="10.1109/LCOMM.2019.2921755",
      title="Blockchained On-Device Federated Learning", expect="Kim", year=2020, year_tol=2),
 # --- D. DP ---
 dict(id="D1", cat="privacy DP", tier="top", mode="crossref", doi="10.1109/CSF.2017.11",
      title="R\u00e9nyi Differential Privacy", expect="Mironov", year=2017),
 dict(id="D2", cat="privacy DP", tier="top", mode="crossref", doi="10.1109/TIFS.2020.2988575",
      title="Federated Learning With Differential Privacy: Algorithms and Performance Analysis",
      expect="Wei", year=2020),
 # --- E. 医疗 FL ---
 dict(id="E1", cat="FL healthcare", tier="top", mode="crossref", doi="10.1038/s41746-020-00323-1",
      title="The future of digital health with federated learning", expect="Rieke", year=2020),
 dict(id="E2", cat="FL healthcare", tier="top", mode="crossref", doi="10.1038/s42256-020-0186-1",
      title="Secure, privacy-preserving and federated machine learning in medical imaging",
      expect="Kaissis", year=2020),
 # --- F. IDS 数据集 ---
 dict(id="F1", cat="IDS dataset", tier="", mode="crossref", doi="10.1109/ACCESS.2020.3000421",
      title="Intrusion Detection System for Healthcare Systems Using Medical and Network Data: A Comparison Study",
      expect="Hady", year=2020),
 dict(id="F2", cat="IDS dataset", tier="", mode="query",
      title="ToN_IoT Telemetry Dataset: A New Generation Dataset of IoT and IIoT for Data-Driven Intrusion Detection Systems",
      expect="Alsaedi", year=2021),
 dict(id="F4", cat="IDS dataset", tier="", mode="crossref", doi="10.3390/s23135941",
      title="CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment",
      expect="Neto", year=2023),
 # --- G. SDN/IoT ---
 dict(id="G1", cat="SDN IoT security", tier="top", mode="crossref", doi="10.1109/JIOT.2020.2977196",
      title="Blockchain-Enabled Distributed Security Framework for Next-Generation IoT: An Edge Cloud and Software-Defined Network-Integrated Approach",
      expect="Medhane", year=2020),
 dict(id="G2", cat="SDN IoT security", tier="", mode="crossref", doi="10.32604/cmc.2026.085763",
      title="A Secure Blockchain-Enabled SDN-Based Edge Computing Framework for IoT Healthcare Systems",
      expect="Tyagi", year=2026),
 dict(id="G3", cat="SDN IoT security", tier="", mode="crossref", doi="10.1145/2620728.2620744",
      title="ONOS: Towards an Open, Distributed SDN OS", expect="Berde", year=2014),
 # --- H. 收敛理论 ---
 dict(id="H1", cat="FL convergence", tier="top", mode="arxiv", arxiv="1907.02189",
      title="On the Convergence of FedAvg on Non-IID Data", expect="Li", year=2020, cite_as="ICLR 2020"),
]

# 近年补充检索（CrossRef, 2024-01-01 起）
RECENT_QUERIES = [
    ("blockchain federated learning", 10),
    ("federated learning intrusion detection IoT", 8),
    ("reputation federated learning trust", 6),
    ("federated learning healthcare medical privacy", 6),
    ("Byzantine robust federated aggregation poisoning", 6),
]
RECENT_TARGET = 22  # 使 2024+ 占比 >= 50%

def crossref_doi(doi):
    j = http_json(CROSSREF + urllib.parse.quote(doi))
    if not j or j.get("status") != "ok":
        return None
    m = j["message"]
    return dict(title=(m.get("title") or [""])[0],
                authors=["{} {}".format(a.get("given", ""), a.get("family", "")).strip()
                         for a in m.get("author", [])],
                container=(m.get("container-title") or [""])[0],
                year=(m.get("issued", {}).get("date-parts", [[None]])[0][0]),
                volume=m.get("volume", ""), issue=m.get("issue", ""),
                page=m.get("page", ""), doi=m.get("DOI", doi), src="CrossRef")

def crossref_query(title, rows=3):
    q = CROSSREF + "?query.bibliography=" + urllib.parse.quote(title) + "&rows=%d" % rows
    j = http_json(q)
    if not j or j.get("status") != "ok":
        return None
    items = j["message"].get("items", [])
    if not items:
        return None
    m = items[0]
    return dict(title=(m.get("title") or [""])[0],
                authors=["{} {}".format(a.get("given", ""), a.get("family", "")).strip()
                         for a in m.get("author", [])],
                container=(m.get("container-title") or [""])[0],
                year=(m.get("issued", {}).get("date-parts", [[None]])[0][0]),
                volume=m.get("volume", ""), issue=m.get("issue", ""),
                page=m.get("page", ""), doi=m.get("DOI", ""), src="CrossRef(query)")

def datacite_arxiv(arxiv_id):
    j = http_json(DATACITE + "10.48550/arxiv." + arxiv_id)
    if not j or "data" not in j:
        return None
    a = j["data"]["attributes"]
    title = (a.get("titles") or [{}])[0].get("title", "")
    creators = [c.get("name", "") for c in a.get("creators", [])]
    return dict(title=title, authors=creators,
                container="arXiv:%s" % arxiv_id,
                year=a.get("publicationYear"),
                volume="", issue="", page="",
                doi="10.48550/arXiv.%s" % arxiv_id, src="DataCite(arXiv)")

def check(seed, rec):
    if rec is None:
        return "FAIL", "API 无返回"
    notes, ok = [], True
    if not (norm(seed["title"])[:40] in norm(rec["title"]) or norm(rec["title"])[:40] in norm(seed["title"])):
        ok = False; notes.append("题名不匹配: '%s'" % rec["title"][:60])
    if not any(seed["expect"].lower() in a.lower() for a in rec["authors"]):
        ok = False; notes.append("作者 %s 未见" % seed["expect"])
    tol = seed.get("year_tol", 1)
    if rec["year"] and abs((rec["year"] or 0) - seed["year"]) > tol:
        ok = False; notes.append("年份: 期望~%d 实际 %s" % (seed["year"], rec["year"]))
    return ("PASS" if ok else "FAIL"), "; ".join(notes) or "一致(%s)" % rec["src"]

def main():
    results, passed = [], []
    print("== 阶段1: 种子池验证 (%d 条) ==" % len(SEEDS))
    for s in SEEDS:
        time.sleep(1.2)
        if s["mode"] == "crossref":
            rec = crossref_doi(s["doi"])
        elif s["mode"] == "arxiv":
            rec = datacite_arxiv(s["arxiv"])
        else:
            rec = crossref_query(s["title"])
        status, notes = check(s, rec)
        results.append(dict(seed=s, rec=rec, status=status, notes=notes))
        print("%s [%s] %s | %s" % ("✅" if status == "PASS" else "❌", s["id"],
                                   s["title"][:55], notes[:85]))
        if status == "PASS":
            passed.append(dict(seed=s, rec=rec))

    print("\n== 阶段2: 近年补充检索 (CrossRef 2024-2026) ==")
    recent, seen = [], set(norm(r["rec"]["title"]) for r in results if r["rec"])
    for q, rows in RECENT_QUERIES:
        if len(recent) >= RECENT_TARGET:
            break
        time.sleep(1.5)
        url = (CROSSREF + "?query=" + urllib.parse.quote(q) +
               "&filter=from-pub-date:2024-01-01,until-pub-date:2026-12-31,type:journal-article"
               "&rows=%d&select=DOI,title,author,container-title,issued,volume,issue,page" % (rows * 2))
        j = http_json(url)
        if not j or j.get("status") != "ok":
            print("⚠️ 查询失败: %s" % q); continue
        cnt = 0
        for m in j["message"].get("items", []):
            if cnt >= rows or len(recent) >= RECENT_TARGET:
                break
            title = (m.get("title") or [""])[0]
            cont = (m.get("container-title") or [""])[0]
            doi = m.get("DOI", "")
            year = m.get("issued", {}).get("date-parts", [[None]])[0][0]
            # 相关性过滤：题名须含 federated
            if not title or "federated" not in title.lower():
                continue
            if not cont or not doi or norm(title) in seen:
                continue
            seen.add(norm(title))
            recent.append(dict(
                title=title, year=year, container=cont, doi=doi,
                authors=["{} {}".format(a.get("given", ""), a.get("family", "")).strip()
                         for a in m.get("author", [])][:6],
                volume=m.get("volume", ""), issue=m.get("issue", ""),
                page=m.get("page", ""), query=q))
            cnt += 1
        print("  [%s] +%d" % (q, cnt))

    # 阶段3: 逐条复核（重新 DOI 直查确认元数据一致）
    print("\n== 阶段3: 近年候选 DOI 复核 ==")
    recent_ok = []
    for r in recent:
        time.sleep(1.2)
        rec = crossref_doi(r["doi"])
        ok = rec and (norm(r["title"])[:35] in norm(rec["title"]) or
                      norm(rec["title"])[:35] in norm(r["title"]))
        if ok:
            recent_ok.append(dict(rec=rec, query=r["query"]))
            print("✅ [%s] %s | %s" % (rec["year"], rec["title"][:48], rec["container"][:40]))
        else:
            print("❌ 复核失败: %s" % r["title"][:60])

    # ---- 汇总 ----
    all_pass = passed + [dict(seed=dict(id="N%d" % i, cat="recent 2024-2026", tier="",
                                        title=x["rec"]["title"]), rec=x["rec"])
                         for i, x in enumerate(recent_ok)]
    n_recent = sum(1 for p in all_pass if (p["rec"].get("year") or 0) >= 2024)
    n_top = sum(1 for p in all_pass if p["seed"].get("tier") == "top")
    ratio = n_recent / max(1, len(all_pass))
    out = dict(total_pass=len(all_pass), n_recent_2024plus=n_recent, recent_ratio=ratio,
               n_top_tier=n_top,
               entries=[dict(id=p["seed"]["id"], cat=p["seed"]["cat"], tier=p["seed"].get("tier", ""),
                             cite_as=p["seed"].get("cite_as", ""), **p["rec"]) for p in all_pass],
               failed=[dict(id=r["seed"]["id"], title=r["seed"]["title"], notes=r["notes"])
                       for r in results if r["status"] == "FAIL"])
    with open("paper/references_verified.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    L = ["# 参考文献逐条验证日志 v2（FedRBC）", "",
         "- 数据源：CrossRef REST API + DataCite（arXiv DOI）",
         "- 验证字段：题名/作者/容器/年份/卷期页码/DOI", "",
         "## 种子池（%d 条）" % len(results), "",
         "| ID | 状态 | 题名(实际) | 年份 | 容器 | DOI | 备注 |",
         "|----|------|-----------|------|------|-----|------|"]
    for r in results:
        rec = r["rec"] or {}
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["seed"]["id"], "✅" if r["status"] == "PASS" else "❌",
            (rec.get("title") or r["seed"]["title"])[:48], rec.get("year", "?"),
            (rec.get("container") or "")[:34], rec.get("doi", ""), r["notes"][:38]))
    L += ["", "## 近年补充 2024-2026（%d 条，CrossRef 检索+复核）" % len(recent_ok), "",
          "| 年份 | 题名 | 期刊 | 卷(期):页 | DOI |",
          "|------|------|------|----------|-----|"]
    for x in recent_ok:
        r = x["rec"]
        vip = "%s(%s):%s" % (r.get("volume", ""), r.get("issue", ""), r.get("page", ""))
        L.append("| %s | %s | %s | %s | %s |" % (r.get("year"), r["title"][:55],
                 (r.get("container") or "")[:34], vip[:20], r.get("doi")))
    L += ["", "## 硬指标核算", "",
          "- 通过总数：**%d**（要求 ≥35）" % len(all_pass),
          "- 2024-2026：**%d** 篇，占比 **%.1f%%**（要求 ≥50%%）" % (n_recent, 100 * ratio),
          "- 顶会顶刊（top 标注）：**%d**（要求 ≥5）" % n_top,
          "- 验证失败待替换：%d" % sum(1 for r in results if r["status"] == "FAIL")]
    with open("results/refs_validation.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n== 汇总: 通过 %d｜2024+ %.1f%%｜top %d ==" % (len(all_pass), 100 * ratio, n_top))

if __name__ == "__main__":
    main()
