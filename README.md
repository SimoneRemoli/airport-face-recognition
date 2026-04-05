# Airport Face Recognition

This project is a local face recognition prototype based on webcam input.

The application allows you to:

- register a person from the webcam
- save the registered face locally
- start live face recognition
- compare the detected face with the registered ones

## Requirements

To run the project you need:

- Python 3
- `pip`
- a working webcam
- webcam permissions enabled for the terminal or editor you are using

Before running `./setup.sh`, make sure that Python 3 is already installed on your system and that `pip` is available through `python3`.

You can verify this with:

```bash
python3 --version
python3 -m pip --version
```

If both commands return a valid version, you can continue with the setup script.

## Python Libraries Required

Before running the project, these Python libraries must be installed:

- `opencv-python==4.10.0.84`
  Used for webcam access, live video windows, face detection, keyboard handling inside the OpenCV window, and image saving.
- `numpy==1.24.4`
  Used for numerical operations and for computing and comparing face descriptors.
- `matplotlib==3.7.5`
  Present in the project requirements because it was used by the original simulation part of the repository.
- `scipy==1.10.1`
  Present in the project requirements because it was used by the original simulation/statistical part of the repository.

When installing these packages, `pip` may also install additional dependencies required by them.

## Installation Commands

If you want to install everything manually, use:

```bash
python3 -m pip install -r requirements.txt
```

The `requirements.txt` file currently contains:

```text
matplotlib==3.7.5
numpy==1.24.4
opencv-python==4.10.0.84
scipy==1.10.1
```

If you want to install the libraries one by one, the commands are:

```bash
python3 -m pip install matplotlib
python3 -m pip install scipy
python3 -m pip install opencv-python==4.10.0.84
```

`numpy` is also installed because it is required by these libraries and by the project itself.

## Setup Script

To simplify setup, the repository includes a script:

```bash
./setup.sh
```

This script:

- moves into the project folder
- creates the folders needed by the project
- installs all Python dependencies from `requirements.txt`

The expected execution flow is:

```bash
python3 --version
python3 -m pip --version
./setup.sh
```

The folders created are:

- `.mplconfig`
- `.cache`
- `plots`
- `data/faces`
- `OUTPUT`

## Run Script

To start the application quickly, use:

```bash
./run.sh
```

This script:

- moves into the project folder
- creates the required local folders if they are missing
- starts the application with:

```bash
python3 main.py
```

If you do not want to use the script, you can also run the program manually:

```bash
python3 main.py
```

## How To Use The Program

After starting the application, the main menu shows:

- `1. Start real face recognition`
- `0. Exit`

### Register a Face

1. Run the program
2. Enter `1`
3. In the next menu choose `1` to register a new face
4. Type the person's name in the terminal
5. The webcam window opens
6. Click on the webcam window to make sure it has focus
7. When the face is correctly framed, press `SPACE` or `ENTER`
8. The face sample is saved locally

### Start Live Recognition

1. Run the program
2. Enter `1`
3. In the next menu choose `2`
4. The webcam opens and the program tries to recognize registered faces live

### List Registered Faces

1. Run the program
2. Enter `1`
3. In the next menu choose `3`
4. The program prints the list of people already registered

## Controls Inside The Webcam Window

The keyboard controls must be used directly inside the webcam window, not in the terminal.

### During Face Registration

- `SPACE` captures the current face
- `ENTER` captures the current face
- `q` exits
- `Q` exits
- `ESC` exits

### During Live Recognition

- `q` exits
- `Q` exits
- `ESC` exits

If the window does not respond to the keyboard:

1. click on the webcam window
2. try again
3. if needed, stop the program from the terminal with `Ctrl+C`

## Saved Data

Registered faces are stored locally in:

- `data/face_db.json`
- `data/faces/`

## Useful Verification Commands

To check which Python libraries are installed:

```bash
python3 -m pip list
```

To show only the main libraries used for this project:

```bash
python3 -m pip list | grep -E 'matplotlib|scipy|opencv-python|numpy'
```

To inspect package details and installation path:

```bash
python3 -m pip show matplotlib scipy opencv-python numpy
```

## Notes

- This is a local prototype, not a production-grade biometric security system.
- The recognition pipeline currently uses OpenCV face detection plus handcrafted face descriptors.
- Good lighting and a stable frontal face position improve recognition quality.
