import sqlite3
import os
from config import config
class Db():
    def __init__(self,schema,path=None,data=None):
          self.schema=schema
          self.path=path
          self.data=data
          if data and not self.file_exists() :
            conn=sqlite3.connect(self.path)
            c = conn.cursor()
            c.execute(schema)
            c.executemany(data[0],data[1])
            conn.commit()
            conn.close()

    def cursor_execute(self,comando):
      try:
       

          conn=sqlite3.connect(self.path)
          cursor=conn.cursor()
          resultado=cursor.execute(comando).fetchall()
          return resultado
      except Exception as e:
         print(e)
         raise
      finally:
         conn.close()
    
      
    def file_exists(self):
       return os.path.isfile(self.path) if self.path else False

      
       
dbCreator=Db(config["schema"],config["db_path"],config["query"])