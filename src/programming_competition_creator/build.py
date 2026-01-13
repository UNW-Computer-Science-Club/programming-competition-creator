import asyncio
import asyncio.subprocess
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
from typing import List
from zipfile import ZipFile

from ruamel.yaml import YAML

from programming_competition_creator.competition import Competition, ProblemTestCase


def ensure_trailing_newline(string: str) -> str:
    return string + "\n" if not string.endswith("\n") else string


async def run_pandoc(outfile: str, input_document: str, options: List[str] = []):
    cmd = [
        "pandoc",
        "--from",
        "markdown",
        "--to",
        "pdf",
        "--pdf-engine=lualatex",
        "--template",
        "eisvogel",
        "-o",
        outfile,
    ]
    cmd.extend(options)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
    )

    proc.stdin.write(input_document.encode())
    await proc.stdin.drain()

    proc.stdin.close()

    await proc.wait()


async def build(args):
    competition = Competition.read()

    output_dir = Path(args.output_dir)

    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "contest.yaml", "w") as f:
        YAML().dump(competition.to_domjudge(), f)

    with open(output_dir / "problems.yaml", "w") as f:
        YAML().dump(competition.to_domjudge_problem_metadata(), f)

    for problem_dir in output_dir.iterdir():
        if problem_dir.is_dir():
            problem = competition.get_problem_by_shortname(problem_dir.name)
            if problem is None:
                shutil.rmtree(problem_dir)

    pandoc_tasks = []

    for problem in competition.problems:
        problems_out_dir = output_dir / "problems"
        problems_out_dir.mkdir(exist_ok=True)

        problem_out_dir = problems_out_dir / problem.shortname
        problem_in_dir = Path("problems") / problem.shortname
        problem_out_dir.mkdir(exist_ok=True)

        with open(problem_out_dir / "problem.yaml", "w") as f:
            YAML().dump(problem.to_domjudge(competition.name), f)

        solution_out_dir = problem_out_dir / "submissions" / "accepted"
        solution_out_dir.mkdir(exist_ok=True, parents=True)

        shutil.copyfile(problem_in_dir / "solution.py", solution_out_dir / "solution.py")

        input_validator_out_dir = problem_out_dir / "input_validators"
        input_validator_out_dir.mkdir(exist_ok=True)

        shutil.copyfile(problem_in_dir / "sanitychecker.ctd", input_validator_out_dir / "input_validator.ctd")

        spec = importlib.util.spec_from_file_location("generator", problem_in_dir / "generator.py")

        if not spec or not spec.loader:
            raise ValueError(f"Generator or loader file not found for problem {problem.shortname}")

        generator = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(generator)

        if not hasattr(generator, "generate") or not callable(generator.generate):
            raise ValueError(f"Generator module for problem {problem.shortname} does not have a generate function")

        generated = generator.generate()
        if type(generated) is not list:
            raise ValueError(f"Generator module for problem {problem.shortname} does not return a list")

        solutions: List[ProblemTestCase] = [ProblemTestCase.model_validate(test_case) for test_case in generated]

        test_data_dir = problem_out_dir / "data"
        shutil.rmtree(test_data_dir, ignore_errors=True)
        test_data_dir.mkdir(exist_ok=True)

        test_data_example_dir = test_data_dir / "sample"
        test_data_example_dir.mkdir(exist_ok=True)

        test_data_secret_dir = test_data_dir / "secret"
        test_data_secret_dir.mkdir(exist_ok=True)

        inputs = set()

        statement_out_dir = problem_out_dir / "problem_statement"
        statement_out_dir.mkdir(exist_ok=True)

        with open(problem_in_dir / "statement.md", "r") as f:
            statement = f.read()

        regex = re.compile(r"@TESTCASE_(IN|ANS)\s+```\s+(.*?)```", re.MULTILINE | re.DOTALL)

        idx = 0
        for match in regex.finditer(statement):
            with open(test_data_example_dir / f"{idx}.{match.group(1).lower()}", "x") as f:
                normalized = ensure_trailing_newline(match.group(2))
                f.write(normalized)
                inputs.add(normalized)
            if match.group(1) == "ANS":
                idx += 1

        for case_index, case in enumerate(solutions):
            normalized = ensure_trailing_newline(case.input)
            if normalized in inputs:
                continue

            inputs.add(normalized)

            with open(test_data_secret_dir / f"{case_index}.in", "w") as f:
                f.write(normalized)

            with open(test_data_secret_dir / f"{case_index}.ans", "w") as f:
                f.write(ensure_trailing_newline(case.answer))

        filtered_statement = statement.replace("@TESTCASE_IN\n", "").replace("@TESTCASE_ANS\n", "")

        pandoc_tasks.append(run_pandoc(statement_out_dir / "problem.pdf", filtered_statement))

    await asyncio.gather(*pandoc_tasks)

    for file in output_dir.glob("*.zip"):
        shutil.rmtree(file, ignore_errors=True)

    problems_out_dir = output_dir / "problems"
    for problem in competition.problems:
        problem_out_dir = problems_out_dir / problem.shortname

        with ZipFile(problems_out_dir / f"{problem.shortname}.zip", "w") as zip_file:
            for file in problem_out_dir.rglob("*"):
                zip_file.write(file, file.relative_to(problem_out_dir))
