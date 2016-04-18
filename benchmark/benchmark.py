import subprocess
import traceback
from genericpath import exists
from os.path import join, splitext, basename
from tempfile import gettempdir

import settings
from checkout import checkout_parent, reset_to_revision
from utils.io import safe_open, create_file
from utils.logger import log_error

CATCH_ERRORS = True  # only used for testing


def analyze(file: str, misuse: dict) -> None:
    """
    Runs the misuse detector on the given misuse
    :param file: The file containing the misuse information
    :param misuse: The dictionary containing the misuse information
    :rtype: None
    :return: Nothing
    """
    try:
        result_dir = join(settings.RESULTS_PATH, splitext(basename(file))[0])
        if any([ignore in file for ignore in settings.IGNORES]):
            print("Warning: ignored {}".format(file))
            create_file(join(result_dir, settings.FILE_IGNORED), truncate=True)
            return

        fix = misuse["fix"]
        repository = fix["repository"]

        base_dir = join(gettempdir(), settings.TEMP_SUBFOLDER)
        project_name = extract_project_name_from_file_path(file)
        checkout_dir = join(base_dir, project_name)

        if not exists(checkout_dir):
            checkout_parent(repository["type"], repository["url"], fix.get('revision', ""), checkout_dir,
                            settings.VERBOSE)
        else:
            reset_to_revision(repository["type"], checkout_dir, fix.get('revision', ""), settings.VERBOSE)

        print("Running \'{}\'; Results in \'{}\'...".format(settings.MISUSE_DETECTOR, result_dir))

        with safe_open(join(result_dir, settings.LOG_DETECTOR_OUT), 'w+') as out_log:
            with safe_open(join(result_dir, settings.LOG_DETECTOR_ERROR), 'w+') as error_log:
                try:
                    subprocess.call(["java", "-jar", settings.MISUSE_DETECTOR, checkout_dir, result_dir],
                                    bufsize=1, stdout=out_log, stderr=error_log, timeout=settings.TIMEOUT)
                except subprocess.TimeoutExpired:
                    print("Timeout: {}".format(file))
                    create_file(join(result_dir, settings.FILE_IGNORED), truncate=True)
                    return

    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        if not CATCH_ERRORS:
            raise

        exception_string = traceback.format_exc()
        print(exception_string)
        log_error("Error: {} in {}".format(exception_string, file))


def extract_project_name_from_file_path(file: str) -> str:
    """
    Extracts the project name from a given file path, using '.' as a separator (<path>/<project>.<rest>)
    :param file: The file path (should be in the form "<path>/<project>.<rest>" or "<path>/synthetic-<rest>")
    :rtype: str
    :return: The project name
    """
    project_name = splitext(basename(file))[0]
    if 'synthetic' not in project_name and '.' in project_name:
        project_name = project_name.split('.', 1)[0]
    return project_name
