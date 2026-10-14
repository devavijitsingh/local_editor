# Contributing

Thanks for considering a contribution to Vortex Media Studio.

## Before opening an issue

- Search existing issues for the same bug or idea.
- Include your operating system, Python version, and `ffmpeg -version` output
  when reporting a media-processing issue.
- Do not attach private media or include sensitive file paths in public reports.

## Development setup

1. Install Python 3.9+ and FFmpeg/FFprobe.
2. Create and activate a virtual environment.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Run checks with `python -m unittest discover -v -p "test_*.py"`.

## Pull requests

- Keep changes focused and explain user-visible behavior changes.
- Add or update tests for bug fixes and new behavior.
- Run the test suite before submitting.
- Do not commit uploaded media, generated output, credentials, or local
  environment files.
