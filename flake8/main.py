import os
import sys
import pep8
import flakey
import select
import optparse
from flake8 import mccabe
from flake8 import __version__
from flake8.util import _initpep8, skip_file

pep8style = None


def get_parser():
    """Create a custom OptionParser"""

    def version(option, opt, value, parser):
        parser.print_usage()
        parser.print_version()
        sys.exit(0)

    # Create our own parser
    parser = optparse.OptionParser('%prog [options] [file.py|directory]',
                                   version=version)
    parser.version = '{0} (pep8: {1}, flakey: {2})'.format(
        __version__, pep8.__version__, flakey.__version__)
    parser.remove_option('--version')
    # don't overlap with pep8's verbose option
    parser.add_option('--builtins', default='', dest='builtins',
                      help="append builtin functions to flakey's "
                           "_MAGIC_BUILTINS")
    parser.add_option('--ignore', default='',
                      help='skip errors and warnings (e.g. E4,W)')
    parser.add_option('--exit-zero', action='store_true', default=False,
                      help='Exit with status 0 even if there are errors')
    parser.add_option('--max-complexity', default=-1, action='store',
                      type='int', help='McCabe complexity threshold')
    parser.add_option('-V', '--version', action='callback',
                      callback=version,
                      help='Print the version info for flake8')
    return parser


def main():
    global pep8style

    # parse out our flags so pep8 doesn't get confused
    parser = get_parser()
    opts, sys.argv = parser.parse_args()

    # make sure pep8 gets the information it expects
    sys.argv.insert(0, 'pep8')

    pep8style = pep8.StyleGuide(parse_argv=True, config_file=True)
    options = pep8style.options
    complexity = opts.max_complexity
    builtins = set(opts.builtins.split(','))
    warnings = 0
    stdin = None

    if builtins:
        orig_builtins = set(flakey.checker._MAGIC_GLOBALS)
        flakey.checker._MAGIC_GLOBALS = orig_builtins | builtins

    if pep8style.paths and options.filename is not None:
        for path in _get_python_files(pep8style.paths):
            if path == '-':
                if stdin is None:
                    stdin = read_stdin()
                warnings += check_code(stdin, opts.ignore, complexity)
            else:
                warnings += check_file(path, opts.ignore, complexity)
    else:
        stdin = read_stdin()
        warnings += check_code(stdin, opts.ignore, complexity)

    if opts.exit_zero:
        raise SystemExit(0)

    raise SystemExit(warnings)


def check_file(path, ignore=(), complexity=-1):
    if pep8style.excluded(path):
        return 0
    warning = flakey.checkPath(path)
    warnings = flakey.print_messages(warning, ignore=ignore)
    warnings += pep8style.input_file(path)
    if complexity > -1:
        warnings += mccabe.get_module_complexity(path, complexity)
    return warnings


def check_code(code, ignore=(), complexity=-1):
    warning = flakey.check(code, '<stdin>')
    warnings = flakey.print_messages(warning, ignore=ignore, code=code)
    warnings += pep8style.input_file(None, lines=code.split('\n'))
    if complexity > -1:
        warnings += mccabe.get_code_complexity(code, complexity)
    return warnings


def read_stdin():
    # wait for 1 second on the stdin fd
    reads, __, __ = select.select([sys.stdin], [], [], 1.)
    if reads == []:
        print('input not specified')
        raise SystemExit(1)

    return sys.stdin.read()


try:
    from setuptools import Command
except ImportError:
    Flake8Command = None
else:
    class Flake8Command(Command):
        description = "Run flake8 on modules registered in setuptools"
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def distribution_files(self):
            if self.distribution.packages:
                for package in self.distribution.packages:
                    yield package.replace(".", os.path.sep)

            if self.distribution.py_modules:
                for filename in self.distribution.py_modules:
                    yield "%s.py" % filename

        def run(self):
            _initpep8()

            # _get_python_files can produce the same file several
            # times, if one of its paths is a parent of another. Keep
            # a set of checked files to de-duplicate.
            checked = set()

            warnings = 0
            for path in _get_python_files(self.distribution_files()):
                if path not in checked:
                    warnings += check_file(path)
                checked.add(path)

            raise SystemExit(warnings > 0)


def _get_python_files(paths):
    for path in paths:
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                if pep8style.excluded(dirpath):
                    continue
                for filename in filenames:
                    if not filename.endswith('.py'):
                        continue
                    fullpath = os.path.join(dirpath, filename)
                    if not skip_file(fullpath) or pep8style.excluded(fullpath):
                        yield fullpath

        else:
            if not skip_file(path) or pep8style.excluded(path):
                yield path
