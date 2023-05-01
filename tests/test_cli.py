import os
import pytest
from click.testing import CliRunner


def test_exit_codes():
    # We shouldn't change exit codes so that clients can rely on them
    from pycobertura.cli import ExitCodes

    assert ExitCodes.OK == 0
    assert ExitCodes.EXCEPTION == 1
    assert ExitCodes.COVERAGE_WORSENED == 2
    assert ExitCodes.NOT_ALL_CHANGES_COVERED == 3


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(x, id="_".join(x))
        for x in [
            [],
            ["-f", "text"],
            ["--format", "text"],
            ["-f", "csv"],
            ["--format", "csv"],
            ["-f", "csv", "--delimiter", "\t"],
            ["-f", "csv", "--delimiter", ";"],
            ["--format", "csv", "--delimiter", "\t"],
            ["--format", "csv", "--delimiter", ";"],
            ["-f", "markdown"],
            ["--format", "markdown"],
            ["-f", "json"],
            ["--format", "json"],
            ["-f", "yaml"],
            ["--format", "yaml"],
            ["-f", "github-annotation"],
            ["--format", "github-annotation"],
            [
                "-f",
                "github-annotation",
                "--annotation-title=JCov",
                "--annotation-level=error",
                "--annotation-message=missing coverage",
            ],
            [
                "--format",
                "github-annotation",
                "--annotation-title=JCov",
                "--annotation-level=error",
                "--annotation-message=missing coverage",
            ],
        ]
    ],
)
def test_show__format(args, snapshot):
    from pycobertura.cli import show, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        show,
        ["tests/dummy.original.xml"] + args,
        catch_exceptions=False,
    )
    assert result.output.encode() == snapshot()
    assert result.exit_code == ExitCodes.OK


def test_show__format_html():
    from pycobertura.cli import show, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        show, ["tests/dummy.original.xml", "--format", "html"], catch_exceptions=False
    )
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.OK


def test_show__output_to_file():
    from pycobertura.cli import show, ExitCodes

    runner = CliRunner()
    for opt in ("-o", "--output"):
        result = runner.invoke(
            show, ["tests/cobertura.xml", opt, "report.out"], catch_exceptions=False
        )
        with open("report.out") as f:
            report = f.read()
        os.remove("report.out")
        assert result.output == ""
        assert (
            report
            == """\
Filename                          Stmts    Miss  Cover    Missing
------------------------------  -------  ------  -------  ---------
Main.java                            15       0  100.00%
search/BinarySearch.java             12       1  91.67%   24
search/ISortedArraySearch.java        0       0  100.00%
search/LinearSearch.java              7       2  71.43%   19-24
TOTAL                                34       3  90.00%"""
        )
    assert result.exit_code == ExitCodes.OK


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(x, id="_".join(x))
        for x in [
            [],
            ["--color"],
            ["--no-color"],
            ["-f", "text"],
            ["--format", "text"],
            ["-f", "csv"],
            ["--format", "csv"],
            ["-f", "csv", "--delimiter", "\t"],
            ["-f", "csv", "--delimiter", ";"],
            ["--format", "csv", "--delimiter", "\t"],
            ["--format", "csv", "--delimiter", ";"],
            ["-f", "markdown"],
            ["--format", "markdown"],
            ["--format", "markdown", "--color"],
            ["--format", "markdown", "--no-color"],
            ["-f", "json"],
            ["--format", "json"],
            ["--format", "json", "--color"],
            ["--format", "json", "--no-color"],
            ["-f", "yaml"],
            ["--format", "yaml"],
            ["-f", "yaml", "--color"],
            ["--format", "yaml", "--color"],
            ["-f", "yaml", "--no-color"],
            ["--format", "yaml", "--no-color"],
        ]
    ],
)
def test_diff__format(args, snapshot):
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "tests/dummy.source1/coverage.xml",
            "tests/dummy.source2/coverage.xml",
        ]
        + args,
        catch_exceptions=False,
    )
    assert result.output.encode() == snapshot
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__output_to_file():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()

    for opt in ("-o", "--output"):
        result = runner.invoke(
            diff,
            [
                "tests/dummy.source1/coverage.xml",
                "tests/dummy.source2/coverage.xml",
                opt,
                "report.out",
            ],
            catch_exceptions=False,
        )
        with open("report.out") as f:
            report = f.read()
        os.remove("report.out")
        assert result.output == ""
        assert (
            report
            == """\
Filename           Stmts    Miss  Cover     Missing
---------------  -------  ------  --------  ---------
dummy/dummy.py         0      -2  +40.00%
dummy/dummy2.py       +2      +1  -25.00%   5
dummy/dummy3.py       +2      +2  +100.00%  1, 2
TOTAL                 +4      +1  +31.06%"""
        )
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__format_html__no_source_on_disk():
    from pycobertura.cli import diff
    from pycobertura.filesystem import FileSystem

    runner = CliRunner()
    pytest.raises(
        FileSystem.FileNotFound,
        runner.invoke,
        diff,
        [
            "--format",
            "html",
            "tests/dummy.with-dummy2-better-cov.xml",
            "tests/dummy.with-dummy2-better-and-worse.xml",
        ],
        catch_exceptions=False,
    )


@pytest.mark.parametrize(
    "source1, source2, prefix1, prefix2",
    [
        ("tests/", "tests/dummy", "dummy/", ""),
        ("tests/dummy", "tests/", "", "dummy/"),
        ("tests/dummy/dummy.zip", "tests/dummy/dummy.zip", "", ""),
        ("tests/dummy/dummy-with-prefix.zip", "tests/dummy", "dummy-with-prefix", ""),
        (
            "tests/dummy/dummy-with-prefix.zip",
            "tests/dummy/dummy.zip",
            "dummy-with-prefix",
            "",
        ),
    ],
)
def test_diff__format_html__with_source_prefix(source1, source2, prefix1, prefix2):
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "--format",
            "html",
            "--source1",
            source1,
            "--source2",
            source2,
            "--source-prefix1",
            prefix1,
            "--source-prefix2",
            prefix2,
            "tests/dummy.with-dummy2-better-cov.xml",
            "tests/dummy.with-dummy2-better-and-worse.xml",
        ],
        catch_exceptions=False,
    )
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


@pytest.mark.parametrize(
    "source1, source2",
    [
        ("tests/dummy", "tests/dummy"),
        ("tests/dummy/dummy.zip", "tests/dummy/dummy.zip"),
    ],
)
def test_diff__format_html__with_source(source1, source2):
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "--format",
            "html",
            "--source1",
            source1,
            "--source2",
            source2,
            "tests/dummy.with-dummy2-better-cov.xml",
            "tests/dummy.with-dummy2-better-and-worse.xml",
        ],
        catch_exceptions=False,
    )
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__format_html__source():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "--format",
            "html",
            "--source",
            "tests/dummy.source1/coverage.xml",
            "tests/dummy.source2/coverage.xml",
        ],
        catch_exceptions=False,
    )
    assert "Missing" in result.output
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__format_html__source_is_default():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "--format",
            "html",
            "tests/dummy.source1/coverage.xml",
            "tests/dummy.source2/coverage.xml",
        ],
        catch_exceptions=False,
    )
    assert "Missing" in result.output
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__format_html__no_source():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "--format",
            "html",
            "--no-source",
            "tests/dummy.source1/coverage.xml",
            "tests/dummy.source2/coverage.xml",
        ],
        catch_exceptions=False,
    )
    assert "Missing" not in result.output
    assert result.output.startswith("<html>")
    assert result.output.endswith("</html>\n")
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__same_coverage_has_exit_status_of_zero():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "tests/dummy.source1/coverage.xml",
            "tests/dummy.source1/coverage.xml",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == ExitCodes.OK


def test_diff__better_coverage_has_exit_status_of_zero():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "tests/dummy.original.xml",
            "tests/dummy.original-full-cov.xml",  # has no uncovered lines
            "--no-source",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == ExitCodes.OK


def test_diff__worse_coverage_exit_status():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "tests/dummy.with-dummy2-no-cov.xml",
            "tests/dummy.with-dummy2-better-and-worse.xml",  # has covered AND uncovered lines
            "--no-source",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == ExitCodes.COVERAGE_WORSENED


def test_diff__changes_uncovered_but_with_better_coverage_exit_status():
    from pycobertura.cli import diff, ExitCodes

    runner = CliRunner()
    result = runner.invoke(
        diff,
        [
            "tests/dummy.zeroexit1/coverage.xml",
            "tests/dummy.zeroexit2/coverage.xml",  # has uncovered changes
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == ExitCodes.NOT_ALL_CHANGES_COVERED


def test_diff__line_status():
    from pycobertura.cli import diff

    runner = CliRunner()
    runner.invoke(
        diff,
        [
            "tests/dummy.linestatus/test1.xml",
            "tests/dummy.linestatus/test2.xml",
        ],
        catch_exceptions=False,
    )
    assert True
