"""Persist editable campaign details separately from secrets in .env."""
import json
from pathlib import Path
import os
import config

PATH = config.BASE_DIR / 'data' / 'campaign.json'
FIELDS = ('brand_name','brand_description','offer','niche','location','keywords','sender')

def defaults():
    return {
        'brand_name':os.getenv('BRAND_NAME','Your Brand'),
        'brand_description':os.getenv('BRAND_DESCRIPTION','A brand looking for relevant creator partnerships.'),
        'offer':os.getenv('COLLAB_OFFER','A potential paid collaboration; final terms to be discussed.'),
        'niche':os.getenv('TARGET_NICHE','Fitness'),
        'location':os.getenv('TARGET_LOCATION','India'),
        'keywords':os.getenv('CAMPAIGN_KEYWORDS','fitness, wellness'),
        'sender':config.SENDER_NAME,
    }

def load_campaign():
    data=defaults()
    if PATH.exists():
        try:
            saved=json.loads(PATH.read_text(encoding='utf-8'))
            if isinstance(saved,dict):
                for key in FIELDS:
                    if isinstance(saved.get(key),str):data[key]=saved[key]
        except (OSError,json.JSONDecodeError):
            pass
    return data

def save_campaign(data):
    PATH.parent.mkdir(parents=True,exist_ok=True)
    clean={key:str(data.get(key,'')).strip() for key in FIELDS}
    PATH.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
    return clean
