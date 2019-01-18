"""Doctest for command line code examples.

A stupid minimal framework for testing command output in documentation. It
has no options and will test any line which begins with a dollar symbol.

"""

from subprocess import Popen, PIPE, STDOUT
import shlex

import pytest


def pytest_addoption(parser):
    """Add command line options required by ShellTest."""
    group = parser.getgroup("collect")
    group.addoption(
        "--shelltest-glob",
        action="append",
        default=[],
        metavar="pat",
        help="shelltests file matching pattern, default: test*.txt",
        dest="shelltestglob",
    )


def pytest_collect_file(parent, path):
    """Determine which files to test."""
    config = parent.config
    for glob in config.getoption('shelltestglob'):
        if path.check(fnmatch=glob):
            return ShellTestFile(path, parent)


class ShellTestFile(pytest.File):
    """File to be ShellTested."""

    @staticmethod
    def get_tests(filename):
        """Extract tests from file.

        Args:
            filename (str): The path to the file to extract tests from.

        Yields:
            tuple - (cmd, expected)
        
        """
        with open(filename, 'r') as test_file:
            in_shelltest = False
            cmd = None
            expected = None
            for line in test_file:
                line = line.strip()
                if not in_shelltest and line.startswith('$'):
                    in_shelltest = True
                    cmd = line[1:]
                    expected = []
                elif in_shelltest and line.startswith('$'):
                    yield (cmd, expected)
                    cmd = line[1:]
                    expected = None
                elif in_shelltest and line:
                    expected.append(line)
                elif in_shelltest:
                    in_shelltest = False
                    yield (cmd, expected)
                    cmd = None
                    expected = None
            if in_shelltest:
                yield (cmd, expected)

    def collect(self):
        """Yields tests to pytest."""
        filename = str(self.fspath)
        for test in self.get_tests(filename):
            yield ShellTestItem(filename, self, test)


class ShellTestFailure(Exception):
    """Exception to be raised when ShellTests fail."""
    pass


class ShellTestItem(pytest.Item):
    """Represents an individual ShellTest."""

    def __init__(self, name, parent, test):
        super(ShellTestItem, self).__init__(name, parent)
        self.test = test

    def runtest(self):
        """Run a ShellTest.

        Args:
            cmd (str): The command to test as it would be written on the
                command line.
            expected (list): List of expected output lines (stdout &  stderr
                are mixed).

        Raises:
            ShellTestFailure - In the event a test should fail.

        """
        cmd, expected = self.test
        cmd = shlex.split(cmd.strip())

        proc = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        got = proc.communicate()[0].decode('UTF-8').splitlines()
        if got != expected:
            raise ShellTestFailure(cmd, expected, got)

    def repr_failure(self, excinfo):
        """Called when runtest raises and exception.
        
        Returns:
            string - If the exception raised represents a failure in the test
                (i.e. an expected failure).
        
        """
        if isinstance(excinfo.value, ShellTestFailure):
            cmd, expected, got = excinfo.value.args
            return '\n'.join([
                'Example failed:',
                '    $ ' + ' '.join(cmd),
                'Expected:',
                '\n'.join('    %s' % line for line in expected),
                'Got:',
                '\n'.join('    %s' % line for line in got),
            ])

    def reportinfo(self):
        """Return the test identifier as it should appear in pytest output."""
        return self.fspath, 0, "shelltest: %s" % self.name
