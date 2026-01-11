# Programming Competition

In this directory, you will find a programming competition problemset.

You can interact with the problemset by both editing the files (if you have MCP
tools enabled) and by using the programming-competition-creator tool. This tool
can be invoked with the `progcc` command. Here is the help page:

```
$program_usage
```

There will be a `competition.yaml` file that contains the problem descriptions.
If not, you can create one using the `init` command.

If the only problem in `competition.yaml` is the hello world problem, that means
that the user has not created any problems yet. They may want you to do that.

The `competition.yaml` file should adhere to the following spec:

```json
$competition_yaml_spec
```

Each problem defined in the competition file must have a directory named after
its shortname. For example, a problem with a `shortName` of `helloworld` must
have a directory called `problems/helloworld`. You don't have to do this
manually. Running `progcc scaffold` will take the `competition.yaml` file and
create the necessary directories for each problem.

Each directory will have four files: `generator.py`, `solution.py`,
`statement.md`, and `sanitychecker.ctd`.

`generator.py` must have a `generate` function that takes no arguments and
returns a `list` of `dicts` that each have an `input` and `answer` key. You
should make use of Python's random number generator to generate random test
cases of a sizable amount. You should also vary the types of test cases. For
example, an arithmetic calculator test generator should not generate 200
variations of `100 + 100`, `38 + 23`, `128 + 298`, etc. Instead, you should
generate a variety of test cases that cover different edge cases and scenarios.
For example, `100 / 2`.

`solution.py` must take the `input` data from STDIN and print the `answer` to
STDOUT.

`statement.md` must contain a Markdown-formatted statement of the problem. Under
an examples section, you may mark code blocks with the input and answer, and
these will be used to generate test cases. To do this:

````markdown
# Examples

@TESTCASE_IN
```
an example of some input for a test case
```

Output:

@TESTCASE_ANS
```
the corresponding output for the input
```
````

Note the `@TESTCASE_IN` and `@TESTCASE_ANS` tags. These will be removed when the
competitor sees the document. They are only used to generate test cases so that
the statement stays in sync with the actual test cases.

`sanitychecker.ctd` must contain a Checktestdata-formatted input validator. That
means it will validate the `input` data, not the competitor's `answer`.

Here is the Checktestdata language specification:

$checktestdata_spec
