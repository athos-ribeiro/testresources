#
#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#  Copyright (C) 2005  Robert Collins <robertc@robertcollins.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import pyunit3k
import testresources


class MockResource(testresources.TestResource):
    """Resource used for testing ResourcedTestCase."""

    def __init__(self, resource):
        testresources.TestResource.__init__(self)
        self._resource = resource

    def makeResource(self):
        return self._resource


class TestResourcedTestCase(pyunit3k.TestCase):

    def setUp(self):
        pyunit3k.TestCase.setUp(self)
        self.resourced_case = testresources.ResourcedTestCase('run')
        self.resource = self.getUniqueString()
        self.resource_manager = MockResource(self.resource)

    def testDefaults(self):
        self.assertEqual(self.resourced_case.resources, [])

    def testSingleResource(self):
        self.resourced_case.resources = [("foo", self.resource_manager)]
        self.resourced_case.setUpResources()
        self.assertEqual(self.resourced_case.foo, self.resource)
        self.assertEqual(self.resource_manager._uses, 1)
        self.resourced_case.tearDownResources()
        self.failIf(hasattr(self.resourced_case, "foo"))
        self.assertEqual(self.resource_manager._uses, 0)

    def testSingleWithSetup(self):
        self.resourced_case.resources = [("foo", self.resource_manager)]
        self.resourced_case.setUp()
        self.assertEqual(self.resourced_case.foo, self.resource)
        self.assertEqual(self.resource_manager._uses, 1)
        self.resourced_case.tearDown()
        self.failIf(hasattr(self.resourced_case, "foo"))
        self.assertEqual(self.resource_manager._uses, 0)

    def testMultipleResources(self):
        mock_resource = MockResource('Boo!')
        self.resourced_case.resources = [
            ("foo", self.resource_manager), ("bar", mock_resource)]
        self.resourced_case.setUpResources()
        self.assertEqual(self.resourced_case.foo, self.resource)
        self.assertEqual(self.resourced_case.bar, "Boo!")
        self.assertEqual(self.resource_manager._uses, 1)
        self.assertEqual(mock_resource._uses, 1)
        self.resourced_case.tearDownResources()
        self.failIf(hasattr(self.resourced_case, "foo"))
        self.assertEqual(self.resource_manager._uses, 0)
        self.failIf(hasattr(self.resourced_case, "bar"))
        self.assertEqual(mock_resource._uses, 0)


def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
