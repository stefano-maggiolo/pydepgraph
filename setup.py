#!/usr/bin/python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2012 Stefano Maggiolo <s.maggiolo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Installation routines."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from setuptools import setup


def do_setup():
    """Execute the setup thanks to setuptools."""
    setup(name="pydepgraph",
          version="0.1",
          author="Stefano Maggiolo",
          author_email="s.maggiolo@gmail.com",
          url="",
          download_url="",
          description="A dependencies analyzer for Python",
          packages=["pydepgraph"],
          entry_points={
              "console_scripts": ["pydepgraph=pydepgraph:main"]
          },
          keywords="dependencies dependency graph dot graphviz python",
          license="General Public License v3",
          classifiers=[
              "Development Status :: 4 - Beta",
              "Natural Language :: English",
              "Operating System :: POSIX :: Linux",
              "Programming Language :: Python :: 2",
              "Programming Language :: Python :: 3",
              "License :: OSI Approved :: "
              "GNU General Public License v3",
          ],
    )


if __name__ == "__main__":
    do_setup()
