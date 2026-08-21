import re 
import sqlite3
class SqlValidator():
    def __init__(self,schema,data):
        self.schema=schema
        self.data=data

    def isSelectOnly(self,querry):
            regex=r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|EXEC|MERGE)\b"
            maisDoqueSelect=re.search(regex,querry)
            if maisDoqueSelect:
                raise ValueError("Essa querry não possui só select")
            return not maisDoqueSelect

    def testeSql(self,querry):
          try:
            conn=sqlite3.connect(':memory:')
            c = conn.cursor()
            c.execute(self.schema)
            c.executemany(self.data[0],self.data[1])
            c.execute(querry)
            conn.commit()
          except Exception as e:
               print(e)
          finally:
            
            conn.close() 