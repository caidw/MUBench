import os
from glob import glob
from os.path import isdir, isfile, join
from typing import Set, List

import yaml

from data.misuse_compile import MisuseCompile
from data.correct_usage import CorrectUsage
from data.snippets import get_snippets, Snippet


class Location:
    def __init__(self, file: str, method: str, line: int):
        self.file = file
        self.method = method
        self.line = line

    def __str__(self):
        return "Location({}, {})".format(self.file, self.method)

    def __eq__(self, other):
        return self.file == other.file and self.method == other.method and self.line == other.line


class Fix:
    def __init__(self, description: str, commit: str, revision: str):
        self.description = description
        self.commit = commit
        self.revision = revision


class Misuse:
    MISUSE_FILE = "misuse.yml"

    @staticmethod
    def is_misuse(path: str) -> bool:
        return isfile(join(path, Misuse.MISUSE_FILE))

    def __init__(self, base_path: str, project_id: str, version_id: str, misuse_id: str):
        self._base_path = base_path
        self.project_id = project_id
        self.version_id = version_id
        self.misuse_id = misuse_id
        self.id = "{}.{}.{}".format(project_id, version_id, misuse_id).lower()

        from data.project import Project
        self.__project = Project(base_path, project_id)

        self.path = join(self.__project.path, Project.MISUSES_DIR, misuse_id)
        self.misuse_file = join(self.path, Misuse.MISUSE_FILE)

        self.__location = None
        self.__fix = None

        self._YAML = None
        self._CORRECT_USAGES = []

    @property
    def _yaml(self):
        if self._YAML is None:
            with open(self.misuse_file, 'r') as stream:
                self._YAML = yaml.load(stream)
        return self._YAML

    @property
    def correct_usages(self) -> Set[CorrectUsage]:
        if not self._CORRECT_USAGES:
            correct_usage_path = self.correct_usage_path
            if isdir(correct_usage_path):
                self._CORRECT_USAGES = set(
                    [CorrectUsage(correct_usage_path, y[len(correct_usage_path) + 1:]) for x in os.walk(correct_usage_path) for y in
                     glob(os.path.join(x[0], '*.java'))])
            else:
                self._CORRECT_USAGES = set()

        return self._CORRECT_USAGES

    @property
    def correct_usage_path(self) -> str:
        return join(self.path, "correct-usages")

    @property
    def location(self) -> Location:
        if not self.__location:
            location = self._yaml["location"]
            self.__location = Location(location.get("file", ""), location.get("method", ""), location.get("line", -1))
        return self.__location

    @property
    def description(self) -> str:
        if getattr(self, '_DESCRIPTION', None) is None:
            description = self._yaml.get("description", "")
            self._DESCRIPTION = description
        return self._DESCRIPTION

    @property
    def fix(self) -> Fix:
        if not self.__fix:
            fix = self._yaml.get("fix", {})
            self.__fix = Fix(fix.get("description", ""), fix.get("commit", ""), str(fix.get("revision", "")))
        return self.__fix

    @property
    def is_crash(self) -> bool:
        if getattr(self, '_IS_CRASH', None) is None:
            self._IS_CRASH = self._yaml["crash"]
        return self._IS_CRASH

    @property
    def source(self):
        if getattr(self, '_source', None) is None:
            source_key = self._yaml.get('source', None)
            if source_key is not None:
                self._source = source_key.get('name', None)
        return self._source

    @property
    def apis(self):
        if getattr(self, '_apis', None) is None:
            self._apis = self._yaml.get('api', [])
        return self._apis

    @property
    def is_apis_are_internal(self):
        return self._yaml.get('internal', False)

    @property
    def violations(self):
        if getattr(self, '_violations', None) is None:
            self._violations = self._yaml.get('violations', [])
        return self._violations

    def get_snippets(self, source_base_paths: List[str]) -> List[Snippet]:
        return get_snippets(source_base_paths, self.location.file, self.location.method, self.location.line)

    def get_misuse_compile(self, base_path: str) -> MisuseCompile:
        return MisuseCompile(join(base_path, self.project_id, "misuses", self.misuse_id), self.correct_usages)

    def __str__(self):
        return "misuse '{}'".format(self.id)

    def __hash__(self):
        return self.path.__hash__()

    def __eq__(self, other):
        return self.path == other.path

    def __ne__(self, other):
        return not self.__eq__(other)
