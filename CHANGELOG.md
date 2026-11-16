# Changelog

## Unreleased

- Plural columns that don't apply to a singular message are now hatched gray,
  so they no longer look like missing translations.
- Fixed import turning singular messages into plural entries when the
  spreadsheet has plural columns. Spreadsheets exported with older versions
  are detected and imported correctly too.
- Plural entries now show both source forms (singular and plural), and the
  import restores both. Previously the singular `msgid` was lost on import.
  Spreadsheets from older versions only contain the plural form, which is
  still used for both.

## 1.1.0

- Programmatic plural hint generation using a safe formula parser.
- Improved CI coverage reporting.
- 100% test coverage.

## 1.0.1

- Unified CLI with `pox-convert` entry point.
- Added Excel-to-PO reverse conversion (`xop`).
- Redesigned spreadsheet styles and column headers.
- Added MIT license, README, and GitHub Actions CI workflow.
- Full type annotations and stricter linting.

## 1.0.0

- Initial release with PO-to-Excel conversion.
