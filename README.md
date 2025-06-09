# rubric-grader

A CLI tool and Python package to grade code submissions using LLM-based rubrics and ensemble code evaluation.

## Features

- Scoring modes:
  - **A**: One-step rubric-based evaluation (default).
  - **B**: Two-step rubric-based evaluation.
  - **C**: Ensemble code evaluation.
  - **D**: AI-O one-shot evaluation.
- Programmatic API via the `eval_submissions()` function.
- CLI entry point: `rubric-grader`.
- Example smoke-test script in `test/tester.py`.

## Installation

### From PyPI

Install the latest released version from PyPI:

```bash
pip install  rubric-grader
```

### From source (editable)

To install the latest development version directly from the GitHub repository, clone the repo and install in editable mode:

```bash
git clone https://github.com/arnavthestud/Rubric-Grader.git
cd Rubric-Grader
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Usage

### Environment Variables

Before running the CLI or using the programmatic API, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### CLI

```bash
rubric-grader RUBRIC_FILE MODEL_SOLUTION_FILE PROBLEM_STATEMENT_FILE SUBMISSIONS_DIR [OPTIONS]
```

Example:

```bash
rubric-grader test/rubric.txt test/sol.txt test/prob.txt test/sub
```

Options:

```text
--scoring_type {A,B,C,D}    Scoring mode: A = one-step rubric evaluation (default); B = two-step rubric evaluation; C = ensemble code evaluation; D = AI-O one-shot evaluation
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
    model_solution_filepath='test/sol.txt',
    problem_statement_filepath='test/prob.txt',
    submissions_dir='test/sub',
    scoring_type='C',      # or 'B', 'D' (defaults to 'A' for one-step rubric evaluation if omitted)
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

- **A: One-step rubric evaluation**
  Assigns scores based on a single rubric-based prompting phase.
- **B: Two-step rubric evaluation**
  Uses the rubric file to assign scores in two phases (one-step parsing, then detailed rubric criteria).
- **C: Ensemble code evaluation**
  Runs an ensemble of LLM queries (default size 5) to judge each submission’s correctness and syntax.
- **D: AI-O one-shot evaluation**
  Performs a one-shot evaluation using the AI-O prompt for logical correctness and syntax.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a pull request.
