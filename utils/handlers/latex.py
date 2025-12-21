import io
import logging
import re
import urllib.parse

import cairosvg
import requests

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

LATEX_TO_EMOJI = {
    # Greek lowercase
    r'\alpha': 'α',
    r'\beta': 'β',
    r'\gamma': 'γ',
    r'\delta': 'δ',
    r'\epsilon': 'ε',
    r'\zeta': 'ζ',
    r'\eta': 'η',
    r'\theta': 'θ',
    r'\iota': 'ι',
    r'\kappa': 'κ',
    r'\lambda': 'λ',
    r'\mu': 'μ',
    r'\nu': 'ν',
    r'\xi': 'ξ',
    r'\pi': 'π',
    r'\rho': 'ρ',
    r'\sigma': 'σ',
    r'\tau': 'τ',
    r'\upsilon': 'υ',
    r'\phi': 'φ',
    r'\chi': 'χ',
    r'\psi': 'ψ',
    r'\omega': 'ω',
    # Greek uppercase
    r'\Gamma': 'Γ',
    r'\Delta': 'Δ',
    r'\Theta': 'Θ',
    r'\Lambda': 'Λ',
    r'\Xi': 'Ξ',
    r'\Pi': 'Π',
    r'\Sigma': 'Σ',
    r'\Upsilon': 'Υ',
    r'\Phi': 'Φ',
    r'\Psi': 'Ψ',
    r'\Omega': 'Ω',
    # Operators
    r'\sum': '∑',
    r'\prod': '∏',
    r'\int': '∫',
    r'\oint': '∮',
    r'\partial': '∂',
    r'\nabla': '∇',
    r'\infty': '∞',
    r'\emptyset': '∅',
    r'\forall': '∀',
    r'\exists': '∃',
    r'\notin': '∉',
    r'\subset': '⊂',
    r'\supset': '⊃',
    r'\subseteq': '⊆',
    r'\supseteq': '⊇',
    r'\cap': '∩',
    r'\cup': '∪',
    r'\setminus': '∖',
    r'\times': '×',
    r'\div': '÷',
    r'\pm': '±',
    r'\mp': '∓',
    r'\cdot': '⋅',
    r'\circ': '∘',
    r'\bullet': '•',
    r'\star': '⋆',
    r'\diamond': '⋄',
    r'\triangle': '△',
    r'\square': '□',
    r'\bigcirc': '○',
    r'\bigtriangleup': '△',
    r'\bigtriangledown': '▽',
    # Arrows
    r'\leftarrow': '←',
    r'\rightarrow': '→',
    r'\uparrow': '↑',
    r'\downarrow': '↓',
    r'\Leftarrow': '⇐',
    r'\Rightarrow': '⇒',
    r'\Uparrow': '⇑',
    r'\Downarrow': '⇓',
    r'\leftrightarrow': '↔',
    r'\Leftrightarrow': '⇔',
    r'\mapsto': '↦',
    r'\hookleftarrow': '↩',
    r'\hookrightarrow': '↪',
    r'\leftharpoonup': '↼',
    r'\leftharpoondown': '↽',
    r'\rightharpoonup': '⇀',
    r'\rightharpoondown': '⇁',
    # Relations
    r'\leq': '≤',
    r'\geq': '≥',
    r'\neq': '≠',
    r'\approx': '≈',
    r'\equiv': '≡',
    r'\cong': '≅',
    r'\sim': '∼',
    r'\simeq': '≃',
    r'\propto': '∝',
    r'\perp': '⊥',
    r'\parallel': '∥',
    r'\asymp': '≍',
    r'\doteq': '≐',
    # Miscellaneous
    r'\cdots': '⋯',
    r'\vdots': '⋮',
    r'\ddots': '⋱',
    r'\hbar': 'ℏ',
    r'\ell': 'ℓ',
    r'\wp': '℘',
    r'\Re': 'ℜ',
    r'\Im': 'ℑ',
    r'\aleph': 'ℵ',
    r'\beth': 'ℶ',
    r'\gimel': 'ℷ',
    r'\daleth': 'ℸ',
}

LATEX_PATTERN = re.compile(
    # fenced code blocks explicitly labeled as latex/tex
    r'```(?:latex|tex)[^\`]*?```|'
    # full LaTeX environments
    r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}|'
    # display math with double dollars
    r'\$\$[\s\S]*?\$\$|'
    # \\\[ ... \\\] display math
    r'\\\[[\s\S]*?\\\]|'
    # inline math with single dollars (avoid matching $$ by requiring not $$ start)
    r'\$[^$][\s\S]*?\$|'
    # common LaTeX environments/commands
    r'\\(?:begin|end)\{(?:equation|align|gather|multline)\*?\}|'
    r'\\frac\{.*?\}\{.*?\}|'
    r'\\sqrt\{.*?\}|'
    r'\\text\{.*?\}|'
    r'\\[a-zA-Z]+'
, flags=re.DOTALL)


def latex_to_svg(formula: str) -> bytes:
    """Récupère le SVG d'une formule LaTeX via math.vercel.app."""
    try:
        encoded = urllib.parse.quote(formula, safe='')
        url = f"https://math.vercel.app?color=white&from={encoded}.svg"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to fetch SVG for LaTeX: {e}")
        raise


def svg_to_png(svg_data: bytes, output_width: int = 400) -> bytes:
    """Convertit des octets SVG en octets PNG."""
    try:
        # Utilisez le paramètre scale pour réduire la taille globale de l'image (ex: 0.5 = moitié, 1 = taille normale)
        # Pour ajuster le facteur de réduction, modifiez la valeur de scale ci-dessous
        return cairosvg.svg2png(bytestring=svg_data, scale=1)
    except Exception as e:
        logger.error(f"Failed to convert SVG to PNG: {e}")
        raise


def convert_latex_to_png(latex: str) -> tuple[io.BytesIO | str, bool]:
    """
    Convert LaTeX string to PNG image using math.vercel.app API.
    
    Args:
        latex (str): The LaTeX formula to convert
        
    Returns:
        tuple: (buffer or error message, success boolean)
    """
    try:
        # Clean the latex string
        latex = latex.strip()
        
        # Handle fenced code blocks
        if latex.startswith('```') and latex.endswith('```'):
            lines = latex.split('\n')
            if len(lines) >= 3 and lines[-1] == '```':
                latex = '\n'.join(lines[1:-1])
            else:
                return "Invalid fenced code block", False
        
        # Remove $ if present for the API
        if latex.startswith('$') and latex.endswith('$'):
            latex = latex[1:-1]

        # Remove $$ if present for the API
        if latex.startswith('$$') and latex.endswith('$$'):
            latex = latex[2:-2]
        
        # Remove \[ \] if present
        if latex.startswith(r'\[') and latex.endswith(r'\]'):
            latex = latex[2:-2]
        
        # Get SVG from API
        svg_bytes = latex_to_svg(latex)
        
        # Convert to PNG sans fixer la largeur, pour garder une taille de police stable
        png_bytes = svg_to_png(svg_bytes)
        
        # Return as BytesIO
        buffer = io.BytesIO(png_bytes)
        buffer.seek(0)
        return buffer, True
        
    except Exception as e:
        logger.error(f"LaTeX conversion failed: {e}")
        # For LaTeX that can't be rendered, return the LaTeX as text
        return f"```\n${latex}$\n```", True


def detect_latex(text: str) -> list[str]:
    """
    Detect LaTeX expressions in text.
    
    Args:
        text (str): The text to search for LaTeX
        
    Returns:
        list: List of LaTeX expressions found
    """
    return LATEX_PATTERN.findall(text)