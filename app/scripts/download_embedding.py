from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.core.config import GlobalConfig


logger = logging.getLogger(__name__)


def _console(text: str) -> None:
    print(text, flush=True)


def resolve_agent_embedding_path() -> Path:
    return Path(str(GlobalConfig.AGENT_PLUGIN_EMBEDDING_MODEL))


def ensure_agent_embedding_ready(
    force: bool = False,
    skip_if_disabled: bool = False,
    allow_download: bool = True,
) -> Path:
    embedding_path = resolve_agent_embedding_path()

    if skip_if_disabled and not GlobalConfig.AGENT_PLUGIN_ENABLED:
        _console("[AgentPlugin] AGENT_PLUGIN_ENABLED=false, skip embedding prepare")
        return embedding_path

    if embedding_path.exists() and not force:
        _console(f"[AgentPlugin] Embedding already exists: {embedding_path}")
        return embedding_path

    if not allow_download:
        raise RuntimeError(
            "Embedding model is missing. Run `python -m app.scripts.download_embedding` "
            "before starting Docker."
        )

    model_name = str(GlobalConfig.AGENT_PLUGIN_EMBEDDING_MODEL_NAME)
    action = "Refreshing" if force and embedding_path.exists() else "Downloading"
    _console(f"[AgentPlugin] {action} embedding model: {model_name}")
    _console(f"[AgentPlugin] Target path: {embedding_path}")
    logger.info(
        "Preparing agent embedding: model=%s, target=%s, force=%s",
        model_name,
        embedding_path,
        force,
    )
    embedding_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            model_name,
            cache_folder=str(GlobalConfig.EMBEDDING_MODELS_DIR),
        )
        model.save(str(embedding_path))
    except Exception as exc:
        _console(f"[AgentPlugin] Embedding prepare failed: {exc}")
        logger.exception("Agent embedding prepare failed: %s", exc)
        raise RuntimeError(
            f"Agent embedding unavailable: {embedding_path}"
        ) from exc

    _console(f"[AgentPlugin] Embedding ready: {embedding_path}")
    logger.info(
        "Agent embedding download completed: model=%s, saved_to=%s",
        model_name,
        embedding_path,
    )
    return embedding_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download or refresh the local embedding model used by the agent plugin.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh the embedding files even if the target directory already exists.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    path = ensure_agent_embedding_ready(force=args.force)
    _console(f"[AgentPlugin] Done: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
