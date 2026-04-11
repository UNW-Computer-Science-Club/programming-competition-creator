import shutil
from pathlib import Path
from string import Template

from programming_competition_creator import Competition
from programming_competition_creator.utils import get_file_contents


def scaffold(args):
    competition = Competition.read()

    output_dir = Path("problems")
    output_dir.mkdir(exist_ok=True)

    if args.purge:
        for problem_dir in output_dir.iterdir():
            if not problem_dir.is_dir():
                continue
            problem = competition.get_problem_by_shortname(problem_dir.name)
            if problem is None:
                shutil.rmtree(problem_dir)

    for problem in competition.problems:
        problem_dir = output_dir / problem.shortname
        problem_dir.mkdir(exist_ok=True)

        statement_path = problem_dir / "statement.md"
        if not statement_path.exists():
            statement_path.write_text(
                Template(get_file_contents("statement-template.md")).substitute(problem_name=problem.name)
            )

        solution_path = problem_dir / "solution.py"
        if not solution_path.exists():
            solution_path.write_text(get_file_contents("solution-template.py"))

        generator_path = problem_dir / "generator.py"
        if not generator_path.exists():
            generator_path.write_text(get_file_contents("generator-template.py"))
