import logging
import subprocess
from glob import glob
from pathlib import Path
from typing import cast

TERM_YELLOW = "\033[33m"
TERM_RESET = "\033[0m"

from ruamel.yaml import YAML

from programming_competition_creator.utils import get_file_contents

logger = logging.getLogger(__name__)


def test(args):
    subprocess_handles = []
    abs_path = Path(args.build_dir).resolve()

    dirs = list(filter(lambda x: x.is_dir(), (abs_path / "problems").iterdir()))

    subprocess.run(["docker", "pull", "problemtools/icpc"], check=True)

    problem_found = not args.problem
    # verifyproblem doesn't like the `legacy-icpc` format, so we need to replace it with `legacy`
    yaml_records = {}
    for file in glob(str(abs_path / "problems") + "/**/problem.yaml"):
        with open(file, "r") as f:
            yaml_record = YAML()
            yaml_records[file] = yaml_record
            content = yaml_record.load(f)
        if content.get("problem_format_version") == "legacy-icpc":
            content["problem_format_version"] = "legacy"
        with open(file, "w") as f:
            yaml_record.dump(content, f)

    try:
        for i, dir in enumerate(dirs):
            if args.problem and dir.name != args.problem:
                continue
            elif args.problem:
                problem_found = True
            dir = cast(Path, dir)
            # Wait for a process to complete if we have 5 running
            if len(subprocess_handles) >= args.jobs:
                # Wait for the oldest process to complete
                subprocess_handles[0].wait()
                subprocess_handles.pop(0)

            logger.debug(f"Starting verification for {dir}")

            if dir.name != "helloworld" and (
                Path("problems") / dir.name / "sanitychecker.ctd"
            ).read_text() == get_file_contents("ctd-template.ctd"):
                print(f"{TERM_YELLOW}WARNING: The problem {dir.name} still has the template statement.{TERM_RESET}")

            docker_args = [
                "docker",
                "run",
                "--rm",
                "-t",
                "-v",
                f"{abs_path}:/work",
                "problemtools/icpc",
                "verifyproblem",
                f"/work/{dir.relative_to(abs_path)}",
            ]

            if args.problem and args.jobs > 1:
                docker_args.append("-j")
                docker_args.append(str(args.jobs))

            if args.parts:
                docker_args.append("--parts")
                docker_args.extend(args.parts)

            subprocess_handles.append(subprocess.Popen(docker_args))

        # Wait for all remaining processes to complete
        for handle in subprocess_handles:
            handle.wait()
    finally:
        yaml_records = {}
        for file in glob(str(abs_path / "problems") + "/**/problem.yaml"):
            with open(file, "r") as f:
                yaml_record = YAML()
                yaml_records[file] = yaml_record
                content = yaml_record.load(f)
            if content.get("problem_format_version") == "legacy":
                content["problem_format_version"] = "legacy-icpc"
            with open(file, "w") as f:
                yaml_record.dump(content, f)
