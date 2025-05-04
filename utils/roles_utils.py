import discord
import os
from supabase import create_client, Client, ClientOptions
import logging

logger = logging.getLogger('AlphaLLM')
url: str = os.environ.get("DB_URL")
key: str = os.environ.get("DB_KEY")
jwt: str = os.environ.get("JWT_KEY")
supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

async def create_role(guild: discord.Guild, role_name: str) -> discord.Role:
    try:
        role = await guild.create_role(name=role_name, reason="Created by AlphaLLM - Do not delete")
        await guild.me.add_roles(role, reason="Assigned to AlphaLLM - Do not remove")
        supabase.table("roles_models").insert({
            "role_id": role.id,
            "model": role_name
        }).execute()
        return role
    except discord.Forbidden:
        logger.error("Permission denied to create and assign a role.")
    except discord.HTTPException as e:
        logger.error(f"Failed to create role: {e}")
    
async def delete_role(guild: discord.Guild, role: discord.Role) -> None:
    try:
        await role.delete(reason="Deleted by AlphaLLM")
        supabase.table("roles_models").delete().eq("role_id", role.id).execute()
    except discord.Forbidden:
        logger.error("Permission denied to delete the role.")
    except discord.HTTPException as e:
        logger.error(f"Failed to delete role: {e}")
    
async def check_role_exists(guild: discord.Guild, role_name: str) -> discord.Role:
    for role in guild.roles:
        if role.name == role_name:
            return role
    logger.warning(f"Role '{role_name}' does not exist in the guild.")
    return None

async def role_to_model(role: discord.Role) -> str:
    model = supabase.table("roles_models").select("model").eq("role_id", role.id).execute()
    logger.debug(f"Model for role {role.name}: {model.data}")
    return model