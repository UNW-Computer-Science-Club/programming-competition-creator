import logging
import subprocess
from glob import glob
from pathlib import Path
from typing import cast

from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


def test(args):
    subprocess_handles = []
    abs_path = Path(args.build_dir).resolve()

    dirs = list((abs_path / "problems").iterdir())

    subprocess.run(["docker", "pull", "problemtools/icpc"], check=True)

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
            dir = cast(Path, dir)
            # Wait for a process to complete if we have 5 running
            if len(subprocess_handles) >= 5:
                # Wait for the oldest process to complete
                subprocess_handles[0].wait()
                subprocess_handles.pop(0)

            logger.debug(f"Starting verification for {dir}")

            subprocess_handles.append(
                subprocess.Popen(
                    [
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
                )
            )

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
