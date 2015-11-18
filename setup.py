# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Configure and install the runtime package."""

from setuptools import find_packages
from setuptools import setup

setup(name='appengine-python-vm-runtime',
      version='0.2',
      description='Google App Engine-compatible Python runtime for Managed VMs',
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
      package_dir={'': 'python_vm_runtime',
                   'google.appengine.vmruntime': 'multicore_runtime',},
      include_package_data=True,
      packages=find_packages('python_vm_runtime',
                             exclude=['lib.*'])+['google.appengine.vmruntime'],
      # namespace_packages=['google'],  # This skips google/__init__.py
      install_requires=['requests>=2.5.0',
                        'webapp2>=2.5.2',
                        'WebOb>=1.4',
                        'PyYAML>=3.11',
                        'Werkzeug>=0.10'],)
