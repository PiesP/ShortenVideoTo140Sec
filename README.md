# ShortenVideoTo140Sec

This application is designed to process video files by potentially inserting an image at the beginning and adjusting the video speed to ensure the final video duration does not exceed 140 seconds. It's particularly useful for platforms with strict video length limitations.

## Features

- Select a video file to process.
- Optionally insert an image at the beginning of the video.
- Adjust the video speed to shorten the duration to 140 seconds if necessary.
- Display processing progress and allow cancellation at any time.
- Generate an executable for easy distribution and use on Windows systems.

## Installation

To run the Video Processing App, you need to have Python and ffmpeg installed on your system. Follow these steps to install the application and its dependencies:

### Python Installation

1. Clone the repository or download the source code.
2. Navigate to the project directory.

### ffmpeg Installation

This application requires ffmpeg for video processing. Follow these steps to install ffmpeg:

- **Windows**: Download the ffmpeg build from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system path.
- **Linux**: Install ffmpeg using your distribution's package manager (e.g., `sudo apt-get install ffmpeg` for Ubuntu).
- **macOS**: Install ffmpeg using Homebrew with the command `brew install ffmpeg`.

## Usage

To use the Video Processing App, follow these steps:

1. Run the main script using Python with the command `python main.py`.
2. Follow the GUI prompts to select a video file and optionally an image file.
3. The application will process the video and provide a progress update.
4. Once processing is complete, the adjusted video will be saved in the same directory.

## Building the Executable

The GitHub Actions workflow provided automates the process of building a Windows executable from the Python script. Here's how it works:

1. The workflow is triggered manually via GitHub Actions.
2. It sets up a Python environment and installs PyInstaller.
3. It installs UPX to compress the executable.
4. It installs all project dependencies.
5. It uses PyInstaller to build a one-file bundled executable.
6. It renames the executable for release.
7. It creates a new release on GitHub and tags it with the current date and time.
8. It uploads the executable to the GitHub release.

## Contributing

Contributions to the Video Processing App are welcome. If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

## Acknowledgments

- Thanks to all the contributors who spend time to help make this project better.
- Special thanks to the open-source community for providing the tools and libraries used in this project.
