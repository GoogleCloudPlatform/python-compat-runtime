# Copyright 2016 Google Inc. All Rights Reserved.
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

import os

from setuptools import find_packages
from setuptools import setup


NAMESPACE_DECLARATION = """
try:
  __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
  __path__ = __import__('pkgutil').extend_path(__path__, __name__)
"""


def patch_namespace_package(file):
    with open(file, 'r') as f:
        contents = f.read()

    if NAMESPACE_DECLARATION in contents:
        return

    with open(file, 'a') as f:
        f.write(NAMESPACE_DECLARATION)

# WARNING: GIANT FLAMING LAVA PIT HACK.
# Patch the App Engine SDK's google/__init__.py to force it to be a namespace
# package. Without this, none of the other google namespace packages will work
# (e.g. protobuf).
# To be removed with github issue #91.
patch_namespace_package(os.path.join(
    os.path.dirname(__file__),
    'exported_appengine_sdk',
    'google',
    '__init__.py'))


setup(
    name='appengine-compat',
    version='0.64',
    description='Google App Engine-compatible Python libraries for Managed VMs',
    url='https://github.com/GoogleCloudPlatform/appengine-python-vm-runtime',
    author='Google',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    package_dir={'': 'exported_appengine_sdk'},
    include_package_data=True,
    packages=find_packages('exported_appengine_sdk', exclude=['lib.*']),
    namespace_packages=['google'],
    install_requires=[
        'requests>=2.5.0',
        'webapp2>=2.5.2',
        'WebOb>=1.4',
        'PyYAML>=3.11'
    ]
)
