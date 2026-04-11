from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import requests

from programming_competition_creator.build import build
from programming_competition_creator.competition import Competition


def _api_base_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/api/v4"):
        return trimmed
    return f"{trimmed}/api/v4"


def _request_or_raise(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        message = response.text.strip()
        detail = f"{exc}\n{message}" if message else str(exc)
        raise RuntimeError(detail) from exc


def _create_contest(
    session: requests.Session,
    api_base: str,
    contest_yaml_path: Path,
    timeout: int,
) -> str:
    with open(contest_yaml_path, "rb") as contest_yaml:
        response = session.post(
            f"{api_base}/contests",
            files={"yaml": (contest_yaml_path.name, contest_yaml, "application/x-yaml")},
            timeout=timeout,
        )

    _request_or_raise(response)

    try:
        payload = response.json()
    except ValueError:
        payload = response.text.strip()

    if isinstance(payload, dict):
        cid = payload.get("id") or payload.get("cid")
        if cid is None:
            raise RuntimeError(f"Contest created, but API did not return a contest ID: {payload}")
        return str(cid)
    if isinstance(payload, int):
        return str(payload)
    if isinstance(payload, str) and payload:
        return payload

    raise RuntimeError(f"Contest created, but API returned an unexpected response: {payload}")


def _upload_problem_metadata(
    session: requests.Session,
    api_base: str,
    cid: str,
    problems_yaml_path: Path,
    timeout: int,
) -> None:
    with open(problems_yaml_path, "rb") as problems_yaml:
        response = session.post(
            f"{api_base}/contests/{cid}/problems/add-data",
            files={"data": (problems_yaml_path.name, problems_yaml, "application/x-yaml")},
            timeout=timeout,
        )

    _request_or_raise(response)


def _upload_problem_archive(
    session: requests.Session,
    api_base: str,
    cid: str,
    problem_id: str,
    archive_path: Path,
    timeout: int,
) -> None:
    with open(archive_path, "rb") as archive:
        response = session.post(
            f"{api_base}/contests/{cid}/problems",
            data={"problem": problem_id},
            files={"zip": (archive_path.name, archive, "application/zip")},
            timeout=timeout,
        )

    _request_or_raise(response)


async def publish(args) -> None:
    output_dir = Path(args.build_dir)
    if not args.skip_build:
        await build(SimpleNamespace(output_dir=str(output_dir)))

    contest_yaml_path = output_dir / "contest.yaml"
    problems_yaml_path = output_dir / "problems.yaml"
    problems_dir = output_dir / "problems"

    if not contest_yaml_path.exists() or not problems_yaml_path.exists() or not problems_dir.exists():
        raise RuntimeError(f"Build output not found in '{output_dir}'. Run `progcc build` first or omit --skip-build.")

    competition = Competition.read()
    api_base = _api_base_url(args.url)
    timeout = args.timeout

    session = requests.Session()
    session.auth = (args.username, args.password)

    cid: Optional[str] = args.contest_id
    if cid:
        print(f"Using existing contest ID: {cid}")
    else:
        print("Creating contest...")
        cid = _create_contest(session, api_base, contest_yaml_path, timeout)
        print(f"Created contest with ID: {cid}")

    print("Uploading problem metadata...")
    _upload_problem_metadata(session, api_base, cid, problems_yaml_path, timeout)

    for problem in competition.problems:
        problem_id = competition.problem_shortname_for_domjudge(problem)
        archive_path = problems_dir / f"{problem_id}.zip"
        if not archive_path.exists():
            raise RuntimeError(f"Missing problem archive: {archive_path}")

        print(f"Uploading problem '{problem_id}'...")
        _upload_problem_archive(session, api_base, cid, problem_id, archive_path, timeout)

    print(f"Publish completed successfully to contest {cid}.")
