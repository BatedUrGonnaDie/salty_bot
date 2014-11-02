import os
import psycopg2 as pg
import urlparse

class thing:
    url = None
    connection = None
    cursor = None

    def __init__(self):
        urlparse.uses_netloc.append("postgres")
        url = self.url = urlparse.urlparse(os.environ["PGURL"])

        try:
            self.connection = pg.connect(database=url.path[1:],user=url.username,password=url.password,host=url.hostname,port=url.port)
            self.cursor = self.connection.cursor()
        except:
            return -1
    
    def get(self,query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

k = thing()