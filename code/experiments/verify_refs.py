#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC 参考文献真实性验证脚本
- 种子文献池：DOI -> CrossRef 直查；顶会/arXiv -> Semantic Scholar 题名查询
- 近年补充：S2 按关键词检索 2024-2026 高相关文献
- 输出：results/refs_validation.md（逐条验证日志）+ paper/references_verified.json
"""
import json, time, sys, ssl, urllib.request, urllib.parse, urllib.error

def _mk_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
        # 企业代理环境下若仍失败，在 http_json 中降级为非严格校验

_SSL_CTX = _mk_ctx()

CROSSREF = "https://api.crossref.org/works/"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
UA = {"User-Agent": "FedRBC-RefVerifier/1.0 (mailto:research@example.org)"}

# ---------------- 种子文献池 ----------------
# cat: 分类; tier: top=顶会顶刊/CCF-A/1区; verify: doi 或 title
SEEDS = [
 # --- A. FL 基础 ---
 dict(id="A1", cat="FL foundations", tier="top", verify="title",
      title="Communication-Efficient Learning of Deep Networks from Decentralized Data",
      expect="McMahan", year=2017),
 dict(id="A2", cat="FL foundations", tier="top", verify="doi", doi="10.1561/2200000083",
      title="Advances and Open Problems in Federated Learning", expect="Kairouz", year=2021),
 dict(id="A3", cat="FL foundations", tier="top", verify="title",
      title="Federated Optimization in Heterogeneous Networks", expect="Li", year=2020),
 dict(id="A4", cat="FL foundations", tier="top", verify="doi", doi="10.1109/MSP.2020.2975749",
      title="Federated Learning: Challenges, Methods, and Future Directions", expect="Li", year=2020),
 dict(id="A5", cat="FL foundations", tier="top", verify="title",
      title="Adaptive Federated Optimization", expect="Reddi", year=2021),
 # --- B. 鲁棒聚合 / Byzantine ---
 dict(id="B1", cat="Byzantine-robust FL", tier="top", verify="title",
      title="Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent",
      expect="Blanchard", year=2017),
 dict(id="B2", cat="Byzantine-robust FL", tier="top", verify="title",
      title="Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates",
      expect="Yin", year=2018),
 dict(id="B3", cat="Byzantine-robust FL", tier="top", verify="doi", doi="10.14722/ndss.2021.24494",
      title="FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping", expect="Cao", year=2021),
 dict(id="B4", cat="Byzantine-robust FL", tier="top", verify="title",
      title="How To Backdoor Federated Learning", expect="Bagdasaryan", year=2020),
 dict(id="B5", cat="Byzantine-robust FL", tier="top", verify="title",
      title="The Hidden Vulnerability of Distributed Learning in Byzantium", expect="Mhamdi", year=2018),
 dict(id="B6", cat="Byzantine-robust FL", tier="top", verify="title",
      title="A Little Is Enough: Circumventing Defenses for Distributed Learning", expect="Baruch", year=2019),
 dict(id="B7", cat="Byzantine-robust FL", tier="top", verify="title",
      title="Mitigating Sybils in Federated Learning Poisoning", expect="Fung", year=2018),
 # --- C. 区块链 + FL ---
 dict(id="C1", cat="blockchain FL", tier="top", verify="doi", doi="10.1109/TDSC.2019.2952332",
      title="DeepChain: Auditable and Privacy-Preserving Deep Learning with Blockchain-based Incentive",
      expect="Weng", year=2021),
 dict(id="C2", cat="blockchain FL", tier="top", verify="doi", doi="10.1109/TII.2019.2942190",
      title="Blockchain and Federated Learning for Privacy-Preserved Data Sharing in Industrial IoT",
      expect="Lu", year=2020),
 dict(id="C3", cat="blockchain FL", tier="top", verify="doi", doi="10.1109/TCOMM.2020.2990686",
      title="Federated Learning With Blockchain for Autonomous Vehicles: Analysis and Design Challenges",
      expect="Pokhrel", year=2020),
 dict(id="C4", cat="blockchain FL", tier="", verify="doi", doi="10.1109/MNET.011.2000263",
      title="A Blockchain-based Decentralized Federated Learning Framework with Committee Consensus",
      expect="Li", year=2021),
 dict(id="C5", cat="blockchain FL", tier="", verify="doi", doi="10.1109/LCOMM.2019.2921755",
      title="Blockchained On-Device Federated Learning", expect="Kim", year=2020),
 # --- D. 隐私 / DP ---
 dict(id="D1", cat="privacy DP", tier="top", verify="doi", doi="10.1109/CSF.2017.11",
      title="R\u00e9nyi Differential Privacy", expect="Mironov", year=2017),
 dict(id="D2", cat="privacy DP", tier="top", verify="doi", doi="10.1109/TIFS.2020.2988575",
      title="Federated Learning With Differential Privacy: Algorithms and Performance Analysis",
      expect="Wei", year=2020),
 dict(id="D3", cat="privacy DP", tier="", verify="title",
      title="Differentially Private Federated Learning: A Client Level Perspective", expect="Geyer", year=2017),
 # --- E. 医疗 FL ---
 dict(id="E1", cat="FL healthcare", tier="top", verify="doi", doi="10.1038/s41746-020-00323-1",
      title="The future of digital health with federated learning", expect="Rieke", year=2020),
 dict(id="E2", cat="FL healthcare", tier="top", verify="doi", doi="10.1038/s42256-020-0186-1",
      title="Secure, privacy-preserving and federated machine learning in medical imaging",
      expect="Kaissis", year=2020),
 dict(id="E3", cat="FL healthcare", tier="", verify="doi", doi="10.1007/s41666-020-00082-4",
      title="Federated Learning for Healthcare Informatics", expect="Xu", year=2021),
 # --- F. IDS 数据集 ---
 dict(id="F1", cat="IDS dataset", tier="", verify="doi", doi="10.1109/ACCESS.2020.2990421",
      title="Intrusion Detection System for Healthcare Systems Using Medical and Network Data: A Comparison Study",
      expect="Hady", year=2020),
 dict(id="F2", cat="IDS dataset", tier="", verify="title",
      title="ToN_IoT Telemetry Dataset: A New Generation Dataset of IoT and IIoT for Data-Driven Intrusion Detection Systems",
      expect="Alsaedi", year=2021),
 dict(id="F3", cat="IDS dataset", tier="", verify="doi", doi="10.1016/j.future.2019.05.041",
      title="Towards the Development of Realistic Botnet Dataset in the Internet of Things for Network Forensic Analytics: Bot-IoT Dataset",
      expect="Koroniotis", year=2019),
 dict(id="F4", cat="IDS dataset", tier="", verify="doi", doi="10.3390/s23135941",
      title="CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment",
      expect="Neto", year=2023),
 dict(id="F5", cat="IDS dataset", tier="", verify="doi", doi="10.5220/0006639801080116",
      title="Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization",
      expect="Sharafaldin", year=2018),
 # --- G. SDN / IoT 安全 ---
 dict(id="G1", cat="SDN IoT security", tier="top", verify="doi", doi="10.1109/JIOT.2020.2977196",
      title="Blockchain-Enabled Distributed Security Framework for Next-Generation IoT: An Edge Cloud and Software-Defined Network-Integrated Approach",
      expect="Medhane", year=2020),
 dict(id="G2", cat="SDN IoT security", tier="", verify="doi", doi="10.32604/cmc.2026.085763",
      title="A Secure Blockchain-Enabled SDN-Based Edge Computing Framework for IoT Healthcare Systems",
      expect="Tyagi", year=2026),
 dict(id="G3", cat="SDN IoT security", tier="", verify="doi", doi="10.1145/2620728.2620744",
      title="ONOS: Towards an Open, Distributed SDN OS", expect="Berde", year=2014),
 # --- H. Non-IID / 收敛理论 ---
 dict(id="H1", cat="FL convergence", tier="top", verify="title",
      title="On the Convergence of FedAvg on Non-IID Data", expect="Li", year=2020),
 dict(id="H2", cat="FL convergence", tier="", verify="title",
      title="Measuring the Effects of Non-Identical Data Distribution for Federated Visual Classification",
      expect="Hsu", year=2019),
]

# 近年补充检索（Semantic Scholar, 2024-2026）
RECENT_QUERIES = [
 ("blockchain federated learning reputation", 6),
 ("federated learning intrusion detection IoT", 6),
 ("Byzantine robust federated learning aggregation", 4),
 ("federated learning healthcare privacy preserving", 4),
]

def http_json(url, retries=3, timeout=30):
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            ctx = _SSL_CTX if k < retries - 1 else ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    return None

def norm(s):
    return "".join(c.lower() for c in (s or "") if c.isalnum())

def crossref_by_doi(doi):
    j = http_json(CROSSREF + urllib.parse.quote(doi))
    if not j or j.get("status") != "ok":
        return None
    m = j["message"]
    return dict(
        title=(m.get("title") or [""])[0],
        authors=["{} {}".format(a.get("given", ""), a.get("family", "")).strip()
                 for a in m.get("author", [])],
        container=(m.get("container-title") or [""])[0],
        year=(m.get("issued", {}).get("date-parts", [[None]])[0][0]),
        volume=m.get("volume", ""), issue=m.get("issue", ""),
        page=m.get("page", ""), doi=m.get("DOI", doi), type=m.get("type", ""),
    )

def crossref_by_title(title):
    q = CROSSREF + "?query.bibliography=" + urllib.parse.quote(title) + "&rows=3"
    j = http_json(q)
    if not j or j.get("status") != "ok":
        return None
    items = j["message"].get("items", [])
    if not items:
        return None
    m = items[0]
    return dict(
        title=(m.get("title") or [""])[0],
        authors=["{} {}".format(a.get("given", ""), a.get("family", "")).strip()
                 for a in m.get("author", [])],
        container=(m.get("container-title") or [""])[0],
        year=(m.get("issued", {}).get("date-parts", [[None]])[0][0]),
        volume=m.get("volume", ""), issue=m.get("issue", ""),
        page=m.get("page", ""), doi=m.get("DOI", ""), type=m.get("type", ""),
    )

def s2_by_title(title):
    q = S2_SEARCH + "?query=" + urllib.parse.quote(title) + "&limit=3" + \
        "&fields=title,year,venue,authors,externalIds,publicationTypes,journal,citationCount"
    j = http_json(q)
    if not j or not j.get("data"):
        return None
    p = j["data"][0]
    doi = (p.get("externalIds") or {}).get("DOI", "")
    venue = p.get("venue") or (p.get("journal") or {}).get("name", "")
    return dict(title=p.get("title", ""),
                authors=[a.get("name", "") for a in p.get("authors", [])],
                container=venue, year=p.get("year"),
                volume="", issue="", page="", doi=doi,
                type="conference/journal", citations=p.get("citationCount", 0))

def check(seed, rec, src):
    """返回 (status, notes)。比对题名相似、期望作者、年份。"""
    if rec is None:
        return "FAIL", "API 无返回"
    notes = []
    ok = True
    t_sim = norm(seed["title"])[:40] in norm(rec["title"]) or norm(rec["title"])[:40] in norm(seed["title"])
    if not t_sim:
        ok = False; notes.append("题名不匹配: 期望'%s' vs 实际'%s'" % (seed["title"][:60], rec["title"][:60]))
    auth_hit = any(seed["expect"].lower() in a.lower() for a in rec["authors"])
    if not auth_hit:
        ok = False; notes.append("期望作者 %s 未在 %s 中" % (seed["expect"], rec["authors"][:3]))
    if rec["year"] and abs((rec["year"] or 0) - seed["year"]) > 1:
        ok = False; notes.append("年份偏差: 期望 %d vs 实际 %s" % (seed["year"], rec["year"]))
    return ("PASS" if ok else "FAIL"), "; ".join(notes) or "一致(%s)" % src

def main():
    results, passed = [], []
    print("== 阶段1: 种子文献池验证 (%d 条) ==" % len(SEEDS))
    for s in SEEDS:
        time.sleep(0.6)
        if s["verify"] == "doi":
            rec = crossref_by_doi(s["doi"]); src = "CrossRef(DOI)"
            if rec is None:  # DOI 查不到时降级题名查
                time.sleep(0.6); rec = s2_by_title(s["title"]); src = "S2(fallback)"
        else:
            rec = s2_by_title(s["title"]); src = "S2(title)"
            if rec is None:
                time.sleep(0.6); rec = crossref_by_title(s["title"]); src = "CrossRef(title-fallback)"
        status, notes = check(s, rec, src)
        results.append(dict(seed=s, rec=rec, status=status, notes=notes))
        mark = "✅" if status == "PASS" else "❌"
        print("%s [%s] %s | %s" % (mark, s["id"], s["title"][:58], notes[:80]))
        if status == "PASS":
            passed.append(dict(seed=s, rec=rec))

    print("\n== 阶段2: 近年文献补充检索 (S2, 2024-2026) ==")
    recent = []
    seen = set(norm(r["rec"]["title"]) for r in results if r["rec"])
    for q, limit in RECENT_QUERIES:
        time.sleep(1.0)
        url = S2_SEARCH + "?query=" + urllib.parse.quote(q) + \
              "&year=2024-2026&limit=%d&fields=title,year,venue,authors,externalIds,journal,citationCount" % (limit * 2)
        j = http_json(url)
        if not j or not j.get("data"):
            print("⚠️ 查询无结果: %s" % q); continue
        cnt = 0
        for p in j["data"]:
            if cnt >= limit: break
            title = p.get("title", "")
            if not title or norm(title) in seen: continue
            venue = p.get("venue") or (p.get("journal") or {}).get("name", "")
            doi = (p.get("externalIds") or {}).get("DOI", "")
            if not doi: continue  # 只要可 DOI 检索的
            seen.add(norm(title))
            recent.append(dict(
                title=title, year=p.get("year"), venue=venue, doi=doi,
                authors=[a.get("name", "") for a in p.get("authors", [])][:6],
                citations=p.get("citationCount", 0), query=q))
            cnt += 1
        print("  [%s] +%d 条候选" % (q, cnt))

    # 阶段3: 近年候选逐条 CrossRef 复核（以 DOI 为准）
    print("\n== 阶段3: 近年候选 CrossRef 复核 ==")
    recent_passed = []
    for r in recent:
        time.sleep(0.6)
        rec = crossref_by_doi(r["doi"])
        if rec is None:
            print("❌ [%s] %s | CrossRef 无此 DOI" % (r["year"], r["title"][:55])); continue
        t_ok = norm(r["title"])[:35] in norm(rec["title"]) or norm(rec["title"])[:35] in norm(r["title"])
        y_ok = rec["year"] and abs(rec["year"] - r["year"]) <= 1
        if t_ok and y_ok:
            recent_passed.append(dict(rec=rec, query=r["query"], citations=r["citations"]))
            print("✅ [%s] %s | %s | DOI:%s" % (rec["year"], rec["title"][:48], rec["container"][:38], r["doi"]))
        else:
            print("❌ [%s] %s | 题名/年份不符 CrossRef" % (r["year"], r["title"][:55]))

    # ---- 汇总落盘 ----
    all_pass = passed + [dict(seed=dict(id="R%d" % i, cat="recent(2024-2026)", tier="", title=x["rec"]["title"]),
                              rec=x["rec"]) for i, x in enumerate(recent_passed)]
    n_recent = sum(1 for p in all_pass if (p["rec"].get("year") or 0) >= 2024)
    n_top = sum(1 for p in all_pass if p["seed"].get("tier") == "top")
    out = dict(
        total_pass=len(all_pass), n_recent_2024plus=n_recent,
        recent_ratio=n_recent / max(1, len(all_pass)), n_top_tier=n_top,
        seeds=[dict(id=r["seed"]["id"], status=r["status"], notes=r["notes"],
                    title=r["seed"]["title"], rec=r["rec"]) for r in results],
        recent=recent_passed,
    )
    with open("paper/references_verified.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # ---- 验证日志 markdown ----
    L = ["# 参考文献逐条验证日志（FedRBC）",
         "",
         "- 验证工具：CrossRef REST API（api.crossref.org）+ Semantic Scholar Graph API",
         "- 验证字段：题名 / 作者 / 期刊(会议) / 年份 / 卷期页码 / DOI",
         "", "## 种子池（%d 条）" % len(results), "",
         "| ID | 状态 | 题名 | 来源 | 年份 | 容器 | DOI | 备注 |",
         "|----|------|------|------|------|------|-----|------|"]
    for r in results:
        rec = r["rec"] or {}
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["seed"]["id"], "✅" if r["status"] == "PASS" else "❌",
            (rec.get("title") or r["seed"]["title"])[:50],
            "CrossRef/S2", rec.get("year", "?"),
            (rec.get("container") or "")[:36], rec.get("doi", ""), r["notes"][:40]))
    L += ["", "## 近年补充（2024-2026, CrossRef 复核通过 %d 条）" % len(recent_passed), "",
          "| 年份 | 题名 | 容器 | DOI | 引用数 |",
          "|------|------|------|-----|--------|"]
    for x in recent_passed:
        L.append("| %s | %s | %s | %s | %s |" % (
            x["rec"].get("year"), x["rec"]["title"][:58],
            (x["rec"].get("container") or "")[:36], x["rec"].get("doi"), x.get("citations", 0)))
    L += ["", "## 硬指标核算", "",
          "- 通过总数：**%d**（要求 ≥35）" % len(all_pass),
          "- 2024-2026 文献：**%d**（占比 **%.1f%%**，要求 ≥50%%）" % (n_recent, 100 * out["recent_ratio"]),
          "- 顶会顶刊（种子池标注 top）：**%d**（要求 ≥5）" % n_top,
          "- 验证失败条目：%d（需替换后重验）" % sum(1 for r in results if r["status"] == "FAIL")]
    with open("results/refs_validation.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n== 汇总 ==")
    print("通过 %d 条｜2024+ 占 %.1f%%｜top-tier %d 条" % (len(all_pass), 100 * out["recent_ratio"], n_top))
    print("日志: results/refs_validation.md｜数据: paper/references_verified.json")

if __name__ == "__main__":
    main()
