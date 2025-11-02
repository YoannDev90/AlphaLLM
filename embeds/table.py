import discord
import logging
import tempfile
import os
import pandas as pd
import re
from io import BytesIO
from utils.config import logger_name

logger = logging.getLogger(logger_name)

def parse_ascii_table_to_dataframe(ascii_table: str):
    """
    Parse un tableau ASCII généré par table_converter.py en DataFrame pandas
    """
    try:
        lines = [line.strip() for line in ascii_table.strip().split('\n') if line.strip()]
        if len(lines) < 3:
            return None
        
        # Trouver les lignes de données (ignorer les bordures supérieure et inférieure)
        data_lines = []
        for line in lines[1:-1]:  # Ignorer première et dernière ligne
            if '|' in line and not line.replace('|', '').replace('-', '').replace('+', '').strip():
                continue  # Ligne de séparation
            if '|' in line:
                # Extraire les cellules
                parts = line.split('|')
                if len(parts) > 2:  # Au moins | contenu |
                    cells = [part.strip() for part in parts[1:-1]]  # Ignorer premier et dernier |
                    data_lines.append(cells)
        
        if len(data_lines) < 2:  # Au moins header + une ligne de données
            return None
        
        # Première ligne = headers, le reste = données
        headers = data_lines[0]
        data = data_lines[1:]
        
        return pd.DataFrame(data, columns=headers)
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing du tableau ASCII: {e}")
        return None

class FormatSelect(discord.ui.Select):
    def __init__(self, table_data):
        self.table_data = table_data
        options = [
            discord.SelectOption(label="CSV", value="csv", description="Comma-separated values"),
            discord.SelectOption(label="Excel (XLSX)", value="xlsx", description="Microsoft Excel format"),
            discord.SelectOption(label="ODS", value="ods", description="OpenDocument Spreadsheet"),
            discord.SelectOption(label="TSV", value="tsv", description="Tab-separated values"),
            discord.SelectOption(label="JSON", value="json", description="JavaScript Object Notation"),
            discord.SelectOption(label="Markdown", value="md", description="Markdown table format"),
        ]
        super().__init__(placeholder="Choisissez le format d'export", options=options)

    async def callback(self, interaction: discord.Interaction):
        format_type = self.values[0]
        await interaction.response.defer()

        try:
            # Convertir les données du tableau en DataFrame pandas
            if isinstance(self.table_data, str):
                # Vérifier si c'est du markdown ou de l'ASCII
                if self.table_data.strip().startswith('|') and '|' in self.table_data:
                    # C'est du markdown - parser directement
                    lines = [line.strip() for line in self.table_data.strip().split('\n') if line.strip()]
                    if len(lines) < 2:
                        await interaction.followup.send("Erreur: Format de tableau invalide", ephemeral=True)
                        return

                    # Extraire les données
                    data = []
                    headers = None
                    for i, line in enumerate(lines):
                        if line.startswith('|') and line.endswith('|'):
                            cells = [cell.strip() for cell in line[1:-1].split('|')]
                            if i == 0:  # Headers
                                headers = cells
                            elif not re.match(r'^\|[\s\-\:\|]*\|$', line):  # Pas une ligne de séparation
                                data.append(cells)

                    if not headers or not data:
                        await interaction.followup.send("Erreur: Impossible de parser le tableau", ephemeral=True)
                        return

                    df = pd.DataFrame(data, columns=headers)
                else:
                    # C'est probablement de l'ASCII - essayer de le parser
                    df = parse_ascii_table_to_dataframe(self.table_data)
                    if df is None or df.empty:
                        await interaction.followup.send("Erreur: Impossible de parser le tableau ASCII", ephemeral=True)
                        return
            else:
                # Si c'est déjà un DataFrame ou une liste
                df = pd.DataFrame(self.table_data)

            # Générer le fichier selon le format choisi
            buffer = BytesIO()

            if format_type == "csv":
                df.to_csv(buffer, index=False, encoding='utf-8')
                filename = "table.csv"
                mime_type = "text/csv"

            elif format_type == "xlsx":
                df.to_excel(buffer, index=False, engine='openpyxl')
                filename = "table.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif format_type == "ods":
                df.to_excel(buffer, index=False, engine='odf')
                filename = "table.ods"
                mime_type = "application/vnd.oasis.opendocument.spreadsheet"

            elif format_type == "tsv":
                df.to_csv(buffer, index=False, sep='\t', encoding='utf-8')
                filename = "table.tsv"
                mime_type = "text/tab-separated-values"

            elif format_type == "json":
                df.to_json(buffer, orient='records', indent=2, force_ascii=False)
                filename = "table.json"
                mime_type = "application/json"

            elif format_type == "md":
                # Convertir en markdown
                md_content = df.to_markdown(index=False)
                buffer.write(md_content.encode('utf-8'))
                filename = "table.md"
                mime_type = "text/markdown"

            buffer.seek(0)

            # Envoyer le fichier
            file = discord.File(buffer, filename=filename)
            await interaction.followup.send(f"Tableau exporté au format {format_type.upper()}", file=file)

        except Exception as e:
            logger.error(f"Erreur lors de l'export du tableau: {e}")
            await interaction.followup.send(f"Erreur lors de l'export: {str(e)}", ephemeral=True)

class TableView(discord.ui.View):
    def __init__(self, table_data):
        super().__init__()
        self.table_data = table_data

    @discord.ui.button(emoji="💾", label="Export", style=discord.ButtonStyle.gray)
    async def export(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Export de tableau demandé par {interaction.user.display_name}")

        # Créer un modal avec le sélecteur de format
        view = discord.ui.View()
        view.add_item(FormatSelect(self.table_data))

        await interaction.response.send_message("Choisissez le format d'export:", view=view, ephemeral=True)