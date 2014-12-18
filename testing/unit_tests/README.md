# How to use Unit test

First, install py.test using:
~~~
pip install pytest
~~~

The concept is that the function py.test will test all files with prefix "test" under the local directory (with recursivity) and containing methods named "test".

~~~
py.test
py.test -s (for verbose)
~~~

