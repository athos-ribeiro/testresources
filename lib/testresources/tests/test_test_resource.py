
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

import testtools

import testresources
from testresources.tests import (
    ResultWithResourceExtensions,
    ResultWithoutResourceExtensions,
    )


def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result


class MockResourceInstance(object):

    def __init__(self, name):
        self._name = name

    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)

    def __repr__(self):
        return self._name


class MockResource(testresources.TestResource):
    """Mock resource that logs the number of make and clean calls."""

    def __init__(self):
        testresources.TestResource.__init__(self)
        self.makes = 0
        self.cleans = 0

    def clean(self, resource):
        self.cleans += 1

    def make(self, dependency_resources):
        self.makes += 1
        return MockResourceInstance("Boo!")


class MockResettableResource(MockResource):
    """Mock resource that logs the number of reset calls too."""

    def __init__(self):
        MockResource.__init__(self)
        self.resets = 0

    def reset(self, resource, result):
        self.resets += 1
        resource._name += "!"
        return resource


class TestTestResource(testtools.TestCase):

    def testUnimplementedGetResource(self):
        # By default, TestResource raises NotImplementedError on getResource
        # because make is not defined initially.
        resource_manager = testresources.TestResource()
        self.assertRaises(NotImplementedError, resource_manager.getResource)

    def testInitiallyNotDirty(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(False, resource_manager._dirty)

    def testInitiallyUnused(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(0, resource_manager._uses)

    def testInitiallyNoCurrentResource(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(None, resource_manager._currentResource)

    def testneededResourcesDefault(self):
        # Calling neededResources on a default TestResource returns the
        # resource.
        resource = testresources.TestResource()
        self.assertEqual([resource], resource.neededResources())

    def testneededResourcesDependenciesFirst(self):
        # Calling neededResources on a TestResource with dependencies puts the
        # dependencies first.
        resource = testresources.TestResource()
        dep1 = testresources.TestResource()
        dep2 = testresources.TestResource()
        resource.resources.append(("dep1", dep1))
        resource.resources.append(("dep2", dep2))
        self.assertEqual([dep1, dep2, resource], resource.neededResources())

    def testneededResourcesClosure(self):
        # Calling neededResources on a TestResource with dependencies includes
        # the needed resources of the needed resources.
        resource = testresources.TestResource()
        dep1 = testresources.TestResource()
        dep2 = testresources.TestResource()
        resource.resources.append(("dep1", dep1))
        dep1.resources.append(("dep2", dep2))
        self.assertEqual([dep2, dep1, resource], resource.neededResources())

    def testDefaultCosts(self):
        # The base TestResource costs 1 to set up and to tear down.
        resource_manager = testresources.TestResource()
        self.assertEqual(resource_manager.setUpCost, 1)
        self.assertEqual(resource_manager.tearDownCost, 1)

    def testGetResourceReturnsMakeResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(resource_manager.make({}), resource)

    def testGetResourceIncrementsUses(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager._uses)
        resource_manager.getResource()
        self.assertEqual(2, resource_manager._uses)

    def testGetResourceDoesntDirty(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(resource_manager._dirty, False)

    def testGetResourceSetsCurrentResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertIs(resource_manager._currentResource, resource)

    def testGetResourceTwiceReturnsIdenticalResource(self):
        resource_manager = MockResource()
        resource1 = resource_manager.getResource()
        resource2 = resource_manager.getResource()
        self.assertIs(resource1, resource2)

    def testGetResourceCallsMakeResource(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)

    def testIsDirty(self):
        resource_manager = MockResource()
        r = resource_manager.getResource()
        resource_manager.dirtied(r)
        self.assertTrue(resource_manager.isDirty())
        resource_manager.finishedWith(r)

    def testIsDirtyIsTrueIfDependenciesChanged(self):
        resource_manager = MockResource()
        dep1 = MockResource()
        dep2 = MockResource()
        dep3 = MockResource()
        resource_manager.resources.append(("dep1", dep1))
        resource_manager.resources.append(("dep2", dep2))
        resource_manager.resources.append(("dep3", dep3))
        r = resource_manager.getResource()
        dep2.dirtied(r.dep2)
        r2 =dep2.getResource()
        self.assertTrue(resource_manager.isDirty())
        resource_manager.finishedWith(r)
        dep2.finishedWith(r2)

    def testIsDirtyIsTrueIfDependenciesAreDirty(self):
        resource_manager = MockResource()
        dep1 = MockResource()
        dep2 = MockResource()
        dep3 = MockResource()
        resource_manager.resources.append(("dep1", dep1))
        resource_manager.resources.append(("dep2", dep2))
        resource_manager.resources.append(("dep3", dep3))
        r = resource_manager.getResource()
        dep2.dirtied(r.dep2)
        self.assertTrue(resource_manager.isDirty())
        resource_manager.finishedWith(r)

    def testRepeatedGetResourceCallsMakeResourceOnceOnly(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)

    def testGetResourceResetsUsedResource(self):
        resource_manager = MockResettableResource()
        resource_manager.getResource()
        resource = resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)
        resource_manager.dirtied(resource)
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)
        self.assertEqual(1, resource_manager.resets)
        resource_manager.finishedWith(resource)

    def testUsedResourceResetBetweenUses(self):
        resource_manager = MockResettableResource()
        # take two refs; like happens with OptimisingTestSuite.
        resource_manager.getResource()
        resource = resource_manager.getResource()
        resource_manager.dirtied(resource)
        resource_manager.finishedWith(resource)
        # Get again, but its been dirtied.
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        resource_manager.finishedWith(resource)
        # The resource is made once, reset once and cleaned once.
        self.assertEqual(1, resource_manager.makes)
        self.assertEqual(1, resource_manager.resets)
        self.assertEqual(1, resource_manager.cleans)

    def testFinishedWithDecrementsUses(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        self.assertEqual(2, resource_manager._uses)
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager._uses)
        resource_manager.finishedWith(resource)
        self.assertEqual(0, resource_manager._uses)

    def testFinishedWithResetsCurrentResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertIs(None, resource_manager._currentResource)

    def testFinishedWithCallsCleanResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager.cleans)

    def testUsingTwiceMakesAndCleansTwice(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(2, resource_manager.makes)
        self.assertEqual(2, resource_manager.cleans)

    def testFinishedWithCallsCleanResourceOnceOnly(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(0, resource_manager.cleans)
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager.cleans)

    def testFinishedWithMarksNonDirty(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.dirtied(resource)
        resource_manager.finishedWith(resource)
        self.assertEqual(False, resource_manager._dirty)

    def testResourceAvailableBetweenFinishedWithCalls(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertIs(resource, resource_manager._currentResource)
        resource_manager.finishedWith(resource)

    # The default implementation of reset() performs a make/clean if
    # the dirty flag is set.
    def testDirtiedSetsDirty(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(False, resource_manager._dirty)
        resource_manager.dirtied(resource)
        self.assertEqual(True, resource_manager._dirty)

    def testDirtyingResourceTriggersCleanOnGet(self):
        resource_manager = MockResource()
        resource1 = resource_manager.getResource()
        resource2 = resource_manager.getResource()
        resource_manager.dirtied(resource2)
        resource_manager.finishedWith(resource2)
        self.assertEqual(0, resource_manager.cleans)
        resource3 = resource_manager.getResource()
        self.assertEqual(1, resource_manager.cleans)
        resource_manager.finishedWith(resource3)
        resource_manager.finishedWith(resource1)
        self.assertEqual(2, resource_manager.cleans)

    def testDefaultResetMethodPreservesCleanResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)
        self.assertEqual(False, resource_manager._dirty)
        resource_manager.reset(resource)
        self.assertEqual(1, resource_manager.makes)
        self.assertEqual(0, resource_manager.cleans)

    def testDefaultResetMethodRecreatesDirtyResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)
        resource_manager.dirtied(resource)
        resource_manager.reset(resource)
        self.assertEqual(2, resource_manager.makes)
        self.assertEqual(1, resource_manager.cleans)

    def testDirtyingWhenUnused(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        resource_manager.dirtied(resource)
        self.assertEqual(1, resource_manager.makes)
        resource = resource_manager.getResource()
        self.assertEqual(2, resource_manager.makes)

    def testFinishedActivityForResourceWithoutExtensions(self):
        result = ResultWithoutResourceExtensions()
        resource_manager = MockResource()
        r = resource_manager.getResource()
        resource_manager.finishedWith(r, result)

    def testFinishedActivityForResourceWithExtensions(self):
        result = ResultWithResourceExtensions()
        resource_manager = MockResource()
        r = resource_manager.getResource()
        expected = [("clean", "start", resource_manager),
            ("clean", "stop", resource_manager)]
        resource_manager.finishedWith(r, result)
        self.assertEqual(expected, result._calls)

    def testGetActivityForResourceWithoutExtensions(self):
        result = ResultWithoutResourceExtensions()
        resource_manager = MockResource()
        r = resource_manager.getResource(result)
        resource_manager.finishedWith(r)

    def testGetActivityForResourceWithExtensions(self):
        result = ResultWithResourceExtensions()
        resource_manager = MockResource()
        r = resource_manager.getResource(result)
        expected = [("make", "start", resource_manager),
            ("make", "stop", resource_manager)]
        resource_manager.finishedWith(r)
        self.assertEqual(expected, result._calls)

    def testResetActivityForResourceWithoutExtensions(self):
        result = ResultWithoutResourceExtensions()
        resource_manager = MockResource()
        resource_manager.getResource()
        r = resource_manager.getResource()
        resource_manager.dirtied(r)
        resource_manager.finishedWith(r)
        r = resource_manager.getResource(result)
        resource_manager.dirtied(r)
        resource_manager.finishedWith(r)
        resource_manager.finishedWith(resource_manager._currentResource)

    def testResetActivityForResourceWithExtensions(self):
        result = ResultWithResourceExtensions()
        resource_manager = MockResource()
        expected = [("clean", "start", resource_manager),
            ("clean", "stop", resource_manager),
            ("make", "start", resource_manager),
            ("make", "stop", resource_manager)]
        resource_manager.getResource()
        r = resource_manager.getResource()
        resource_manager.dirtied(r)
        resource_manager.finishedWith(r)
        r = resource_manager.getResource(result)
        resource_manager.dirtied(r)
        resource_manager.finishedWith(r)
        resource_manager.finishedWith(resource_manager._currentResource)
        self.assertEqual(expected, result._calls)
