import os
from dotenv import load_dotenv

load_dotenv()  


class Config:
    FP_GOLDEN_KEY = os.environ.get('FP_GOLDEN_KEY')
    SITE_URL = os.environ.get("SITE_URL")
