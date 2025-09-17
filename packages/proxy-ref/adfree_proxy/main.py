"""Punto de entrada para proxy-ref"""
from aiohttp import web
from .metrics import MetricsCollector


async def handle(request):
    return web.Response(text="adfree-proxy running")


def create_app():
    app = web.Application()
    app.router.add_get('/', handle)
    app['metrics'] = MetricsCollector()
    return app


def main():
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
