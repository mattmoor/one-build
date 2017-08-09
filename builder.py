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
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import zipfile

from containerregistry.client.v2_2 import append


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


class JustApp(Base):

  def __init__(self, ctx):
    super(JustApp, self).__init__(ctx)

  def __enter__(self):
    """Override."""
    return self

  def CreatePackageBase(self, base_image, cache):
    """Override."""
    # JustApp doesn't install anything, it just appends
    # the application layer, so return the base image as
    # our package base.
    return base_image

  def BuildAppLayer(self):
    """Override."""
    buf = cStringIO.StringIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as out:
      for name in self._ctx.ListFiles():
        content = self._ctx.GetFile(name)
        info = tarfile.TarInfo(os.path.join('app', name))
        info.size = len(content)
        out.addfile(info, fileobj=cStringIO.StringIO(content))
    return buf.getvalue()

_PYTHON_NAMESPACE = 'python-requirements-cache'


class Python(JustApp):

  def __init__(self, ctx):
    super(Python, self).__init__(ctx)

  def __enter__(self):
    """Override."""
    # TODO(mattmoor): Clean up.
    self._tempdir = tempfile.mkdtemp()
    return self

  def _ResolveWHLs(self, descriptor):
    requirements = os.path.join(self._tempdir, 'requirements.txt')
    with open(requirements, 'wb') as f:
      f.write(descriptor)
    # For now, invoke `pip wheel` on a temporary directory and return a list
    # of the resulting .whl files.
    fnull = open(os.devnull, 'w') # or verbose?
    subprocess.check_call(
      ['pip', 'wheel', '-w', self._tempdir, '-r', requirements],
      stdout=fnull, stderr=fnull)
    # Return a list of all of the .whl files.
    return [os.path.join(self._tempdir, f)
            for f in os.listdir(self._tempdir)
            if f.endswith('.whl')]

  def _AddWHLFiles(self, whl, tar):
    # Open the .whl (zip) and put all its files into a .tar.gz laid
    # out like it should be on the filesystem.
    zf = zipfile.ZipFile(whl, 'r')

    target_dir = 'usr/local/lib/python2.7/dist-packages/'
    for name in zf.namelist():
      content = zf.read(name)
      info = tarfile.TarInfo(os.path.join(target_dir, name))
      info.size = len(content)
      tar.addfile(info, fileobj=cStringIO.StringIO(content))

  def _AddWHLScripts(self, whl, tar):
    # Open the .whl (zip) and create the scripts described in package metadata.
    zf = zipfile.ZipFile(whl, 'r')

    # http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
    basename = os.path.basename(whl)
    dist_parts = basename.split('-')
    distribution = '-'.join(dist_parts[:2])
    metadata = json.loads(zf.read(
      os.path.join(distribution + '.dist-info', 'metadata.json')))

    extensions = metadata.get('extensions')
    if not extensions:
      return

    commands = extensions.get('python.commands')
    if not commands:
      return

    scripts = commands.get('wrap_console', {})
    # TODO(mattmoor): Use distutils when doing this for realz
    target_dir = 'usr/local/bin'
    # Create the scripts in a deterministic ordering.
    for script in sorted(scripts):
      descriptor = scripts[script]
      (module, obj) = descriptor.split(':')
      content = """#!/usr/bin/python

# -*- coding: utf-8 -*-
import re
import sys

from {module} import {obj}

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(run())
""".format(module=module, obj=obj)

      target_path = os.path.join('usr/local/bin')
      info = tarfile.TarInfo(os.path.join(target_dir, script))
      info.size = len(content)
      info.mode = 0777
      tar.addfile(info, fileobj=cStringIO.StringIO(content))

  def CreatePackageBase(self, base_image, cache):
    """Override."""
    descriptor = self._ctx.GetFile('requirements.txt')
    checksum = hashlib.sha256(descriptor).hexdigest()
    hit = cache.Get(base_image, _PYTHON_NAMESPACE, checksum)
    if hit:
      return hit

    buf = cStringIO.StringIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as out:
      for whl in self._ResolveWHLs(descriptor):
        self._AddWHLFiles(whl, out)
        self._AddWHLScripts(whl, out)
    layer = buf.getvalue()

    with append.Layer(base_image, layer) as dep_image:
      cache.Store(base_image, _PYTHON_NAMESPACE, checksum, dep_image)
    return append.Layer(base_image, layer)


class Node(JustApp):

  def __init__(self, ctx):
    super(Python, self).__init__(ctx)

  def __enter__(self):
    """Override."""
    return self

  def CreatePackageBase(self, base_image, cache):
    """Override."""
    raise Exception('npm install is not implemented')

# TODO(mattmoor): class Java(Base):


def From(ctx):
  if ctx.Contains('requirements.txt'):
    return Python(ctx)
  elif ctx.Contains('package.json'):
    return Node(ctx)
  else:
    return JustApp(ctx)
