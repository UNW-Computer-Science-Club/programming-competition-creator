from importlib.resources import files


def get_file_contents(path: str) -> str:
    return files("programming_competition_creator").joinpath("data", path).read_text(encoding="utf-8")
