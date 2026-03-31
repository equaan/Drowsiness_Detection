 The Expansion Plan — Make It A Major Project
Here's what I suggest. Turn it into a complete Driver Safety Intelligence System with 3 clear independent modules — one per person.

👤 Member 1 — Core Detection Engine
"The Vision Module"
What they build:

Upgrade current Haar cascade code to MediaPipe Face Mesh
Implement proper EAR (Eye Aspect Ratio) with actual math
Implement MAR (Mouth Aspect Ratio) for yawn detection
3-level severity system (Warning → Danger → Critical)
Real-time HUD overlay on webcam feed

Machine Vision concepts covered:

468-point 3D facial landmark detection
Euclidean distance geometry
Real-time video pipeline
Thresholding and temporal frame logic


👤 Member 2 — Head Pose & Distraction Detection
"The Kinematics Module"
What they build:

Head nodding detection using MediaPipe depth coordinates
Head turning detection (looking away from road = distraction)
Euler angle calculation (Pitch, Yaw, Roll)
Integrate findings into the main alert system

Machine Vision concepts covered:

3D spatial coordinate mapping
Euler angle estimation
Exponentially Weighted Moving Average (EWMA)
Pose estimation without depth camera


👤 Member 3 — Analytics Dashboard & Logging System
"The Intelligence Module"
What they build:

CSV logging of every event with timestamp, severity, duration
Session summary screen shown when you press Q to quit — total alerts, total yawns, total nods
Matplotlib graph generated at session end showing EAR values over time (so you can literally SEE when the driver got drowsy)
A simple HTML report auto-generated after each session

Machine Vision concepts covered:

Data visualization of vision metrics
Longitudinal behavioral analysis
Performance benchmarking (FPS counter)


📊 Full Project Architecture
┌─────────────────────────────────────────────────┐
│         DRIVER SAFETY INTELLIGENCE SYSTEM        │
├─────────────────┬──────────────────┬─────────────┤
│   Member 1      │    Member 2      │  Member 3   │
│                 │                  │             │
│ Detection       │ Head Pose &      │ Analytics & │
│ Engine          │ Distraction      │ Dashboard   │
│                 │                  │             │
│ • MediaPipe     │ • Euler Angles   │ • CSV Log   │
│ • EAR/MAR       │ • Pitch/Yaw/Roll │ • Matplotlib│
│ • 3 Severity    │ • Nodding        │ • Session   │
│   Levels        │ • Distraction    │   Report    │
│ • Alarm         │   Detection      │ • FPS HUD   │
└─────────────────┴──────────────────┴─────────────┘
              ↓             ↓              ↓
         ┌────────────────────────────────────┐
         │         main.py — Fuses all 3      │
         │         modules into one system    │
         └────────────────────────────────────┘

📁 Project File Structure
DriverSafetySystem/
│
├── main.py                  # Entry point, fuses all modules
│
├── modules/
│   ├── detection.py         # Member 1 — EAR, MAR, alerts
│   ├── head_pose.py         # Member 2 — Euler angles, nodding
│   └── analytics.py         # Member 3 — logging, graphs, report
│
├── assets/
│   └── alarm.wav
│
├── output/
│   ├── drowsiness_log.csv   # Auto-generated
│   └── session_report.html  # Auto-generated
│
└── requirements.txt

🔧 New Requirements
pip install mediapipe opencv-python numpy matplotlib
Still no GPU needed. Runs on any laptop.

✅ What Each Person Says During Presentation
Member 1 says:
"I built the core vision engine. It uses MediaPipe's 468-point face mesh to calculate Eye Aspect Ratio and Mouth Aspect Ratio in real time, implementing a 3-level alert system backed by IEEE research thresholds of EAR < 0.22 and MAR > 0.65."
Member 2 says:
"I built the head pose and distraction module. Using MediaPipe's 3D depth coordinates I calculate Euler angles — pitch, yaw and roll — to detect head nodding and whether the driver is looking away from the road, which catches drowsiness even when eyes are partially open."
Member 3 says:
"I built the analytics and intelligence layer. Every alert event is logged to CSV with full metadata. At session end, a Matplotlib graph of EAR over time is auto-generated showing exactly when the driver got drowsy, and an HTML session report is produced automatically."

📋 Contribution Summary Table
Member 1Member 2Member 3ModuleDetection EngineHead PoseAnalyticsCore filedetection.pyhead_pose.pyanalytics.pyCV conceptsEAR, MAR, landmarksEuler angles, poseData viz, loggingOutputLive alerts on screenNodding/distraction flagsCSV + graph + reportDifficultyHighHighMediumLines of code~120~100~80