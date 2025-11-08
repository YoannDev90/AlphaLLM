import json
import logging
from utils.config.app_config import LOGGER_NAME, DEBUG
from utils.database.client import get_supabase_client

logger = logging.getLogger(LOGGER_NAME)
supabase = get_supabase_client()

def get_announce_channel(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['announce_channel']
        else:
            logger.warning(f"Aucun salon d'annonces pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du salon d'annonces pour {server_id} : {str(e)}")
        return None
    
def get_guild_language(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['lang']
        else:
            logger.warning(f"Aucun paramètre de langue pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre de langue pour {server_id} : {str(e)}")
        return None
    
def get_allow_images(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['allow_images']
        else:
            logger.warning(f"Aucun paramètre \"allow_images\" pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre \"allow_images\" pour {server_id} : {str(e)}")
        return None
    
def get_allow_user_preprompt(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['allow_user_preprompt']
        else:
            logger.warning(f"Aucun paramètre \"allow_user_preprompt\" pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre \"allow_user_preprompt\" pour {server_id} : {str(e)}")
        return None

def get_allow_audios(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['allow_audios']
        else:
            logger.warning(f"Aucun paramètre \"allow_audios\" pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre \"allow_audios\" pour {server_id} : {str(e)}")
        return None

def get_guild_system_prompt(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['guild_system_prompt']
        else:
            logger.warning(f"Aucun prompt système pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du prompt système pour {server_id} : {str(e)}")
        return None

def get_allowed_channels(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['allowed_channels']
        else:
            logger.warning(f"Aucun salon autorisé pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des salons autorisés pour {server_id} : {str(e)}")
        return None

def get_forbidden_roles(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['forbidden_roles']
        else:
            logger.warning(f"Aucun rôle interdit pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des rôles interdits pour {server_id} : {str(e)}")
        return None

# Fonctions de mise à jour/création
def set_server_setting(server_id, field, value):
    try:
        # Vérifier si l'enregistrement existe
        response = supabase.table("server_settings").select("id_discord").eq("id_discord", server_id).execute()
        
        if response.data:
            # Mise à jour
            result = supabase.table("server_settings").update({field: value}).eq("id_discord", server_id).execute()
            logger.info(f"Paramètre {field} mis à jour pour le serveur {server_id}.")
        else:
            # Création
            result = supabase.table("server_settings").insert({"id_discord": server_id, field: value}).execute()
            logger.info(f"Nouveau paramètre {field} créé pour le serveur {server_id}.")
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du paramètre {field} pour {server_id} : {str(e)}")
        return False

def create_server_settings(server_id, owner_id=None, announce_channel=None, lang='EN', 
                          guild_name=None, owner_name=None, allow_images=None, 
                          allow_user_preprompt=None, allow_audios=None, 
                          guild_system_prompt=None, allowed_channels=None, 
                          forbidden_roles=None):
    try:
        data = {
            "id_discord": server_id,
            "owner_id": owner_id,
            "announce_channel": announce_channel,
            "lang": lang,
            "guild_name": guild_name,
            "owner_name": owner_name,
            "allow_images": allow_images,
            "allow_user_preprompt": allow_user_preprompt,
            "allow_audios": allow_audios,
            "guild_system_prompt": guild_system_prompt,
            "allowed_channels": allowed_channels,
            "forbidden_roles": forbidden_roles
        }
        
        result = supabase.table("server_settings").insert(data).execute()
        logger.info(f"Paramètres du serveur créés pour {server_id}.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création des paramètres du serveur {server_id} : {str(e)}")
        return False

def update_server_settings(server_id, **kwargs):
    try:
        result = supabase.table("server_settings").update(kwargs).eq("id_discord", server_id).execute()
        logger.info(f"Paramètres du serveur mis à jour pour {server_id}.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres du serveur {server_id} : {str(e)}")
        return False

def delete_server_settings(server_id):
    try:
        result = supabase.table("server_settings").delete().eq("id_discord", server_id).execute()
        logger.info(f"Paramètres du serveur supprimés pour {server_id}.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des paramètres du serveur {server_id} : {str(e)}")
        return False

def get_all_server_settings(server_id):
    try:
        response = supabase.table("server_settings").select("*").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]
        else:
            logger.warning(f"Aucun paramètre trouvé pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de tous les paramètres pour {server_id} : {str(e)}")
        return None

async def update_all_guilds_info(bot):
    """
    Parcourt tous les serveurs du bot et met à jour les informations dans la base de données.
    Supprime également les enregistrements de serveurs qui n'existent plus.
    """

    if DEBUG:
        return

    updated_count = 0
    created_count = 0
    deleted_count = 0
    error_count = 0
    
    logger.info(f"Démarrage de la mise à jour des informations pour {len(bot.guilds)} serveurs...")
    
    # retrieve tous les serveurs présents dans la base de données
    try:
        db_response = supabase.table("server_settings").select("id_discord").execute()
        db_guild_ids = {row['id_discord'] for row in db_response.data} if db_response.data else set()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des serveurs de la base de données : {str(e)}")
        db_guild_ids = set()
    
    # retrieve les IDs des serveurs actuels du bot
    current_guild_ids = {guild.id for guild in bot.guilds}
    
    # Mettre à jour/create les serveurs actuels
    for guild in bot.guilds:
        try:
            # retrieve les informations du serveur
            guild_id = guild.id
            guild_name = guild.name
            join_timestamp = guild.me.joined_at.isoformat() if guild.me.joined_at else None
            owner_name = None
            
            # retrieve le nom du propriétaire de manière plus robuste
            if guild.owner:
                owner_name = guild.owner.name  # Utiliser .name au lieu de .display_name
            elif guild.owner_id:
                # if we n'a pas l'objet owner mais qu'on a l'ID, essayer de le retrieve
                try:
                    owner = await bot.fetch_user(guild.owner_id)
                    owner_name = owner.name if owner else None
                except:
                    owner_name = None
            
            # Vérifier si l'enregistrement existe déjà
            response = supabase.table("server_settings").select("id_discord").eq("id_discord", guild_id).execute()
            
            if response.data:
                # Mise à jour de l'enregistrement existant
                update_data = {
                    "guild_name": guild_name,
                    "owner_name": owner_name,
                    "bot_join": join_timestamp
                }
                
                result = supabase.table("server_settings").update(update_data).eq("id_discord", guild_id).execute()
                logger.debug(f"Serveur mis à jour: {guild_name} (ID: {guild_id}) - Owner: {owner_name}")
                updated_count += 1
            else:
                # Création d'un nouvel enregistrement
                new_data = {
                    "id_discord": guild_id,
                    "guild_name": guild_name,
                    "owner_name": owner_name,
                    "bot_join": join_timestamp,
                    "lang": "EN"  # Valeur par défaut
                }
                
                result = supabase.table("server_settings").insert(new_data).execute()
                logger.info(f"Nouveau serveur créé: {guild_name} (ID: {guild_id}) - Owner: {owner_name}")
                created_count += 1
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du serveur {guild.name} (ID: {guild.id}) : {str(e)}")
            error_count += 1
    
    # delete les serveurs qui ne sont plus dans la liste du bot
    servers_to_delete = db_guild_ids - current_guild_ids
    
    for guild_id_to_delete in servers_to_delete:
        try:
            result = supabase.table("server_settings").delete().eq("id_discord", guild_id_to_delete).execute()
            logger.info(f"Serveur supprimé de la base de données: ID {guild_id_to_delete}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du serveur {guild_id_to_delete} : {str(e)}")
            error_count += 1
    
    logger.info(f"Mise à jour terminée - Mis à jour: {updated_count}, Créés: {created_count}, Supprimés: {deleted_count}, Erreurs: {error_count}")
    return {
        "updated": updated_count,
        "created": created_count,
        "deleted": deleted_count,
        "errors": error_count,
        "total": len(bot.guilds)
    }