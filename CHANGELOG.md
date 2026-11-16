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
- `export` now accepts absolute paths and glob patterns. Previously they
  failed with `NotImplementedError: Non-relative patterns are unsupported`.
- `export` warns about each path or pattern that matches no files, and exits
  with status 1 if no `.po` files are found at all. Previously it silently did
  nothing.
- Fixed import crashing when a translation cell holds a number, such as a
  "42" that Excel converted on entry.
- Fixed text starting with `=` being exported as an Excel formula. It was lost
  on import, and a source string like `=HYPERLINK(...)` would run as a formula
  when the spreadsheet was opened.
- Fixed obsolete entries losing their context, and entries with the context
  `obsolete` being imported as obsolete. The real context and obsolete flag
  are now stored in hidden columns; the visible Context column is unchanged.
- Fixed import dropping the `Plural-Forms` header, which made `msgfmt --check`
  fail and gettext fall back to its two-form rule. Spreadsheets from older
  versions don't contain it, so files imported from them still lack it.
- Fixed `export` silently overwriting a spreadsheet when several `.po` files
  have the same language, or the filename has no `{lang}`. The first file is
  kept and the others are skipped with a warning.

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
