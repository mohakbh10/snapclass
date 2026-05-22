import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


@st.cache_resource #cache the loaded models to avoid reloading on every run as it is expensive to load (time and memory wise)
def load_dlib_models():
    # Load the dlib models for face detection and recognition
    detector= dlib.get_frontal_face_detector()

    sp= dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location())
    

    facerec= dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
        )

    return detector, sp, facerec
"""
theory of above code:
1. We are using dlib's frontal face detector to detect faces in the input image.
2. We are using dlib's shape predictor to get the facial landmarks for the detected faces, which are used to compute the face embeddings.
3. We are using dlib's face recognition model to compute the 128D face embeddings for the detected faces using the facial landmarks.
4. We are caching the loaded models using Streamlit's cache_resource decorator to avoid reloading the models on every run, which can be expensive in terms of time and memory.
5. We can use the get_face_embedding function (which we will implement next) to get the face embeddings for the input image and compare them with the stored embeddings in the database to authenticate the student using FaceID.
"""
def get_face_embedding(image_np):
    # Get the face embedding for a given image
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1) #why 1? - upsample the image once to detect smaller faces since the default dlib detector is not very good at detecting small faces

    encodings= []

    for face in faces:
        shape = sp(image_np, face) # Get the facial landmarks for the detected face
        face_descriptor = facerec.compute_face_descriptor(image_np, shape) # Compute the 128D face embedding using the facial landmarks
        encodings.append(np.array(face_descriptor)) # Append the face embedding to the list of encodings
    return encodings

"""
theory of above code:
1. The get_face_embedding function takes an input image in the form of a numpy array and returns a list of face embeddings for the detected faces in the image.
2. We first load the dlib models using the load_dlib_models function, which is cached to avoid reloading on every run.
3. We then use the dlib face detector to detect faces in the input image and get the facial landmarks for each detected face using the shape predictor.
4. Finally, we compute the 128D face embedding for each detected face using the face recognition model and return the list of embeddings.
5. We can use the returned face embeddings to compare with the stored embeddings in the database to authenticate the student using FaceID.
"""
@st.cache_resource
def get_trained_model():
    # Get the trained SVM model for face recognition
    X= [] # List to store the face embeddings for all students
    y= [] # List to store the corresponding student IDs for the face embeddings

    student_db = get_all_students() # Fetch all students from the database

    if not student_db:
        return None
    
    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding: # Check if the student has a face embedding stored in the database
            X.append(np.array(embedding)) # Append the face embedding to the list of embeddings
            y.append(student.get('student_id')) # Append the corresponding student ID to the list of labels

    if len(X) == 0:
        return 0
    
    clf= SVC(kernel='linear', probability=True, class_weight='balanced') # We use a linear kernel for SVM and set probability=True to enable probability estimates for the predictions. 
    #We also set class_weight='balanced' to handle if a student has like 100 face embeddings and another student who will look similar to the first student has only 1 face embedding, this will help the SVM model to give more weight to the second student with fewer samples and prevent it from being overshadowed by the first student with more samples.

    try:
        clf.fit(X, y) # Fit the SVM model to the training data
    except ValueError:
        pass # Handle the case where there are not enough samples to train the SVM model (e.g., if there is only one student with a face embedding in the database)


    return {'clf': clf, 'X': X, 'y': y} # Return the trained SVM model along with the training data (face embeddings and corresponding student IDs)


def train_classifier():
    st.cache_resource.clear() # Clear the cached resources to ensure that the latest data from the database is used for training the SVM model
    model_data = get_trained_model() # Get the trained SVM model using the latest data from the database
    return bool(model_data) # Return True if the model was successfully trained, False otherwise (e.g., if there are not enough samples to train the SVM model)


def predict_attendance(class_image_np):
    encodings = get_face_embedding(class_image_np) # Get the face embeddings for the input image


    detected_student ={}

    model_data = get_trained_model() # Get the trained SVM model

    if not model_data:
        return detected_student, [], len(encodings) # return an empty dictionary for detected_student, an empty list for probabilities, and the number of detected faces in the input image if the model is not trained (e.g., if there are no students with face embeddings in the database)

    clf = model_data['clf'] # Get the trained SVM model from the returned data
    X_train = model_data['X'] # Get the training data (face embeddings) from the returned data
    y_train = model_data['y'] # Get the corresponding student IDs for the training data from the returned data

    all_students = sorted(list(set(y_train))) # Get a sorted list of unique student IDs from the training data  

    for encoding in encodings:
        if len(all_students) >=2:
            predicted_id = int (clf.predict([encoding])[0]) # Predict the student ID for the input face embedding using the trained SVM model
        else:
            predicted_id = int(all_students[0]) # If there is only one student in the training data, we can directly assign the predicted student ID to that student without using the SVM model for prediction since there is no other class to compare against.

        student_embedding = X_train [y_train.index(predicted_id)] # Get the face embedding for the predicted student ID from the training data
        best_match_score = np.linalg.norm(student_embedding - encoding) # Calculate the Euclidean distance between the input face embedding and the face embedding of the predicted student to get a match score (lower score indicates a better match)

        resemblance_threshold = 0.6 # set threshold for resemblance score to determine if the predicted student is a good match for the input face embedding

        if best_match_score <= resemblance_threshold: 
            detected_student[predicted_id] = best_match_score
    return detected_student, all_students, len(encodings) # Return the dictionary of detected students with their corresponding match scores, the list of all student IDs in the training data, and the number of detected faces in the input image


"""
summary of each function:
1. load_dlib_models: This function loads the dlib models for face detection and recognition and caches them using Streamlit's cache_resource decorator to avoid reloading on every run, which can
be expensive in terms of time and memory.
2. get_face_embedding: This function takes an input image in the form of a numpy array and returns a list of face embeddings for the detected faces in the image. It uses the loaded dlib models to detect faces, get facial landmarks, and compute face embeddings.
3. get_trained_model: This function retrieves the face embeddings and corresponding student IDs from the database, trains an SVM model for face recognition using the retrieved data, and returns the trained model along with the training data.
4. train_classifier: This function clears the cached resources to ensure that the latest data from the database is used for training the SVM model and returns True if the model was successfully trained, False otherwise (e.g., if there are not enough samples to train the SVM model).
5. predict_attendance: This function takes an input image, gets the face embeddings for the detected faces, retrieves the trained SVM model, and predicts the student IDs for the input face embeddings. It also calculates a match score for each predicted student and returns a dictionary of detected students with their corresponding match scores, a list of all student IDs in the training data, and the number of detected faces in the input image.
"""