"""launcher/wrapper for executing CLI"""
from os import path
import platform
import logging

from plumbum import cli, local, TEE

import prosper.common.prosper_cli as p_cli
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

from . import _version

HERE = path.abspath(path.dirname(__file__))


def parse_command(command):
    """generate plumbum command given an incoming string

    Args:
        command (str): console command

    Returns:
        plumbum.local: shell command
        list: list of commands to go with the shell command (OPTIONAL)

    Raises:
        plumbum.commands.processes.CommandNotFound: invalid command

    """
    split_list = command.split()
    return local[split_list[0]], split_list[1:]

class RunTestsCLI(p_cli.ProsperApplication):
    PROGNAME = _version.PROGNAME
    VERSION = _version.__version__

    config_path = path.join(HERE, 'app.cfg')

    def main(self):
        """launcher logic"""
        self.logger.info('hello world')
        project_path = self.config.get('TEST_STEPS', 'project_path')
        local.cwd.chdir(project_path)
        self.logger.info('setting CWD: %s', local.cwd)

        self.logger.info('Updating from MAIN')
        git_log = local['git']('pull') & TEE
        self.logger.debug(git_log)


def run_main():
    """entry point for launching app"""
    RunTestsCLI.run()

if __name__ == '__main__':
    run_main()
