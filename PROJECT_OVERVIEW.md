# Drowsiness Detection Project Overview

## 1. Project Title

Real-Time Driver Drowsiness Detection and Alert System

## 2. What This Project Is

This project is a real-time computer vision system that monitors a person's face through a webcam and detects signs of drowsiness. It is designed as a safety-focused application that can warn a user before fatigue becomes dangerous.

The system continuously analyzes facial behavior and attention-related patterns such as:

- prolonged eye closure
- yawning
- head nodding

When these signs are detected, the project gives visual warnings on screen and can also play an audio alarm to alert the user.

## 3. Main Goal of the Project

The goal of this project is to reduce the risk of accidents caused by fatigue by identifying early and late signs of drowsiness in real time.

Instead of only detecting sleep after it happens, this project tries to detect progressive warning signals, which makes it more practical for real-world monitoring.

## 4. What the System Can Do

The current system can:

- capture live video from a webcam
- detect a face in each video frame
- detect the eyes and monitor whether they remain closed for too long
- detect yawning using facial landmarks and mouth opening measurements
- detect head nodding by tracking downward face movement across frames
- classify drowsiness into multiple severity stages
- show a live visual HUD with session statistics
- play a custom looping audio alarm during critical drowsiness
- log alert events into a CSV file for later analysis

## 5. Key Features

### 5.1 Eye Closure Detection

The project monitors whether both eyes are visible. If the eyes are not detected for a sustained number of frames, it treats this as a drowsiness signal.

This is the core detection method for the main alert system.

### 5.2 Yawn Detection

Yawning is treated as an early sign of fatigue. The system uses facial landmarks around the lips and computes a mouth opening ratio to decide whether the user is yawning.

This is more reliable than simple mouth-box detection because it measures the actual geometry of the mouth.

### 5.3 Head Nodding Detection

Head nodding is another important sign of low alertness. The system tracks the vertical position of the detected face over time. If the face drops repeatedly below its normal position, the system flags it as head nodding.

### 5.4 Multi-Level Alert System

The project does not use only a binary alert. It uses three levels:

- Level 1: Warning
- Level 2: Danger
- Level 3: Critical

This makes the system more realistic because drowsiness usually develops gradually.

### 5.5 On-Screen Dashboard

The system displays a small live dashboard on the video window showing:

- total session time
- number of drowsiness events in the session
- current alert level
- duration of the current alert

### 5.6 Audio Alert System

When the drowsiness level becomes critical, the system plays a looping custom `.wav` alarm file from the project folder.

### 5.7 CSV Logging

Every important alert event can be stored in `drowsiness_log.csv` with:

- timestamp
- alert level
- duration
- whether yawning was detected

This makes the project more useful for reporting, analysis, and demonstration.

## 6. Technology Stack

This project is implemented in Python and uses a combination of computer vision, facial landmark tracking, audio alerting, and data logging.

### 6.1 Python

Python is the main programming language used in the project.

Why it is used:

- simple and readable syntax
- strong support for computer vision libraries
- fast development for academic projects
- large ecosystem for image processing and automation

### 6.2 OpenCV

Library: `opencv-python`

OpenCV is used for the main video processing pipeline.

In this project, OpenCV is responsible for:

- reading webcam input
- resizing frames
- converting color spaces
- face detection using Haar cascades
- eye detection using Haar cascades
- drawing overlays, contours, bounding boxes, and text
- showing the final live output window

Why OpenCV matters:

- it is lightweight and fast for real-time webcam applications
- it provides ready-made detection tools
- it is widely used in academic and industrial vision systems

### 6.3 MediaPipe Face Mesh

Library: `mediapipe==0.10.14`

MediaPipe Face Mesh is used for accurate facial landmark detection, especially for mouth and lip tracking.

In this project, it is used to:

- detect facial landmarks around the lips
- map upper lip points and lower lip points
- calculate a mouth aspect ratio
- improve yawn detection compared to basic mouth-box detection

Why it matters:

- it provides dense and structured face landmarks
- it is more robust than simple cascade-based mouth detection
- it enables geometric measurement instead of rough object-box estimation

### 6.4 NumPy

Library: `numpy`

NumPy is used to work with coordinate arrays for lip contours and point processing.

In this project, it supports:

- storing lip landmark points as arrays
- preparing point data for OpenCV drawing functions

### 6.5 Winsound + Windows MCI Audio API

Libraries/modules:

- `winsound`
- `ctypes`
- Windows `winmm` MCI interface

These are used for audio alert playback on Windows.

Why both are used:

- `winsound` is simple but supports limited audio formats
- the Windows MCI audio interface is used to play the custom alert sound more reliably
- `ctypes` allows Python to call the system audio API directly

In this project, they are used to:

- play a looping alarm sound
- stop the sound when the danger condition is removed
- provide a fallback alert behavior if needed

### 6.6 CSV Module

Library/module: built-in `csv`

The CSV module is used for event logging.

It records important alert events in a structured way so the results can be:

- opened in Excel
- analyzed later
- included in a report

### 6.7 Datetime and Time

Modules:

- `datetime`
- `time`

These modules are used for:

- session timing
- alert duration tracking
- timestamp creation in logs
- yawn duration timing

### 6.8 Pathlib

Module: built-in `pathlib`

`pathlib` is used for safe and readable file handling.

In this project, it helps manage:

- alarm audio file paths
- CSV log file paths
- project-root-relative resources

## 7. Detection Logic Used in the Project

### 7.1 Face Detection

The system first detects the user's face in the frame. This provides the base region for other calculations.

### 7.2 Eye-Based Drowsiness Detection

The system checks whether both eyes are visible. If the eyes remain undetected for a continuous number of frames, it assumes the user may be drowsy or asleep.

Three thresholds are used:

- warning threshold
- danger threshold
- critical threshold

### 7.3 Yawn Detection with Mouth Aspect Ratio

Using MediaPipe landmarks, the system selects lip points from the upper and lower lips. It then measures:

- mouth width
- vertical mouth opening

From this, it calculates a normalized mouth ratio. If the mouth remains open above a threshold for a certain duration, it detects a yawn.

### 7.4 Head Nodding Detection

The face position is tracked across frames. A running baseline of the face's vertical position is maintained. If the detected face drops lower than its expected position for repeated frames, the system marks it as head nodding.

## 8. Output of the System

The system produces both real-time and stored outputs.

### Real-Time Outputs

- live webcam display
- face and eye bounding boxes
- lip landmark mapping
- mouth ratio display
- warning text overlays
- flashing border during alerts
- alarm sound during critical drowsiness

### Stored Outputs

- `drowsiness_log.csv` log file

## 9. Use Cases

This project can be adapted for many real-world use cases:

- driver monitoring in cars, buses, and trucks
- fatigue detection for night-shift workers
- machine operator safety monitoring
- student or researcher demonstration of computer vision concepts
- smart surveillance systems
- human attention analysis prototypes

## 10. Why This Project Is Useful Academically

This project is a strong academic project because it combines multiple important areas of computing:

- computer vision
- machine perception
- human behavior analysis
- real-time systems
- user alert systems
- data logging and analysis

It also moves beyond a very basic demo because it includes:

- multiple behavioral indicators
- graded severity levels
- real-time visualization
- persistent logs
- custom audio alerting

That makes it easier to justify as a meaningful mini project or final-year style prototype.

## 11. Strengths of the Current Approach

- works in real time with a webcam
- does not require cloud processing
- runs locally on a standard laptop
- combines multiple indicators instead of relying on one
- easy to demonstrate in front of a teacher
- generates measurable outputs through logs and statistics

## 12. Current Limitations

Like all vision-based systems, this project still has limitations:

- performance depends on lighting conditions
- webcam quality affects detection accuracy
- glasses, masks, or face angle can reduce reliability
- eye detection with Haar cascades is simpler than deep learning methods
- head pose detection is heuristic, not full 3D pose estimation
- thresholds may need calibration for different users

These are normal research and prototype limitations and can be discussed honestly in a report.

## 13. Possible Future Enhancements

Future improvements could include:

- replacing Haar-based eye detection with facial-landmark-based eye aspect ratio
- adding blink-rate analysis
- using full head pose estimation with solvePnP
- storing screenshots of alert events
- building a graphical dashboard
- adding cloud or database storage for logs
- creating a desktop app or web dashboard
- optimizing the model for embedded systems such as Raspberry Pi

## 14. Simple Explanation for a Teacher

If you need to explain it simply, you can say:

This project is a webcam-based drowsiness detection system built in Python. It detects signs like eye closure, yawning, and head nodding in real time. Based on the seriousness of these signs, it shows warning messages, plays an alarm, and stores alert data in a CSV file. OpenCV is used for video processing, and MediaPipe Face Mesh is used for accurate lip landmark tracking for yawn detection.

## 15. Short Viva/Presentation Version

This project is a real-time fatigue monitoring system. It uses OpenCV for webcam capture, face detection, and eye detection, and MediaPipe Face Mesh for lip landmark analysis to detect yawning. It tracks multiple drowsiness indicators, classifies severity into stages, shows visual warnings, plays a custom alarm, and logs events for analysis.
