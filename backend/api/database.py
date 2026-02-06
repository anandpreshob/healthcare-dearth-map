import databases

from backend.api.config import settings

# The `databases` library expects a URL like postgresql+asyncpg://...
# but can also accept postgresql://... -- normalize to the asyncpg scheme.
_url = settings.DATABASE_URL
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)

database = databases.Database(_url)


async def connect():
    await database.connect()


async def disconnect():
    await database.disconnect()
