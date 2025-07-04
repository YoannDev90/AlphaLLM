import discord
from discord.ext import commands
import logging
from utils.ai_utils import search_memory
from utils.memory_ai import add_memory, search_similar_memories, get_hybrid_history

logger = logging.getLogger('AlphaLLM')

class MemoryTestCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="memory_search", aliases=["msearch"])
    async def memory_search(self, ctx, *, query: str):
        """Recherche dans la mémoire vectorielle"""
        try:
            results = await search_memory(ctx.author.id, ctx.guild.id if ctx.guild else ctx.channel.id, query)
            
            embed = discord.Embed(
                title="🔍 Recherche dans la mémoire",
                description=f"Résultats pour: `{query}`",
                color=0x00ff00
            )
            
            if len(results) > 1900:  # Limite Discord
                results = results[:1900] + "..."
                
            embed.add_field(name="Résultats", value=results, inline=False)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur commande memory_search: {e}")
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name="memory_test", aliases=["mtest"])
    async def memory_test(self, ctx):
        """Test rapide du système de mémoire"""
        try:
            # Ajouter une mémoire de test
            test_content = f"Test de mémoire par {ctx.author.display_name}: Comment utiliser Python pour l'IA ?"
            await add_memory(ctx.author.id, ctx.guild.id if ctx.guild else ctx.channel.id, test_content)
            
            # Rechercher cette mémoire
            results = await search_similar_memories(
                ctx.author.id, 
                ctx.guild.id if ctx.guild else ctx.channel.id, 
                "Python intelligence artificielle", 
                limit=3
            )
            
            embed = discord.Embed(
                title="🧪 Test de mémoire",
                color=0x0099ff
            )
            
            embed.add_field(name="✅ Mémoire ajoutée", value=test_content, inline=False)
            
            if results:
                results_text = "\n".join([
                    f"**{i}.** [Similarité: {(1-r.get('distance', 0)):.1%}] {r['content'][:100]}..."
                    for i, r in enumerate(results, 1)
                ])
                embed.add_field(name="🔍 Résultats de recherche", value=results_text[:1000], inline=False)
            else:
                embed.add_field(name="🔍 Résultats de recherche", value="Aucun résultat trouvé", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur commande memory_test: {e}")
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name="memory_stats", aliases=["mstats"])
    async def memory_stats(self, ctx):
        """Statistiques de la mémoire"""
        try:
            from utils.memory_ai import get_history
            
            history = await get_history(ctx.author.id, ctx.guild.id if ctx.guild else ctx.channel.id, limit=100)
            
            embed = discord.Embed(
                title="📊 Statistiques de mémoire",
                color=0xff9900
            )
            
            embed.add_field(name="Total mémoires", value=len(history), inline=True)
            embed.add_field(name="Utilisateur", value=ctx.author.display_name, inline=True)
            embed.add_field(name="Serveur", value=ctx.guild.name if ctx.guild else "DM", inline=True)
            
            if history:
                latest = history[0]['created_at']
                embed.add_field(name="Dernière mémoire", value=latest, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur commande memory_stats: {e}")
            await ctx.send(f"❌ Erreur: {str(e)}")

async def setup(bot):
    await bot.add_cog(MemoryTestCommands(bot))
