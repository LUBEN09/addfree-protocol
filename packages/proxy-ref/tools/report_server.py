from aiohttp import web
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_report(request):
    data = await request.json()
    logger.info(f"Received report: {data}")
    return web.json_response({"status": "received"})

app = web.Application()
app.router.add_post('/adfree', handle_report)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=9090)
