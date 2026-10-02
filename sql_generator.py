import os
import re
import sqlite3

import dspy


class TextToSQL(dspy.Signature):
    """
    Gera uma consulta SQL a partir de uma pergunta em linguagem natural.
    """

    dbschema = dspy.InputField(
        desc="Database schema"
    )

    question = dspy.InputField(
        desc="Natural language question"
    )

    sql_query = dspy.OutputField(
        desc="Valid SQL query"
    )


class SqlValidator:
    def __init__(self, schema, data):
        self.schema = schema
        self.data = data

    def isSelectOnly(self, query):
        regex = (
            r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|"
            r"GRANT|REVOKE|CREATE|EXEC|MERGE)\b"
        )

        comando_perigoso = re.search(
            regex,
            query,
            re.IGNORECASE
        )

        if comando_perigoso:
            raise ValueError(
                "Essa query não possui somente SELECT"
            )

        return True

    def testeSql(self, query):
        conexao = None

        try:
            conexao = sqlite3.connect(":memory:")
            cursor = conexao.cursor()

            cursor.execute(self.schema)

            cursor.executemany(
                self.data[0],
                self.data[1]
            )

            cursor.execute(query)
            conexao.commit()

        except Exception as error:
            print(error)
            raise

        finally:
            if conexao:
                conexao.close()


class ReliableSQLGenerator(dspy.Module):
    def __init__(self, sql_validator):
        super().__init__()

        self.generate_sql = dspy.ChainOfThought(TextToSQL)
        self.sql_validator = sql_validator

    def forward(self, schema, question):
        resultado = self.generate_sql(
            dbschema=schema,
            question=question
        )

        self.sql_validator.isSelectOnly(resultado.sql_query)
        self.sql_validator.testeSql(resultado.sql_query)

        print(resultado)

        return resultado


def configure_lm(model_name=None):
    name = model_name or os.getenv("IALOCAL")
    if not name:
        raise ValueError("Configure IALOCAL no .env (ex.: openai/modelo-local)")
    lm = dspy.LM(
        name,
        api_base=os.getenv("LM_API_BASE", "http://localhost:1337/v1"),
        api_key=os.getenv("apiKey", "local"),
    )
    return lm


def build_generator(schema, data, artifact=None):
    generator = ReliableSQLGenerator(SqlValidator(schema, data))
    if artifact:
        generator.generate_sql.load(artifact)
    return generator
