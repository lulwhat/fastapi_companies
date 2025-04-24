import aio_pika

from app.config import settings


async def get_rabbitmq_connection():
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)


async def publish_export_task(task_id: int):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()

        queue = await channel.declare_queue(
            settings.EXPORT_QUEUE,
            durable=True
        )

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=str(task_id).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue.name
        )
