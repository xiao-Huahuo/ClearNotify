from __future__ import annotations

import argparse
import inspect
import logging
from pathlib import Path

from app.core.config import GlobalConfig


logger = logging.getLogger(__name__)


def _console(text: str) -> None:
    print(text, flush=True)


def _console_banner(title: str) -> None:
    _console("=" * 80)
    _console(title)
    _console("=" * 80)


def _resolve_structure_factory() -> tuple[object | None, str | None]:
    try:
        from paddleocr import PPStructure  # type: ignore

        return PPStructure, "PPStructure"
    except Exception as first_exc:
        try:
            from paddleocr import PPStructureV3  # type: ignore

            return PPStructureV3, "PPStructureV3"
        except Exception:
            logger.info("PaddleOCR structure factory is unavailable: %s", first_exc)
            return None, None


def resolve_paddleocr_model_paths() -> dict[str, Path]:
    return {
        "base": Path(str(GlobalConfig.PADDLEOCR_MODELS_DIR)),
        "det": Path(str(GlobalConfig.PADDLEOCR_DET_MODEL_DIR)),
        "rec": Path(str(GlobalConfig.PADDLEOCR_REC_MODEL_DIR)),
        "cls": Path(str(GlobalConfig.PADDLEOCR_CLS_MODEL_DIR)),
        "layout": Path(str(GlobalConfig.PADDLEOCR_LAYOUT_MODEL_DIR)),
        "table": Path(str(GlobalConfig.PADDLEOCR_TABLE_MODEL_DIR)),
    }


def _path_has_model_files(path: Path) -> bool:
    return path.exists() and any(item.is_file() for item in path.rglob("*"))


def _required_model_keys() -> list[str]:
    keys = ["det", "rec"]
    if GlobalConfig.PADDLEOCR_USE_ANGLE_CLS:
        keys.append("cls")
    structure_factory, _ = _resolve_structure_factory() if GlobalConfig.PADDLEOCR_ENABLE_STRUCTURE else (None, None)
    if GlobalConfig.PADDLEOCR_ENABLE_STRUCTURE and structure_factory is not None:
        keys.extend(["layout", "table"])
    return keys


def _all_required_models_ready(paths: dict[str, Path]) -> bool:
    return all(_path_has_model_files(paths[key]) for key in _required_model_keys())


def _filter_supported_kwargs(factory, kwargs: dict[str, object]) -> dict[str, object]:
    try:
        parameters = inspect.signature(factory).parameters
    except (TypeError, ValueError):
        return kwargs
    supported = set(parameters.keys())
    accepts_var_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    passthrough_kwargs = {"enable_mkldnn", "enable_hpi", "device", "cpu_threads"}
    return {
        key: value
        for key, value in kwargs.items()
        if value is not None and (key in supported or (accepts_var_kwargs and key in passthrough_kwargs))
    }


def ensure_paddleocr_models_ready(
    force: bool = False,
    skip_if_disabled: bool = False,
    allow_download: bool = True,
) -> dict[str, Path]:
    paths = resolve_paddleocr_model_paths()

    if skip_if_disabled and not GlobalConfig.PADDLEOCR_ENABLED:
        _console("[PaddleOCR] PADDLEOCR_ENABLED=false, skip model prepare")
        return paths

    if _all_required_models_ready(paths) and not force:
        _console(f"[PaddleOCR] Models already exist: {paths['base']}")
        return paths

    if not allow_download:
        raise RuntimeError(
            "PaddleOCR models are missing. Run `python -m app.scripts.download_paddleocr_models` "
            "before starting Docker."
        )

    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:
        _console(f"[PaddleOCR] Import failed: {exc}")
        raise RuntimeError(
            "PaddleOCR is unavailable. Install paddleocr and paddlepaddle first."
        ) from exc

    action = "Refreshing" if force else "Downloading"
    _console(f"[PaddleOCR] {action} models into: {paths['base']}")
    logger.info(
        "Preparing PaddleOCR models: base=%s, lang=%s, cls=%s, structure=%s, force=%s",
        paths["base"],
        GlobalConfig.PADDLEOCR_LANG,
        GlobalConfig.PADDLEOCR_USE_ANGLE_CLS,
        GlobalConfig.PADDLEOCR_ENABLE_STRUCTURE,
        force,
    )

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    def _build_ocr_kwargs(use_angle_cls: bool) -> dict[str, object]:
        return _filter_supported_kwargs(PaddleOCR, {
            "lang": GlobalConfig.PADDLEOCR_LANG,
            "use_angle_cls": use_angle_cls,
            "use_textline_orientation": use_angle_cls,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "enable_mkldnn": False,
            "det_model_dir": str(paths["det"]),
            "rec_model_dir": str(paths["rec"]),
            "cls_model_dir": str(paths["cls"]),
            "show_log": False,
        })

    try:
        PaddleOCR(**_build_ocr_kwargs(GlobalConfig.PADDLEOCR_USE_ANGLE_CLS))
    except Exception as exc:
        if not GlobalConfig.PADDLEOCR_USE_ANGLE_CLS:
            raise
        _console("[PaddleOCR] Base OCR warmup with angle classification failed, retry without it.")
        logger.warning("Base PaddleOCR warmup with angle classification failed: %s", exc, exc_info=True)
        PaddleOCR(**_build_ocr_kwargs(False))

    if GlobalConfig.PADDLEOCR_ENABLE_STRUCTURE:
        structure_factory, structure_name = _resolve_structure_factory()
        if structure_factory is None:
            _console(
                "[PaddleOCR] Structured OCR API is unavailable in the installed paddleocr package. "
                "Skip structure model prepare and continue with base OCR."
            )
            logger.warning(
                "Structured PaddleOCR warmup skipped because neither PPStructure nor PPStructureV3 "
                "is available in the installed package."
            )
        else:
            structure_kwargs = _filter_supported_kwargs(structure_factory, {
                "lang": GlobalConfig.PADDLEOCR_LANG,
                "use_angle_cls": GlobalConfig.PADDLEOCR_USE_ANGLE_CLS,
                "det_model_dir": str(paths["det"]),
                "rec_model_dir": str(paths["rec"]),
                "cls_model_dir": str(paths["cls"]),
                "layout_model_dir": str(paths["layout"]),
                "table_model_dir": str(paths["table"]),
                "show_log": False,
            })
            structure_factory(**structure_kwargs)
            logger.info("Structured PaddleOCR warmup completed with %s.", structure_name)

    _console(f"[PaddleOCR] Models ready: {paths['base']}")
    logger.info("PaddleOCR model prepare completed: base=%s", paths["base"])
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download or refresh local PaddleOCR models used by the backend OCR pipeline.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh model directories even if they already exist.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _console("")
    _console_banner("[Startup] PaddleOCR Model Prepare Start")
    paths = ensure_paddleocr_models_ready(force=args.force)
    _console_banner(f"[Startup] PaddleOCR Model Prepare Done: {paths['base']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
