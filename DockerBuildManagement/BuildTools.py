from SwarmManagement import SwarmTools
from DockerBuildSystem import DockerImageTools, TerminalTools, YamlTools, DockerComposeTools
import os

COMMAND_KEY = 'cmd'
SELECTIONS_KEY = 'selections'
FILES_KEY = 'files'
ENVIRONMENT_VARIABLES_KEY = 'environmentVariables'
DIRECTORY_KEY = 'directory'
ADDITIONAL_TAG_KEY = 'additionalTag'
ADDITIONAL_TAGS_KEY = 'additionalTags'
COMPOSE_FILE_WITH_DIGESTS_KEY = 'composeFileWithDigests'
PRESERVE_MERGED_COMPOSE_FILE = 'preserveMergedComposeFile'
CONTAINER_NAMES_KEY = 'containerNames'
REMOVE_CONTAINERS_KEY = 'removeContainers'
PLATFORMS_TAG_KEY = 'platforms'
DIGEST_FILES_KEY = 'digestFiles'

COPY_FROM_CONTAINER_TAG = 'copyFromContainer'
COPY_CONTAINER_SRC_TAG = 'containerSrc'
COPY_HOST_DEST_TAG = 'hostDest'

TARGET_TAGS_KEY = 'targetTags'
TARGET_FEED_KEY = 'targetFeed'
SOURCE_FEED_KEY = 'sourceFeed'
USER_KEY = 'user'
PASSWORD_KEY = 'password'
LOGOUT_KEY = 'logout'
DRY_RUN_KEY = 'dryRun'


DEFAULT_BUILD_MANAGEMENT_YAML_FILES = [
    'build.management.yml', 
    'build.management.yaml',
    'build-management.yml',
    'build-management.yaml']


_PLATFORMS_OVERRIDE = None
_PUSH_BY_DIGEST = False
_DIGESTS_FILE = None
_DIGEST_FILES_OVERRIDE = None

DEFAULT_DIGESTS_FILE = 'dbm-digests.json'


def SetGlobalPlatformsOverride(platforms):
    global _PLATFORMS_OVERRIDE
    _PLATFORMS_OVERRIDE = platforms if platforms else None


def GetGlobalPlatformsOverride():
    return _PLATFORMS_OVERRIDE


def GetEffectivePlatforms(selection):
    if _PLATFORMS_OVERRIDE:
        return _PLATFORMS_OVERRIDE
    if PLATFORMS_TAG_KEY in selection:
        return selection[PLATFORMS_TAG_KEY]
    return None


def SetGlobalPushByDigest(enabled):
    global _PUSH_BY_DIGEST
    _PUSH_BY_DIGEST = bool(enabled)


def GetGlobalPushByDigest():
    return _PUSH_BY_DIGEST


def SetGlobalDigestsFile(digestsFile):
    global _DIGESTS_FILE
    _DIGESTS_FILE = digestsFile if digestsFile else None


def GetGlobalDigestsFile():
    if _DIGESTS_FILE:
        return _DIGESTS_FILE
    return DEFAULT_DIGESTS_FILE


def SetGlobalDigestFilesOverride(digestFiles):
    global _DIGEST_FILES_OVERRIDE
    _DIGEST_FILES_OVERRIDE = digestFiles if digestFiles else None


def GetEffectiveDigestFiles(selection):
    if _DIGEST_FILES_OVERRIDE:
        return _DIGEST_FILES_OVERRIDE
    if DIGEST_FILES_KEY in selection:
        return selection[DIGEST_FILES_KEY]
    return None


def GetInfoMsg():
    infoMsg = "One or more yaml files are used to configure the build.\r\n"
    infoMsg += "The yaml file 'build.management.yml' is used by default if no other files are specified.\r\n"
    infoMsg += "A yaml file may be specified by adding '-file' or '-f' to the arguments.\r\n"
    infoMsg += "Example: -f build.management-1.yml -f build.management-2.yml\r\n"
    infoMsg += SwarmTools.GetEnvironmentVariablesInfoMsg()
    infoMsg += SwarmTools.GetYamlDumpInfoMsg()
    return infoMsg


def HandleTerminalCommandsSelection(selection):
    if COMMAND_KEY in selection:
        terminalCommands = selection[COMMAND_KEY]
        TerminalTools.ExecuteTerminalCommands(terminalCommands, True)


def AddEnvironmentVariablesFromSelection(selection):
    oldEnvironmentVariable = {}
    if ENVIRONMENT_VARIABLES_KEY in selection:
        for key in selection[ENVIRONMENT_VARIABLES_KEY]:
            oldEnvironmentVariable[key] = None
            if key in os.environ:
                oldEnvironmentVariable[key] = os.environ[key]
            os.environ[key] = selection[ENVIRONMENT_VARIABLES_KEY][key]
    return oldEnvironmentVariable


def RemoveEnvironmentVariables(oldEnvironmentVariable):
    for key in oldEnvironmentVariable:
        oldVariable = oldEnvironmentVariable[key]
        if key in os.environ:
            if oldVariable is None:
                os.environ.pop(key)
            else:
                os.environ[key] = oldVariable


def TryChangeToDirectoryAndGetCwd(selection):
    cwd = os.getcwd()
    if DIRECTORY_KEY in selection:
        if len(selection[DIRECTORY_KEY]) > 0:
            os.chdir(selection[DIRECTORY_KEY])
    return cwd


def HandleCopyFromContainer(dictionary):
    if not(COPY_FROM_CONTAINER_TAG in dictionary):
        return

    for containerName in dictionary[COPY_FROM_CONTAINER_TAG]:
        containerSrc = dictionary[COPY_FROM_CONTAINER_TAG][containerName][COPY_CONTAINER_SRC_TAG]
        hostDest = dictionary[COPY_FROM_CONTAINER_TAG][containerName][COPY_HOST_DEST_TAG]
        if not os.path.exists(hostDest):
            os.makedirs(hostDest)
        DockerImageTools.CopyFromContainerToHost(containerName, containerSrc, hostDest)


def GenerateComposeFileWithDigests(composeFiles, outputComposeFile):
    TerminalTools.LoadDefaultEnvironmentVariablesFile()
    yamlData = YamlTools.GetYamlData(composeFiles, replaceEnvironmentVariablesMatches=False)
    DockerComposeTools.AddDigestsToImageTags(yamlData)
    YamlTools.DumpYamlDataToFile(yamlData, outputComposeFile)


def RemoveComposeFileIfNotPreserved(composeFile, selection):
    preserveComposeFile = False
    if PRESERVE_MERGED_COMPOSE_FILE in selection:
        preserveComposeFile = bool(selection[PRESERVE_MERGED_COMPOSE_FILE])
    if not(preserveComposeFile):
        os.remove(composeFile)


def GetAvailableComposeFilename(selectionTag, defaultTag):
    composeFile = 'docker-compose.{0}.{1}.yml'.format(selectionTag, defaultTag)
    return composeFile


def MergeAndPopulateWithContainerNames(composeFiles, testComposeFile):
    DockerComposeTools.MergeComposeFiles(composeFiles, testComposeFile)
    yamlData = YamlTools.GetYamlData([testComposeFile])
    DockerComposeTools.AddContainerNames(yamlData)
    YamlTools.DumpYamlDataToFile(yamlData, testComposeFile)
    containerNames = DockerComposeTools.GetContainerNames(yamlData)
    return containerNames
