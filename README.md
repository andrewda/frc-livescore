# FRC Livescore

A package which can determine the score of a live FRC game from an image.

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

## Usage

*Check out the `examples` directory for full examples on the usage of
`frc-livescore`.*

A very simple example program would be to just get the score data from a single
image. To do this, we'll use OpenCV to read the image.

```python
from livescore import Livescore
import cv2

# Initialize a new Livescore instance
frc = Livescore()

# Read the image from disk
image = cv2.imread('./examples/scenes/scene1.png')

# Get score data
data = frc.read(image)

print('Red {0} : {2} : {1} Blue'.format(data.red.score,
                                        data.blue.score,
                                        data.time))
```

## API

### Methods

#### Livescore(options)

- `options` - [optional] a dict of options
    - `scoreboard` - A template image to match for the whole scoreboard
    - `scores` - A template image to match for the scores
    - `time` - A template image to match for the time remaining
    - `top` - A template image to match for the top bar

Creates and returns a new Livescore instance with specified options.

#### .read(img)

- `img` - The image to read from

Reads an image and returns an [OngoingMatchDetails](#ongoingmatchdetails) class
containing the score data. Values that could not be determined from the input
image will be `False`.

#### .getScoreboard(img)

- `img` - The image to read from

Returns the same image, cropped around the scoreboard.

#### .getTopBar(img)

- `img` - The image to read from

Returns the same image, cropped around the top bar.

#### .getTimeArea(img)

- `img` - The image to read from

Returns the same image, cropped around the time remaining area.

#### .getScoreArea(img)

- `img` - The image to read from

Returns the same image, cropped around the score area (for both red and blue).

#### .getRedScoreArea(img)

- `img` - The image to read from

Returns the same image, cropped around the red score area.

#### .getBlueScoreArea(img)

- `img` - The image to read from

Returns the same image, cropped around the blue score area.

#### .matchTemplate(img, template)

- `img` - The base image
- `template` - The template image to match against `img`

Returns two values, the top left point of the template match, and the bottom
right point. This is mostly used internally.

### Classes

#### Alliance

= `score` - The alliance's score
- `teams` - An array of team numbers (NOT YET IMPLEMENTED)

#### OngoingMatchDetails

- `match` - The match identification, such as "Qualifications 16"
- `time` - The time remaining in the match
- `red` - An [Alliance](#alliance) class for the red alliance
- `blue` - An [Alliance](#alliance) class for the blue alliance

<!--
#### CompletedMatchDetails

- `match` - The match identification, such as "Qualifications 16"
- `winner` - A string containing the match winner; either "red" or "blue"
- `red` - An [Alliance](#alliance) class for the red alliance
- `blue` - An [Alliance](#alliance) class for the blue alliance
-->
