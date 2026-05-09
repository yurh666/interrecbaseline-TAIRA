#!/usr/bin/env python3
"""
Convert InterRec processed data (any dataset subfolder) to TAIRA `data/<domain>/` layout.

Fair protocol (aligned with InterRec):
  - `new_query` uses only observed_history (no target title / ID in the question text).
  - `targets` = all future_test IDs (pipe-separated) for direct ID-matching eval.

Usage:
  python3 convert_interrec_to_taira.py --dataset lastfm
  python3 convert_interrec_to_taira.py --dataset yelp
  python3 convert_interrec_to_taira.py --dataset movielens
  python3 convert_interrec_to_taira.py --dataset amazon_book

Paths:
  InterRec processed: /root/interrec/data/processed/<dataset>/
  TAIRA output:       .../TAIRA/data/<domain>/
  Domain names match TAIRA DOMAIN config: lastfm | yelp | movielens | amazon_book
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

PROCESSED_ROOT = Path("/root/interrec/data/processed")
TAIRA_DATA = Path("/root/main_table_experiments/baselines/taira_official/TAIRA/data")


def _token_bits(text: str, max_tokens: int = 8) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", (text or "").lower())[:max_tokens]


def _load_items(path: Path) -> dict[str, dict[str, str]]:
    items: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            iid = str(row.get("item_id", "")).strip()
            if not iid:
                continue
            items[iid] = {k: (row.get(k) or "").strip() for k in row}
    return items


def _build_knowledge_from_tags(items: dict[str, dict[str, str]], cap: int = 200) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    for row in items.values():
        tags = row.get("tags", "")
        if not tags or tags == "nan":
            continue
        for part in re.split(r"[,|]", tags):
            t = part.strip()
            if len(t) > 2 and t.lower() not in seen:
                seen[t.lower()] = f"Items tagged or categorized with {t}."
            if len(seen) >= cap:
                break
        if len(seen) >= cap:
            break
    return [{"attribute": k, "usage": v} for k, v in list(seen.items())[:cap]]


def _query_for_dataset(
    dataset: str,
    obs_titles: list[str],
    tag_tokens: list[str],
) -> tuple[str, str]:
    titles = ", ".join(obs_titles[:6]) if obs_titles else ""
    tags = " ".join(tag_tokens[:6]) if tag_tokens else ""

    if dataset == "lastfm":
        if titles:
            if tags:
                q = (
                    f"I enjoy listening to artists like {titles}. "
                    f"I generally like {tags} music. "
                    f"Can you recommend similar music artists I might enjoy?"
                )
            else:
                q = (
                    f"I enjoy listening to artists like {titles}. "
                    f"Can you recommend similar music artists I might enjoy?"
                )
        else:
            q = "Can you recommend some music artists I might enjoy?"
        pref = f"The user likes: {', '.join(obs_titles[:5])}" if obs_titles else "Music listener"

    elif dataset == "movielens":
        if titles:
            if tags:
                q = (
                    f"I enjoy movies like {titles}. "
                    f"I generally like {tags} films. "
                    f"Can you recommend similar movies I might enjoy?"
                )
            else:
                q = (
                    f"I enjoy movies like {titles}. "
                    f"Can you recommend similar movies I might enjoy?"
                )
        else:
            q = "Can you recommend some movies I might enjoy?"
        pref = f"The user likes: {', '.join(obs_titles[:5])}" if obs_titles else "Movie watcher"

    elif dataset == "yelp":
        if titles:
            if tags:
                q = (
                    f"I have liked businesses like {titles}. "
                    f"I generally enjoy {tags} places. "
                    f"Can you recommend similar local businesses I might try?"
                )
            else:
                q = (
                    f"I have liked businesses like {titles}. "
                    f"Can you recommend similar local businesses I might try?"
                )
        else:
            q = "Can you recommend some local businesses I might enjoy?"
        pref = f"The user likes: {', '.join(obs_titles[:5])}" if obs_titles else "Local customer"

    elif dataset == "amazon_book":
        if titles:
            if tags:
                q = (
                    f"I enjoy reading books like {titles}. "
                    f"I generally like {tags} books. "
                    f"Can you recommend similar books I might enjoy?"
                )
            else:
                q = (
                    f"I enjoy reading books like {titles}. "
                    f"Can you recommend similar books I might enjoy?"
                )
        else:
            q = "Can you recommend some books I might enjoy?"
        pref = f"The user likes: {', '.join(obs_titles[:5])}" if obs_titles else "Reader"

    else:
        raise ValueError(f"unknown dataset: {dataset}")

    return q, pref


def convert_dataset(dataset: str) -> None:
    if dataset not in {"lastfm", "yelp", "movielens", "amazon_book"}:
        raise SystemExit(f"Unsupported dataset: {dataset}")

    proc = PROCESSED_ROOT / dataset
    if not proc.is_dir():
        raise SystemExit(f"Missing processed dir: {proc}")

    sessions_path = proc / "sessions.json"
    items_path = proc / "items.csv"
    if not sessions_path.exists() or not items_path.exists():
        raise SystemExit(f"Need {sessions_path} and {items_path}")

    sessions = json.loads(sessions_path.read_text(encoding="utf-8"))
    items = _load_items(items_path)

    out_dir = TAIRA_DATA / dataset
    out_dir.mkdir(parents=True, exist_ok=True)

    # metadata.csv (TAIRA)
    meta_rows: list[dict] = []
    for iid, row in items.items():
        title = row.get("title", "") or ""
        category = (row.get("category", "") or row.get("tags", "") or "")[:200]
        if dataset == "amazon_book" and not title.strip():
            title = f"book_{iid}"
        meta_rows.append({"id": iid, "title": title, "category": category, "price": 0.0, "rating": 4.0})
    with (out_dir / "metadata.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "category", "price", "rating"])
        w.writeheader()
        w.writerows(meta_rows)
    print(f"✓ {dataset} metadata.csv: {len(meta_rows)} items")

    know = _build_knowledge_from_tags(items)
    if not know:
        know = [
            {"attribute": "general", "usage": "User preferences inferred from past interactions and item associations."}
        ]
    with (out_dir / "knowledge1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["attribute", "usage"])
        w.writeheader()
        w.writerows(know)
    print(f"✓ {dataset} knowledge1.csv: {len(know)} rows")

    test_sessions = [s for s in sessions if s.get("future_test")]
    query_rows: list[dict] = []
    for s in test_sessions:
        targets = [str(t).strip() for t in s.get("future_test", []) if str(t).strip()]
        if not targets:
            continue
        target_id = targets[0]
        tgt = items.get(target_id, {})
        target_title = (tgt.get("title") or "").strip() or f"item_{target_id}"
        target_cat = (tgt.get("category") or tgt.get("tags") or "")[:200]

        obs_titles: list[str] = []
        tag_tokens: list[str] = []
        for obs_id in s.get("observed_history", [])[:12]:
            obs = items.get(str(obs_id), {})
            t = (obs.get("title") or "").strip()
            if not t and dataset == "amazon_book":
                t = f"book_{obs_id}"
            if t:
                obs_titles.append(t)
            for col in ("tags", "category"):
                raw = obs.get(col, "")
                if raw:
                    tag_tokens.extend(_token_bits(raw.replace(",", " "), 4))
            tag_tokens = list(dict.fromkeys(tag_tokens))[:20]

        new_query, preferences = _query_for_dataset(dataset, obs_titles, tag_tokens[:8])

        query_rows.append({
            "id": target_id,
            "title": target_title,
            "category": target_cat,
            "price": 0.0,
            "rating": 4.0,
            "user_id": str(s["user_id"]),
            "remaining_interaction_string": "|".join(str(x) for x in s.get("future_train", [])[:5]),
            "query": new_query,
            "classification": 1,
            "preferences": preferences,
            "new_query": new_query,
            "target_count": 1,
            "targets": "|".join(targets),
            "primary_target_id": target_id,
        })

    with (out_dir / "query_data1.csv").open("w", newline="", encoding="utf-8") as f:
        if not query_rows:
            raise SystemExit("No query rows produced")
        w = csv.DictWriter(f, fieldnames=list(query_rows[0].keys()))
        w.writeheader()
        w.writerows(query_rows)
    print(f"✓ {dataset} query_data1.csv: {len(query_rows)} rows → {out_dir}")
    print(f"  sample query: {query_rows[0]['new_query'][:120]}…")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True, choices=["lastfm", "yelp", "movielens", "amazon_book"])
    args = p.parse_args()
    convert_dataset(args.dataset)


if __name__ == "__main__":
    main()
