#!/usr/bin/env python3

import unittest

from tools import check_compat

DRIVER = "1111111111111111111111111111111111111111"
INTERFACES = "2222222222222222222222222222222222222222"
MODEL = "3333333333333333333333333333333333333333"


def deps(revision):
    return f"""repositories:
  src/vendor/robot_interfaces:
    type: git
    url: https://github.com/SevenovaHangzhou/robot_interfaces.git
    version: "{revision}"
"""


SOURCE_LOCK = f"""schema_version: 1
package: robot_description
repository: https://github.com/SevenovaHangzhou/robot_description.git
source_revision: "{MODEL}"
"""

COMPAT = f"""robot_driver:
  repository: https://github.com/SevenovaHangzhou/robot_driver.git
  revision: "{DRIVER}"
"""


class CheckCompatTest(unittest.TestCase):
    def driver_files(self, revision):
        files = {"deps.repos": deps(INTERFACES), "src/description/source-lock.yaml": SOURCE_LOCK}

        def fetch(repository, commit, path):
            self.assertEqual(commit, DRIVER)
            return files[path]

        return check_compat.check(COMPAT, deps(revision), fetch)

    def test_matching_interfaces_pin_reports_the_model_revision(self):
        findings, model = self.driver_files(INTERFACES)
        self.assertEqual(findings, [])
        self.assertEqual(model, MODEL)

    def test_different_interfaces_pin_is_reported(self):
        findings, _ = self.driver_files("4444444444444444444444444444444444444444")
        self.assertEqual(len(findings), 1)
        self.assertIn(INTERFACES, findings[0])

    def test_branch_names_are_not_pins(self):
        with self.assertRaises(ValueError):
            check_compat.check(COMPAT.replace(DRIVER, "main"), deps(INTERFACES), None)

    def test_unquoted_numeric_revision_is_rejected_not_coerced(self):
        unquoted = COMPAT.replace(f'"{DRIVER}"', DRIVER)
        with self.assertRaises(ValueError):
            check_compat.check(unquoted, deps(INTERFACES), None)


if __name__ == "__main__":
    unittest.main()
