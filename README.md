# llm-grader

A CLI tool and Python package to grade code submissions using LLM-based rubrics and ensemble code evaluation.

## Features

- Two scoring modes:
  - **B**: Two-step rubric-based evaluation.
  - **C**: Ensemble code evaluation (default).
- Programmatic API via the `eval_submissions()` function.
- CLI entry point: `llm-grader`.
- Example smoke-test script in `test/tester.py`.

## Installation

First, create and activate a virtual environment, then install in editable mode:

```bash
# create and activate venv (if needed)
python3 -m venv llm-env
source llm-env/bin/activate

# install the package
pip install -e .
```

## Usage

### CLI

```bash
llm-grader RUBRIC_FILE MODEL_SOLUTION_FILE PROBLEM_STATEMENT_FILE SUBMISSIONS_DIR [OPTIONS]
```

Example:

```bash
llm-grader test/rubric.txt sol.txt test/rubric.txt test/sub
```

Options:

```text
--scoring_type {B,C}         Scoring mode: B = two-step rubric evaluation; C = ensemble code evaluation (default: C)
--output_csv OUTPUT_CSV      Path for CSV results (default: results.csv)
--log_file LOG_FILE          Path for log file (default: evaluation.log)
--syntaxMarks SYNTAXMARKS    Maximum syntax marks (default: 5)
--penalty PENALTY            Penalty per syntax error (default: 1)
--ensemble_size ENSEMBLE     Ensemble size for scoring type C (default: 5)
--file_ext FILE_EXT          Submission file extension (default: .txt)
--debug                      Enable debug output
```

### Programmatic API

You can also call the grading function directly from Python:

```python
from llm_grader.code_evaluator import eval_submissions

eval_submissions(
    rubric_filepath='test/rubric.txt',
    model_solution_filepath='sol.txt',
    problem_statement_filepath='test/rubric.txt',
    submissions_dir='test/sub',
    scoring_type='C',      # or 'B'
    output_csv='output/results.csv',
    log_file='output/evaluation.log',
    syntaxMarks=5,
    penalty=1,
    ensemble_size=5,
    debug=False,
    file_ext='.java'
)
```

### Example Test Script

A simple smoke-test script is provided at `test/tester.py`. Run it with:

```bash
python test/tester.py
```

Inspect `test/tester.py` to see how it imports `eval_submissions()` and sets up example file paths.

## Scoring Types

- **B: Two-step rubric evaluation**
  Uses the rubric file to assign scores in two phases (one-step parsing, then detailed rubric criteria).
- **C: Ensemble code evaluation**
  Runs an ensemble of LLM queries (default size 5) to judge each submission’s correctness and syntax.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a pull request.