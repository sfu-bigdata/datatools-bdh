from setuptools import setup, find_packages

setup(name='datatools_bdh',
      version='0.1',
      description='Data tools used at SFU\'s Big Data Hub',
      url='http://github.com/sfu-bigdata/datatools-bdh',
      author='Steven Bergner',
      author_email='bdi-consulting@sfu.ca',
      license='MIT',
      packages=find_packages(),
      package_data={'datatools_bdh': ['resources/*']},
      include_package_data=True,
      zip_safe=False)
