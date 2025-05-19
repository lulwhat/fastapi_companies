import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from database import create_session
from rabbitmq.export_service import process_task
from config import settings


async def process_export_message(message: AbstractIncomingMessage):
    async with message.process():
        task_id = int(message.body.decode())
        db = await create_session()
        try:
            await process_task(db, task_id)
        finally:
            await db.close()


async def consume():
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue(
                    settings.EXPORT_QUEUE,
                    durable=True
                )
                await queue.consume(process_export_message)
                print(' [*] Waiting for messages. To exit press CTRL+C')
                # Keep the consumer alive
                await asyncio.Future()  # Runs forever until cancelled
        except ConnectionError:
            print('Connection lost, reconnecting in 5 seconds...')
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(consume())
