import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.status import get_status
import asyncio
import logging

logger = logging.getLogger("AlphaLLM")

app = FastAPI(
    title="AlphaLLM API",
    description="API pour le projet AlphaLLM",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Tous les headers
)

@app.get("/")
async def read_root():
    """Point d'entrée principal de l'API"""
    try:
        return {"message": "AlphaLLM API", "version": "1.0.0", "status": "running"}
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la racine : {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/status")
async def status_check():
    """Point de contrôle de statut de l'API"""
    try:
        status = get_status()
        return status
    except Exception as e:
        logger.error(f"Erreur lors du point de contrôle de statut : {str(e)}")
        return {"status": "error", "message": str(e)}

def start_api(host: str = "0.0.0.0", port: int = 25692, reload: bool = False):
    """
    Démarre le serveur API FastAPI
    
    Args:
        host: Adresse IP d'écoute (défaut: 0.0.0.0)
        port: Port d'écoute (défaut: 25692)
        reload: Rechargement automatique en cas de modification (défaut: False)
    """
    logger.info(f"API démarrée sur {host}:{port}")
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="error",
        access_log=False,
    )

async def start_api_async(host: str = "0.0.0.0", port: int = 25692):
    """
    Version asynchrone pour démarrer l'API dans une boucle d'événements existante
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"API démarrée sur {host}:{port}")
    await server.serve()


if __name__ == "__main__":
    start_api(reload=True)