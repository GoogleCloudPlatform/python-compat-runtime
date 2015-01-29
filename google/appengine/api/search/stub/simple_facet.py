#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""A Simple facet analyzer."""

from google.appengine.datastore import document_pb


class SimpleFacet(object):
  """A Simple facet analyzer."""

  def __init__(self, params):
    self._params = params

  def FillFacetResponse(self, results, response):
    """Extract facet results and add them to the response."""


    manual_facet_map = {}
    manual_facets = {}
    for manual_facet in self._params.include_facet_list():
      manual_facet_map[manual_facet.name()] = manual_facet.params()


      if (manual_facet.params().range_list() and
          manual_facet.params().value_constraint_list()):
        raise ValueError('Manual facet request should either specify range '
                         'or value constraint, not both')
      facet_obj = _Facet(
          manual_facet.name(),
          (manual_facet.params().value_limit()
           if manual_facet.params().has_value_limit()
           else self._params.facet_auto_detect_param().value_limit()))
      manual_facets[manual_facet.name()] = facet_obj


      for value in manual_facet.params().value_constraint_list():
        facet_obj.AddValue(value, 0)


      for range_pb in manual_facet.params().range_list():
        range_pair = (
            float(range_pb.start()) if range_pb.has_start() else None,
            float(range_pb.end()) if range_pb.has_end() else None)
        facet_obj.AddValue(self._GetFacetLabel(range_pb),
                           0, refinement=range_pair)

    if not manual_facet_map and not self._params.auto_discover_facet_count():
      return
    discovered_facets = {}



    for result in results[:self._params.facet_depth()]:
      for facet in result.document.facet_list():

        if facet.value().type() == document_pb.FacetValue.ATOM:

          if facet.name() in manual_facet_map:
            manual_facet_req = manual_facet_map[facet.name()]
            facet_obj = manual_facets[facet.name()]



            if not manual_facet_req.range_list() and (
                not manual_facet_req.value_constraint_list() or
                facet.value().string_value() in
                manual_facet_req.value_constraint_list()):
              facet_obj.AddValue(facet.value().string_value())
          elif self._params.auto_discover_facet_count():
            if facet.name() in discovered_facets:
              facet_obj = discovered_facets[facet.name()]
            else:
              facet_obj = discovered_facets[facet.name()] = _Facet(
                  facet.name(),
                  self._params.facet_auto_detect_param().value_limit())
            facet_obj.AddValue(facet.value().string_value())

        elif facet.value().type() == document_pb.FacetValue.NUMBER:
          facet_value = float(facet.value().string_value())
          if facet.name() in manual_facet_map:
            manual_facet_req = manual_facet_map[facet.name()]
            facet_obj = manual_facets[facet.name()]
            if manual_facet_req.range_list():
              for range_pb in manual_facet_req.range_list():
                range_pair = (
                    float(range_pb.start()) if range_pb.has_start() else None,
                    float(range_pb.end()) if range_pb.has_end() else None)
                if ((range_pair[0] is None or facet_value >= range_pair[0]) and
                    (range_pair[1] is None or facet_value < range_pair[1])):
                  facet_obj.AddValue(self._GetFacetLabel(range_pb),
                                     refinement=range_pair)
            elif manual_facet_req.value_constraint_list():
              for constraint in manual_facet_req.value_constraint_list():
                if facet_value == float(constraint):
                  facet_obj.AddValue(constraint)
            else:
              facet_obj.AddNumericValue(facet_value)
          elif self._params.auto_discover_facet_count():
            if facet.name() in discovered_facets:
              facet_obj = discovered_facets[facet.name()]
            else:
              facet_obj = discovered_facets[facet.name()] = _Facet(
                  facet.name(),
                  self._params.facet_auto_detect_param().value_limit())
            facet_obj.AddNumericValue(facet_value)
        else:
          raise ValueError('Facet type %d is not supported' %
                           facet.value().type())



    for facet in manual_facets.values():
      self._FillResponseForSingleFacet(facet, response.add_facet_result())
    for facet in  _GetTopN(discovered_facets.values(),
                           self._params.auto_discover_facet_count()):
      self._FillResponseForSingleFacet(facet, response.add_facet_result())

  def _FillResponseForSingleFacet(self, facet, facet_result_pb):
    """Convert a single _Facet to a facet_result_pb."""


    if facet.min is not None:
      facet.AddValue('[%s,%s)' % (facet.min, facet.max), facet.min_max_count,
                     (facet.min, facet.max))
    facet_result_pb.set_name(facet.name)
    for value in facet.GetTopValues(facet.value_limit):
      value_pb = facet_result_pb.add_value()
      ref_pb = value_pb.mutable_refinement()


      if value.refinement is not None:
        if value.refinement[0] is not None:
          ref_pb.mutable_range().set_start(str(value.refinement[0]))
        if value.refinement[1] is not None:
          ref_pb.mutable_range().set_end(str(value.refinement[1]))
      else:


        ref_pb.set_value(str(value.label))
      ref_pb.set_name(facet.name)
      value_pb.set_name(str(value.label))
      value_pb.set_count(value.count)

  def _GetFacetLabel(self, range_pb):
    if range_pb.has_name():
      return range_pb.name()
    else:
      return '[%s,%s)' % (str(float(range_pb.start()))
                          if range_pb.has_start() else '-Infinity',
                          str(float(range_pb.end()))
                          if range_pb.has_end() else 'Infinity')

  def RefineResults(self, results):
    """Returns refined results using facet refinement parameters."""
    if not self._params.facet_refinement_list():
      return results


    ref_groups = {}
    for refinement in self._params.facet_refinement_list():
      if refinement.name() in ref_groups:
        ref_groups[refinement.name()].append(refinement)
      else:
        ref_groups[refinement.name()] = [refinement]

    return [doc for doc in results
            if self._MatchFacetRefinements(doc, ref_groups)]

  def _MatchFacetRefinements(self, doc, ref_groups):


    return all([self._MatchFacetRefinementSameName(doc, ref_same_names)
                for ref_same_names in ref_groups.values()])

  def _MatchFacetRefinementSameName(self, doc, ref_same_names):

    return any([self._MatchFacetRefinement(doc, ref)
                for ref in ref_same_names])

  def _MatchFacetRefinement(self, doc, refinement):


    doc_facets = []
    for facet in doc.document.facet_list():
      if facet.name() == refinement.name():
        doc_facets.append(facet)
    return any([self._MatchSingleFacetRefinement(doc_facet, refinement)
                for doc_facet in doc_facets])

  def _MatchSingleFacetRefinement(self, doc_facet, refinement):

    if refinement.has_value():
      if refinement.has_range():
        raise ValueError('Refinement request for facet %s should either '
                         'specify range or value constraint, '
                         'not both.' % refinement.name())
      facet_value = doc_facet.value().string_value()
      if doc_facet.value().type() == document_pb.FacetValue.NUMBER:
        return float(facet_value) == float(refinement.value())
      else:
        return facet_value == refinement.value()
    else:
      if not refinement.has_range():
        raise ValueError('Refinement request for facet %s should specify '
                         'range or value constraint.' % refinement.name())


      if doc_facet.value().type() != document_pb.FacetValue.NUMBER:
        return False
      facet_value = float(doc_facet.value().string_value())
      ref_range = refinement.range()
      start = float(ref_range.start()) if ref_range.has_start() else None
      end = float(ref_range.end()) if ref_range.has_end() else None
      return ((start is None or facet_value >= start) and
              (end is None or facet_value < end))


class _FacetValue(object):
  """A representation of a single facet value."""

  def __init__(self, label, count=0, refinement=None):
    """Initilizer.

    Args:
      label: label of this value. can be the actual value or a custom label for
        ranges. If this is a custom label, refinement should be set.
      count: Initial number of facets with this value. This number can be
        increased later.
      refinement: If this value does not need a custom refinement, this value
        should be None. If the value needs a range refinement, this value should
        be a pair representing start and end value for the range.
    """
    self._label = label
    self._count = count
    self._refinement = refinement

  @property
  def label(self):
    return self._label

  @property
  def count(self):
    return self._count

  @property
  def refinement(self):
    return self._refinement

  def IncCount(self, value):
    self._count += value

  def __repr__(self):
    return '_FacetValue(label=%s, count=%d, refinement=%s)' % (self.label,
                                                               self.count,
                                                               self.refinement)


class _Facet(object):
  """Simple facet implementation that holds values and overall count."""

  def __init__(self, name, value_limit):
    """Initilizer.

    Args:
      name: The name of the facet.
      value_limit: Maximum number of values for this facet.
    """
    self._name = name
    self._value_limit = value_limit
    self._values = {}
    self._count = 0
    self._min = self._max = None
    self._min_max_count = 0

  @property
  def name(self):
    return self._name

  @property
  def value_limit(self):
    return self._value_limit

  @property
  def count(self):
    return self._count + self._min_max_count

  @property
  def min(self):
    return self._min

  @property
  def max(self):
    return self._max

  @property
  def min_max_count(self):
    return self._min_max_count

  def AddNumericValue(self, value):
    """Add value for discovered numeric facets.

    For numeric facets, we only keep minimum and maximum values not the actual
    value.

    Args:
      value: numeric value.
    """
    if self._min is None or self._min > value:
      self._min = value
    if self._max is None or self._max < value:
      self._max = value
    self._min_max_count += 1

  def AddValue(self, label, count=1, refinement=None):
    if label in self._values:
      self._values[label].IncCount(count)
    else:
      self._values[label] = _FacetValue(label, count, refinement)
    self._count += count

  def GetTopValues(self, n):
    return _GetTopN(self._values.values(), n)

  def __repr__(self):
    return '_Facet(name=%s, count=%d, values=%s)' % (
        self.name, self.count, self._values)


def _GetTopN(objects, n):
  """Returns top n objects with maximum count.

  Args:
    objects: any object that has count property
    n: number of top elements to return
  Returns:
    top N elements if objects size is greater than N otherwise the map elements
    in a sorted order.
  """
  return sorted(objects, key=lambda o: o.count, reverse=True)[:n]
