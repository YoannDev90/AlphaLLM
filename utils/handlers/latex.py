"""Helpers for detecting and rendering LaTeX content."""

import io
import logging
import re
import urllib.parse

import requests

from utils.logger import get_logger

# Note: cairosvg might need installation: pip install cairosvg
try:
    import cairosvg
except ImportError:
    cairosvg = None

logger = get_logger()

LATEX_TO_EMOJI = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\zeta": "ζ",
    r"\eta": "η",
    r"\theta": "θ",
    r"\iota": "ι",
    r"\kappa": "κ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\xi": "ξ",
    r"\pi": "π",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\upsilon": "υ",
    r"\phi": "φ",
    r"\chi": "χ",
    r"\psi": "ψ",
    r"\omega": "ω",
    r"\sum": "∑",
    r"\prod": "∏",
    r"\int": "∫",
    r"\infty": "∞",
    r"\neq": "≠",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\approx": "≈",
    r"\times": "×",
    r"\div": "÷",
}

LATEX_PATTERN = re.compile(
    r"```(?:latex|tex)[\s\S]*?```|"
    r"\$\$[\s\S]*?\$\$|"
    r"\\\[[\s\S]*?\\\]|"
    r"\$[^$][\s\S]*?\$",
    flags=re.DOTALL,
)


def latex_to_svg(formula: str) -> bytes:
    """Render a LaTeX formula to SVG bytes.

    Parameters
    ----------
    formula : str
        LaTeX formula to render.

    Returns
    -------
    bytes
        SVG payload bytes.
    """
    encoded = urllib.parse.quote(formula, safe="")
    url = f"https://math.vercel.app?color=white&from={encoded}.svg"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.content


def convert_latex_to_png(latex: str) -> tuple[io.BytesIO | str, bool]:
    """Convert LaTeX to a PNG buffer when possible.

    Parameters
    ----------
    latex : str
        LaTeX content to convert.

    Returns
    -------
    tuple[io.BytesIO | str, bool]
        PNG buffer or fallback text, plus success flag.
    """
    if not cairosvg:
        return f"```\n{latex}\n``` (cairosvg missing)", True
    try:
        svg_bytes = latex_to_svg(latex)
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, scale=2)
        return io.BytesIO(png_bytes), True
    except Exception as e:
        logger.error(f"LaTeX conversion failed: {e}")
        return f"```\n{latex}\n```", True


def detect_latex(text: str) -> list[str]:
    """Find LaTeX fragments in text.

    Parameters
    ----------
    text : str
        Text to inspect.

    Returns
    -------
    list[str]
        List of matched LaTeX fragments.
    """
    return LATEX_PATTERN.findall(text)
