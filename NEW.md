# TODO

## Structure du dossier utils

utils/
    discord_utils/
        smart_long_messages()
        send_text_chunks()
        send_code_blocks()
        process_attachements()
        send_audio_message()
    image_utils/
        image_gen.py
    files_utils/
        markdown_converter.py
        table_converter.py
        audio_process()
    api_utils/
        status.py
    database_utils/
        database.py
        server_config.py
        user_config.py
        user_manager.py
    ai_utils/
        ai_mod.py
        memory.py
    web_utils/
        crawl_website()
        perform_web_research()
        get_sources()
    tools_utils/
        image_tool()
        web_tool()
    config_utils/
        config.py
    logger_utils/
        logger_utils.py
    lang_utils/
        get_lang()

## Commandes

`/status`
`/set-model` (text_model=Llama 3.3 70b, image_model=Flux Schnell)
`/models-list` (list=image/text)
`/set-language` (lang=EN/FR)
`/daily-usage`
`/personnal-preprompt` (preprompt)
`/audio-gen` (audio-gen=enable/disable)
`/ping`
`/config` [permission: manage server] :
(allow-images - allow-user-preprompt - allow-audios - edit-system-prompt - announcements-channel - announcements-language)
`/tier`
`/support`
`/help`
`/image-gen`
`/install`
`/uninstall`
`/ask-ai`
`/contact-developer`
`/api-key`

recois le message => vérifie que le message n'est pas vide => enlève la mention => extrait les paramètres => extrait les pièces jointes, les liens et les images => vérifie si la génération audio est activée + le modèle => envoie une requete au modele correspondant => recois la réponse => découpe la réponse en paragraphes => ajoute des réactions : 🔄 (régénère la réponse) / ❌ (supprime) / ⚙️ (envoie un embed avec les infos supplémentaires) / ⭐️ (envoie un embed avec des boutons pour noter le résultat) / ✏️ (édite la question puis régénère la réponse) / ⏮️/⏭️ (pagination si plusieurs régénérations) / ✂️ (résume le texte généré)