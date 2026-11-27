# SnapClass — AI-Powered Classroom Attendance System

> An AI-assisted classroom attendance management application using face recognition, voice recognition, and cloud-based student and subject management.

**Live Demo:** https://snapclass-bymohak.streamlit.app/  
**Source Code:** https://github.com/mohakbh10/snapclass

---

## Overview

SnapClass is a classroom attendance management application designed to reduce manual attendance-taking through computer vision and voice-based identification.

The application provides separate interfaces for teachers and students. Teachers can create and manage subjects, enroll students, process classroom images or audio recordings for attendance, and review attendance records. Students can register their biometric profiles, enroll in subjects, and view their attendance history.

The project combines machine learning pipelines with a Streamlit interface and Supabase-backed data storage.

## Key Features

### 1. Face Recognition Attendance

- Capture a student's face during profile registration.
- Generate 128-dimensional facial embeddings using Dlib.
- Train a Support Vector Machine (SVM) classifier using registered student embeddings.
- Process classroom images containing multiple students.
- Match detected faces against registered student profiles.
- Review attendance results before saving them.

### 2. Voice-Based Attendance

- Capture voice samples during student registration.
- Generate voice embeddings using Resemblyzer.
- Process classroom audio recordings.
- Split audio into speech segments using Librosa's silence-based segmentation.
- Compare voice embeddings using cosine similarity.
- Identify enrolled students and prepare attendance results.

### 3. Teacher Portal

- Teacher registration and login.
- Create and manage subjects.
- Generate subject-sharing QR codes.
- Upload or capture classroom photographs.
- Run face recognition attendance.
- Record attendance through voice recognition.
- Review and confirm attendance before saving.
- View historical attendance records.

### 4. Student Portal

- Register using a facial profile.
- Optional voice enrollment.
- Log in through face recognition.
- Enroll in subjects using subject codes.
- View enrolled subjects and attendance statistics.
- Unenroll from subjects.

### 5. Subject Enrollment

- Teachers create subjects with a subject code, name, and section.
- Students enroll using the subject code.
- QR codes and shareable links are provided for subject enrollment.

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Frontend / Application | Streamlit |
| Face Recognition | Dlib, face_recognition_models |
| Machine Learning | Scikit-learn, SVM |
| Audio Processing | Librosa |
| Voice Recognition | Resemblyzer |
| Image Processing | Pillow, NumPy |
| Data Processing | Pandas |
| Database | Supabase (PostgreSQL) |
| Authentication | bcrypt |
| QR Code Generation | Segno |

## System Architecture

```text
                 Streamlit Application
                          |
                 Role-Based Navigation
                    /           \
                   /             \
             Teacher Portal   Student Portal
                   |             |
          Subject Management  Registration
                   |             |
          Attendance Capture  Face Enrollment
              /       \           |
             /         \       Supabase
       Face Pipeline  Voice Pipeline
             |             |
          Dlib + SVM   Librosa + Resemblyzer
             |             |
             +------+------+
                    |
             Attendance Results
                    |
             Teacher Confirmation
                    |
                 Supabase
                    |
        Attendance Logs & Dashboards
```

## Face Recognition Pipeline

1. Load the Dlib frontal-face detector, facial landmark predictor, and face recognition model.
2. Detect faces in the input image.
3. Extract facial landmarks.
4. Generate 128-dimensional face descriptors.
5. Retrieve registered student embeddings from Supabase.
6. Train a linear SVM classifier.
7. Predict student identities for detected faces.
8. Apply an Euclidean-distance matching threshold of 0.6.
9. Return detected student IDs for attendance processing.

The Dlib models and trained classifier are cached using Streamlit's `st.cache_resource` to avoid unnecessary repeated loading and training.

## Voice Recognition Pipeline

1. Load the recorded audio using Librosa.
2. Resample audio to 16 kHz.
3. Preprocess the waveform using Resemblyzer.
4. Generate voice embeddings.
5. Split longer recordings into segments based on silence.
6. Ignore segments shorter than 0.5 seconds.
7. Compare each segment with enrolled student voice embeddings using cosine similarity.
8. Identify matching students using a default similarity threshold of 0.65.

## Database Design

SnapClass uses Supabase as its cloud database.

| Table | Purpose |
|---|---|
| `students` | Student profiles and biometric embeddings |
| `teachers` | Teacher accounts and password hashes |
| `subjects` | Subjects created by teachers |
| `subject_students` | Student-to-subject enrollment mapping |
| `attendance_logs` | Attendance records, timestamps, and status |

### Authentication

Teacher passwords are hashed using bcrypt before being stored.

Supabase credentials are loaded through Streamlit secrets rather than hardcoded into application code.

## Project Structure

```text
snapclass/
│
├── app.py
├── requirements.txt
│
└── src/
    ├── components/
    │   ├── dialog_add_photo.py
    │   ├── dialog_attendance_results.py
    │   ├── dialog_auto_enroll.py
    │   ├── dialog_create_subject.py
    │   ├── dialog_enroll.py
    │   ├── dialog_share_subject.py
    │   ├── dialog_voice_attendance.py
    │   ├── header.py
    │   ├── footer.py
    │   └── subject_card.py
    │
    ├── database/
    │   ├── config.py
    │   └── db.py
    │
    ├── pipelines/
    │   ├── face_pipeline.py
    │   └── voice_pipeline.py
    │
    ├── screens/
    │   ├── home_screen.py
    │   ├── student_screen.py
    │   └── teacher_screen.py
    │
    └── ui/
        └── base_layout.py
```

## Getting Started

### Prerequisites

- Python 3.10 or a compatible Python version for the installed dependencies.
- A Supabase project.
- Supabase project URL and API key.

### 1. Clone the repository

```bash
git clone https://github.com/mohakbh10/snapclass.git
cd snapclass
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS / Linux**
```bash
source venv/bin/activate
```

**Windows**
```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Supabase secrets

Create a `.streamlit/secrets.toml` file:

```toml
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_KEY = "your_supabase_api_key"
```

Use appropriate credentials for your Supabase project. Never commit secrets to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

The application will be available at the local URL provided by Streamlit.

## Limitations

- Face recognition performance can vary with lighting, camera quality, pose, and occlusion.
- Voice recognition can be affected by background noise, overlapping speech, and recording quality.
- Recognition thresholds are implementation parameters and have not been established as production-grade biometric guarantees.
- The application is an educational project and should not be treated as a high-assurance biometric security system.
- Attendance results are presented for teacher review and confirmation before being saved.

## Future Improvements

- Improve biometric matching and confidence calibration.
- Add more robust audio preprocessing for noisy classrooms.
- Improve QR-based enrollment flow.
- Add attendance export and richer analytics.
- Add automated tests and stronger production security controls.

## What I Learned

- Building end-to-end machine learning pipelines.
- Generating and comparing facial embeddings.
- Training an SVM classifier for identity prediction.
- Extracting speaker embeddings from audio.
- Processing longer audio recordings using silence-based segmentation.
- Integrating Streamlit with Supabase.
- Designing relational database workflows for enrollment and attendance.
- Implementing password hashing and role-specific application flows.

## Author

**Mohak Bhattacharya**  
Computer Science Engineering, KIIT University

- GitHub: https://github.com/mohakbh10

---

*Built as an educational project exploring the integration of computer vision, audio AI, and full-stack application development.*
