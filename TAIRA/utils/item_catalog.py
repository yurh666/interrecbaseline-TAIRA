"""Load per-domain metadata and build `project_info` text (shared by ItemRetrievalAgent and embedding scripts)."""
import pandas as pd


def load_items_metadata(domain: str, domain_root: str = "data") -> pd.DataFrame:
    """
    Returns a copy with columns including `product_id` and `project_info`,
    aligned with `agents/item_retrieval_agent.py` domain branches.
    """
    domain_path = f"{domain_root}/{domain}"
    if domain in [
        "amazon_clothing",
        "amazon_music",
        "lastfm",
        "yelp",
        "movielens",
        "amazon_book",
    ]:
        df = pd.read_csv(f"{domain_path}/metadata.csv")
        df["project_info"] = df["title"].fillna("").astype(str) + " " + df[
            "category"
        ].fillna("").astype(str)
        df = df.rename(columns={"id": "product_id"})
    elif domain == "amazon_beauty":
        df = pd.read_csv(f"{domain_path}/metadata.csv")
        df["title"] = df["title"].fillna("").astype(str)
        df["description"] = df["description"].fillna("").astype(str)
        df["category"] = df["category"].fillna("").astype(str)
        df["project_info"] = df["title"] + " " + df["description"] + df["category"]
        df = df.rename(columns={"id": "product_id"})
    else:
        raise ValueError(f"Unsupported domain: {domain}")

    df = df.reset_index(drop=True)
    return df
