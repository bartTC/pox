# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Python 3.15 is supported and tested.

## [1.2.0] - 2026-11-16

### Added

- The import restores every PO header field, such as `Project-Id-Version`,
  `Last-Translator` and `Plural-Forms`, stored in a hidden "PO Header" sheet.
- The import keeps translator comments, developer comments, `#:` references
  and `#,` flags, stored in hidden columns. The `fuzzy` flag is dropped, since
  the imported translation counts as reviewed.
- `export` warns about each path or pattern that matches no files.

### Changed

- Plural entries show both source forms, singular and plural, on two lines.
- Plural columns that don't apply to a singular message are hatched gray, so
  they no longer look like missing translations.
- Translation cells are formatted as Text, so Excel keeps what translators
  type as typed instead of turning `1/2` into a date, `42` into a number, or
  `=...` into a formula.
- `export` exits with status 1 if no `.po` files are found at all. Previously
  it silently did nothing.
- If several `.po` files would write the same spreadsheet, because they have
  the same language or the filename has no `{lang}`, the first one is kept and
  the others are skipped with a warning. Previously the last one silently
  overwrote the others.

### Fixed

- Import turned singular messages into plural entries when the spreadsheet
  had plural columns. Spreadsheets from older versions are detected and
  imported correctly too.
- Import lost the singular `msgid` of plural entries. Spreadsheets from older
  versions only contain the plural form, which is still used for both.
- Import dropped the PO header, including `Plural-Forms`, which made
  `msgfmt --check` fail and gettext fall back to its two-form rule.
  Spreadsheets from older versions don't store the header, so only
  `Content-Type` and `Language` are written for them.
- Obsolete entries lost their context, and entries with the context
  `obsolete` were imported as obsolete. The real context and obsolete status
  are now stored in hidden columns; the visible Context column is unchanged.
- Import crashed when a translation cell held a number, such as a `42` that
  Excel converted on entry.
- Text starting with `=` was exported as an Excel formula. It was lost on
  import, and a source string like `=HYPERLINK(...)` would run as a formula
  when the spreadsheet was opened.
- `export` failed with `NotImplementedError` for absolute paths and patterns.
- The help for a PO file without a `Language` header suggested a `--locale`
  option that doesn't exist. It now names `--language`.

## [1.1.0] - 2026-02-11

### Added

- Programmatic plural hint generation using a safe formula parser.

### Changed

- Improved CI coverage reporting.
- 100% test coverage.

## [1.0.1] - 2026-02-09

### Added

- Unified CLI with `pox-convert` entry point.
- Excel-to-PO reverse conversion (`xop`).
- MIT license, README, and GitHub Actions CI workflow.

### Changed

- Redesigned spreadsheet styles and column headers.
- Full type annotations and stricter linting.

## [1.0.0] - 2026-02-09

### Added

- Initial release with PO-to-Excel conversion.

[Unreleased]: https://github.com/bartTC/pox/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/bartTC/pox/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/bartTC/pox/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/bartTC/pox/releases/tag/v1.0.1
[1.0.0]: https://github.com/bartTC/pox/commit/57925a7
