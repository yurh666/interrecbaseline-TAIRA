#!/usr/bin/env python3
"""
Convert InterRec LastFM sessions to TAIRA query_data1.csv format.

Input:
  - interrec/data/processed/sessions.json   (user sessions with future_test targets)
  - interrec/data/processed/items.csv       (item metadata)
  - interrec/data/processed/user_splits.json (train/valid/test splits)

Output:
  - TAIRA/data/lastfm/query_data1.csv       (TAIRA query format)
  - TAIRA/data/lastfm/metadata.csv          (TAIRA item metadata format)
  - TAIRA/data/lastfm/knowledge1.csv        (domain knowledge from tags)

Usage:
  python scripts/convert_lastfm_to_taira.py

Notes:
  - query text is generated from target item description (no LLM needed)
  - classification=1 marks valid test cases
  - targets = '|'.join(target_item_ids)
  - preferences = summary of observed_history items' tags
"""
import json
import pandas as pd
from pathlib import Path

INTERREC_DIR = Path("/root/interrec/data/processed")
TAIRA_DIR = Path("/root/main_table_experiments/baselines/taira_official/TAIRA/data/lastfm")
TAIRA_DIR.mkdir(parents=True, exist_ok=True)

# ── Load InterRec data ──────────────────────────────────────────────
sessions = json.loads((INTERREC_DIR / "sessions.json").read_text())
items_df = pd.read_csv(INTERREC_DIR / "items.csv")
items_df["item_id"] = items_df["item_id"].astype(str)
item_lookup = {row["item_id"]: row for _, row in items_df.iterrows()}

# ── Build metadata.csv (TAIRA format) ──────────────────────────────
metadata_rows = []
for _, row in items_df.iterrows():
    metadata_rows.append({
        "id": str(row["item_id"]),
        "title": str(row.get("title", "")),
        "category": str(row.get("tags", ""))[:200],   # use tags as category
        "price": 0.0,
        "rating": 4.0,
    })
metadata_df = pd.DataFrame(metadata_rows)
metadata_df.to_csv(TAIRA_DIR / "metadata.csv", index=False)
print(f"✓ metadata.csv: {len(metadata_df)} items")

# ── Build knowledge1.csv (domain knowledge from tag co-occurrence) ──
# Extract unique tag phrases as attribute-usage pairs
tags_set = {}
for _, row in items_df.iterrows():
    tags_raw = str(row.get("tags", ""))
    if tags_raw and tags_raw != "nan":
        tags = [t.strip() for t in tags_raw.split() if len(t.strip()) > 2]
        for tag in tags[:5]:
            if tag not in tags_set:
                tags_set[tag] = f"Music with {tag} style, suitable for listeners who enjoy {tag}"

knowledge_rows = [{"attribute": k, "usage": v} for k, v in list(tags_set.items())[:200]]
knowledge_df = pd.DataFrame(knowledge_rows)
knowledge_df.to_csv(TAIRA_DIR / "knowledge1.csv", index=False)
print(f"✓ knowledge1.csv: {len(knowledge_df)} attributes")

# ── Build query_data1.csv (TAIRA query format) ──────────────────────
# Use test sessions only (future_test items as targets)
test_sessions = [s for s in sessions if s.get("future_test")]
print(f"\nUsing {len(test_sessions)} sessions for test queries")

query_rows = []
for s in test_sessions:
    targets = [str(t) for t in s.get("future_test", [])]
    if not targets:
        continue

    # Primary target: first future_test item (used ONLY for evaluation, NOT in query)
    target_id = targets[0]
    target_item = item_lookup.get(target_id, {})
    target_title = str(target_item.get("title", target_id))
    target_category = str(target_item.get("tags", "music"))[:80]

    # Build natural language query ONLY from observed_history (same info as InterRec)
    # IMPORTANT: do NOT reveal target item name/tags in the query — that gives TAIRA an
    # unfair advantage (BM25 would trivially return the target when its name is in the query).
    obs_titles = []
    obs_tags_set = []
    for obs_id in s.get("observed_history", [])[:10]:
        obs_item = item_lookup.get(str(obs_id), {})
        t = str(obs_item.get("title", ""))
        if t and t != "nan":
            obs_titles.append(t)
        tags_raw = str(obs_item.get("tags", ""))
        if tags_raw and tags_raw != "nan":
            obs_tags_set.extend(tags_raw.split()[:2])

    top_obs_titles = obs_titles[:6]
    top_obs_tags = list(dict.fromkeys(obs_tags_set))[:5]  # deduplicated

    if top_obs_titles:
        history_str = ", ".join(top_obs_titles)
        if top_obs_tags:
            tag_str = " ".join(top_obs_tags)
            query = (f"I enjoy listening to artists like {history_str}. "
                     f"I generally like {tag_str} music. "
                     f"Can you recommend similar music artists I might enjoy?")
        else:
            query = (f"I enjoy listening to artists like {history_str}. "
                     f"Can you recommend similar music artists I might enjoy?")
    else:
        query = "Can you recommend some music artists I might enjoy?"

    preferences = f"The user likes: {', '.join(obs_titles[:5])}" if obs_titles else "Music listener"

    query_rows.append({
        "id": str(target_id),
        "title": target_title,
        "category": target_category,
        "price": 0.0,
        "rating": 4.0,
        "user_id": str(s["user_id"]),
        "remaining_interaction_string": "|".join(str(x) for x in s.get("future_train", [])[:5]),
        "query": query,
        "classification": 1,
        "preferences": preferences,
        "new_query": query,
        "target_count": 1,
        # Store ALL future_test ids for direct ID-matching evaluation (pipe-separated)
        "targets": "|".join(targets),
        # Primary target for LLM-based evaluation (first future_test item)
        "primary_target_id": str(target_id),
    })

query_df = pd.DataFrame(query_rows)
query_df.to_csv(TAIRA_DIR / "query_data1.csv", index=False)
print(f"✓ query_data1.csv: {len(query_df)} test queries")
print(f"\n  Sample query: {query_rows[0]['new_query'][:80]}")
print(f"  Sample target: {query_rows[0]['targets'][:50]}")
print(f"  Sample preference: {query_rows[0]['preferences'][:60]}")

print(f"\n✓ Done! TAIRA data ready at: {TAIRA_DIR}")
print(f"  To run: update system_config.yaml DOMAIN='lastfm' and run main.py")
