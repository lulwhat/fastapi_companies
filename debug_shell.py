import asyncio
import platform
from contextlib import asynccontextmanager

from sqlalchemy import select
from app.database import *
from app.models import Building, Category


get_session = asynccontextmanager(get_session)


async def run_shell():
    try:
        async with get_session() as db:
            res = await select_category(1, db)
            print('\n' + '_' * 20)
            print(f'result: {res.children}')
            print('\n' + '_' * 20)
    finally:
        await db.bind.dispose()

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(run_shell())
