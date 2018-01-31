"""launcher/wrapper for executing CLI"""
import atexit
from os import path, linesep
import platform
import logging

from plumbum import cli, local
import emails

import prosper.common.prosper_cli as p_cli
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

from . import _version
from . import exceptions

HERE = path.abspath(path.dirname(__file__))


#class Virtualenv():
#    """virtualenv context manager"""
#    def __init__(self, venv_name, which_python, cwd='', logger=p_logging.DEFAULT_LOGGER):
#        self.venv_name = venv_name
#        self.which_python = which_python
#        self.cwd = cwd
#        if not self.cwd:
#            self.cwd = local.cwd
#
#        self.logger = logger
#
#        self.logger.info('--building virtualenv')
#        try:
#            self.activate_path = self.build_venv(venv_name, which_python)
#        except Exception:
#            self.logger.error('Unable to build virtualenv', exc_info=True)
#            raise exceptions.FailedVirtualenvCreate()
#
#    def build_venv(self, venv_name, which_python):
#        """TODO
#
#        """
#        venv_log = local['virtualenv']



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


        self.logger.info('Updating from MAIN')
        try:
            git_log = local['git']('pull', '--force', timeout=30)
            self.logger.debug(git_log)
        except Exception:
            self.logger.critical('Unable to pull project from git', exc_info=True)
            exit(1)


        self.logger.info('Starting Virtual Environment')
        try:
            venv_name = self.config.get('TEST_STEPS', 'venv_name')
            self.logger.info('--removing existing venv')
            rm_log = local['rm']('-rf', venv_name)
            self.logger.debug(rm_log)

            self.logger.info('--creating fresh virtualenv')
            venv_log = local['virtualenv'](
                venv_name, '-p', self.config.get('TEST_STEPS', 'which_python'))
            self.logger.debug(venv_log)

            self.logger.info('--mapping virtualenv')
            self.venv_python = local[
                path.join(local.cwd, venv_name, 'bin', 'python')
            ]
            self.venv_pip = local[
                path.join(local.cwd, venv_name, 'bin', 'pip')
            ]

            self.logger.info('--registering atexit handle')
            atexit.register(atexit_deactivate_venv, venv_name, local.cwd, logger=self.logger)
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

def run_main():  # pragma: no cover
    """entry point for launching app"""
    RunTestsCLI.run()

if __name__ == '__main__':  # pragma: no cover
    run_main()
