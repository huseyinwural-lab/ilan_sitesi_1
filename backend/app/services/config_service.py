from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.config import SystemConfig

class ConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self, key: str, default: dict = None) -> dict:
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalar_one_or_none()
        return config.value if config else (default or {})

    async def set_config(self, key: str, value: dict, description: str = None):
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value
            if description: config.description = description
        else:
            config = SystemConfig(key=key, value=value, description=description)
            self.db.add(config)
            
        await self.db.commit()
        return config
