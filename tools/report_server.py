# tools/report_server.py

import asyncio
import logging
from aiohttp import web
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReportServer")

async def handle_report(request):
    """Handler para recibir reportes de violación de política."""
    try:
        # Leer el cuerpo como JSON
        data = await request.json()
        logger.info("✅ Reporte recibido:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))

        # Responder con éxito
        return web.json_response({
            "status": "received",
            "message": "Report processed successfully"
        }, status=200)

    except json.JSONDecodeError:
        logger.error("❌ Reporte recibido con cuerpo no JSON")
        return web.json_response({
            "error": "Invalid JSON"
        }, status=400)

    except Exception as e:
        logger.error(f"❌ Error procesando reporte: {e}")
        return web.json_response({
            "error": "Internal server error"
        }, status=500)

async def health_check(request):
    """Endpoint de salud para verificar que el servidor está vivo."""
    return web.json_response({"status": "healthy"}, status=200)

def create_app():
    app = web.Application()
    app.router.add_post('/adfree', handle_report)
    app.router.add_get('/health', health_check)
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("🚀 Servidor de reportes Adfree escuchando en http://127.0.0.1:8089")
    logger.info("   POST /adfree para recibir reportes")
    logger.info("   GET  /health para chequeo de salud")
    web.run_app(app, host='127.0.0.1', port=8089)
