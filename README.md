# Airport Face Recognition

This repository now contains two separate modes:

- `Real face recognition`: a local webcam-based MVP for registering faces and matching them live.
- `Legacy simulation`: the original queueing/simulation project.

## Run

```bash
python3 main.py
```

Then choose:

- `1` for the real face recognition app
- `2` for the legacy simulation

## Real Face Recognition Workflow

1. Start `python3 main.py`
2. Choose `1` for `Real face recognition`
3. Choose `1` again to register a person from the webcam
4. Press `SPACE` when a face is framed correctly
5. Choose `2` to start live recognition
6. Press `q` to close the live window

## Data

Registered faces are stored locally in:

- `data/face_db.json`
- `data/faces/`

## Notes

- The recognition pipeline is a lightweight local MVP based on OpenCV face detection plus handcrafted descriptors.
- It is suitable for demos and local experiments, not for production-grade biometric security.
