import os 
config= {
    "schema":"""CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT not null, 
                departamento TEXT not null ,
                data_vencimento TEXT not null ,
                data_cadastro TEXT not null 

            )""",
    "db_path":os.path.join(os.path.dirname(os.path.abspath(__file__)), "lojas.db"),

    "query":("INSERT INTO produtos(nome,departamento,data_vencimento,data_cadastro) VALUES (?,?,?,?)", [
                ("sabonete", "higiene","2026-10-08","2026-08-08"),
                ("agua", "bebidas","2026-07-08","2026-08-08"),
                ("coca", "bebidas","2026-09-08","2026-08-08"),
                                                             ]        ),
    "colunas":["id","nome","departamento","data_vencimento","data_cadastro"]

}