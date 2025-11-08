import re
import textwrap
import logging
from utils.config.app_config import logger_name
from typing import List, Tuple

logger = logging.getLogger(logger_name)

def clean_cell_content(cell: str) -> str:
    """
    Nettoie le contenu d'une cellule : supprime markdown, HTML et émojis
    """
    # delete le formatage markdown **gras**
    cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cell)
    
    # Remplacer <br> par des sauts de ligne
    cell = re.sub(r'<br\s*/?>', '\n', cell, flags=re.IGNORECASE)
    
    # delete les autres balises HTML
    cell = re.sub(r'<[^>]+>', '', cell)
    
    # delete les émojis (caractères Unicode dans les plages d'émojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # dingbats
        "\U0001f926-\U0001f937"  # gestures
        "\U00010000-\U0010ffff"  # other unicode
        "\u2640-\u2642"  # gender symbols
        "\u2600-\u2B55"  # misc symbols
        "\u200d"  # zero width joiner
        "\u23cf"  # eject symbol
        "\u23e9"  # fast forward
        "\u231a"  # watch
        "\ufe0f"  # variation selector
        "\u3030"  # wavy dash
        "]+",
        flags=re.UNICODE
    )
    cell = emoji_pattern.sub('', cell)
    
    # Normaliser les espaces : remplacer les espaces multiples par un seul espace
    cell = re.sub(r'\s+', ' ', cell)
    
    return cell.strip()

def markdown_to_ascii_table(markdown_table: str, max_line_length: int = 100) -> str:
    """
    Convertit un tableau Markdown en tableau ASCII avec optimisation de la largeur des colonnes
    """
    try:
        # Étape 1: parse les lignes du tableau markdown
        lines = [line.strip() for line in markdown_table.strip().split('\n') if line.strip()]
        if len(lines) < 2:
            return markdown_table
        
        rows = []
        separator_index = -1
        
        # Étape 2: Extraire les cellules nettoyées de chaque ligne
        for i, line in enumerate(lines):
            if line.startswith('|') and line.endswith('|'):
                if re.match(r'^\|[\s\-\:\|]*\|$', line):
                    separator_index = i
                    continue
                
                cells = [clean_cell_content(cell.strip()) for cell in line[1:-1].split('|')]
                rows.append(cells)
        
        if not rows or separator_index == -1:
            return markdown_table
        
        # Étape 3: Calculer le nombre maximum de colonnes
        max_cols = max(len(row) for row in rows) if rows else 0
        
        # Étape 4: Calculer la largeur naturelle de chaque colonne (sans limite)
        # Liste qui stocke la largeur optimale de chaque colonne
        natural_col_widths = [0] * max_cols
        for row in rows:
            for i, cell in enumerate(row):
                if i < max_cols:
                    # Pour les cellules multi-lignes (avec \n), prendre la largeur de la ligne la plus longue
                    cell_lines = cell.split('\n')
                    max_line_width = max(len(line) for line in cell_lines) if cell_lines else 0
                    natural_col_widths[i] = max(natural_col_widths[i], max_line_width)
        
        # Étape 5: Calculer la largeur totale naturelle du tableau
        total_natural_width = sum(natural_col_widths) + (3 * max_cols) + 1  # +3 par colonne pour "| " et " |", +1 pour le dernier "|"
        
        # Étape 6: if the tableau dépasse la largeur max, redistribuer l'espace proportionnellement
        if total_natural_width > max_line_length:
            # Calculer le ratio de réduction
            available_width = max_line_length - (3 * max_cols) - 1  # largeur disponible pour le contenu
            total_natural_content_width = sum(natural_col_widths)
            
            if total_natural_content_width > 0:
                ratio = available_width / total_natural_content_width
                col_widths = [max(1, int(width * ratio)) for width in natural_col_widths]
            else:
                col_widths = [1] * max_cols
        else:
            # Utiliser les largeurs naturelles if the tableau tient
            col_widths = natural_col_widths
        
        # Étape 7: Générer les lignes ASCII du tableau
        ascii_lines = []
        
        # Ligne supérieure
        top_line = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
        ascii_lines.append(top_line)
        
        # En-tête (première ligne en majuscules, avec wrapping possible)
        if rows:
            header_cells = [cell.upper() for cell in rows[0]] + [""] * (max_cols - len(rows[0]))
            
            # Préparer les headers wrappés selon la largeur de leur colonne
            wrapped_headers = []
            for i, cell in enumerate(header_cells):
                if i < len(col_widths):
                    # Wrapper le header selon la largeur calculée pour cette colonne
                    wrapped = textwrap.wrap(cell, width=col_widths[i])
                    wrapped_headers.append(wrapped if wrapped else [cell])
                else:
                    wrapped_headers.append([cell])
            
            # Déterminer le nombre maximum de lignes pour les headers
            max_header_wrap = max(len(w) for w in wrapped_headers) if wrapped_headers else 1
            
            # Générer chaque sous-ligne des headers
            for i in range(max_header_wrap):
                header_sub_row = [w[i] if i < len(w) else '' for w in wrapped_headers]
                header_padded_row = header_sub_row + [""] * (max_cols - len(header_sub_row))
                header_row = "|" + "|".join(f" {cell:<{col_widths[j]}} " for j, cell in enumerate(header_padded_row)) + "|"
                ascii_lines.append(header_row)
            
            # Ligne de séparation
            sep_line = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
            ascii_lines.append(sep_line)
        
        # Corps du tableau (lignes de données)
        for row in rows[1:]:
            # Préparer les cellules wrappées selon la largeur de leur colonne
            wrapped_cells = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    # Wrapper le contenu selon la largeur calculée pour cette colonne
                    wrapped = textwrap.wrap(cell, width=col_widths[i])
                    wrapped_cells.append(wrapped if wrapped else [cell])
                else:
                    wrapped_cells.append([cell])
            
            # Déterminer le nombre maximum de lignes pour cette rangée
            max_wrap = max(len(w) for w in wrapped_cells) if wrapped_cells else 1
            
            # Générer chaque sous-ligne de la rangée
            for i in range(max_wrap):
                sub_row = [w[i] if i < len(w) else '' for w in wrapped_cells]
                padded_sub_row = sub_row + [""] * (max_cols - len(sub_row))
                data_row = "|" + "|".join(f" {cell:<{col_widths[j]}} " for j, cell in enumerate(padded_sub_row)) + "|"
                ascii_lines.append(data_row)
            
            # add la ligne de séparation après chaque rangée de données
            ascii_lines.append(sep_line)
                
        return "\n".join(ascii_lines)
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion du tableau: {e}")
        return markdown_table

def detect_and_convert_tables(text: str, max_line_length: int = 100) -> str:
    """
    Détecte et convertit tous les tableaux Markdown en tableaux ASCII dans le texte
    """
    try:
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.strip().startswith('|') and line.strip().endswith('|'):
                table_lines = []
                start_i = i
                
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                
                if len(table_lines) >= 2:
                    markdown_table = '\n'.join(table_lines)
                    ascii_table = markdown_to_ascii_table(markdown_table, max_line_length)
                    result_lines.append(f"```\n{ascii_table}\n```")
                else:
                    result_lines.extend(table_lines)
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection et conversion des tableaux: {e}")
        return text