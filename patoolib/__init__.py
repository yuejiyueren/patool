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
import os
import shutil
from distutils.spawn import find_executable
from . import util

# Supported archive commands
ArchiveCommands = ('list', 'extract', 'test', 'create')

# Supported archive formats
ArchiveFormats = ('gzip', 'bzip2', 'tar', 'zip', 'compress', '7z', 'rar',
  'cab', 'arj', 'cpio', 'rpm', 'deb', 'lzop')

# Supported encodings (used with tar for example)
# Note that all encodings must also be archive formats
ArchiveEncodings = ('gzip', 'bzip2', 'compress')

# Map MIME types to archive format
ArchiveMimetypes = {
    'application/x-bzip2': 'bzip2',
    'application/x-tar': 'tar',
    'application/x-gzip': 'gzip',
    'application/zip': 'zip',
    'application/java-archive': 'zip',
    'application/x-7z-compressed': '7z',
    'application/x-compress': 'compress',
    'application/x-rar': 'rar',
    'application/rar': 'rar',
    'application/x-cab': 'cab',
    'application/vnd.ms-cab-compressed': 'cab',
    'application/x-arj': 'arj',
    'application/x-cpio': 'cpio',
    'application/x-redhat-package-manager': 'rpm',
    'application/x-rpm': 'rpm',
    'application/x-debian-package': 'deb',
    'application/x-lzop': 'lzop',
}

# List of programs supporting the given archive format and command.
# If command is None, the program supports all commands (list, extract, ...)
ArchivePrograms = {
    'bzip2': {
        'extract': ('pbzip2', 'bzip2', '7z'),
        'test': ('pbzip2', 'bzip2', '7z'),
        'create': ('pbzip2', 'bzip2', '7z'),
        'list': ('7z', 'echo',),
    },
    'tar': {
        None: ('tar', 'star',),
    },
    'zip': {
        'extract': ('unzip', '7z'),
        'list': ('unzip', '7z'),
        'test': ('unzip', '7z'),
    },
    'gzip': {
        None: ('gzip', '7z'),
    },
    'compress': {
        'extract': ('gzip', '7z', 'uncompress.real'),
        'list': ('7z', 'echo',),
        'test': ('gzip', '7z'),
        'create': ('compress',),
    },
    '7z': {
        None: ('7z',),
    },
    'rar': {
        None: ('rar',),
        'extract': ('unrar', '7z'),
        'list': ('unrar', '7z'),
        'test': ('unrar', '7z'),
    },
    'cab': {
        'extract': ('cabextract', '7z'),
        'list': ('cabextract', '7z'),
        'test': ('cabextract', '7z'),
    },
    'arj': {
        None: ('arj',),
        'extract': ('7z',),
        'list': ('7z',),
        'test': ('7z',),
    },
    'cpio': {
        'extract': ('cpio', '7z'),
        'list': ('cpio', '7z'),
        'test': ('7z',),
        'create': ('cpio',),
    },
    'rpm': {
        # XXX rpm2cpio depends on cpio which is not checked
        'extract': ('rpm2cpio', '7z'),
        'list': ('rpm', '7z'),
        'test': ('rpm', '7z'),
    },
    'deb': {
        'extract': ('dpkg-deb', '7z'),
        'list': ('dpkg-deb', '7z'),
        'test': ('dpkg-deb', '7z'),
    },
    'lzop': {
        None: ('lzop',),
    },
}

# only list those programs that have different python module names
ProgramModules = {
    '7z': 'p7zip',
    'uncompress.real': 'uncompress',
    'dpkg-deb': 'dpkg',
}


def get_archive_format (filename):
    """Detect filename archive format."""
    mime, encoding = util.guess_mime(filename)
    if not (mime or encoding):
        raise util.PatoolError("unknown archive format for file `%s'" % filename)
    if mime in ArchiveMimetypes:
        format = ArchiveMimetypes[mime]
    elif encoding in ArchiveEncodings:
        # Files like 't.txt.gz' are recognized with encoding as format, and
        # an unsupported mime-type like 'text/plain'. Fix this.
        format, encoding = encoding, None
    else:
        raise util.PatoolError("unknown archive format for file `%s' (mime-type is `%s')" % (filename, mime))
    return format, encoding


def check_archive_format (format, encoding):
    if format not in ArchiveFormats:
        raise util.PatoolError("unknown archive format `%s'" % format)
    if encoding is not None and encoding not in ArchiveEncodings:
        raise util.PatoolError("unkonwn archive encoding `%s'" % encoding)


def check_archive_command (command):
    if command not in ArchiveCommands:
        raise util.PatoolError("invalid archive command `%s'" % command)


def find_archive_program (format, command):
    """Find suitable archive program for given format and mode."""
    commands = ArchivePrograms[format]
    programs = []
    # first try the universal programs with key None
    for key in (None, command):
        if key in commands:
            programs.extend(commands[key])
    if not programs:
        raise util.PatoolError("%s archive format `%s' is not supported" % (command, format))
    # return the first existing program
    for program in programs:
        exe = find_executable(program)
        if exe:
            return exe
    # no programs found
    raise util.PatoolError("could not find an executable program to %s format %s; candidates are (%s)," % (command, format, ",".join(programs)))


def list_formats ():
    for format in ArchiveFormats:
        print format, "files:"
        for command in ArchiveCommands:
            program = find_archive_program(format, command)
            if program:
                print "   %8s: %s" % (command, program)
            else:
                print "   %8s: NOT SUPPORTED"
    return 0


def parse_config (format, command, **kwargs):
    """The configuration determines which program to use for which
    archive format for the given command.
    """
    config = {
        'verbose': False,
        'force': False,
    }
    configfile = parse_config_file()
    if configfile.has_option(None, "verbose"):
        config['verbose'] = configfile.getboolean(None, "verbose")
    if configfile.has_option(None, "force"):
        config['verbose'] = configfile.getboolean(None, "force")
    if configfile.has_option(format, command):
        config['program'] = configfile.get(format, command)
    else:
        config['program'] = find_archive_program(format, command)
    for key, value in kwargs.items():
        if value is not None:
            config[key] = value
    return config


def parse_config_file ():
    """Parse system-wide and then user-specific configuration."""
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    files = []
    # system wide config settings
    files.append("/etc/patool.conf")
    # per user config settings
    files.append(os.path.expanduser("~/.patool.conf"))
    # weed out invalid files
    files = [f for f in files if os.path.isfile(f) and os.path.exists(f)]
    config.read(files)
    return config


def move_outdir_orphan (outdir, force):
    """Move a single file or directory inside outdir a level up.
    Overwrite files if force evaluates True.
    Return (True, outfile) if successful, (False, reason) if not."""
    entries = os.listdir(outdir)
    reason = ""
    if len(entries) == 1:
        src = os.path.join(outdir, entries[0])
        dst = os.path.join(os.path.dirname(outdir), entries[0])
        if os.path.exists(dst):
            if not force:
                return (False, "local file exists")
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.unlink(dst)
        shutil.move(src, dst)
        os.rmdir(outdir)
        return (True, entries[0])
    return (False, "multiple files in root")


def run_archive_cmdlist (archive_cmdlist):
    """Handle result of archive command function."""
    # archive_cmdlist is a command list with optional keyword arguments
    if isinstance(archive_cmdlist, tuple):
        cmdlist, runkwargs = archive_cmdlist
    else:
        cmdlist, runkwargs = archive_cmdlist, {}
    util.run(cmdlist, **runkwargs)


def cleanup_outdir (archive, outdir, force):
    """Cleanup outdir after extraction and return target file name."""
    if outdir:
        # move single directory or file in outdir
        (res, msg) = move_outdir_orphan(outdir, force)
        if res:
            target = "`%s'" % msg
        else:
            target = "`%s' (%s)" % (outdir, msg)
    else:
        target = "`%s'" % util.stripext(archive)
    return target


def _handle_archive (archive, command, *args, **kwargs):
    if command != 'create':
        # check that archive is a regular file
        util.check_filename(archive)
    encoding = None
    format, encoding = get_archive_format(archive)
    check_archive_format(format, encoding)
    check_archive_command(command)
    config = parse_config(format, command, **kwargs)
    if command == 'create':
        # check if archive already exists
        if os.path.exists(archive) and not config['force']:
            raise util.PatoolError("archive `%s' already exists, and --force option was not given" % archive)
    program = config['program']
    # get python module for given archive program
    key = os.path.basename(program).lower()
    module = ProgramModules.get(key, key)
    # import archive handler (eg. patoolib.programs.star.extract_tar())
    exec "from patoolib.programs.%s import %s_%s as func" % (module, command, format)
    get_archive_cmdlist = locals()['func']
    # prepare func() call arguments
    kwargs = dict(verbose=config['verbose'])
    outdir = None
    if command == 'extract':
        outdir = util.tmpdir(dir=os.getcwd())
        kwargs['outdir'] = outdir
    try:
        cmdlist = get_archive_cmdlist(archive, encoding, program, *args, **kwargs)
        run_archive_cmdlist(cmdlist)
        if command == 'extract':
            target = cleanup_outdir(archive, outdir, config['force'])
            print "%s: extracted to %s" % (archive, target)
    finally:
        if outdir:
            try:
                os.rmdir(outdir)
            except OSError:
                pass


def handle_archive (archive, command, *args, **kwargs):
    """Handle archive file command."""
    try:
        _handle_archive(archive, command, *args, **kwargs)
        res = 0
    except util.PatoolError, msg:
        util.log_error(msg)
        res = 1
    except StandardError, msg:
        util.log_internal_error()
        res = 1
    return res