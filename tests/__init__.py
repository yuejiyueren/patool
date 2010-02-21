# -*- coding: utf-8 -*-
# Copyright (C) 2010 Bastian Kleineidam
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os
import shutil
import nose
import patoolib
from distutils.spawn import find_executable

basedir = os.path.dirname(__file__)
datadir = os.path.join(basedir, 'data')

class ArchiveTest (unittest.TestCase):
    """Helper class for achive tests."""

    def archive_commands (self, filename, cmd, singlefile=False):
        self.archive_list(filename, cmd)
        self.archive_test(filename, cmd)
        self.archive_extract(filename, cmd)
        self.archive_create(filename, cmd, singlefile=singlefile)

    def archive_extract (self, filename, cmd):
        archive = os.path.join(datadir, filename)
        # create a temporary directory for extraction
        tmpdir = patoolib.util.tmpdir(dir=basedir)
        os.chdir(tmpdir)
        try:
            patoolib._handle_archive(archive, 'extract', program=cmd)
            patoolib._handle_archive(archive, 'extract', program=cmd, force=True)
        finally:
            os.chdir(basedir)
            shutil.rmtree(tmpdir)

    def archive_list (self, filename, cmd):
        archive = os.path.join(datadir, filename)
        patoolib._handle_archive(archive, 'list', program=cmd)
        patoolib._handle_archive(archive, 'list', program=cmd, verbose=True)

    def archive_test (self, filename, cmd):
        archive = os.path.join(datadir, filename)
        patoolib._handle_archive(archive, 'test', program=cmd)
        patoolib._handle_archive(archive, 'test', program=cmd, verbose=True)

    def archive_create (self, filename, cmd, singlefile=False):
        # the file or directory to pack
        if singlefile:
            topack = os.path.join(datadir, 'foo.txt')
        else:
            topack = os.path.join(datadir, 'foo')
        # create a temporary directory for creation
        tmpdir = patoolib.util.tmpdir(dir=basedir)
        archive = os.path.join(tmpdir, filename)
        os.chdir(tmpdir)
        try:
            patoolib._handle_archive(archive, 'create', topack, program=cmd)
            # not all programs can test what they create
            if cmd == 'compress':
                cmd = 'gzip'
            patoolib._handle_archive(archive, 'test', program=cmd)
        finally:
            os.chdir(basedir)
            shutil.rmtree(tmpdir)


def needs_cmd (cmd):
    """Decorator skipping test if given command is not available."""
    def check_prog (f):
        def newfunc (*args, **kwargs):
            if not find_executable(cmd):
                raise nose.SkipTest("command `%s' not available" % cmd)
            return f(*args, **kwargs)
        newfunc.func_name = f.func_name
        return newfunc
    return check_prog