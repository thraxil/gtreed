"""Package Index Tests
"""
# More would be better!

import os, shutil, tempfile, unittest
import pkg_resources
import setuptools.package_index

class TestPackageIndex(unittest.TestCase):

    def test_bad_urls(self):
        index = setuptools.package_index.PackageIndex()
        url = 'http://127.0.0.1/nonesuch/test_package_index'
        try:
            index.open_url(url)
        except Exception, v:
            self.assert_(url in str(v))
        else:
            self.assert_(False)
