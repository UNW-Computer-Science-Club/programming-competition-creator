import subprocess
from pathlib import Path
from string import Template

import requests

from programming_competition_creator.utils import get_file_contents


def init(args, help_text):
    template_content = get_file_contents("competition-template.yaml")

    if not Path("competition.yaml").exists():
        with open("competition.yaml", "x") as new_file:
            new_file.write(template_content)
        print("Wrote competition.yaml")

    Path("problems").mkdir(exist_ok=True)

    rules_path = Path(".rules")

    if not rules_path.exists():
        competition_json_spec = requests.get(
            "https://raw.githubusercontent.com/UNW-Computer-Science-Club/programming-competition-creator/refs/heads/main/schemas/competition.json"
        ).text

        checktestdata_spec = requests.get(
            "https://raw.githubusercontent.com/DOMjudge/checktestdata/refs/heads/main/doc/format-spec.md"
        ).text

        rules_path.write_text(
            Template(get_file_contents("rules-template.md")).substitute(
                program_usage=help_text,
                competition_json_spec=competition_json_spec,
                checktestdata_spec=checktestdata_spec,
            )
        )

        print("Created .rules")

    gitignore_path = Path(".gitignore")

    if not gitignore_path.exists():
        gitignore_path.write_text(get_file_contents("gitignore-template.gitignore"))

        print("Created .gitignore")

    git_dir_path = Path(".git")

    if not git_dir_path.exists():
        subprocess.run(["git", "init"])

        print("Initialized git")
