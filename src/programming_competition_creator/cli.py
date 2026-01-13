import argparse
import asyncio
import logging

from programming_competition_creator import build, init, scaffold, test

logging.basicConfig(level=logging.INFO)

arg_parser = argparse.ArgumentParser(description="Build Domjudge competitions")
subparsers = arg_parser.add_subparsers(dest="command", required=True)

subparsers.add_parser("init", help="Create directory structure for a new competition")

build_args = subparsers.add_parser("build", help="Build the problem archives")
build_args.add_argument("--output-dir", default="build", help="Output directory for the problem archives")

scaffold_args = subparsers.add_parser(
    "scaffold", help="Takes a competition YAML file and generates a directory structure"
)
scaffold_args.add_argument("-P", "--purge", action="store_true", help="Removes problems that are not in the YAML file")

test_args = subparsers.add_parser("test", help="Test the problem archives")
test_args.add_argument("--build-dir", default="build", help="Directory containing the built problems")
test_args.add_argument("--problem", type=str, help="Problem to test")
test_args.add_argument("-j", "--jobs", type=int, default=1, help="Number of jobs to run in parallel")
test_args.add_argument(
    "--parts",
    "-p",
    type=str,
    choices=["config", "data", "graders", "statement", "submissions", "validators"],
    nargs="+",
    help="Parts to test",
)


async def async_main():
    args = arg_parser.parse_args()

    if args.command == "init":
        init(args, arg_parser.format_help())
    elif args.command == "build":
        await build(args)
    elif args.command == "scaffold":
        scaffold(args)
    elif args.command == "test":
        test(args)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
