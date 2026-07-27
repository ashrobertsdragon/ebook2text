# Ebook2Text

## Overview

This Python script provides functionality for converting various ebook file formats (EPUB, DOCX, PDF, TXT) into a standardized text format. The script processes each file, identifying chapters, and replaces chapter headers with asterisks. It also performs OCR (Optical Character Recognition) for image-based text using a vision-capable AI model and standardizes the text by converting smart punctuation.

## Features

- **File Format Support**: Handles EPUB, DOCX, PDF, and TXT formats.
- **Chapter Identification**: Detects and marks chapter breaks.
- **OCR Capability**: Converts text from images using OCR.
- **Multiple AI Providers**: OpenAI, Google Gemini, Anthropic, and OpenRouter.
- **Text Standardization**: Replaces smart punctuation with ASCII equivalents.

## Requirements

To run this script, you need Python 3.10 or above and the following packages:

- `bs4`
- `ebooklib-autoupdate`
- `pdfminer.six`
- `pillow`
- `python-docx`
- `python-dotenv`
- `openai`

The OpenAI SDK is a core dependency and also serves OpenRouter. Gemini and Anthropic need optional extras:

```bash
pip install ebook2text[gemini]     # Google Gemini
pip install ebook2text[anthropic]  # Anthropic Claude
pip install ebook2text[all]        # both
```

## AI provider configuration

OCR runs through one of four providers, selected by environment variable. See `.env.sample` for a complete template.

| Variable                                                                         | Purpose                                          | Default                      |
| -------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------- |
| `OCR_PROVIDER`                                                                   | `openai`, `gemini`, `anthropic`, or `openrouter` | `openai`                     |
| `OCR_MODEL`                                                                      | Model name for the chosen provider               | falls back to `OPENAI_MODEL` |
| `OCR_MAX_TOKENS`                                                                 | Maximum tokens in the OCR response               | `1000`                       |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` | API key for the selected provider                | —                            |

API keys and models are read the first time an image is actually processed, so importing the library and converting text-only books requires no configuration at all.

To choose a provider programmatically instead, pass one to `convert_file`:

```python
from ebook2text import convert_file, get_ocr_provider

provider = get_ocr_provider(provider="anthropic", model="claude-haiku-4-5")
text = convert_file(
    file_path, metadata, save_file=False, ocr_provider=provider
)
```

Any object with a `perform_ocr(base64_images: list[str]) -> str` method satisfies the `OCRProvider` protocol, so you can supply your own implementation.

## Usage

1. Ensure all dependencies are installed.
1. Set your environment variables for the AI provider (see above).
1. Run `convert_file` from the `convert_file` module with the path to the ebook file and a metadata dictionary with keys of 'title' and 'author' as arguments.

- set `save_file` to False, if you want a string returned.
- set `save_file` to True or leave blank, and provide a Path object to `save_path` to use a custom output filename.
- set `save_file` to True or leave blank, and leave `save_path` blank for the output text file to be saved with the same base name as the input file name, in the same directory.

### Example

```python
from pathlib import Path
from ebook2text.convert_file import convert_file

metadata = {"title": "My Ebook", "author": "John Doe"}
file_path = Path("my_ebook.epub")

# Convert and save to a file
convert_file(file_path, metadata, save_file=True, save_path=Path("output.txt"))

# Convert and return as a string
text = convert_file(file_path, metadata, save_file=False)
print(text)
```

## Functions

### `convert_file`

Converts an ebook file to a standardized text format.

**Location**
`ebook2text.convert_file.py`

**Signature**:
`convert_file(file_path: Path, metadata: dict, *, save_file: bool = True, save_path: Path | None = None, ocr_provider: OCRProvider | None = None) -> str | None`

**Arguments**:

- `file_path`: Path to the input file. Must include the file extension.
- `metadata`: Dictionary containing the book's `title` and `author`.
- `save_file`: Boolean flag. If `True`, saves the converted text to a file; otherwise, returns it as a string. Defaults to `True`.
- `save_path`: Optional path to save the output file. Defaults to a generated name in the input file's directory.
- `ocr_provider`: Optional OCR provider for image text extraction. Defaults to the provider configured by environment variables.

**Returns**:

- If `save_file` is `True`: Returns `None`.
- If `save_file` is `False`: Returns the converted text as a string.

**Raises**:

- `ValueError`: If the file type is unsupported.

### `initialize_pdf_converter`

Initializes a PDFConverter instance for handling PDF files.

**Location**:
`ebook2_text.pdf_converter`

**Signature**:
`initialize_pdf_converter(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> PDFConverter`

**Arguments**:

- `file_path`: Path to the PDF file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Returns**:

- A PDFConverter instance configured for the provided PDF file and metadata.

### `convert_pdf`

Convenience function for reading and processing a PDF file, splitting its content into chapters.

**Location**:
`ebook2_text.pdf_converter`

**Signature**:

convert_pdf(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> Generator[str, None, None]

**Arguments**:

- `file_path`: Path to the PDF file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Yields**:

- Strings representing parsed text from each page of the PDF.

**Raises**:

- `PDFConversionError`: Any errors related to bad PDF's or IO errors. Subtype of `EbookConversionError`

#### convert_pdf Example

```python
from pathlib import Path
from ebook2text.pdf_converter import convert_pdf

metadata = {"title": "Sample PDF", "author": "Jane Doe"}
file_path = Path("sample.pdf")

# Iterate through parsed content
for page_content in convert_pdf(file_path, metadata):
    print(page_content)
```

### `initialize_epub_converter`

Initializes a EpubConverter instance for handling Epub files.

**Location**:
`ebook2_text.epub_converter`

**Signature**:
`initialize_epub_converter(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> EpubConverter`

**Arguments**:

- `file_path`: Path to the Epub file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Returns**:

- A EpubConverter instance configured for the provided Epub file and metadata.

### `convert_epub`

Convenience function for reading and processing a Epub file, splitting its content into chapters.

**Location**:
`ebook2_text.epub_converter`

**Signature**:

convert_epub(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> Generator[str, None, None]

**Arguments**:

- `file_path`: Path to the Epub file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Yields**:

- Strings representing parsed text from each page of the Epub.

**Raises**:

- `EpubConversionError`: Any errors related to bad Epub's or IO errors. Subtype of `EbookConversionError`

#### convert_epub Example

```python
from pathlib import Path
from ebook2text.epub_converter import convert_epub

metadata = {"title": "Sample Epub", "author": "Jane Doe"}
file_path = Path("sample.epub")

# Iterate through parsed content
for page_content in convert_epub(file_path, metadata):
    print(page_content)
```

### `initialize_docx_converter`

Initializes a DocxConverter instance for handling Docx files.

**Location**:
`ebook2_text.docx_converter`

**Signature**:
`initialize_docx_converter(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> DocxConverter`

**Arguments**:

- `file_path`: Path to the Docx file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Returns**:

- A DocxConverter instance configured for the provided Docx file and metadata.

### `convert_docx`

Convenience function for reading and processing a Docx file, splitting its content into chapters.

**Location**:
`ebook2_text.docx_converter`

**Signature**:

convert_docx(file_path: Path, metadata: dict, ocr_provider: OCRProvider | None = None) -> Generator[str, None, None]

**Arguments**:

- `file_path`: Path to the Docx file to be processed.
- `metadata`: Dictionary containing `title` and `author`.
- `ocr_provider`: Optional OCR provider. Defaults to the environment-configured provider.

**Yields**:

- Strings representing parsed text from each page of the Docx.

**Raises**:

- `DocxConversionError`: Any errors related to bad Docx's or IO errors. Subtype of `EbookConversionError`

#### convert_docx Example

```python
from pathlib import Path
from ebook2text.docx_converter import convert_docx

metadata = {"title": "Sample Docx", "author": "Jane Doe"}
file_path = Path("sample.docx")

# Iterate through parsed content
for page_content in convert_docx(file_path, metadata):
    print(page_content)
```

## Contributing

Contributions to this project are welcome. Please use Ruff for formatting to ensure that your code follows the existing style for consistency, and follow the [ProsePal Open Source Contributor's Code of Contact](https://github.com/ashrobertsdragon/Ebook-conversion-to-Text-for-Machine-Learning/blob/main/prosepal-contributors-code-of-conduct.md).

## TODO

- Increase test coverage
  - Tests for text converter
  - More edge cases and failure states
- Better handling of ebooklib dependency
- Explore additional filetypes
- Other options for determining filetype

## License

This project is licensed by ProsePal LLC under the MIT license
