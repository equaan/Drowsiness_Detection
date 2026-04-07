import csv
import ctypes
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import winsound


FRAME_WIDTH = 450
EYE_WARNING_FRAMES = 8
EYE_DANGER_FRAMES = 15
EYE_CRITICAL_FRAMES = 25
YAWN_SECONDS_THRESHOLD = 1.2
YAWN_MAR_THRESHOLD = 0.45
NOD_FRAME_THRESHOLD = 8
NOD_DROP_RATIO = 0.18
YAWN_WINDOW_SECONDS = 60
YAWN_WARNING_COUNT = 2
YAWN_DANGER_COUNT = 4
YAWN_CRITICAL_COUNT = 6
DISTRACTION_FRAME_THRESHOLD = 15
DISTRACTION_X_RATIO = 0.18

ALARM_FLAGS = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
PROJECT_ROOT = Path(__file__).resolve().parent
ALARM_SOUND = PROJECT_ROOT / "alarm.wav"
LOG_FILE = PROJECT_ROOT / "drowsiness_log.csv"
ALERTS_DIR = PROJECT_ROOT / "alerts"
MCI_ALIAS = "drowsy_alarm"
winmm = ctypes.WinDLL("winmm")
mp_face_mesh = mp.solutions.face_mesh

UPPER_LIP_INDICES = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]
LOWER_LIP_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]
MOUTH_OPEN_PAIRS = [(13, 14), (82, 87), (312, 317)]
MOUTH_WIDTH_PAIR = (78, 308)


def load_cascade(filename: str) -> cv2.CascadeClassifier:
    cascade_path = Path(cv2.data.haarcascades) / filename
    cascade = cv2.CascadeClassifier(str(cascade_path))
    if cascade.empty():
        raise RuntimeError(f"Could not load cascade file: {cascade_path}")
    return cascade


def resize_frame(frame, width: int):
    height, current_width = frame.shape[:2]
    scale = width / float(current_width)
    resized_height = int(height * scale)
    return cv2.resize(frame, (width, resized_height))


def play_alarm():
    if ALARM_SOUND.exists():
        sound_path = str(ALARM_SOUND)
        winmm.mciSendStringW(f'close {MCI_ALIAS}', None, 0, None)
        open_result = winmm.mciSendStringW(
            f'open "{sound_path}" type mpegvideo alias {MCI_ALIAS}',
            None,
            0,
            None,
        )
        if open_result == 0:
            play_result = winmm.mciSendStringW(
                f"play {MCI_ALIAS} repeat",
                None,
                0,
                None,
            )
            if play_result == 0:
                return

        winsound.PlaySound(sound_path, ALARM_FLAGS)
    else:
        winsound.MessageBeep(winsound.MB_ICONHAND)


def stop_alarm():
    winmm.mciSendStringW(f"stop {MCI_ALIAS}", None, 0, None)
    winmm.mciSendStringW(f"close {MCI_ALIAS}", None, 0, None)
    winsound.PlaySound(None, 0)


def ensure_log_file():
    ALERTS_DIR.mkdir(exist_ok=True)

    if LOG_FILE.exists():
        return

    with LOG_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["timestamp", "event_type", "alert_level", "duration_seconds", "details"])


def write_log(event_type: str, alert_level: str, duration_seconds: float, details: str):
    with LOG_FILE.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                event_type,
                alert_level,
                f"{duration_seconds:.2f}",
                details,
            ]
        )


def save_alert_frame(frame, alert_level: str):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = ALERTS_DIR / f"{alert_level}_{timestamp}.jpg"
    cv2.imwrite(str(filename), frame)
    return filename


def get_alert_state(closed_eye_frames: int):
    if closed_eye_frames >= EYE_CRITICAL_FRAMES:
        return "critical", "CRITICAL - Drowsiness detected", (0, 0, 255)
    if closed_eye_frames >= EYE_DANGER_FRAMES:
        return "danger", "DANGER - Take a break", (0, 140, 255)
    if closed_eye_frames >= EYE_WARNING_FRAMES:
        return "warning", "WARNING - Stay alert", (0, 255, 255)
    return "normal", "", (0, 255, 0)


def get_yawn_alert_state(recent_yawn_count: int):
    if recent_yawn_count >= YAWN_CRITICAL_COUNT:
        return "critical", "CRITICAL - Frequent yawning", (0, 0, 255)
    if recent_yawn_count >= YAWN_DANGER_COUNT:
        return "danger", "DANGER - Repeated yawning", (0, 140, 255)
    if recent_yawn_count >= YAWN_WARNING_COUNT:
        return "warning", "WARNING - Frequent yawning", (0, 255, 255)
    return "normal", "", (0, 255, 0)


def merge_alert_states(primary_state, secondary_state):
    priority = {"normal": 0, "warning": 1, "danger": 2, "critical": 3}
    primary_level = primary_state[0]
    secondary_level = secondary_state[0]
    if priority[secondary_level] > priority[primary_level]:
        return secondary_state
    return primary_state


def normalized_point(landmarks, index: int, frame_width: int, frame_height: int):
    landmark = landmarks[index]
    return int(landmark.x * frame_width), int(landmark.y * frame_height)


def euclidean_distance(point_a, point_b):
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    return (dx * dx + dy * dy) ** 0.5


def get_mouth_aspect_ratio(landmarks, frame_width: int, frame_height: int):
    mouth_width = euclidean_distance(
        normalized_point(landmarks, MOUTH_WIDTH_PAIR[0], frame_width, frame_height),
        normalized_point(landmarks, MOUTH_WIDTH_PAIR[1], frame_width, frame_height),
    )
    if mouth_width == 0:
        return 0.0

    vertical_openings = []
    for upper_index, lower_index in MOUTH_OPEN_PAIRS:
        upper_point = normalized_point(landmarks, upper_index, frame_width, frame_height)
        lower_point = normalized_point(landmarks, lower_index, frame_width, frame_height)
        vertical_openings.append(euclidean_distance(upper_point, lower_point))

    return sum(vertical_openings) / (len(vertical_openings) * mouth_width)


def draw_lip_mapping(frame, landmarks):
    frame_height, frame_width = frame.shape[:2]
    upper_lip_points = np.array([
        normalized_point(landmarks, index, frame_width, frame_height)
        for index in UPPER_LIP_INDICES
    ], dtype=np.int32)
    lower_lip_points = np.array([
        normalized_point(landmarks, index, frame_width, frame_height)
        for index in LOWER_LIP_INDICES
    ], dtype=np.int32)

    cv2.polylines(
        frame,
        [upper_lip_points],
        True,
        (255, 0, 255),
        2,
    )
    cv2.polylines(
        frame,
        [lower_lip_points],
        True,
        (255, 255, 0),
        2,
    )

    for index in UPPER_LIP_INDICES:
        cv2.circle(
            frame,
            normalized_point(landmarks, index, frame_width, frame_height),
            1,
            (255, 0, 255),
            -1,
        )

    for index in LOWER_LIP_INDICES:
        cv2.circle(
            frame,
            normalized_point(landmarks, index, frame_width, frame_height),
            1,
            (255, 255, 0),
            -1,
        )


def draw_hud(frame, session_start_time: float, event_count: int, alert_start_time, alert_level: str):
    elapsed_seconds = int(time.time() - session_start_time)
    minutes, seconds = divmod(elapsed_seconds, 60)

    if alert_start_time is None or alert_level == "normal":
        alert_duration = 0.0
    else:
        alert_duration = time.time() - alert_start_time

    hud_lines = [
        f"Session Time: {minutes:02d}:{seconds:02d}",
        f"Drowsiness Events: {event_count}",
        f"Current Alert: {alert_level.upper()}",
        f"Alert Duration: {alert_duration:.1f}s",
    ]

    for index, text in enumerate(hud_lines):
        y = 25 + (index * 25)
        cv2.putText(
            frame,
            text,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )


ensure_log_file()

face_detector = load_cascade("haarcascade_frontalface_default.xml")
eye_detector = load_cascade("haarcascade_eye_tree_eyeglasses.xml")
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise RuntimeError("Could not open the webcam.")


session_start_time = time.time()
closed_eye_frames = 0
alarm_active = False
alert_start_time = None
last_logged_level = "normal"
session_event_count = 0
total_yawns = 0
total_nods = 0
total_distractions = 0

yawn_start_time = None
yawn_detected = False
yawn_active = False
recent_yawn_detected = False
yawn_mar = 0.0
yawn_timestamps = deque()

baseline_face_y = None
head_nod_frames = 0
head_nodding_detected = False
baseline_face_x = None
distraction_frames = 0
distracted_detected = False
last_saved_critical_frame = 0.0

while True:
    ok, frame = camera.read()
    if not ok:
        break

    frame = resize_frame(frame, FRAME_WIDTH)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_mesh_result = face_mesh.process(rgb_frame)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80),
    )

    eyes_found = 0
    yawn_detected = False
    head_nodding_detected = False
    distracted_detected = False

    if len(faces) > 0:
        x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 200, 0), 2)

        if baseline_face_y is None:
            baseline_face_y = float(y)
        else:
            baseline_face_y = (baseline_face_y * 0.9) + (y * 0.1)

        face_center_x = x + (w / 2.0)
        if baseline_face_x is None:
            baseline_face_x = face_center_x
        else:
            baseline_face_x = (baseline_face_x * 0.9) + (face_center_x * 0.1)

        nod_drop_threshold = baseline_face_y + (h * NOD_DROP_RATIO)
        if y > nod_drop_threshold:
            head_nod_frames += 1
        else:
            head_nod_frames = max(0, head_nod_frames - 1)

        if head_nod_frames >= NOD_FRAME_THRESHOLD:
            head_nodding_detected = True

        distraction_threshold = w * DISTRACTION_X_RATIO
        if abs(face_center_x - baseline_face_x) > distraction_threshold:
            distraction_frames += 1
        else:
            distraction_frames = max(0, distraction_frames - 1)

        if distraction_frames >= DISTRACTION_FRAME_THRESHOLD:
            distracted_detected = True

        roi_gray = gray[y : y + int(h * 0.6), x : x + w]
        roi_color = frame[y : y + int(h * 0.6), x : x + w]

        eyes = eye_detector.detectMultiScale(
            roi_gray,
            scaleFactor=1.1,
            minNeighbors=7,
            minSize=(20, 20),
        )

        eyes = sorted(eyes, key=lambda eye: eye[0])[:2]
        eyes_found = len(eyes)

        for ex, ey, ew, eh in eyes:
            cv2.rectangle(
                roi_color,
                (ex, ey),
                (ex + ew, ey + eh),
                (0, 255, 0),
                2,
            )

        if face_mesh_result.multi_face_landmarks:
            face_landmarks = face_mesh_result.multi_face_landmarks[0].landmark
            draw_lip_mapping(frame, face_landmarks)
            yawn_mar = get_mouth_aspect_ratio(face_landmarks, frame.shape[1], frame.shape[0])

            cv2.putText(
                frame,
                f"Mouth Ratio: {yawn_mar:.2f}",
                (10, frame.shape[0] - 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

            if yawn_mar >= YAWN_MAR_THRESHOLD:
                if yawn_start_time is None:
                    yawn_start_time = time.time()
                elif time.time() - yawn_start_time >= YAWN_SECONDS_THRESHOLD:
                    if not yawn_active:
                        yawn_detected = True
                        yawn_timestamps.append(time.time())
                    yawn_active = True
                    recent_yawn_detected = True
            else:
                yawn_start_time = None
                yawn_active = False
        else:
            yawn_mar = 0.0
            yawn_start_time = None
            yawn_active = False
    else:
        head_nod_frames = 0
        distraction_frames = 0
        yawn_mar = 0.0
        yawn_start_time = None
        yawn_active = False

    if eyes_found < 2:
        closed_eye_frames += 1
    else:
        closed_eye_frames = 0

    now = time.time()
    while yawn_timestamps and now - yawn_timestamps[0] > YAWN_WINDOW_SECONDS:
        yawn_timestamps.popleft()

    eye_alert_state = get_alert_state(closed_eye_frames)
    yawn_alert_state = get_yawn_alert_state(len(yawn_timestamps))
    alert_level, alert_message, alert_color = merge_alert_states(eye_alert_state, yawn_alert_state)

    if alert_level != "normal":
        if alert_start_time is None:
            alert_start_time = time.time()

        if alert_level != last_logged_level:
            session_event_count += 1
            write_log(
                "alert",
                alert_level,
                time.time() - alert_start_time,
                f"yawn_detected={recent_yawn_detected or yawn_detected}",
            )
            last_logged_level = alert_level
    else:
        alert_start_time = None
        last_logged_level = "normal"
        recent_yawn_detected = False

    if yawn_active or yawn_detected:
        if yawn_detected:
            total_yawns += 1
            write_log("yawn", "warning", 0.0, f"count_last_{YAWN_WINDOW_SECONDS}s={len(yawn_timestamps)}")

        cv2.putText(
            frame,
            "YAWNING DETECTED",
            (10, frame.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Yawns (last {YAWN_WINDOW_SECONDS}s): {len(yawn_timestamps)}",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 0, 255),
            2,
        )

    if head_nodding_detected:
        total_nods += 1
        write_log("head_nod", "warning", 0.0, "head_nodding_detected=True")
        cv2.putText(
            frame,
            "HEAD NODDING",
            (10, frame.shape[0] - 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2,
        )

    if distracted_detected:
        total_distractions += 1
        write_log("distraction", "warning", 0.0, "driver_looking_away=True")
        cv2.putText(
            frame,
            "DISTRACTION DETECTED",
            (10, frame.shape[0] - 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2,
        )

    if alert_level != "normal":
        if alert_level == "critical" and (closed_eye_frames // 8) % 2 == 0:
            border_color = (0, 255, 255)
        else:
            border_color = alert_color

        cv2.putText(
            frame,
            alert_message,
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            alert_color,
            2,
        )
        cv2.rectangle(
            frame,
            (5, 5),
            (frame.shape[1] - 5, frame.shape[0] - 5),
            border_color,
            4,
        )

    if alert_level == "critical":
        if not alarm_active:
            play_alarm()
            alarm_active = True
        if time.time() - last_saved_critical_frame > 5:
            saved_path = save_alert_frame(frame, alert_level)
            write_log("screenshot", alert_level, 0.0, saved_path.name)
            last_saved_critical_frame = time.time()
    else:
        if alarm_active:
            stop_alarm()
            alarm_active = False

    draw_hud(
        frame,
        session_start_time,
        session_event_count,
        alert_start_time,
        alert_level,
    )

    cv2.imshow("Drowsiness Detection", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

stop_alarm()
face_mesh.close()
camera.release()
cv2.destroyAllWindows()

session_duration = time.time() - session_start_time
print("Session summary")
print(f"Session duration: {session_duration:.1f} seconds")
print(f"Drowsiness events: {session_event_count}")
print(f"Total yawns: {total_yawns}")
print(f"Total nods: {total_nods}")
print(f"Total distractions: {total_distractions}")
