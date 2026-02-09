# pox-convert

[![PyPI](https://img.shields.io/pypi/v/pox-convert)](https://pypi.org/project/pox-convert/)
[![Python](https://img.shields.io/pypi/pyversions/pox-convert)](https://pypi.org/project/pox-convert/)
[![License](https://img.shields.io/pypi/l/pox-convert)](https://github.com/bartTC/pox/blob/main/LICENSE)

Convert `.po` (gettext) files to Excel spreadsheets and back. Supports fuzzy entries and multiple plural forms.

![Screenshot](https://github.com/bartTC/pox/raw/main/screenshot.png)

## Usage

### PO to Excel

```bash
uvx pox-convert export path/to/messages.po
```

Use globbing to convert multiple files at once:

```bash
uvx pox-convert export locales/**/django.po
```

Options:

```
-o, --outdir      Output directory (default: current directory)
-f, --filename    Filename template using {lang} and {date} variables
                  (default: translations_{lang}.xlsx)
-l, --language    Override the language metadata from the PO file
--fuzzy           How to handle fuzzy entries: stop, ignore, include (default: stop)
```

### Excel to PO

```bash
uvx pox-convert import path/to/translations.xlsx
```

Options:

```
-o, --outdir      Output directory (default: current directory)
-f, --filename    Filename template using {lang} variable (default: {lang}.po)
```

## Spreadsheet format

The generated Excel file has the following structure:

| id | Context   | Singular Form | Translation |
|----|-----------|---------------|-------------|
| 1  |           | Hello         | Hallo       |
| 2  | adjective | Open          | Offen       |
| 3  |           | Goodbye       |             |

- Empty translations are highlighted in yellow with a black border
- The header row is frozen for easy scrolling
- Alternating row stripes improve readability
- Plural forms get additional translation columns
- Language metadata is stored as a custom document property

## Django integration

pox-convert ships with a Django management command that wraps
`makemessages` to skip fuzzy matching:

```bash
python manage.py makemessages_nofuzzy -l de
```

Add `pox.contrib.django.pox` to your `INSTALLED_APPS` to use it.

