from setuptools import setup, find_packages

setup(
    name="llm-grader",
    version="0.1.0",
    description="A CLI tool to grade code submissions with LLM-based rubrics and ensemble code evaluation.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["tqdm", "langchain_openai", "openai"],
    entry_points={
        "console_scripts": [
            "llm-grader=llm_grader.code_evaluator:main",
        ],
    },
)