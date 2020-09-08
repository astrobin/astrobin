from os.path import dirname, abspath


def get_project_root():
    # type: () -> str
    return dirname(dirname(abspath(__file__)))
