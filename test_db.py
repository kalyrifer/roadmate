#!/usr/bin/env python
import asyncio
from asyncpg import create_pool

async def test_db():
    try:
        pool = await create_pool(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='roadmate_db',
            min_size=1,
            max_size=1
        )
        async with pool.acquire() as conn:
            db_name = await conn.fetchval('SELECT current_database()')
            print(f'SUCCESS: Connected to database: {db_name}')
        await pool.close()
    except Exception as e:
        print(f'DATABASE ERROR: {e}')

if __name__ == '__main__':
    asyncio.run(test_db())