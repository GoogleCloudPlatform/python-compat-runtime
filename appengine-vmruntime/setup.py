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
#
from setuptools import find_packages
from setuptools import setup

setup(
    name='appengine-vm-runtime',
    version='0.62',
    description='Python Managed VMs Runtime',
    url='https://github.com/GoogleCloudPlatform/appengine-python-vm-runtime',
    author='Google',
    license='Apache License 2.0',
    include_package_data=True,
    packages=find_packages('.'),
    install_requires=[
        'appengine-compat',
        'Werkzeug>=0.10'
    ]
)
