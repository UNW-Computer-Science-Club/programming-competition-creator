import asyncio
import logging
from pathlib import Path

import aiodocker
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


async def test(args):
    abs_path = Path(args.build_dir).resolve()
    problems_root = abs_path / "problems"

    dirs = [path for path in problems_root.iterdir() if path.is_dir()]
    yaml = YAML()

    docker_client = aiodocker.Docker()
    container = None

    problem_found = not args.problem
    # verifyproblem doesn't like the `legacy-icpc` format, so we need to replace it with `legacy`
    changed_problem_yamls = []

    for file in problems_root.rglob("problem.yaml"):
        with open(file, "r") as f:
            content = yaml.load(f)

        if content.get("problem_format_version") == "legacy-icpc":
            content["problem_format_version"] = "legacy"
            changed_problem_yamls.append(str(file))
            with open(file, "w") as f:
                yaml.dump(content, f)

    try:
        await docker_client.images.pull("problemtools/icpc")
        container = await docker_client.containers.run(
            config={
                "Image": "problemtools/icpc",
                "Cmd": ["sleep", "infinity"],
                "Tty": True,
                "WorkingDir": "/work",
                "HostConfig": {
                    "Binds": [f"{abs_path}:/work:rw"],
                },
            }
        )

        run_jobs: list[tuple[Path, list[str]]] = []

        for dir in dirs:
            if args.problem and dir.name != args.problem:
                continue
            elif args.problem:
                problem_found = True

            logger.debug(f"Starting verification for {dir}")

            command = [
                "verifyproblem",
                f"/work/{dir.relative_to(abs_path)}",
            ]

            if args.problem and args.jobs > 1:
                command.append("-j")
                command.append(str(args.jobs))

            if args.parts:
                command.append("--parts")
                command.extend(args.parts)

            run_jobs.append((dir, command))

        if not problem_found:
            raise ValueError(f"Problem '{args.problem}' not found in {abs_path / 'problems'}")

        failures = []

        semaphore = asyncio.Semaphore(max(1, args.jobs))

        async def run_verifyproblem(problem_dir: Path, command: list[str]) -> tuple[Path, int, bytes]:
            async with semaphore:
                exec_instance = await container.exec(command, stdout=True, stderr=True, tty=False)
                output = await exec_instance.start(detach=True)
                info = await exec_instance.inspect()
                return problem_dir, info.get("ExitCode", 1), output

        tasks = [asyncio.create_task(run_verifyproblem(problem_dir, command)) for problem_dir, command in run_jobs]

        for task in asyncio.as_completed(tasks):
            problem_dir, exit_code, output = await task
            if output:
                logger.info("verifyproblem output for %s:\n%s", problem_dir.name, output.decode(errors="replace"))
            if exit_code != 0:
                failures.append((problem_dir, exit_code))

        if failures:
            failed_problems = ", ".join(f"{problem.name} (exit {code})" for problem, code in failures)
            raise RuntimeError(f"verifyproblem failed for: {failed_problems}")
    finally:
        if container is not None:
            try:
                await container.stop(t=3)
            finally:
                await container.delete(force=True)

        await docker_client.close()

        for file in changed_problem_yamls:
            with open(file, "r") as f:
                content = yaml.load(f)
            if content.get("problem_format_version") == "legacy":
                content["problem_format_version"] = "legacy-icpc"
            with open(file, "w") as f:
                yaml.dump(content, f)
