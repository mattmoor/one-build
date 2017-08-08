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

class Base(object):

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Initialize the context."""

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Cleanup the context."""
    pass


class Registry(Base):

  def __init__(self, repo, creds, transport):
    super(Base, self).__init__()
    self._repo = repo
    self._creds = creds
    self._transport = transport

  def __enter__(self):
    return self
