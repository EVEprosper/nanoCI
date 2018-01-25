"""test_cli: make sure user experiance works as expected"""

from plumbum import local
import pytest

from testhelpers import _version
import helpers


class TestCLI:
    """validate cli launches and works as users expect"""
    app_command = local['RunTests']

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
