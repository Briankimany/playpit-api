
from sqlalchemy import create_engine 
from sqlalchemy.orm import scoped_session ,sessionmaker
from config.config import ConfigClass

config = ConfigClass()
if str(config.DATABASE_LOCATION) == '':
    raise ValueError("DATABASE_LOCATION is not set in the config file.")
else:   
    db_url = f"sqlite:///{config.DATABASE_LOCATION.absolute()}"
    # db_url = f"sqlite:///{config.DATABASE_LOCATION}"      

engine = create_engine(db_url,pool_size = 1 ,max_overflow=1 ,pool_timeout=10)

session = scoped_session(
    sessionmaker(
        autoflush=False,
        autocommit = False,
        bind=engine
    )
)


