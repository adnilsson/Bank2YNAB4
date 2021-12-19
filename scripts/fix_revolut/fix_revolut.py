import argparse
import re
from pathlib import Path
from typing import Optional

class NumberQuoter():
    def __init__(self, *, thousands_sep: str=',', decimal_sep: str='.', n_decimals: int=2) -> None:
        self._group_tag = 'largeamount'

        match_number_with_thousands_sep = r'([0-9]{{1,3}}{})+[0-9]{{3}}{}[0-9]{{{}}}(?![0-9])'.format(
            re.escape(thousands_sep), re.escape(decimal_sep), n_decimals)
        self._pattern =  re.compile(r'(?!")(?=[0-9])(?P<{}>{})(?!")'.format(
            self._group_tag, match_number_with_thousands_sep)
        )

    def quote_str_number(self, string: str) -> str:
        """ Surround numbers with thousands seperators in quotes.
        Only numbers that aren't already in quotation marks will be replaced.
        """
        return self._pattern.sub(fr'"\g<{self._group_tag}>"', string)


def quote_numbers(file: Path, *,
    replace: bool=False,
    out_dir: Optional[Path]=None,
    **numberquoter_kwargs,
) -> Path:
    """
    Fix unquoted large numbers in a Revoult CSV-statement file.

    Revolut uses a comma for thousands separator as well as the CSV value separator.
    This is bad because a row that has an amount greater than 999.99 cannot be parsed
    in a good way. A common way to solve the problem of having "commas in values" is
    to surround the value in question with quotation marks. This function does just
    that to any number greater than 999.99 that isn't already in quotes.

    Only one of ``replace`` and ``out_dir`` parameters should be specified.
    Specifying both is an error.
    Unless ``replace`` is ``True``, the output file name will be the same
    as the original except that '_OUT' is appended before the suffix.

    :param file: Path to the file to be fixed.
    :param replace:
        The original file will be overwritten if this parameter is True.
        Mutually exclusive with ``out_dir``.
    :param out_dir:
        If set, the updated file will be written to this directory.
        Mutually exclusive with ``replace``.
    :keyword thousands_sep:
        The thousands separator. Must be escaped to fit
        in a regular expression. Defaults to a comma (``','``).
    :keyword decimal_sep:
        The decimal separator. Must be escaped to fit
        in a regular expression). Defaults to a period (``'.'``).
    :keyword n_decimals:
        The number of decimal digits in numbers present in ``file``.
        Defaults to ``2``.
    :returns: Path to the fixed file.
    :raises ValueError: if the arguments are invalid
    """
    if replace and out_dir is not None:
        raise ValueError(f"arguments {replace=} and {out_dir=} are mutually exclusive")
    elif not file.is_file():
        raise ValueError(f"{file} is not a file")
    elif out_dir is not None and (not out_dir.is_dir()):
        raise ValueError(f"{out_dir=} is not a directory")

    nq =  NumberQuoter(**numberquoter_kwargs)
    new_file_contents = nq.quote_str_number(file.read_text())

    new_name = file.stem + '_OUT' + file.suffix
    if not replace:
        file = file.with_name(new_name)

    if out_dir is not None: # guaranteed to be a directory
        file = out_dir / new_name

    file.write_text(new_file_contents)

    return file


def main():
    parser = argparse.ArgumentParser(description="Makes sure all values with thousands separators are in quotes in an exported CSV file from Revolut.")
    parser.add_argument('file', type=Path,
        help="path to the CSV statement file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--replace', action="store_true",
        help="replace the original statement file")
    group.add_argument('--out', type=Path,
        help="write the updated file to this directory")
    parser.add_argument("-ts", "--thousands-sep", type=str, default=',',
        help="the thousands separator")
    parser.add_argument("-ds", "--decimal_sep", type=str, default='.',
        help="the decimal separator")
    parser.add_argument("-p", "--percision", type=int, default=2,
        help="number of decimal digits used in the input file")

    args = parser.parse_args()
    quote_numbers(args.file,
        replace=args.replace,
        out_dir=args.out,
        thousands_sep=args.thousands_sep,
        decimal_sep=args.decimal_sep,
        n_decimals=args.percision,
    )

if __name__ == '__main__':
    main()