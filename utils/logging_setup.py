import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Configuration du logging pour l'historique
    history_logger = logging.getLogger('HistoryLogger')
    history_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('history-logs.txt', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    history_logger.addHandler(file_handler)

    # Configuration du logging pour les commandes
    cmd_logger = logging.getLogger('CommandLogger')
    cmd_logger.setLevel(logging.INFO)
    cmd_file_handler = logging.FileHandler('cmd-logs.txt', encoding='utf-8')
    cmd_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    cmd_logger.addHandler(cmd_file_handler)

    # Configuration du logging pour les erreurs
    error_logger = logging.getLogger('ErrorLogger')
    error_logger.setLevel(logging.ERROR)
    error_file_handler = logging.FileHandler('errors-logs.txt', encoding='utf-8')
    error_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(error_file_handler)
