"""test_cli: make sure user experiance works as expected"""
from os import path, sep
import logging
import tempfile
import uuid
import sys
import pip

from plumbum import local
import yaml
import plumbum
import pytest
from parse import *

import helpers
from testhelpers import _version
import testhelpers.RunTests as RunTests
import testhelpers.exceptions as exceptions

def test_build_virtualenv():
    """validate RunTests.build_virtualenv works as expected"""
    assert not path.isdir(helpers.VENV_NAME)

    python_local, pip_local = RunTests.build_virtualenv(helpers.VENV_NAME, _atexit_register=False)

    assert path.isdir(helpers.VENV_NAME)
    assert isinstance(python_local, plumbum.commands.ConcreteCommand)
    assert isinstance(pip_local, plumbum.commands.ConcreteCommand)

    assert sep + helpers.VENV_NAME + sep in str(python_local)
    assert sep + helpers.VENV_NAME + sep in str(pip_local)

    python_version = python_local('-V').rstrip()
    assert python_version == 'Python ' + sys.version.split()[:1][0]

    pip_version = pip_local('-V').rstrip()
    pip_info = parse('pip {version} from {path} ({python_version})', pip_version)
    assert pip_info['version'] == pip.__version__
    assert False

def test_parse_command():
    """validate RunTests.parse_command behavior"""
    dummy_command = 'echo "hello world"'
    command, arguments = RunTests.RunTestsCLI.parse_command(None, dummy_command)
    assert isinstance(command, plumbum.commands.ConcreteCommand)

    command_returns = command(arguments)
    assert command_returns.rstrip() == '"hello world"'

def test_bad_command():
    """validate RunTests.parse_command throws expected errors"""
    with pytest.raises(plumbum.commands.processes.CommandNotFound):
        command, arguments = RunTests.RunTestsCLI.parse_command(None, 'garbage_command')

def test_parse_command_exceptions():
    """validate parse_command raises expected exceptions"""
    class DummyCLI:
        venv_python = None
        venv_pip = None
        logger = logging.getLogger()

    dummy_cli = DummyCLI()

    with pytest.raises(exceptions.VirtualenvException):
        command, arguments = RunTests.RunTestsCLI.parse_command(dummy_cli, 'python -V')

    with pytest.raises(exceptions.VirtualenvException):
        command, arguments = RunTests.RunTestsCLI.parse_command(dummy_cli, 'pip install plumbum')

def test_parse_command_list():
    """validate parse_command_list behavior"""
    easy_command = '''command1
command2
command3
'''
    assert RunTests.parse_command_list(easy_command) == ['command1', 'command2', 'command3']

    weird_command = '''

command1
command2

command3
'''

    assert RunTests.parse_command_list(weird_command) == ['command1', 'command2', 'command3']

def test_update_coveralls():
    """validate RunTests.update_coveralls_config behavior"""
    with tempfile.TemporaryDirectory() as tempdir:
        dummy_coveralls = path.join(tempdir, '.coveralls.yml')
        dummy_token = str(uuid.uuid1())
        print(dummy_coveralls)

        # Virgin Try
        RunTests.update_coveralls_config(
            dummy_coveralls,
            dummy_token
        )

        with open(dummy_coveralls, 'r') as stream:
            coveralls_yaml = yaml.load(stream)

        assert coveralls_yaml['repo_token'] == dummy_token

        # Existing Retry
        RunTests.update_coveralls_config(
            dummy_coveralls,
            str(uuid.uuid1())
        )

        with open(dummy_coveralls, 'r') as stream:
            coveralls_yaml = yaml.load(stream)

        # Should be original token, not new token
        assert coveralls_yaml['repo_token'] == dummy_token

class TestCLI:
    """validate cli launches and works as users expect"""
    app_command = local['nanoci']

    def test_help(self):
        """validate -h works"""
        output = self.app_command('-h')

    def test_version(self):
        """validate app name/version are as expected"""
        output = self.app_command('--version')

        assert output.rstrip() == '{PROGNAME} {version}'.format(
            PROGNAME=_version.PROGNAME,
            version=_version.__version__,
        )
