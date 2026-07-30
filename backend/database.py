import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

kwargs = {}
if 'mongodb+srv' in MONGO_URI or 'tls=true' in MONGO_URI.lower():
    kwargs['tlsCAFile'] = certifi.where()

client = AsyncIOMotorClient(MONGO_URI, **kwargs)
db = client[os.getenv('MONGO_DB', 'shiksha_ai')]

async def setup_indexes():
    await db.users.create_index('email', unique=True)
