"""主模組單元測試。"""

import unittest

from tw_stock_indicator import __version__
from tw_stock_indicator.main import main


class TestPackageImport(unittest.TestCase):
    """驗證套件可正常載入。"""

    def test_version_exists(self):
        """確認版本號已定義。"""
        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)

    def test_main_runs(self):
        """確認 main 函式可正常執行。"""
        main()


if __name__ == "__main__":
    unittest.main()
