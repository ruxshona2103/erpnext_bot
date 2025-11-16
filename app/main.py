import asyncio
import uvicorn

from app.config import config
from app.services.notification import notification_worker

async def start_background_tasks():
    """
    Barcha background workerlarni ishga tushirish.
    """
    asyncio.create_task(notification_worker())


def main():
    # Asosiy event loop
    loop = asyncio.get_event_loop()

    # Background tasks qo‘shamiz
    loop.create_task(start_background_tasks())

    # FastAPI webhook serverni ishga tushiramiz
    uvicorn.run(
        "app.webhook.server:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
        workers=1
    )


if __name__ == "__main__":
    main()
