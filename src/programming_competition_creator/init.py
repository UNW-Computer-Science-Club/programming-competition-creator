from pathlib import Path

from programming_competition_creator.utils import get_file_contents


def init(args):
    template_content = get_file_contents("competition-template.yaml")

    if not Path("competition.yaml").exists():
        with open("competition.yaml", "x") as new_file:
            new_file.write(template_content)

    Path("problems").mkdir()
