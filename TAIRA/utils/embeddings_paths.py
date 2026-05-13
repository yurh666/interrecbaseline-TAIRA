"""Resolve directories for BGE item embeddings (supports data-disk layouts, e.g. AutoDL /root/autodl-tmp)."""
from __future__ import annotations

import os


def domain_embedding_artifacts_dir(domain: str) -> str:
    """
    Directory containing ``project_embeddings.npy`` and ``bge_embedding_manifest.json``.

    If ``TAIRA_EMBEDDINGS_ROOT`` is set (absolute path recommended), uses
    ``<root>/<domain>``. Otherwise uses ``data/<domain>`` relative to the
    current working directory (expected: ``TAIRA/`` after ``os.chdir``).
    """
    root = (os.environ.get("TAIRA_EMBEDDINGS_ROOT") or "").strip()
    if root:
        return os.path.join(os.path.abspath(os.path.expanduser(root)), domain)
    return os.path.join("data", domain)
