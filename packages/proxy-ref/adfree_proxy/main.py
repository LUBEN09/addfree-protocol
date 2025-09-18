# adfree_proxy/main.py

import asyncio
import argparse
import logging
from aiohttp import web, ClientSession
from .interceptor import AdfreeInterceptor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Adfree Protocol Reference Proxy")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind')
    parser.add_argument('--mode', choices=['transparent', 'tls-terminator'], default='transparent')
    args = parser.parse_args()

    # Crear sesión HTTP reutilizable
    session = ClientSession()

    # Crear interceptor con la sesión
    interceptor = AdfreeInterceptor(session)

    # Crear app y registrar middleware
    app = web.Application(middlewares=[interceptor.intercept_request])

    # Ruta para métricas Prometheus
    app.router.add_get('/metrics', interceptor.metrics_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()

    logger.info(f"Adfree Proxy running on http://{args.host}:{args.port}")
    logger.info(f"Metrics available at http://{args.host}:{args.port}/metrics")

    # Keep alive
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await session.close()  # Cerrar sesión
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())