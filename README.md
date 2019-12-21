PLEASE NOTE:
====================

This library is currently still under development. The API will likely undergo significant changes that may break any code you write with it.
The documentation will fall out of sync with the updates regularly until development slows down. Use it at your own risk.

Overview
====================

Provides a wide range of useful classes and functions:

The `NestedParser` class
--------------------

* Parse a string by user-specified opening/closing tokens, recursively
* Can ignore tokens between specific tags (for example, within string quotation marks)
* Return an object tree (currently traversal methods are limited)

Context manager classes
--------------------

* `SysTrayApp` hides the console and runs a system tray app which can have its options customized with callbacks
* `Timer` counts the time since it was instanciated, and prints it on exiting context
* `Suppressor` supresses all console output and warnings on enter and resores it on exiting
* `PrintRedirector` redirects stdout to a given file
* `NullContext` will always return itself on attribute access or when called, and does nothing when used as a context manager or when attributes are set on it

Other misc classes
--------------------

* `Counter` is an object-oriented replacement for manipulating an integer var for iteration purposes
* `WhoCalledMe` can be dropped in to print out the call stack
* `EnvironmentVariables` can be used on Windows to get and set environment variables permanently
* `Beep` produces a beeping sound of variable duration on Windows
* `Version` object to represent versions, with comparator magic methods and wildcard support

Misc functions
--------------------

* `is_running_in_ipython` returns `True` if in an ipython session, else `False`
* `issubclass_safe` is a version of the built-in `issubclass` that doesn't raise an error if the candidate is an instance rather than a class, just returns `False`

Installation
====================

To install use pip:

    $ pip install pymiscutils


Or clone the repo:

    $ git clone https://github.com/matthewgdv/miscutils.git
    $ python setup.py install


Usage
====================

Usage examples coming soon.

Contributing
====================

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

You can contribute in many ways:

Report Bugs
--------------------

Report bugs at https://github.com/matthewgdv/miscutils/issues

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
--------------------

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

Implement Features
--------------------

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

Write Documentation
--------------------

The repository could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

Submit Feedback
--------------------

The best way to send feedback is to file an issue at https://github.com/matthewgdv/miscutils/issues.

If you are proposing a new feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are welcome :)

Get Started!
--------------------

Before you submit a pull request, check that it meets these guidelines:

1.  If the pull request adds functionality, it should include tests and the docs should be updated. Write docstrings for any functions that are part of the external API, and add
    the feature to the README.md.

2.  If the pull request fixes a bug, tests should be added proving that the bug has been fixed. However, no update to the docs is necessary for bugfixes.

3.  The pull request should work for the newest version of Python (currently 3.7). Older versions may incidentally work, but are not officially supported.

4.  Inline type hints should be used, with an emphasis on ensuring that introspection and autocompletion tools such as Jedi are able to understand the code wherever possible.

5.  PEP8 guidelines should be followed where possible, but deviations from it where it makes sense and improves legibility are encouraged. The following PEP8 error codes can be
    safely ignored: E121, E123, E126, E226, E24, E704, W503

6.  This repository intentionally disallows the PEP8 79-character limit. Therefore, any contributions adhering to this convention will be rejected. As a rule of thumb you should
    endeavor to stay under 200 characters except where going over preserves alignment, or where the line is mostly non-algorythmic code, such as extremely long strings or function
    calls.
