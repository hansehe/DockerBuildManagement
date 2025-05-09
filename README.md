# Docker Build Management

[![PyPI version](https://badge.fury.io/py/DockerBuildManagement.svg)](https://badge.fury.io/py/DockerBuildManagement)
[![Build Status](https://travis-ci.com/hansehe/DockerBuildManagement.svg?branch=master)](https://travis-ci.com/hansehe/DockerBuildManagement)
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)

Build Management is a python application, installed with pip.
The application makes it easy to manage a build system based on Docker by configuring a single yaml file describing how to build, test, run or publish a containerized solution.

## Install Or Upgrade
- pip install --upgrade DockerBuildManagement

## Verify Installation
- `dbm -help`

## Example

Either of the sections (`run`, `build`, `test`, `publish`, `promote`) in the yaml file is triggered with the following cli commands:
- `dbm -run`
- `dbm -build`
- `dbm -test`
- `dbm -publish`
- `dbm -promote`

Each of the command sections (`run`, `build`, `test`, `publish`, `promote`) includes context sections, each defined by a suitable key describing that section. Each of the context sections are executed in sequence from top to bottom by default, or you may specify the sections to execute by adding the section keys to the command line:
- `dbm -run secondSelection`

It is also possible to execute multiple command sections in the same command line:
- `dbm -test -build -run secondSelection`

The `swarm` section helps deploying necessary domain services needed in the development.
Start/Stop/Restart/Wait the swarm:
- `dbm -swarm -start`
- `dbm -swarm -stop`
- `dbm -swarm -restart`
- `dbm -swarm -wait`

Please refer to the [SwarmManagement](https://github.com/hansehe/SwarmManagement) project for further info on how to configure the swarm deployment.

By convention, the default yaml filename is `build.management.yml`.
It is possible to specify a separate yaml file (or multiple) with the `-f` key:
- `dbm -f my-build.yml -run`

```yml
changelog:
    directory: src
    cmd:
        - python ./pythonSnippet.py
    file: CHANGELOG.md
    envKey: VERSION
    envMajorVersionKey: VERSIONMAJOR
    envMinorVersionKey: VERSIONMINOR

env_files: 
    - environment.env

run:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            copyFromContainer:
                pythonSnippet:
                    containerSrc: /src/
                    hostDest: output/
            cmd:
                - python ./pythonSnippet.py
            abortOnContainerExit: true
            verifyContainerExitCode: true
            removeContainers: true
            detached: false
            preserveMergedComposeFile: false
            files:
                - docker-compose.pythonSnippet.yml
                - docker-compose.pythonSnippet.overriden.yml
        secondSelection:
            directory: src
            files:
                - docker-compose.pythonSnippet.yml

build:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            cmd:
                - python ./pythonSnippet.py
            additionalTag: latest
            additionalTags:
                - ${VERSION:-1.0.0}.beta
                - ${VERSION:-1.0.0}.zeta
            platforms:
                - linux/amd64
                - linux/arm64
            saveImages: ../output
            composeFileWithDigests: docker-compose.digest.pythonSnippet.yml
            preserveMergedComposeFile: false
            files:
                - docker-compose.pythonSnippet.yml

test:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            cmd:
                - python ./pythonSnippet.py
            removeContainers: true
            preserveMergedComposeFile: false
            platforms:
                - linux/amd64
                - linux/arm64
            files:
                - docker-compose.pythonSnippet.yml

publish:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            cmd:
                - python ./pythonSnippet.py
            additionalTag: latest
            additionalTags:
                - ${VERSION:-1.0.0}.beta
                - ${VERSION:-1.0.0}.zeta
            platforms:
                - linux/amd64
                - linux/arm64
            composeFileWithDigests: docker-compose.digest.pythonSnippet.yml
            preserveMergedComposeFile: false
            files:
                - docker-compose.pythonSnippet.yml
        secondSelection:
            directory: src
            containerArtifact: false
            files:
                - docker-compose.pythonSnippet.yml

promote:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            cmd:
                - python ./pythonSnippet.py
            targetTags:
                - latest
                - qaapproved
            sourceFeed: <docker.dockerserver>
            targetFeed: <docker2.dockerserver>
            user: <user_for_target_and_source_feed>
            password: <password_for_target_and_source_feed>
            logout: false
            dryRun: false
            files:
                - docker-compose.pythonSnippet.yml

swarm:
    selections:
        firstSelection:
            directory: src
            environmentVariables:
                ENVIRONMENT_VARIABLE_KEY: environment_variable
            cmd:
                - python ./pythonSnippet.py
            properties:
                - -stack -remove proxy
            files:
                - swarm-management.yml
```

Please have a look at an example of use here:
- https://github.com/hansehe/DockerBuildManagement/tree/master/example

Or take a look at another project which takes use of this library:
- https://github.com/hansehe/FluentDbTools

## Section Features

### General features
- `directory` -> Each section has a `directory` property defining in which relative directory the section will be executed. Note that all relative position to files and command lines will be executed relative to this directory during execution of that section.
- `environmentVariables` -> Each section has an `environmentVariables` property with a subsection of key value pairs of environment variables to set.
- `files` -> Each section has a `files` property listing all `docker-compose.yml` files to use when either building, testing or running the services listed in `docker-compose.yml`.
- `preserveMergedComposeFile` -> Each section has a `preserveMergedComposeFile` property which is set to `true` or `false`. When set to `true` it will preserve a merged compose file version of the listed compose files. It is by default set to `false`.
- `cmd` -> Executes a list of command lines before initiating the main job of the section.

### Run Features
The `run` section runs all listed docker-compose files with `docker-compose up`.
- `abortOnContainerExit: true/false` -> Tell docker-compose to abort when either of the containers exits. Default is `true`.
- `detached: true/false` -> Tell docker-compose to run the services in detached mode. Default is `false`.
    - Note that the `abortOnContainerExit` property will be ignored if `detached` is set to `true`. 
      - docker-compose does not allow to run a compose file as detached while telling it to abort on container exit.
- `copyFromContainer` -> Copy anything from a docker container to a destination on your computer. The section contains keys matching the container name, and this key has the following sub-keys:
    - `containerSrc: <folder_path/file_path>` -> Source path to copy from the container.
    -  `hostDest: <folder_path/file_path>` -> Destination path on your computer to copy the container content.

### Build Features
The `build` section builds all docker images as described by the `docker-compose.yml` files.
- `additionalTag: <additional_image_tag>` -> Include an additional tag to all built docker images.
- `additionalTags: <list_of_additional_image_tags>` -> Include a list of additional tags to all built docker images.
- `saveImages: <output_folder>` -> Save all built docker images from the compose file as tar files. The files will be saved in the given output folder.
- `composeFileWithDigests: <docker-compose.with_digests.yml>` -> Get an updated version of the compose files with the unique digest included in the image names. An unique digest is generated for each published image and should always be used in production.
  - Note! The image digest is produced by docker only when the image is published to a remote repository, meaning the image must exist on a remote repository to have the image tag replaced with the image digest.

### Test Features
The `test` section runs all services listed in the `docker-compose.yml` files, and detects if either of the services exited with a non-zero exit code due to an error.
- `containerNames` -> List of container names of the services to check for the non-zero exit code.
- `removeContainers: true/false` -> Remove containers created by the services. Default is `true`.

### Publish Features
The `publish` section publishes all docker images listed in the `docker-compose.yml` files.
- `additionalTag: <additional_image_tag>` -> Include an additional tag to publish with the docker images.
- `additionalTags: <list_of_additional_image_tags>` -> Include a list of additional tags to publish with the docker images.
- `platforms: <list_of_image_platforms_for_multi_build>` -> Include a list of platforms for multi target architecture, such as linux/amd64 and linux/arm64.
- `containerArtifact: true/false` -> Sometimes the solution does not publish docker images, but just something else such as nugets, pypi or gem packages. With this property set to `true`, you can make a docker container do the work of publishing the artifact. Default is `false`.
- `composeFileWithDigests: <docker-compose.with_digests.yml>` -> Get an updated version of the compose files with the unique digest included in the image names. An unique digest is generated for each published image and should always be used in production.

### Promote Features
The `promote` section promotes docker images listed in the `images` property using docker pull, docker tag and docker push.
- `targetTags: <list_of_target_tags>` -> the tags you want to use when you push the image to the new feed. Mandatory to set.
- `sourceFeed: <dockerfeed.dockerserver>` -> the feed you want to pull the images from (should match the compose file). Not mandatory to set.
- `targetFeed: <dockerfeed.dockerserver>` -> the feed you want to push to. Not mandatory to set.
- `user: <dockerfeed_user>` -> used for authenticating to sourceFeed and targetFeed. Not mandatory to set.
- `password: <dockerfeed_password>` -> used for authenticating to sourceFeed and targetFeed. Not mandatory to set.
- `logout: true/false` -> logout from source and target feed after promotion. Default is `false`.
- `dryRun: true/false` -> True if you want to do a dry run. This will print what would have happened. Default is `false`.
     

### Swarm Features
The `swarm` section helps to deploy service stacks to your local swarm. It reuses the [SwarmManagement](https://github.com/hansehe/SwarmManagement) deployment tool to deploy and remove services to and from the Swarm.
- `files` -> The `files` property lists all `swarm-management.yml` deployment files to use for deploying stacks on the Swarm.
- `properties` -> This property is a list of `SwarmManagement` commands to run in addition to starting or stopping the Swarm stacks.

### General Properties
- `changelog` -> The `changelog` property parses a [CHANGELOG.md](example/CHANGELOG.md) file and sets an environment variables with current version. It contains following sub-keys:
    - `file` -> Path to the changelog file. The changelog file must be of a format similar to either of the changelog formats:
      - [example/src/CHANGELOG.md](example/src/CHANGELOG.md)
      - [example/src/CHANGELOG.v2.md](example/src/CHANGELOG.v2.md).
    - `envKey` -> On which environment variable to expose the version value. Default is `VERSION`.
    - `envMajorVersionKey` -> Optional environment variable to expose the version major value.
    - `envMinorVersionKey` -> Optional environment variable to expose the version minor value.
- `env_files` -> List of `.env` files listing default environment variables to expose. By convention, a present `.env` file will automatically be used to expose environment variables. 
- `Environment variable replacement` -> Any area in the yaml template may use environment variable replacemenet with the `${ENV_KEY:-default_value}` syntax. 
  - `Default environment variables`:
    - `PWD` -> Exposes the present working directory.

## Prerequisites
- Docker:
    - https://www.docker.com/get-docker
- Install Dependencies:
    - pip install -r requirements.txt
- If you update dependencies or add new ones, they need to be updated both in requirements.txt and in setup.py.

## Additional Info
- The pip package may be located at:
    - https://pypi.org/project/DockerBuildManagement

## Publish New Version
1. Configure setup.py with new version.
2. Install build tools: `pip install twine wheel`
3. Build: python setup.py bdist_wheel
4. Check: twine check dist/*
5. Publish: twine upload dist/*

## Test a new version locally
1. Build: python setup.py bdist_wheel
2. Install from local file with force-reinstall and no-cache-dir options to force reinstallation when you have changed the code without changing the version number: `python -m pip install path\to\yourgitrepo\DockerBuildManagement\dist\DockerBuildManagement-0.0.65-py2.py3-none-any.whl --force-reinstall --no-cache-dir`

## Run Unit Tests
- python -m unittest discover -p *Test*.py
