# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This package defines the interface for orchestrating image builds."""

import abc
import cStringIO
import gzip

import context

class Base(object):

  __metaclass__ = abc.ABCMeta  # For enforcing that methods are overriden.

  def __init__(self, ctx):
    self._ctx = ctx

  @abc.abstractmethod
  def CreatePackageBase(self, base_image, cache):
    """Create an image exists with the packages on this base.

    Args:
      base_image: docker_name.Tag, the base image atop which we install pkgs.
      cache: cache.Base, a cache into which artifacts may be read/written.

    Returns:
      a v2_2.docker_image.DockerImage of the above.
    """

  @abc.abstractmethod
  def BuildAppLayer(self):
    """Synthesizes the application layer from the context.

    Returns:
      a raw string of the layer's .tar.gz
    """

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Initialize the builder."""

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Cleanup after the builder."""
    pass


class Null(Base):

  def __init__(self, ctx):
    super(Null, self).__init__(ctx)

  def __enter__(self):
    """Override."""
    return self

  def CreatePackageBase(self, base_image, cache):
    """Override."""
    # TODO(mattmoor): WE NEED TO APPEND SHIT.
    print('TODO: Write the application layer.')
    return base_image

  def BuildAppLayer(self):
    """Override."""
    buf = cStringIO.StringIO()
    f = gzip.GzipFile(mode='wb', fileobj=buf)
    try:
      print('TODO: Write the application data.')
      # TODO(mattmoor): f.write(unzipped)
    finally:
      f.close()
    return buf.getvalue()

# TODO(mattmoor): class Python(Base):
# TODO(mattmoor): class Node(Base):
# TODO(mattmoor): class Java(Base):


def From(ctx):
  return Null(ctx)
