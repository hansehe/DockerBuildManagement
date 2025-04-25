from DockerBuildManagement import BuildManager
import sys
import logging


def main():
    """Entry point for the application script"""
    arguments = sys.argv[1:]
    BuildManager.HandleManagement(arguments)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()