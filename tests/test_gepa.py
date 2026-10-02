import tempfile
from pathlib import Path
import unittest

import dspy
from dspy.utils import DummyLM

from db_config import config
from optimize_gepa import execute_query, load_examples, optimize, sql_metric
from sql_generator import build_generator


class GepaTests(unittest.TestCase):
    def metric(self, reference, prediction, ordered=False):
        return sql_metric(
            dspy.Example(question="Consulta de teste", sql_query=reference, ordered=ordered),
            dspy.Prediction(sql_query=prediction),
        )

    def test_equivalent_results(self):
        result = self.metric("SELECT nome FROM produtos", "SELECT nome FROM produtos ORDER BY nome")
        self.assertEqual(result.score, 1)

    def test_order_is_checked_when_requested(self):
        result = self.metric("SELECT nome FROM produtos ORDER BY nome",
                             "SELECT nome FROM produtos ORDER BY nome DESC", True)
        self.assertEqual(result.score, 0)

    def test_duplicates_are_significant(self):
        self.assertEqual(self.metric("SELECT departamento FROM produtos",
                                     "SELECT DISTINCT departamento FROM produtos").score, 0)

    def test_wrong_results_have_feedback(self):
        result = self.metric("SELECT COUNT(*) FROM produtos", "SELECT 42")
        self.assertEqual(result.score, 0)
        self.assertIn("Esperado", result.feedback)

    def test_invalid_and_unsafe_sql(self):
        for query in (None, "DELETE FROM produtos", "PRAGMA user_version",
                      "SELECT * FROM inexistente", "SELECT 1; DROP TABLE produtos"):
            with self.subTest(query=query):
                result = self.metric("SELECT 1", query)
                self.assertEqual(result.score, 0)
                self.assertIn("SQL inválido", result.feedback)
        self.assertEqual(execute_query("SELECT COUNT(*) FROM produtos"), [(3,)])

    def test_dataset_references_and_splits(self):
        train = load_examples("data/gepa_train.json")
        val = load_examples("data/gepa_val.json")
        self.assertFalse({e.question for e in train} & {e.question for e in val})
        for example in train + val:
            self.assertEqual(sql_metric(example, example).score, 1)
            self.assertEqual(set(example.inputs().keys()), {"dbschema", "question"})

    def test_real_gepa_compile_save_load_and_inference(self):
        # Smoke test da API real: o orçamento cobre apenas a avaliação inicial.
        # Não pretende medir melhoria; nenhuma chamada de rede é realizada.
        lm = DummyLM([{"reasoning": "Contar produtos", "sql_query": "SELECT COUNT(*) FROM produtos"}] * 10)
        examples = [dspy.Example(
            dbschema=config["schema"], question="Quantos produtos?",
            sql_query="SELECT COUNT(*) FROM produtos", ordered=False,
        ).with_inputs("dbschema", "question")]
        with dspy.context(lm=lm):
            program = optimize(examples, examples, lm, budget=1)
            with tempfile.TemporaryDirectory() as directory:
                artifact = str(Path(directory) / "program.json")
                program.save(artifact)
                generator = build_generator(config["schema"], config["query"], artifact)
                prediction = generator(schema=config["schema"], question="Quantos produtos?")
                self.assertEqual(prediction.sql_query, "SELECT COUNT(*) FROM produtos")

    def test_no_artifact_and_missing_artifact(self):
        self.assertIsNotNone(build_generator(config["schema"], config["query"]))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                build_generator(config["schema"], config["query"], str(Path(directory) / "missing.json"))


if __name__ == "__main__":
    unittest.main()
