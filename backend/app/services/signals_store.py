from datetime import datetime,timedelta
from sqlalchemy import select
from app.models import Signal
import json

def persist_signals(db,user_id,signals):
    created=[]
    for s in signals:
        if db.scalar(select(Signal).where(Signal.user_id==user_id,Signal.symbol==s['symbol'],Signal.type==s['type'],Signal.created_at>=datetime.utcnow()-timedelta(hours=6))):continue
        row=Signal(user_id=user_id,symbol=s['symbol'],type=s['type'],severity=s.get('severity','medium'),metrics=json.dumps(s.get('metrics',{})),explanation=s.get('explanation',''),confidence=s.get('confidence'));db.add(row);created.append(row)
    db.commit();return created
