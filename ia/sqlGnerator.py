from ia.txtTosql import TextToSQL
import dspy
from ia.sqlValidator import SqlValidator
class ReliableSQLGenerator(dspy.Module):
    def __init__(self,sqlValidator):
        super().__init__()
        self.generate_sql = dspy.ChainOfThought(TextToSQL)
        self.sqlValidator= sqlValidator

    def forward(self, schema, question):
        try:
            pred = self.generate_sql(schema=schema, question=question)
            self.sqlValidator.testeSql(pred.sql_query)
            self.sqlValidator.isSelectOnly(pred.sql_query)
            print(pred)
            return pred
        except Exception as e:
            print(e)
            raise 
