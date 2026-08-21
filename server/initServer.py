from flask import Flask
from server.dbClass import dbCreator
from server.descritor import Descritor
from server.config import config

app = Flask(__name__)

@app.route("/<string:query>")
def ResultadoSql(query):
     try:
        print(query)
        resultado=dbCreator.cursor_execute(query)
        colunasPossiveis=config["colunas"]+['*']
        colunasParaQuery=None
        sql=query.lower()
        queryAntesdoFrom=sql[:sql.find('from')].split()
        print(queryAntesdoFrom)
        if '*' in queryAntesdoFrom:
            colunasParaQuery=config["colunas"]
        else:
              colunasParaQuery=[x for x in queryAntesdoFrom if x in colunasPossiveis]

            
        descritor= Descritor(colunasParaQuery,resultado)

        resposta=descritor.descrever()

        return resposta

     except Exception as e:
         print(e)
         return "A requisição não foi possivel"

if __name__ == "__main__":
    app.run(port=5001)