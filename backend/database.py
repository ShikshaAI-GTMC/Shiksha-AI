import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI=os.getenv('MONGO_URI','mongodb://localhost:27017')
client=AsyncIOMotorClient(MONGO_URI)
db=client[os.getenv('MONGO_DB','shiksha_ai')]

async def setup_indexes():
    await db.users.create_index('email',unique=True)
