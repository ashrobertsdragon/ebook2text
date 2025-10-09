# Version History

- **v0.1.0** (Release date: November 30, 2023)
  - Initial release

- **v0.1.1** (Release date: December 2, 2023)
  - fixed false positives for is_number

- **v0.2.0** (Release date: December 3, 2023)
  - Conversion of docx files

- **v0.3.0** (Release date: December 8, 2023)
  - Conversion of PDF files

- **v0.3.1** (Release date: January 23, 2024)
  - fixed concatenation of text in pdf conversion
  - updated pillow version to secure version

- **v1.0.0** (Release date: January 23, 2024)
  - created library instead of single module

- **v1.0.1** (Release date: March 13, 2024)
  - setup.py and requirements.txt typo fixed

- **v1.0.2** (Release date: May 17, 2024)
  - added tests, fixed minor typos

- **v1.1.0** (Release date: May 30, 2024)
  - Change to abstract factory pattern

- **v1.1.1** (Release date: May 31, 2024)
  - Pull current version of ebooklib from Github and folded it into library since package repo out of date

- **v1.1.2** (Release date: May 31, 2024)
  - FIX: Put ebooklib in correct directory.

- **v1.1.3** (Release date: October 27, 2024)
  - FIX: Initialize logging

- **v1.1.4** (Release date: November 7, 2024)
  - YANKED

- **v1.1.5** (Release date: November 7, 2024)
  - FIX: Move logging to own module

- **v1.1.6** (Release date: November 9, 2024)
  - FIX: Catch PDFSyntaxError and empty image lists, small performance improvement to run_ocr

- **v1.1.7** (Release date November 10, 2024)
  - FIX: Line concatenation issue in PDFs

- **v2.0.0** (Release date December 4, 2024)
  - REFACTOR: Converters are now packages with more streamlined constructors.
  - BREAKING FEATURE: ebook2text now takes Path objects instead of string filenames.
  - BREAKING FEATURE: Converters no longer have a ChapterSplit class. This is handled by the BookConversion class, with no more circular imports.
  - NEW FEATURE: `convert_file` now has optional `save_file` and `save_path` arguments to allow for custom output filenames or for a string to be returned instead.

- **v2.0.1** (Release date December 16, 2024)
  - FIX: Re-raise errors raised by PDFConverter._readfile(filename)

- **v2.0.2** (Release date December 17, 2024)
  - FIX: Add missing . to extension name for text files in converter initializer

- **v2.1.0** (Release date January 7, 2025)
  - Create library-wide exceptions & improve documentation

- **v2.1.1** (Release date January 7, 2025)
  - Add missing dependency in readme

- **v2.1.2** (Release date January 8, 2025)
  - uv adds custom sources to uv-specific section by default where it is not seen by build systems. Ebooklib custom source now directly in dependencies section.

- **v2.2.0** (Release date October 9, 2025)
  - Move LLM model name into environment configuration to allow updating or user configuration.
  - Upgrade tools and run updated configurations on file.
  - Fix typo in changelog filename.
