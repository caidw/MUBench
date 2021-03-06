from data.detector import Detector
from tests.test_utils.runner_interface_test_impl import RunnerInterfaceTestImpl


class StubDetector(Detector):
    def __init__(self):
        self._Detector__load_release_file = lambda *_: [{'cli_version': RunnerInterfaceTestImpl.TEST_VERSION}]
        super().__init__("-detectors-", "StubDetector", [], "latest")
