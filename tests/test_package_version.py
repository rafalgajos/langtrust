import re

import langtrust


def test_package_exposes_pep440_version():
    assert re.fullmatch(
        r"\d+\.\d+\.\d+(\.(dev|a|b|rc)\d+)?",
        langtrust.__version__,
    )
