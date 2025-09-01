import re
import logging
from utils.config import logger_name
from typing import List, Tuple

logger = logging.getLogger(logger_name)

def markdown_to_ascii_table(markdown_table: str) -> str:
    """
    Convertit un tableau Markdown en tableau ASCII
    """
    try:
        lines = [line.strip() for line in markdown_table.strip().split('\n') if line.strip()]
        if len(lines) < 2:
            return markdown_table
        
        # Parse les lignes du tableau
        rows = []
        separator_index = -1
        
        for i, line in enumerate(lines):
            if line.startswith('|') and line.endswith('|'):
                # Vérifie si c'est une ligne de séparation
                if re.match(r'^\|[\s\-\:\|]*\|$', line):
                    separator_index = i
                    continue
                
                # Enlève les | du début et de la fin, puis split
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                rows.append(cells)
        
        if not rows or separator_index == -1:
            return markdown_table
        
        # Calcule la largeur de chaque colonne
        max_cols = max(len(row) for row in rows) if rows else 0
        col_widths = [0] * max_cols
        
        for row in rows:
            for i, cell in enumerate(row):
                if i < max_cols:
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # Assure une largeur minimale
        col_widths = [max(3, width) for width in col_widths]
        
        # Génère le tableau ASCII
        ascii_lines = []
        
        # Ligne de séparation supérieure
        top_line = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
        ascii_lines.append(top_line)
        
        # En-tête (première ligne)
        if rows:
            header_cells = rows[0] + [""] * (max_cols - len(rows[0]))
            header_row = "|" + "|".join(f" {cell:<{col_widths[i]}} " for i, cell in enumerate(header_cells)) + "|"
            ascii_lines.append(header_row)
            
            # Ligne de séparation après l'en-tête
            sep_line = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
            ascii_lines.append(sep_line)
        
        # Lignes de données (à partir de la deuxième ligne)
        for row in rows[1:]:
            # Pad les cellules manquantes
            padded_row = row + [""] * (max_cols - len(row))
            data_row = "|" + "|".join(f" {cell:<{col_widths[i]}} " for i, cell in enumerate(padded_row)) + "|"
            ascii_lines.append(data_row)
        
        # Ligne de séparation inférieure
        ascii_lines.append(top_line)
        
        return "\n".join(ascii_lines)
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion du tableau: {e}")
        return markdown_table

def detect_and_convert_tables(text: str) -> str:
    """
    Détecte et convertit tous les tableaux Markdown dans un texte
    """
    try:
        lines = text.split('\n')
        result_lines = []
        i = 0
        in_code_block = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Vérifie si on entre ou sort d'un bloc de code
            if line.startswith('```'):
                in_code_block = not in_code_block
                result_lines.append(lines[i])
                i += 1
                continue
            
            # Ignore les tableaux à l'intérieur des blocs de code
            if in_code_block:
                result_lines.append(lines[i])
                i += 1
                continue
            
            # Détecte le début d'un tableau (ligne avec des |)
            if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
                # Cherche la fin du tableau
                table_lines = [lines[i]]
                j = i + 1
                
                # Cherche la ligne de séparation
                separator_found = False
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('|') and next_line.endswith('|'):
                        table_lines.append(lines[j])
                        if re.match(r'^\|[\s\-\:\|]*\|$', next_line):
                            separator_found = True
                        j += 1
                    else:
                        break
                
                # Convertit le tableau s'il est valide
                if len(table_lines) >= 2 and separator_found:
                    table_text = '\n'.join(table_lines)
                    ascii_table = markdown_to_ascii_table(table_text)
                    result_lines.append(f"```\n{ascii_table}\n```")
                    i = j
                else:
                    result_lines.append(lines[i])
                    i += 1
            else:
                result_lines.append(lines[i])
                i += 1
        
        return '\n'.join(result_lines)

    except Exception as e:
        logger.error(f"Erreur lors de la détection des tableaux: {e}")
        return text