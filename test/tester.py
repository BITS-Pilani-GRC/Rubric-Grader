import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

from llm_grader.code_evaluator import eval_submissions

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
rubric_fp = os.path.join(base_dir, 'test', 'rubric.txt')
sol_fp = os.path.join(base_dir, 'test', 'sol.txt')
prob_fp = os.path.join(base_dir, 'test', 'prob.txt')
subs_dir = os.path.join(base_dir, 'test', 'sub')
output_dir = os.path.join(base_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

eval_submissions(
    rubric_filepath=rubric_fp,
    model_solution_filepath=sol_fp,
    problem_statement_filepath=prob_fp,
    submissions_dir=subs_dir,
    scoring_type='C',      # or 'B', 'D' (defaults to 'A' if omitted)
    output_csv=os.path.join(output_dir, 'results.csv'),
    log_file=os.path.join(output_dir, 'evaluation.log'),
    syntaxMarks=5,
    penalty=1,
    debug=False,
    file_ext=".java"
)
