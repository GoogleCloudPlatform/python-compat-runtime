from setuptools import setup, find_packages

setup(name='python-runtime',
      version='0.1',
      description='Google App Engine-compatible Python runtime for Managed VMs',
      url='https://github.com/GoogleCloudPlatform/appengine-python-vm-runtime',
      author='Google',
      license='Apache License 2.0',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
      ],
      package_dir={'': 'python_vm_runtime',
                   'google.appengine.vmruntime': 'multicore_runtime',},
      include_package_data=True,
      packages=find_packages('python_vm_runtime') + ['google.appengine.vmruntime'],
      # namespace_packages=['google'], # While google is a namespace, marking
                                       # it as such makes the installer skip
                                       # __init__.py, which breaks some
                                       # packages expecting google to have
                                       # a __file__ attribute.
      install_requires=['requests>=2.5.0',
                        'webapp2>=2.5.2',
                        'WebOb>=1.4',
                        'PyYAML>=3.11',
                        'Werkzeug>=0.10',],)
