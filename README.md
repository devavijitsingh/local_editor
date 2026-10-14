# Vortex Media Studio

A local web app for trimming and converting audio/video, extracting audio from
video, and browsing processed files. The Flask server runs on your computer and
uses FFmpeg for media operations.

## Features

- Video trimming, with stream-copy or re-encoding options.
- Video conversion to MP4, MKV, MOV, WEBM, AVI, GIF, FLV, WMV, M4V, and TS.
- Audio extraction from video, with optional trimming.
- Audio trimming with optional fade-in and fade-out.
- Audio conversion to MP3, WAV, AAC, FLAC, OGG, M4A, OPUS, WMA, and AIFF.
- A local output library with playback, download, and delete actions.
- No account or cloud upload is needed. Uploaded media stays in the local
  `uploads/` folder; results are written to `outputs/`.

FFmpeg support for particular codecs and containers depends on the FFmpeg build
installed on your system. Re-encoding may be lossy; stream copy avoids
re-encoding where supported.

## Requirements

- Python 3.9 or newer.
- FFmpeg and FFprobe available on your `PATH`.
- Windows, macOS, or Linux.

Check that both media tools are available:

```text
ffmpeg -version
ffprobe -version
```

## Quick start

### Windows

1. Install Python and FFmpeg if they are not already installed.
2. Download or clone this repository.
3. Double-click `run.bat` to create a local `.venv`, install dependencies, and
   launch the app, or run:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```

### macOS and Linux

Install Python and FFmpeg using your operating system's package manager, then:

```sh
python3 -m venv .venv
```

Activate the environment and install dependencies:

```sh
# macOS / Linux
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1` instead.

The app opens `http://127.0.0.1:5000` in your default browser. Set
`NO_BROWSER=1` to suppress automatic browser launch. The server binds to
loopback only and is intended for personal, local use; do not expose it to an
untrusted network.

## Using the app

1. Choose Video Studio or Audio Studio.
2. Select or drag a media file into the upload area.
3. Choose an operation and its available options, then start processing.
4. Preview or download the result. Processed files remain in `outputs/` until
   you delete them.

Uploads and outputs are local working files and are excluded from Git by
default. The small `sample_audio.mp3` and `sample_video.mp4` files that may be
present in a local checkout are not required; tests create temporary media
fixtures with FFmpeg instead.

## Development and tests

Install the Python dependency:

```sh
python -m pip install -r requirements.txt
```

Run the test suite from the project root:

```sh
python -m unittest discover -v -p "test_*.py"
```

The tests require both FFmpeg and FFprobe on `PATH`. They generate short,
synthetic audio/video fixtures in a temporary directory and remove test
uploads/outputs when each test completes.

## Project layout

```text
.
├── app.py                   # Flask app and media processing API
├── run.bat                  # Windows launcher
├── requirements.txt         # Python dependencies
├── test_app.py              # unittest suite
├── templates/
│   └── index.html           # Single-page interface
├── static/
│   ├── css/style.css        # Interface styles
│   └── js/app.js            # Browser-side interactions
├── uploads/                 # Local input files (ignored by Git)
└── outputs/                 # Local processed files (ignored by Git)
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
