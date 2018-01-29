"""launcher/wrapper for executing CLI"""
from os import path, linesep
import platform
import logging

from plumbum import cli, local
import emails

import prosper.common.prosper_cli as p_cli
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

from . import _version

HERE = path.abspath(path.dirname(__file__))

def update_coveralls_config(
        path_to_coverage,
        coveralls_token,
        token_key='repo_token',
):
    """updates .coveralls.yml file to allow upload of coverage report

    Args:
        path_to_coverage (str): path to .coveralls.yml file
        coveralls_token (str): token to upload to .coveralls.yml
        token_key (str): key to add to .coveralls.yml file for upload

    Returns:
        None

    Raises:
        IOError: unable to update file

    """
    try:
        with open(path_to_coverage, 'r') as cover_fh:
            raw_file = cover_fh.read()
    except FileNotFoundError:
        raw_file = ''

    # check if repo_token is already in .coveralls.yml
    if token_key in raw_file:
        return  # already has coveralls credentials
        # TODO: check if `repo_token` is blank

    lines = raw_file.splitlines()
    lines.append(token_key + ': ' + coveralls_token)

    with open(path_to_coverage, 'w') as cover_fh:
        cover_fh.writelines(lines)


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

    def main(self):  # pragma: no cover
        """launcher logic"""
        self.logger.info('hello world')
        project_path = self.config.get('TEST_STEPS', 'project_path')
        local.cwd.chdir(project_path)
        self.logger.info('setting CWD: %s', local.cwd)

        self.logger.info('Updating from MAIN')
        try:
            git_log = local['git']('pull', '--force', timeout=30)
        except Exception:
            self.logger.critical('Unable to pull project from git', exc_info=True)
            exit(1)

        self.logger.debug(git_log)


def run_main():
    """entry point for launching app"""
    RunTestsCLI.run()

if __name__ == '__main__':
    run_main()
