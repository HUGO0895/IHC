import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "lojas.db")
class Db():
    def __init__(self,schema,path,data=None):
        self.schema=schema
        self.path=path
        if data and not self.file_exists():
          conn=sqlite3.connect(self.path)
          c = conn.cursor()
          c.execute(schema)
          c.executemany(data[0],data[1])
          conn.commit()
          conn.close()

    def cursor_executeSelect(self,comando):
      try:
        conn=sqlite3.connect(self.path)
        cursor=conn.cursor()
        resultado=cursor.execute(comando).fetchall()
        conn.close()
        return resultado
      except Exception as e:
         return "Não foi possivel executar esse comando,pois "+e
      
    def file_exists(self):
       print(os.path.isfile(self.path))
       return os.path.isfile(self.path)

      
       
dbCreator=Db("""CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT not null, 
                departamento TEXT not null ,
                data_vencimento TEXT not null ,
                data_cadastro TEXT not null 

            )""",db_path,
            ("INSERT INTO produtos(nome,departamento,data_vencimento,data_cadastro) VALUES (?,?,?,?)", [
            ("sabonete", "higiene","2026-10-08","2026-08-08"),
            ("agua", "bebidas","2026-07-08","2026-08-08"),
            ("coca", "bebidas","2026-09-08","2026-08-08"),
                                                         ]        ))
      
