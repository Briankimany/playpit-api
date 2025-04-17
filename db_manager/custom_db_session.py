from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from concurrent.futures import as_completed , ThreadPoolExecutor as Executor

class CustomDbSession:
    def __init__(self,engine):
        self.engine =engine
        self.Session = sessionmaker(engine)
    
    @contextmanager
    def scoped_sesson(self ,logger,commit = False ,*args ,**kwargs):
        logger.info("[CustomDbSes] initiating transactioins  args=({}) ,kwargs=({})".format(args ,kwargs))
        db_session = self.Session()
        try:
            yield db_session
        except Exception as e:
            db_session.rollback()
            logger.error("[CustomDbSes] error occured {}".format(e))
        finally:
            db_session.close()


if __name__ == "__main__":
    import requests ,json

    payload = {"reference_id":"cadc5ac2-f154-4dbb-9e56-6dcdc255c8e4"}
    headers = {"Authorization": "Bearer 261e50a6-64c6-4f50-a26e-abef519c7350"}

    def make_req():
        response = requests.get("http://localhost:5000/transfers/transfer-status" ,
                                json=payload,
                                headers=headers,
                                timeout=50)
        return response.json()

    d = [Executor().submit(make_req ) for i in range (4)]
    c=0
    for i in as_completed(d):
        print(c)
        print(i.result())
        c+=1


