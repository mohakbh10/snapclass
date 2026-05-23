from src.database.config import supabase
import bcrypt

def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns false when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0 



def create_teacher(username, password, name):

    data = { "username" : username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None

def get_all_students():
    response = supabase.table("students").select("*").execute()
    return response.data

def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {
        "name": new_name,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding
    }
    response = supabase.table("students").insert(data).execute()
    return response.data

def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    # Query subjects for the teacher and include enrolled student count plus unique class count
    # SQL equivalent:
    # SELECT s.*,
    # (SELECT COUNT(*) FROM subject_students ss WHERE ss.subject_id = s.subject_id) AS total_students,
    # (SELECT COUNT(DISTINCT timestamp) FROM attendance_logs al WHERE al.subject_id = s.subject_id) AS total_classes
    response = supabase.table('subjects').select(
        "*, subject_students(count), attendance_logs(timestamp)"
    ).eq("teacher_id", teacher_id).execute()

    subjects = response.data
    for sub in subjects:
        sub['total_students'] = sub.get('subject_students', [{}])[0].get('count', 0)
        attendance = sub.get('attendance_logs', [])

        unique_sessions = len(
            set(log['timestamp'] for log in attendance)
        )

        sub['total_classes'] = unique_sessions


        sub.pop('subject_student', None)
        sub.pop('attendance_logs', None)

    return subjects

def enroll_student_to_subject(student_id, subject_id):
    #eq sql query: INSERT INTO subject_students (student_id, subject_id) VALUES (student_id, subject_id)
    data = {
        "student_id": student_id,
        "subject_id": subject_id
    }
    response = supabase.table("subject_students").insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    #eq sql query: DELETE FROM subject_students WHERE student_id = student_id AND subject_id = subject_id
    response = supabase.table("subject_students").delete().eq("student_id", student_id).eq("subject_id", subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    #eq sql query: SELECT * FROM subject_students JOIN subjects ON subject_students.subject_id = subjects.subject_id WHERE subject_students.student_id = student_id
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute() 
    return response.data


def get_student_attendance(student_id):
    #eq sql query: SELECT * FROM attendance_logs JOIN subjects ON attendance_logs.subject_id = subjects.subject_id WHERE attendance_logs.student_id = student_id
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data