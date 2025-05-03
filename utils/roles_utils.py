import discord

async def create_role(guild: discord.Guild, role_name: str) -> discord.Role:
    try:
        role = await guild.create_role(name=role_name, reason="Created by AlphaLLM - Do not delete")
        await guild.me.add_roles(role, reason="Assigned to AlphaLLM - Do not remove")
        return role
    except discord.Forbidden:
        raise Exception("Permission denied to create and assign a role.")
    except discord.HTTPException as e:
        raise Exception(f"Failed to create role: {e}")
    
async def delete_role(guild: discord.Guild, role: discord.Role) -> None:
    try:
        await role.delete(reason="Deleted by AlphaLLM")
    except discord.Forbidden:
        raise Exception("Permission denied to delete the role.")
    except discord.HTTPException as e:
        raise Exception(f"Failed to delete role: {e}")
    
async def check_role_exists(guild: discord.Guild, role_name: str) -> discord.Role:
    for role in guild.roles:
        if role.name == role_name:
            return role
    return None