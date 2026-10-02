"""Otimização offline do gerador SQL com feedback de execução em SQLite."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sqlite3

import dspy
from dotenv import load_dotenv

from db_config import config
from sql_generator import TextToSQL, configure_lm


def execute_query(query):
    # Cada avaliação recebe os mesmos dados, sem acessar lojas.db.
    if not isinstance(query, str) or not re.match(r"^\s*SELECT\b", query, re.I):
        raise ValueError("Retorne uma única consulta SELECT, sem Markdown.")
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(config["schema"])
        connection.executemany(*config["query"])
        connection.execute("PRAGMA query_only = ON")
        remaining = 1000

        def limit_work():
            nonlocal remaining
            remaining -= 1
            return int(remaining <= 0)

        connection.set_progress_handler(limit_work, 1000)
        return connection.execute(query).fetchall()
    finally:
        connection.close()


def sql_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    expected = execute_query(gold.sql_query)
    try:
        actual = execute_query(getattr(pred, "sql_query", None))
    except (ValueError, sqlite3.Error) as error:
        return dspy.Prediction(score=0.0, feedback=f"SQL inválido: {error}")
    matches = (actual == expected if gold.get("ordered", False)
               else Counter(actual) == Counter(expected))
    return dspy.Prediction(
        score=float(matches),
        feedback=("Resultado correto." if matches else
                  f"Resultado incorreto para {gold.question!r}. "
                  f"Esperado: {expected!r}; obtido: {actual!r}. "
                  "Revise filtros, colunas, agregações e ordenação."),
    )


def load_examples(path):
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path}: informe uma lista não vazia de exemplos.")
    examples = []
    for record in records:
        if not isinstance(record.get("question"), str) or not record["question"].strip():
            raise ValueError(f"{path}: cada exemplo precisa de question.")
        execute_query(record["sql_query"])
        examples.append(dspy.Example(
            dbschema=config["schema"], question=record["question"],
            sql_query=record["sql_query"], ordered=record.get("ordered", False),
        ).with_inputs("dbschema", "question"))
    return examples


def optimize(trainset, valset, reflection_lm, budget):
    optimizer = dspy.GEPA(
        metric=sql_metric, max_metric_calls=budget,
        reflection_lm=reflection_lm, num_threads=1, seed=0,
    )
    return optimizer.compile(
        dspy.ChainOfThought(TextToSQL), trainset=trainset, valset=valset,
    )


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/gepa_train.json")
    parser.add_argument("--val", default="data/gepa_val.json")
    parser.add_argument("--output", default="artifacts/sql_gepa.json")
    parser.add_argument("--max-metric-calls", type=int, default=100)
    parser.add_argument("--reflection-model", help="Padrão: IALOCAL; mesmo endpoint local")
    args = parser.parse_args()
    trainset, valset = load_examples(args.train), load_examples(args.val)
    if args.max_metric_calls <= len(valset):
        parser.error("O orçamento precisa exceder o tamanho do conjunto de validação.")
    if {e.question for e in trainset} & {e.question for e in valset}:
        parser.error("Use perguntas distintas para treino e validação.")
    output = Path(args.output)
    if output.suffix != ".json":
        parser.error("--output deve ter extensão .json")
    dspy.configure(lm=configure_lm())
    optimized = optimize(trainset, valset, configure_lm(args.reflection_model),
                         args.max_metric_calls)
    output.parent.mkdir(parents=True, exist_ok=True)
    optimized.save(str(output))
    print(f"Programa salvo em {output}. Configure GEPA_PROGRAM_PATH={output} no .env.")


if __name__ == "__main__":
    main()
