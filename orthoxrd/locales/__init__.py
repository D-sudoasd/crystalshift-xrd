"""Locale message catalogs for CrystalShift XRD."""

from orthoxrd.locales.en import EN_HELP, EN_TEXT
from orthoxrd.locales.zh import ZH_HELP, ZH_TEXT

TEXT = {"zh": ZH_TEXT, "en": EN_TEXT}
HELP = {"zh": ZH_HELP, "en": EN_HELP}

__all__ = ["HELP", "TEXT"]
