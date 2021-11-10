# FRC Livescore

A package which can determine the score of a live FRC game from an image.

![Travis](https://img.shields.io/travis/andrewda/frc-livescore.svg?style=flat-square)
[![License](https://img.shields.io/github/license/andrewda/frc-livescore.svg?style=flat-square)](https://github.com/andrewda/frc-livescore/blob/master/LICENSE)
![Version](https://img.shields.io/pypi/v/livescore.svg?style=flat-square)
![Downloads](https://img.shields.io/pypi/dm/livescore.svg?style=flat-square)

## Features

- Access to many parts of the scoreboard (and more coming soon)
- Easy to use
- Super fast
- Template matching (it doesn't matter where the scoreboard is on the screen)

## Installation

```bash
$ pip install livescore
```

You will also need to have [Tesseract](https://github.com/tesseract-ocr/tesseract/wiki#installation)
and OpenCV 3 (instructions for
[macOS](http://www.pyimagesearch.com/2016/12/19/install-opencv-3-on-macos-with-homebrew-the-easy-way/),
[Windows](http://docs.opencv.org/3.2.0/d5/de5/tutorial_py_setup_in_windows.html) and
[Linux](http://docs.opencv.org/3.2.0/d7/d9f/tutorial_linux_install.html))
installed in order for `frc-livescore` to work.

Depends on python 3.6 as this project uses SURF algorithm which is not included in newer versions of opencv.

## Usage

*Check out the `examples` directory for full examples on the usage of
`frc-livescore`.*

A very simple example program would be to just get the score data from a single
image. To do this, we'll use OpenCV to read the image.

```python
from livescore import Livescore2018
import cv2

# Initialize a new Livescore instance
frc = Livescore2018()

# Read the image from disk
image = cv2.imread('./examples/scenes/scene1.png')

# Get score data
data = frc.read(image)

print(data)
```

## API

### Constructor

#### LivescoreYEAR(debug=False, save_training_data=False, training_data=None)

> Currently supported years: 2017, 2018, 2019
>
> e.g. Livescore2017(), Livescore2018() or Livescore2019()

- `debug` - Debug mode, where outputs are displayed.
- `save_training_data` - Whether the training should be saved to disk.
- `append_training_data` - Whether to start training from scratch

Creates and returns a new Livescore instance with specified options.

### Methods

#### .read(img, force_find_overlay=False)

- `img` - The image to read from.
- `force_find_overlay` - Whether we should forcefully find the overlay or only do
   so if the overlay cannot be found.

Reads an image and returns an [OngoingMatchDetails](#ongoingmatchdetails) class
containing the score data. Values that could not be determined from the input
image will be `False`.

### Classes

#### AllianceYEAR

> Currently supported years: 2017, 2018, 2019
>
> e.g. Alliance2017, Alliance2018 or Alliance2019

- `score` - The alliance's score.
- ... many more year-specific properties.

Stores year-specific properties for an alliance, such as whether the switch or
scale is owned for the 2018 game.

#### OngoingMatchDetails

- `match_key` - The match key, such as "qf1m2".
- `match_name` - The match name, such as "Qualifications 16 of 128".
- `mode` - The current game mode, one of `pre_match`, `auto`, `teleop`, or
  `post_match`.
- `time` - The time remaining in the match.
- `red` - An [Alliance](#alliance) class for the red alliance.
- `blue` - An [Alliance](#alliance) class for the blue alliance.

<!--
#### CompletedMatchDetails

- `match` - The match identification, such as "Qualifications 16"
- `winner` - A string containing the match winner; either "red" or "blue"
- `red` - An [Alliance](#alliance) class for the red alliance
- `blue` - An [Alliance](#alliance) class for the blue alliance
-->
