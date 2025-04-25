import unittest
import os
import logging
from tests import TestTools
from DockerBuildManagement import ChangelogSelections
from DockerBuildManagement import TestSelections
from DockerBuildManagement import BuildSelections
from DockerBuildManagement import RunSelections
from DockerBuildManagement import SwarmSelections
from DockerBuildManagement import PromoteSelections

log = logging.getLogger(__name__)

class TestSelectionHandlers(unittest.TestCase):

    def test_a_changelog(self):
        log.info('EXECUTING CHANGELOG TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = []
        ChangelogSelections.HandleChangelogSelections(arguments)
        self.assertEqual(os.environ['VERSION'], '1.0.0')
        self.assertEqual(os.environ['VERSIONMAJOR'], '1')
        self.assertEqual(os.environ['VERSIONMINOR'], '0')
        os.chdir(cwd)
        log.info('DONE EXECUTING CHANGELOG TEST')

    def test_b_test(self):
        log.info('EXECUTING TEST SELECTION TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = ['-test']
        TestSelections.HandleTestSelections(arguments)
        os.chdir(cwd)
        log.info('DONE EXECUTING TEST SELECTION TEST')

    def test_c_build(self):
        log.info('EXECUTING BUILD SELECTION TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = ['-build']
        BuildSelections.HandleBuildSelections(arguments)
        os.chdir(cwd)
        log.info('DONE EXECUTING BUILD SELECTION TEST')

    def test_d_run(self):
        log.info('EXECUTING RUN SELECTION TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = ['-run']
        RunSelections.HandleRunSelections(arguments)
        os.chdir(cwd)
        log.info('DONE EXECUTING RUN SELECTION TEST')

    def test_e_swarm(self):
        log.info('EXECUTING SWARM SELECTION TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = ['-start']
        SwarmSelections.HandleSwarmSelections(arguments)
        arguments = ['-stop']
        SwarmSelections.HandleSwarmSelections(arguments)
        os.chdir(cwd)
        log.info('DONE EXECUTING SWARM SELECTION TEST')

    def test_f_promote(self):
        log.info('EXECUTING PROMOTE SELECTION TEST')
        cwd = TestTools.ChangeToSampleFolderAndGetCwd()
        arguments = ['-promote']
        PromoteSelections.HandlePromoteSelections(arguments)
        os.chdir(cwd)
        log.info('DONE EXECUTING PROMOTE SELECTION TEST')

if __name__ == '__main__':
    unittest.main()