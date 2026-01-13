from datetime import datetime, timedelta
from typing import List, Optional, Type
from uuid import UUID, uuid4

import pytz
from dateutil.parser import parse
from pydantic import BaseModel, Field
from ruamel.yaml import YAML


class ProblemTestCase(BaseModel):
    input: str
    answer: str


class Problem(BaseModel):
    name: str
    shortname: str
    uuid: UUID = Field(default_factory=uuid4)
    color: str
    author: str
    label: str

    def to_domjudge(self: "Problem", contest_name: str) -> dict:
        return {
            "problem_format_version": "legacy-icpc",
            "name": self.name,
            "author": self.author,
            "source": contest_name,
            "license": "educational",
            "uuid": str(self.uuid),
        }

    def to_domjudge_metadata(self: "Problem") -> dict:
        return {
            "id": self.shortname,
            "label": self.label,
            "name": self.name,
            "rgb": self.color,
            "uuid": str(self.uuid),
        }


class Competition(BaseModel):
    name: str
    id: str
    shortName: str
    activateTime: datetime
    startTime: datetime
    endTime: datetime
    problems: List[Problem]

    @classmethod
    def create_from_dict(cls, data: dict) -> "Competition":
        # Parse timezone
        timezone = pytz.timezone(data["timeZone"])

        # Parse activate_time with timezone
        activate_time = parse(
            data["activateTime"],
            default=timezone.localize(datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)),
        )
        if activate_time.tzinfo is None:
            activate_time = timezone.localize(activate_time)

        # Parse start and end times - handle both absolute dates and relative times
        start_datetime = parse(data["startTime"], default=activate_time)
        end_datetime = parse(data["endTime"], default=activate_time)

        return cls(
            name=data["name"],
            id=data["id"],
            shortName=data["shortName"],
            activateTime=activate_time,
            startTime=start_datetime,
            endTime=end_datetime,
            problems=[Problem.model_validate(problem) for problem in data["problems"]],
        )

    @classmethod
    def read(cls: Type["Competition"]) -> "Competition":
        competition_yaml = YAML()
        with open("competition.yaml", "r") as f:
            data = competition_yaml.load(f)

        result = cls.create_from_dict(data)

        did_edit = False
        for idx, problem in enumerate(data["problems"]):
            if not problem.get("uuid"):
                problem["uuid"] = str(result.problems[idx].uuid)
                did_edit = True
        if did_edit:
            with open("competition.yaml", "w") as f:
                competition_yaml.dump(data, f)

        return result

    @property
    def duration(self) -> timedelta:
        return self.endTime - self.startTime

    def to_domjudge(self: "Competition") -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "short_name": self.shortName,
            "activate_time": self.activateTime.isoformat(),
            "start_time": self.startTime.isoformat(),
            "duration": f"{self.duration}",
            "scoreboard_type": "pass-fail",
        }

    def to_domjudge_problem_metadata(self: "Competition") -> List[dict]:
        return [x.to_domjudge_metadata() for x in self.problems]

    def get_problem_by_shortname(self, shortname: str) -> Optional[Problem]:
        for problem in self.problems:
            if problem.shortname == shortname:
                return problem
        return None
