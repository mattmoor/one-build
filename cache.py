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

"""This package defines the interface for caching objects."""

import abc
import hashlib

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_image
from containerregistry.client.v2_2 import docker_session

class Base(object):

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Initialize the context."""

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Cleanup the context."""
    pass

  @abc.abstractmethod
  def Get(self, base_image, namespace, checksum):
    """Lookup a cached image.

    Args:
      base_image: the docker_image.Image on which things are based.
      namespace: a namespace for this cache.
      checksum: the checksum of the package descriptor atop our base.

    Returns:
      the docker_image.Image of the cache hit, or None.
    """

  @abc.abstractmethod
  def Store(self, base_image, namespace, checksum, value):
    """Lookup a cached image.

    Args:
      base_image: the docker_image.Image on which things are based.
      namespace: a namespace for this cache.
      checksum: the checksum of the package descriptor atop our base.
      value: the docker_image.Image to store into the cache.
    """


class Registry(Base):

  def __init__(self, repo, creds, transport, threads=1, mount=None):
    super(Base, self).__init__()
    self._repo = repo
    self._creds = creds
    self._transport = transport
    self._threads = threads
    self._mount = mount or []

  def __enter__(self):
    return self

  def _tag(self, base_image, namespace, checksum):
    # TODO(mattmoor): pick up the latest containerregistry then use:
    # fingerprint = '%s %s' % (base_image.digest(), checksum)
    fingerprint = checksum
    return docker_name.Tag('{base}/{namespace}:{tag}'.format(
      base=str(self._repo),
      namespace=namespace,
      tag=hashlib.sha256(fingerprint).hexdigest()))

  def Get(self, base_image, namespace, checksum):
    entry = self._tag(base_image, namespace, checksum)
    with docker_image.FromRegistry(
        entry, self._creds, self._transport) as img:
      if img.exists():
        print('Found cached base image: %s.' % entry)
        return img
    return None

  def Store(self, base_image, namespace, checksum, value):
    entry = self._tag(base_image, namespace, checksum)
    with docker_session.Push(
        entry, self._creds, self._transport, threads=self._threads,
        mount=self._mount) as session:
      session.upload(value)
      print('Stored base image to cache: %s.' % entry)
