"""launcher/wrapper for executing CLI"""
import atexit
import collections
from os import path
import platform
import logging

from plumbum import cli, local
import plumbum
import emails
import git
from junit2htmlreport import parser
from parse import *

import prosper.common.prosper_cli as p_cli
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

from . import _version
from . import exceptions

HERE = path.abspath(path.dirname(__file__))

LocalResults = collections.namedtuple('LocalResults', ['retcode', 'stdout', 'stderr'])


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

def parse_command_list(config_str):
    """turn multi-line config entry into a list of commands

    Args:
        config_str (str): string from ConfigParser entry

    Returns:
        list: list of commands, blank-lines removed

    """
    return [command for command in config_str.splitlines() if command]

def atexit_deactivate_venv(
        venv_name,
        cwd,
        logger=p_logging.DEFAULT_LOGGER
):  # pragma: no cover
    """atexit handler for deactivating and removing local venv even if tools crash

    Args:
        venv_name (str): name of venv to deactivate
        cwd (str): path to cwd (in case local.cwd changes)
        logger (:obj:`logging.logger`): logging handle for messaging

    Returns:
        None

    Raises:
        IOError: file permission issues

    """
    logger.info('Cleaning up venv post-test')

    logger.info('--removing venv')
    try:
        rm_log = local['rm']('-rf', path.join(cwd, venv_name))
        logger.debug(rm_log)
    except Exception:
        logger.error('Unable to remove venv files post-test', exc_info=True)

    # TODO: remove .egg/pycache/dist files?

    logger.info('venv cleanup complete!')

def build_virtualenv(
        venv_name,
        which_python='python3',
        _atexit_register=True,
        logger=p_logging.DEFAULT_LOGGER,
):
    """build a virtualenv to run python in (do not use system python)

    Note:
        nukes-and-paves existing venv_name
        registers atexit handle to delete testing venv at end of testpass

    Args:
        venv_name (str): name of test venv
        which_python (str): path to desired python
        atexit_register (bool): register an atexit handle to ease cleanup
        logger (:obj:`logging.logger`): logging handle

    Returns:
        plumbum.local: python handle
        plumbum.local: pip handle

    """
    logger.info('--removing existing venv %s', path.abspath(venv_name))
    rm_log = local['rm']('-rf', venv_name)
    logger.debug(rm_log)

    logger.info('--creating fresh virtualenv')
    venv_log = local['virtualenv'](venv_name, '-p', which_python)
    logger.debug(venv_log)

    logger.info('--mapping virtualenv')
    venv_python = local[
        path.join(local.cwd, venv_name, 'bin', 'python')
    ]
    venv_pip = local[
        path.join(local.cwd, venv_name, 'bin', 'pip')
    ]

    if _atexit_register:  #pragma: no cover
        logger.info('--registering atexit handle')
        atexit.register(atexit_deactivate_venv, venv_name, local.cwd, logger=logger)

    return venv_python, venv_pip

class RunTestsCLI(p_cli.ProsperApplication):
    PROGNAME = _version.PROGNAME
    VERSION = _version.__version__

    config_path = path.join(HERE, 'app.cfg')

    venv_python = None
    venv_pip = None

    def parse_command(self, command):
        """generate plumbum command given an incoming string

        Args:
            command (str): console command

        Returns:
            plumbum.local: shell command
            list: list of commands to go with the shell command (OPTIONAL)

        Raises:
            plumbum.commands.processes.CommandNotFound: invalid command
            VirtualenvException: no command found for python/pip

        """
        split_list = command.split()
        command = local[split_list[0]]
        if 'python' in split_list[0]:
            self.logger.debug(self.venv_pip)
            command = self.venv_python

        if split_list[0] == 'pip' or split_list[0] == 'pip3':
            self.logger.debug(self.venv_pip)
            command = self.venv_pip

        if not command:
            raise exceptions.VirtualenvException(
                'Unable to map {} to command'.format(split_list[0]))

        return command, split_list[1:]

    def main(self):  # pragma: no cover
        """launcher logic"""
        self.logger.info('hello world')
        project_path = self.config.get('TEST_STEPS', 'project_path')
        local.cwd.chdir(project_path)
        self.logger.info('setting CWD: %s', local.cwd)

        git_repo = git.Repo()


        self.logger.info('Updating from MAIN')
        try:
            git_log = git_repo.git.pull()
            self.logger.debug(git_log)
        except Exception:
            self.logger.critical('Unable to pull project from git', exc_info=True)
            exit(1)


        self.logger.info('Starting Virtual Environment')
        try:
            self.venv_python, self.venv_pip = build_virtualenv(
                self.config.get('TEST_STEPS', 'venv_name'),
                which_python=self.config.get('TEST_STEPS', 'which_python'),
                logger=self.logger,
            )
        except Exception:
            self.logger.critical('Unable to create virtualenv for test', exc_info=True)
            exit(1)


        self.logger.info('Preparing Environment')
        try:

            for command in parse_command_list(self.config.get('TEST_STEPS', 'prep_commands')):
                self.logger.info('--`%s`', command)
                local_command, arguments = self.parse_command(command)
                step_log = local_command(arguments)
                self.logger.debug(step_log)
        except Exception:
            self.logger.critical('Unable to execute test prep commands', exc_info=True)
            exit(1)


        self.logger.info('Running Tests')
        failed_logs = []
        try:
            for command in parse_command_list(self.config.get('TEST_STEPS', 'test_commands')):
                self.logger.info('--`%s`', command)
                local_command, arguments = self.parse_command(command)
                retcode, stdout, stderr = local_command.run(arguments, retcode=[0, 1])
                results = LocalResults(retcode, stdout, stderr)
                if retcode != 0:
                    self.logger.warning('Test step failed: `%s`: %s', command, results)
                    failed_logs.append(results)
                self.logger.debug(step_log)
        except Exception:
            self.logger.critical('Unable to execute test step commands', exc_info=True)
            exit(1)

        if failed_logs:
            self.logger.info('Processing failures')
            commit_name = git_repo.head.commit.message

            try:
                self.logger.info('--parsing JUNIT')
                # TODO: merge JUNIT in case of TOX reports
                junit = parser.Junit(
                    self.config.get('TEST_STEPS', 'junit_path')
                )
                results = junit.html()
            except Exception:
                self.logger.warning(
                    'Unable to open junit results %s',
                    self.config.get('TEST_STEPS', 'junit_path'),
                    exc_info=True
                )
                results = '\n'.join(failed_logs)

        else:
            pass





def run_main():  # pragma: no cover
    """entry point for launching app"""
    RunTestsCLI.run()

if __name__ == '__main__':  # pragma: no cover
    run_main()
