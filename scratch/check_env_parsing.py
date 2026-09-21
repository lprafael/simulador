
import os
from app.core.config import settings

print(f"BILLETAJE_DB_URL from settings: {settings.BILLETAJE_DB_URL}")
print(f"BILLETAJE_DB_URL from os.environ: {os.getenv('BILLETAJE_DB_URL')}")
