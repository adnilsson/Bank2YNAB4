## Fixing Revolut v1

An earlier version of Revolut's exported statements were not well-formatted CSV.
A major problem is that they used comma both as thousands separator and as the value delimiter.
The way you would solve this is to simply surround numbers in quotation marks, change the delimiter, or change the thousands separator.
Alas, they did not do this, and it has been a known issue since at least [2017](https://community.revolut.com/t/statements-in-excel-csv-format-errors/8655).
You can see an example of how an exported file might look like in `revolut_v1_example.csv`.
Fortunately, the format was updated in in Q4 of 2021.

This repository provides a script that fixes the ill-formed CSV-files of the v1 Revolut config.
The approach is to surround any large number (i.e., greater than 999.99) in the file with quotation marks.
The script is tested and documented, and you should be able to figure out how to use it from the help output:

```bash
python fix_revolut.py --help
```

You can also try it on the examlpe file:
```bash
python fix_revolut.py revolut_v1_example.csv --out ./
cat revolut_v1_example_OUT.csv
```