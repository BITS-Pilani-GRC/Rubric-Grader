import argparse
import csv
import getpass
import json
import logging
import os
import re
import subprocess

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda iterable, **kwargs: iterable

from langchain_openai import ChatOpenAI

from llm_grader.scoring_impl import (
    evaluate_one_step_impl,
    evaluate_two_step_impl,
    check_java_syntax,
    evaluate_codev,
)
#############################
# Input Loading Functions
#############################

def load_rubric(rubric_filepath):
    if rubric_filepath.lower().endswith('.json'):
        with open(rubric_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return load_text_file(rubric_filepath)

def load_text_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def get_student_submissions(directory, file_ext=".txt"):
    submissions = []
    for file in os.listdir(directory):
        if file.endswith(file_ext):
            student_id = os.path.splitext(file)[0]
            file_path = os.path.join(directory, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            submissions.append({
                "student_id": student_id,
                "submission": content,
                "filepath": file_path
            })
    return submissions

#############################
# Syntax Check Function
#############################

def check_syntax(code_filepath: str) -> tuple[int, float, dict]:
    error_dict = {}
    try:
        result = subprocess.run(
            ["javac", code_filepath],
            capture_output=True,
            text=True
        )
        error_count = 0
        if result.stderr:
            errors = result.stderr.strip().split('\n')
            for error in errors:
                if 'error' in error and not re.search(r'\d+ errors?$', error):
                    line_match = re.search(r':(\d+):', error)
                    if line_match:
                        line_num = int(line_match.group(1))
                        error_msg = re.sub(r'^.*?:\d+:', '', error).strip()
                        if line_num not in error_dict:
                            error_dict[line_num] = []
                        error_dict[line_num].append(error_msg)
            last_line = errors[-1]
            if match := re.search(r'(\d+) errors?', last_line):
                error_count = int(match.group(1))
        syntax_score = max(5.0 - (0.75 * len(error_dict)), 0.0)
        syntax_score = round(syntax_score, 2)
        return error_count, syntax_score, error_dict
    except Exception as e:
        print(f"An error occurred during syntax check: {e}")
        return -1, 0.0, {}

#############################
# CodeJudge Class
#############################

class CodeJudge:
    def __init__(self, model="gpt-4o-mini", base_url=None, api_key=None):
        if base_url:
            if not api_key:
                raise ValueError("API key is required when using a custom base URL.")
            self.llm = ChatOpenAI(model=model, temperature=0, base_url=base_url, api_key=api_key)
        else:
            if "OPENAI_API_KEY" not in os.environ:
                from getpass import getpass
                os.environ["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
            self.llm = ChatOpenAI(model=model, temperature=0)
        self._load_prompts()

    def _load_prompts(self):
        self.oneStepPrompt = (
            "You are an expert code evaluator. You are provided with a question, a rubric, "
            "the student's code submission, and the compiler response. Ignore any syntax errors and "
            "evaluate only the logical correctness. Return a JSON dictionary mapping each rubric item to marks. \n"
            "Question: {} \nRubric: {} \nCode Submission: {} \nCompiler Response: {}"
        )
        self.twoStepPrompts = [
            "You are an expert code evaluator. Evaluate the following code to infer the student's logical flow and intention, ignoring syntax errors. \nCode Submission: {}",
            "You are now provided with the question, the rubric, and the student's inferred logical flow. Compare the student's logic with the requirements. \n"
            "Question: {} \nRubric: {} \nLogical Flow and Intention: {}"
        ]

    def evaluate_one_step(self, question, rubric, code_filepath, syntaxMarks=5, penalty=1, debug=False):
        _, _, comp_response = check_syntax(code_filepath)
        try:
            with open(code_filepath, "r") as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading file {code_filepath}: {e}")
            code = ""
        return evaluate_one_step_impl(self.llm, self.oneStepPrompt, question, rubric, code, comp_response, syntaxMarks, penalty, debug)

    def evaluate_two_step(self, question, rubric, code_filepath, syntaxMarks=5, penalty=1, debug=False):
        _, _, comp_response = check_syntax(code_filepath)
        try:
            with open(code_filepath, "r") as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading file {code_filepath}: {e}")
            code = ""
        return evaluate_two_step_impl(self.llm, self.twoStepPrompts, question, rubric, code, comp_response, syntaxMarks, penalty, debug)


###########################
# POINT WISE EVAL CLASS
###########################
class pointWiseEval:
    def __init__(self, model="gpt-4o-mini", base_url=None, api_key=None):
        if base_url:
            if not api_key:
                raise ValueError("API key is required when using a custom base URL.")
            self.llm = ChatOpenAI(model=model, temperature=0, base_url=base_url, api_key=api_key)
        else:
            if "OPENAI_API_KEY" not in os.environ:
                from getpass import getpass
                os.environ["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
            self.llm = ChatOpenAI(model=model, temperature=0)
        self._load_prompts()

    def _load_prompts(self):
        self.oneStepPrompt = (
            """You are evaluating a Java code submission for a Cricket Analytics System.
            Provide your evaluation in VALID JSON format only          
          

            You are required to implement functionalities for a Cricket Analytics application. 
            The provided template code for this application contains multiple classes and methods related to cricket players, 
            their roles, team information, and various data-handling operations. Your tasks involve implementing several methods, 
            each responsible for performing specific actions like reading data from a file, writing data back, updating player 
            statistics, and filtering data.
            
            "Question: {} \nRubric: {} \nCode Submission: {} \nCompiler Response: {}"

            Respond ONLY with a JSON object in this exact format:
            {{
                "function_scores": {{
                    "compare": {{"score": 0, "max_score": 2, "feedback": "feedback here"}},
                    "readPlayersFromFile": {{"score": 0, "max_score": 9, "feedback": "feedback here"}},
                    "writePlayersToFile": {{"score": 0, "max_score": 4, "feedback": "feedback here"}},
                    "updatePlayerStats": {{"score": 0, "max_score": 5, "feedback": "feedback here"}},
                    "calculateTeamAverageRuns": {{"score": 0, "max_score": 5, "feedback": "feedback here"}},
                    "teamFilter": {{"score": 0, "max_score": 5, "feedback": "feedback here"}},
                    "allRounderFilter": {{"score": 0, "max_score": 5, "feedback": "feedback here"}}
                }},
                "total_score": 0,
                "overall_feedback": "overall feedback here"
            }}"""
        )

        # TBD WHAT TO DO ABOUT TWO STEPS PROMPTS
        self.twoStepPrompts = [
            "" , ""
        ]
        

    def evaluate_one_step(self, question, rubric, code_filepath, syntaxMarks=5, penalty=1, debug=False):
        _, _, comp_response = check_syntax(code_filepath)
        try:
            with open(code_filepath, "r") as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading file {code_filepath}: {e}")
            code = ""
        return evaluate_one_step_impl(self.llm, self.oneStepPrompt, question, rubric, code, comp_response, syntaxMarks, penalty, debug)

    def evaluate_two_step(self, question, rubric, code_filepath, syntaxMarks=5, penalty=1, debug=False):
        _, _, comp_response = check_syntax(code_filepath)
        try:
            with open(code_filepath, "r") as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading file {code_filepath}: {e}")
            code = ""
        return evaluate_two_step_impl(self.llm, self.twoStepPrompts, question, rubric, code, comp_response, syntaxMarks, penalty, debug)
    
    #do you need ensemble size or do i take it as default?
    def evaluate_ensemble(self, question, rubric, code_filepath, syntaxMarks=5, penalty=1, debug=False, ensemble_size=5):
         _, _, comp_response = check_syntax(code_filepath)
         try:
            with open(code_filepath, "r") as f:
                code = f.read()
         except Exception as e:
            print(f"Error reading file {code_filepath}: {e}")
            code = ""
         return evaluate_ensemble_impl(self.llm, self.oneStepPrompts, question, rubric, code, comp_response, syntaxMarks, penalty, debug, ensemble_size)

#############################
# JavaJudge Class
#############################
class JavaJudge:
    def __init__(self, model="gpt-4o-mini", baseURL=None, api_key=None):
        self._loadKeys()
        if baseURL is None:
            self.llm = ChatOpenAI(model=model, temperature=0).bind(response_format={"type": "json_object"})
        else:
            if api_key is None:
                raise Exception("API key required for custom baseURL")
            self.llm = ChatOpenAI(model=model, temperature=0, base_url=baseURL, api_key=api_key).bind(response_format={"type": "json_object"})
        self._loadPrompts()

    def _loadKeys(self):
        if "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key:")

    def _loadPrompts(self) -> list[str]:
        self.oneStepPrompt = '''You are an expert code evaluator, evaluating code submissions for a Java based Object Oriented Programming test at a university level.
You will be provided with the question and a rubric that describes the criteria for evaluation, with a marking scheme. 
The question is a code sample that the examiner provides, containing a template wherein the student is required to write the code as well as comments and instructions from the examiner's end.
Following this you will be provided with the code submission, along with the response from the Java compiler that runs this code.
Note that the code may be formatted liberally, the specific positioning of the code within the methods are not important.
Code may be present either before or after the comments prepared by the instructor.
You are to evaluate the code based only on logical correctness. You are to ignore any syntax errors that the compiler may have thrown. 
Any syntax errors that you encounter can be treated as correct syntax, and you are to infer the student's logical flow and intention from the code.
You are to return your response as a JSON dictionary containing a detailed, nested evaluation of the student's marks for each line in the rubric.
For each line in the rubric, you are to provide the line as the key and your assigned marks as the value.
DO NOT RETURN ANY ADDITIONAL TEXT ASIDE FROM THE JSON DICTIONARY.
Question: {}
Rubric: {}
Code Submission: {}
Compiler Response: {}
'''
        self.twoStepPrompt = [
            '''You are an expert code evaluator, evaluating code submissions for a Java based Object Oriented Programming test at a university level.
You will be provided with the code submission and no context whatsoever. You are to infer the student's logical flow and intention from the code.
You are to ignore any syntaxical errors, and are solely to evaluate the code based on logical correctness.
Code Submission: {}
''', 
'''You are an expert code evaluator, evaluating code submissions for a Java based Object Oriented Programming test at a university level.
You will be provided a question, a marking rubric, and also with the logical flow and intention of a student's code. 
The question is a code sample that the examiner provides, containing a template wherein the student is required to write the code as well as comments and instructions from the examiner's end.
You are to compare the student's logic with what was asked by the question and the rubric.
Question: {}
Rubric: {}
Logical Flow and Intention: {}
'''
    ]

    def _getOneStepResponse(self, question, rubric, code, compilerResponse):
        prompt = self.oneStepPrompt.format(question, rubric, code, compilerResponse)
        print(prompt)
        return json.loads(self.llm.invoke(prompt).content)

    def _syntaxMarks(self, compilerResponse, syntaxMarks, penalty):
        errorCount = len(compilerResponse)
        return max(syntaxMarks - (penalty * errorCount), 0)

    def evaluateAIO(self, question, rubric, codeFilepath, syntaxMarks=5, penalty=1, debug=False):
        compilerResponse = check_java_syntax(codeFilepath)
        try:
            with open(codeFilepath, "r") as f:
                solution = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return 0, 0, 0

        response = self._getOneStepResponse(question, rubric, solution, compilerResponse)

        logicalMarks = 0
        def accumulate(d):
            nonlocal logicalMarks
            for v in d.values():
                if isinstance(v, dict): accumulate(v)
                elif isinstance(v, int): logicalMarks += v
        accumulate(response)

        syntaxScore = self._syntaxMarks(compilerResponse, syntaxMarks, penalty)
        final = logicalMarks + syntaxScore

        if debug:
            print("compilerResponse:", compilerResponse)
            print("LLM response:", response)
            print("Logical:", logicalMarks, "Syntax:", syntaxScore, "Final:", final)

        return logicalMarks, syntaxScore, final

#############################
# Top-Level Evaluation Function
#############################

def eval_submissions(rubric_filepath,
                     model_solution_filepath,
                     problem_statement_filepath,
                     submissions_dir,
                     scoring_type='A',
                     output_csv='results.csv',
                     log_file='evaluation.log',
                     syntaxMarks=5,
                     penalty=1,
                     debug=False,
                     ensemble_size=5,
                     file_ext=".txt"):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    logging.info("Evaluation started")

    try:
        rubric = load_rubric(rubric_filepath)
        question = load_text_file(model_solution_filepath)
        problem_statement = load_text_file(problem_statement_filepath)
    except Exception as e:
        logging.error("Error loading input files: " + str(e))
        raise

    submissions = get_student_submissions(submissions_dir, file_ext=file_ext)
    logging.info(f"Found {len(submissions)} submissions.")

    judge = CodeJudge(model="gpt-4o-mini")
    java_judge = JavaJudge(model="gpt-4o-mini")

    results = []

#add scoring type c for ensemble
    for sub in tqdm(submissions, desc="Evaluating submissions"):
        filepath = sub.get("filepath")
        student_id = sub.get("student_id", "unknown")
        # try:
        if scoring_type == 'A':
            logical, syntax, final = judge.evaluate_one_step(question, rubric, filepath, syntaxMarks, penalty, debug)
        elif scoring_type == 'B':
            logical, syntax, final = judge.evaluate_two_step(question, rubric, filepath, syntaxMarks, penalty, debug)
        elif scoring_type == 'D':
            logical, syntax, final = java_judge.evaluateAIO(question, rubric, filepath, syntaxMarks, penalty, debug)
        elif scoring_type == 'C':
            if "OPENAI_API_KEY" not in os.environ:
                from getpass import getpass
                os.environ["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
            api_key = os.environ.get("OPENAI_API_KEY")
            logical, syntax, final = evaluate_codev(filepath, api_key=api_key, ensemble_size=ensemble_size, debug=debug)

        else:
            logical, syntax, final = judge.evaluate_one_step(question, rubric, filepath, syntaxMarks, penalty, debug)
        results.append({
            "student_id": student_id,
            "logical_marks": logical,
            "syntax_marks": syntax,
            "total_marks": final
        })
        # except Exception as e:
        #     logging.error(f"Error evaluating submission {student_id}: {e}")

    headers = ['student_id', 'logical_marks', 'syntax_marks', 'total_marks']
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
        logging.info("Evaluation completed. Results written to " + output_csv)
    except Exception as e:
        logging.error("Error writing CSV output: " + str(e))
        raise

#############################
# Command-line Execution
#############################

def main():
    parser = argparse.ArgumentParser(description="Evaluate student code submissions.")
    parser.add_argument("rubric_filepath", help="Path to the rubric file (text or JSON).")
    parser.add_argument("model_solution_filepath", help="Path to the model solution file.")
    parser.add_argument("problem_statement_filepath", help="Path to the problem statement file.")
    parser.add_argument("submissions_dir", help="Directory containing student submissions.")
    parser.add_argument(
        "--scoring_type",
        choices=["A", "B", "C", "D"],
        default="A",
        help=(
            "Scoring type: 'A' one-step rubric evaluation (default), "
            "'B' two-step rubric evaluation, 'C' ensemble code evaluation, "
            "or 'D' AI-O one-shot evaluation."
        ),
    )
    parser.add_argument(
        "--output_csv", default="results.csv", help="Output CSV path (default: results.csv)."
    )
    parser.add_argument(
        "--log_file", default="evaluation.log", help="Log file path (default: evaluation.log)."
    )
    parser.add_argument(
        "--syntaxMarks", type=float, default=5,
        help="Maximum syntax marks (default: 5)."
    )
    parser.add_argument(
        "--penalty", type=float, default=1,
        help="Penalty per syntax error (default: 1)."
    )
    parser.add_argument(
        "--ensemble_size", type=int, default=5,
        help="Ensemble size for scoring type C (default: 5)."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output."
    )
    parser.add_argument(
        "--file_ext", default=".txt",
        help="Submission file extension (default: .txt)."
    )
    args = parser.parse_args()

    eval_submissions(
        rubric_filepath=args.rubric_filepath,
        model_solution_filepath=args.model_solution_filepath,
        problem_statement_filepath=args.problem_statement_filepath,
        submissions_dir=args.submissions_dir,
        scoring_type=args.scoring_type,
        output_csv=args.output_csv,
        log_file=args.log_file,
        syntaxMarks=args.syntaxMarks,
        penalty=args.penalty,
        debug=args.debug,
        ensemble_size=args.ensemble_size,
        file_ext=args.file_ext,
    )

if __name__ == "__main__":
    main()