from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine
from app.models import *
from app.api.routes import router
from app.services.scheduler import start_scheduler
from app.seed import seed

app=FastAPI(title="Watch Me Groww API",version="2.0.0",description="Indian market intelligence watchlist API")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
Base.metadata.create_all(bind=engine)
app.include_router(router)

@app.get('/health')
def health():return {"status":"ok","demo_mode":settings.demo_mode}

@app.on_event('startup')
def startup():
    try:
        seed()
    except Exception as e:
        print('[seed]',e)
    try:
        start_scheduler()
    except Exception as e:
        print('[scheduler]',e)
