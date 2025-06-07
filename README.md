# rubric-grader

A CLI tool and Python package to grade code submissions using LLM-based rubrics and ensemble code evaluation.

## Features

- Two scoring modes:
  - **B**: Two-step rubric-based evaluation.
  - **C**: Ensemble code evaluation (default).
- Programmatic API via the `eval_submissions()` function.
- CLI entry point: `rubric-grader`.
- Example smoke-test script in `test/tester.py`.

## Installation

### From PyPI

Install the latest released version from PyPI:

```bash
pip install rubric-grader
```

### From source (editable)

First, create and activate a virtual environment, then install in editable mode:

```bash
# create and activate venv (if needed)
python3 -m venv llm-env
source llm-env/bin/activate

# install the package in editable mode
pip install -e .
```

## Usage

### CLI

```bash
rubric-grader RUBRIC_FILE MODEL_SOLUTION_FILE PROBLEM_STATEMENT_FILE SUBMISSIONS_DIR [OPTIONS]
```

Example:

```bash
rubric-grader test/rubric.txt sol.txt test/rubric.txt test/sub
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

## Publishing to PyPI via GitHub Actions

You can automate publishing to PyPI using GitHub Actions' OpenID Connect (OIDC). Read more about OpenID Connect in GitHub Actions [here](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect).

To configure the PyPI publisher in your repository settings, provide the following information:

| Field               | Required | Value/Example        | Description                                                                                                                                 |
|---------------------|----------|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| PyPI Project Name   | Yes      | `rubric-grader`      | The name of the project on PyPI that will be created when this publisher is used.                                                            |
| Owner               | Yes      | `arnavthestud`       | The GitHub organization or username that owns this repository.                                                                                |
| Repository name     | Yes      | `Rubric-Grader`      | The name of the GitHub repository containing the publishing workflow.                                                                         |
| Workflow name       | Yes      | `workflow.yml`       | The filename of the publishing workflow. This file should exist in the `.github/workflows/` directory in the repository configured above. |
| Environment name    | No       | `rubric-grader` (optional) | The GitHub Actions environment used for publishing. Configuring a dedicated environment is recommended to restrict access to the PyPI token. |

Ensure that you have a corresponding workflow file in `.github/workflows/` (e.g., `workflow.yml`) and an environment (if used) configured under your repository settings with a secret (e.g., `PYPI_TOKEN`) for package publishing.