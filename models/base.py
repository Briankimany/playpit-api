
from models.init_db import session
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column ,DateTime
from datetime import datetime ,timezone



BaseModel = declarative_base()
BaseModel.query = session.query_property()

class Base(BaseModel):
    __abstract__ = True

    created_at = Column(DateTime , default = datetime.now(timezone.utc))
    updated_at = Column(DateTime , onupdate = datetime.now(timezone.utc))

