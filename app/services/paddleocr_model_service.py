from __future__ import annotations

import logging
import os
import time

from app.core.config import GlobalConfig
from app.scripts.download_paddleocr_models import ensure_paddleocr_models_ready


logger = logging.getLogger(__name__)


def _console(text: str) -> None:
    print(text, flush=True)


def _console_banner(title: str) -> None:
    _console("=" * 80)
    _console(title)
    _console("=" * 80)


def warmup_paddleocr_models() -> None:
    if not GlobalConfig.PADDLEOCR_ENABLED:
        _console("[PaddleOCR] PADDLEOCR_ENABLED=false, skip warmup")
        return

    started = time.perf_counter()
    _console("")
    _console_banner("[Startup] PaddleOCR Warmup Start")
    try:
        ensure_paddleocr_models_ready(
            skip_if_disabled=True,
            allow_download=not os.getenv("DOCKER_DEPLOYMENT"),
        )
    except Exception as exc:
        _console_banner(f"[Startup] PaddleOCR Warmup Skipped: {exc}")
        logger.warning("PaddleOCR warmup skipped due to error: %s", exc, exc_info=True)
        return

    elapsed = time.perf_counter() - started
    _console_banner(f"[Startup] PaddleOCR Warmup Done ({elapsed:.2f}s)")
    logger.info(
        "PaddleOCR warmup finished: lang=%s, cls=%s, structure=%s",
        GlobalConfig.PADDLEOCR_LANG,
        GlobalConfig.PADDLEOCR_USE_ANGLE_CLS,
        GlobalConfig.PADDLEOCR_ENABLE_STRUCTURE,
    )
