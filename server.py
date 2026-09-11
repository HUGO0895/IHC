import os
import sqlite3

from flask import Flask


config = {
    "schema": """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            departamento TEXT NOT NULL,
            data_vencimento TEXT NOT NULL,
            data_cadastro TEXT NOT NULL
        )
    """,

    "db_path": os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "lojas.db"
    ),

    "query": (
        """
        INSERT INTO produtos
        (nome, departamento, data_vencimento, data_cadastro)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                "sabonete",
                "higiene",
                "2026-10-08",
                "2026-08-08"
            ),
            (
                "agua",
                "bebidas",
                "2026-07-08",
                "2026-08-08"
            ),
            (
                "coca",
                "bebidas",
                "2026-09-08",
                "2026-08-08"
            )
        ]
    ),

    "colunas": [
        "id",
        "nome",
        "departamento",
        "data_vencimento",
        "data_cadastro"
    ]
}


class Db:
    def __init__(self, schema, path=None, data=None):
        self.schema = schema
        self.path = path
        self.data = data

        if data and not self.file_exists():
            conn = sqlite3.connect(self.path)

            try:
                cursor = conn.cursor()
                cursor.execute(schema)
                cursor.executemany(data[0], data[1])
                conn.commit()
            finally:
                conn.close()

    def cursor_execute(self, comando):
        conn = None

        try:
            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()

            return cursor.execute(comando).fetchall()

        except Exception as error:
            print(error)
            raise

        finally:
            if conn:
                conn.close()

    def file_exists(self):
        return os.path.isfile(self.path) if self.path else False


dbCreator = Db(
    config["schema"],
    config["db_path"],
    config["query"]
)


class Descritor:
    def __init__(self, colunas, lista):
        self.colunas = colunas
        self.lista = lista

    def descrever(self):
        return (
            self.descreverLinhas()
            + "\n"
            + self.descreverColunas()
            + "\n"
            + self.descreverLinhas()
            + "\n"
            + self.descreverValores()
        )

    def maiorStringDeUmaColuna(self, coluna):
        valores = [
            len(str(linha[coluna]))
            for linha in self.lista
        ]

        valores.append(len(self.colunas[coluna]))

        return max(valores)

    def descreverLinhas(self):
        string = ""

        for coluna in range(len(self.colunas)):
            tamanho = self.maiorStringDeUmaColuna(coluna)
            string += "+" + ("-" * tamanho)

        return string + "+"

    def descreverColunas(self):
        string = ""

        for coluna in range(len(self.colunas)):
            nome = self.colunas[coluna]
            tamanho = self.maiorStringDeUmaColuna(coluna)
            espacos = tamanho - len(nome)

            string += "|" + nome + (" " * espacos)

        return string + "|"

    def descreverValores(self):
        string = ""

        for linha in self.lista:
            for coluna in range(len(linha)):
                valor = str(linha[coluna])
                tamanho = self.maiorStringDeUmaColuna(coluna)
                espacos = tamanho - len(valor)

                string += "|" + valor + (" " * espacos)

            string += "|\n"
            string += self.descreverLinhas() + "\n"

        return string


app = Flask(__name__)


@app.route("/<path:query>")
def ResultadoSql(query):
    try:
        print(query)

        resultado = dbCreator.cursor_execute(query)

        colunas_possiveis = config["colunas"] + ["*"]
        query_minuscula = query.lower()

        if "from" in query_minuscula:
            query_antes_do_from = (
                query_minuscula[:query_minuscula.find("from")]
                .split()
            )
        else:
            query_antes_do_from = query_minuscula.split()

        if "*" in query_antes_do_from:
            colunas_query = config["colunas"]
        else:
            colunas_query = [
                coluna
                for coluna in query_antes_do_from
                if coluna in colunas_possiveis
            ]

        if not colunas_query:
            colunas_query = config["colunas"]

        descritor = Descritor(
            colunas_query,
            resultado
        )

        return descritor.descrever()

    except Exception as error:
        print(error)
        return "A requisição não foi possível"


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001
    )
