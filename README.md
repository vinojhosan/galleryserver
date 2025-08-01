# GalleryServe

GalleryServe is a Python-based tool for serving and managing image galleries. It provides a command-line interface and server functionality for easy gallery hosting and management.

## Features
- Command-line interface for gallery operations
- License management
- Utility functions for gallery handling
- Server to host and serve image galleries

## Installation

You can install GalleryServe using pip:

```bash
pip install .
```

Or, for development:

```bash
pip install -e .
```

## Usage

### Command Line Interface

Run the CLI to interact with GalleryServe:

```bash
python -m galleryserve.cli [options]
```

#### CLI Options

The following options are available for the GalleryServe CLI:

- `--help`, `-h`: Show help message and exit.
- `--activate-license <LICENSE_KEY>`: Activate your GalleryServe license.
- `--serve`: Start the gallery server.
- `--port <PORT>`: Specify the port for the server (default: 8000).
- `--gallery-path <PATH>`: Path to the image gallery directory.
- `--list-galleries`: List all available galleries.
- `--add-gallery <PATH>`: Add a new gallery from the specified path.
- `--remove-gallery <NAME>`: Remove a gallery by name.
- `--version`: Show the version of GalleryServe.

Refer to the CLI help (`--help`) for the most up-to-date list of options.



## Activating Your License

To activate your GalleryServe license, use the CLI with the `--activate-license` option:

```bash
python -m galleryserve.cli --activate-license <LICENSE_KEY>
```

Replace `<LICENSE_KEY>` with your provided license key. Successful activation will enable all features of GalleryServe.