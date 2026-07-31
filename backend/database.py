import os
import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

# Build connection kwargs
kwargs = {
    'serverSelectionTimeoutMS': 10000,
    'connectTimeoutMS': 10000,
    'socketTimeoutMS': 20000,
}

# For Atlas / TLS connections, supply the certifi CA bundle.
# Do NOT explicitly pass tls=True with mongodb+srv — it is already implied
# and double-specifying it can cause handshake failures on some PyMongo 4.x builds.
if 'mongodb+srv' in MONGO_URI or 'tls=true' in MONGO_URI.lower():
    kwargs['tlsCAFile'] = certifi.where()

client = AsyncIOMotorClient(MONGO_URI, **kwargs)

db = client[os.getenv('MONGO_DB', 'shiksha_ai')]

async def setup_indexes():
    try:
        await db.users.create_index('email', unique=True)
        print("Database indexes created successfully.")
    except Exception as e:
        logging.warning(f"Database startup warning: {e}")
