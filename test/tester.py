import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

from llm_grader.code_evaluator import eval_submissions

eval_submissions(
    rubric_filepath='/Users/anandramamoorthy/Downloads/llm-grader/test/rubric.txt',
    model_solution_filepath='sol.txt',
    problem_statement_filepath='/Users/anandramamoorthy/Downloads/llm-grader/test/rubric.txt',
    submissions_dir='/Users/anandramamoorthy/Downloads/llm-grader/test/sub/',
    scoring_type='C',      # or 'B'
    output_csv='output/results.csv',
    log_file='output/evaluation.log',
    syntaxMarks=5,
    penalty=1,
    debug=False,
    file_ext=".java"
)
