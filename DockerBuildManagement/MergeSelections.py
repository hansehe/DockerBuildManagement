from DockerBuildSystem import DockerComposeTools, YamlTools, TerminalTools, DockerImageTools, MultiArchTools
from SwarmManagement import SwarmTools
from DockerBuildManagement import BuildTools, PublishSelections
import sys
import os
import logging

log = logging.getLogger(__name__)

MERGE_KEY = 'merge'


def GetInfoMsg():
    infoMsg = "Merge selections is configured by adding a 'merge' property to the .yaml file.\r\n"
    infoMsg += "The 'merge' property is a dictionary of merge selections.\r\n"
    infoMsg += "Add '-merge' to the arguments to merge all selections in sequence, \r\n"
    infoMsg += "or add specific selection names to merge those only.\r\n"
    infoMsg += "Each selection combines per-arch image digests (produced by '-publish -pushByDigest') "
    infoMsg += "into a single multi-arch manifest using 'docker buildx imagetools create'.\r\n"
    infoMsg += "Provide digest files via the 'digestFiles' yaml property, "
    infoMsg += "or via '-digestFiles a.json b.json' on the cli (cli overrides yaml).\r\n"
    infoMsg += "If no matching 'merge' selection is found, the same-named image 'publish' selection "
    infoMsg += "is used as fallback - so a separate 'merge' yaml block is usually not required.\r\n"
    infoMsg += "Example: 'dbm -merge myMergeSelection -digestFiles digests-amd64.json digests-arm64.json'.\r\n"
    return infoMsg


def GetMergeSelections(arguments):
    yamlData = SwarmTools.LoadYamlDataFromFiles(
        arguments, BuildTools.DEFAULT_BUILD_MANAGEMENT_YAML_FILES)
    mergeProperty = YamlTools.GetProperties(MERGE_KEY, yamlData)
    if BuildTools.SELECTIONS_KEY in mergeProperty:
        return mergeProperty[BuildTools.SELECTIONS_KEY]
    return {}


def MergeSelections(selectionsToMerge, mergeSelections):
    if len(selectionsToMerge) == 0:
        for mergeSelection in mergeSelections:
            MergeSelection(mergeSelections[mergeSelection], mergeSelection)
    else:
        for selectionToMerge in selectionsToMerge:
            if selectionToMerge in mergeSelections:
                MergeSelection(mergeSelections[selectionToMerge], selectionToMerge)
            else:
                log.info(
                    "Skipping merge for selection '{0}': no matching merge or image publish selection found.".format(
                        selectionToMerge))


def BuildEffectiveSelections(mergeSelections, publishSelections):
    """Combine merge and publish selections into a single dict.

    Merge selections take precedence over publish selections of the same name.
    Only publish selections that publish container images (containerArtifact
    defaults to True) are eligible as fallback sources - artifact publishes
    (nuget, pypi, etc.) are filtered out because they have no docker image
    to merge.
    """
    effective = {}
    for name in publishSelections:
        publishSelection = publishSelections[name]
        if not YamlTools.TryGetFromDictionary(
                publishSelection, PublishSelections.CONTAINER_ARTIFACT_KEY, True):
            continue
        effective[name] = publishSelection
    for name in mergeSelections:
        effective[name] = mergeSelections[name]
    return effective


def MergeSelection(mergeSelection, selectionToMerge):
    cwd = BuildTools.TryChangeToDirectoryAndGetCwd(mergeSelection)
    oldEnvironmentVariable = BuildTools.AddEnvironmentVariablesFromSelection(mergeSelection)
    BuildTools.HandleTerminalCommandsSelection(mergeSelection)
    TerminalTools.LoadDefaultEnvironmentVariablesFile()

    if BuildTools.FILES_KEY in mergeSelection:
        composeFiles = mergeSelection[BuildTools.FILES_KEY]
        mergeComposeFile = BuildTools.GetAvailableComposeFilename('merge', selectionToMerge)
        DockerComposeTools.MergeComposeFiles(composeFiles, mergeComposeFile)

        try:
            digestFiles = BuildTools.GetEffectiveDigestFiles(mergeSelection)
            if not digestFiles:
                raise Exception(
                    "Merge selection '{0}' requires digest files. Provide them via the "
                    "'digestFiles' yaml property or '-digestFiles' on the cli.".format(selectionToMerge))

            groupedDigests = MultiArchTools.LoadDigestsFiles(digestFiles)
            yamlData = YamlTools.GetYamlData([mergeComposeFile])

            for service in yamlData.get('services', {}):
                svc = yamlData['services'][service]
                if 'image' not in svc:
                    continue
                if service not in groupedDigests:
                    log.info(
                        "Skipping service '{0}' in merge: no digest entries found in any digest file.".format(service))
                    continue

                image = svc['image']
                repo, primaryTag = DockerImageTools.SplitImageRepoAndTag(image)

                entries = groupedDigests[service]
                _AssertConsistentRepo(service, repo, entries)
                digests = [entry['digest'] for entry in entries]

                tags = [primaryTag]
                if BuildTools.ADDITIONAL_TAG_KEY in mergeSelection:
                    tags.append(mergeSelection[BuildTools.ADDITIONAL_TAG_KEY])
                if BuildTools.ADDITIONAL_TAGS_KEY in mergeSelection:
                    for tag in mergeSelection[BuildTools.ADDITIONAL_TAGS_KEY]:
                        tags.append(tag)

                tags = _DeduplicatePreserveOrder(tags)

                MultiArchTools.CreateMultiArchManifest(repo, tags, digests)
        except:
            BuildTools.RemoveComposeFileIfNotPreserved(mergeComposeFile, mergeSelection)
            raise

        BuildTools.RemoveComposeFileIfNotPreserved(mergeComposeFile, mergeSelection)

    BuildTools.RemoveEnvironmentVariables(oldEnvironmentVariable)
    os.chdir(cwd)


def _AssertConsistentRepo(service, expectedRepo, entries):
    for entry in entries:
        entryRepo = entry.get('repo')
        if entryRepo and entryRepo != expectedRepo:
            raise Exception(
                "Service '{0}' has mismatched repo across digest files: expected '{1}', got '{2}'".format(
                    service, expectedRepo, entryRepo))


def _DeduplicatePreserveOrder(items):
    seen = set()
    result = []
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def HandleMergeSelections(arguments):
    if len(arguments) == 0:
        return
    if not('-merge' in arguments):
        return

    if '-help' in arguments:
        log.info(GetInfoMsg())
        return

    selectionsToMerge = SwarmTools.GetArgumentValues(arguments, '-merge')

    mergeSelections = GetMergeSelections(arguments)
    publishSelections = PublishSelections.GetPublishSelections(arguments)
    effectiveSelections = BuildEffectiveSelections(mergeSelections, publishSelections)
    MergeSelections(selectionsToMerge, effectiveSelections)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    HandleMergeSelections(arguments)
