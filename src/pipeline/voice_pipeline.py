#voice pipeline code with short comments 
from resemblyzer import VoiceEncoder, preprocess_wav 
import numpy as np
import io
import librosa
import streamlit as st

@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder() #load the voice encoder model

def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder() #get the loaded voice encoder

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000) #load the audio file and resample to 16kHz
        wav = preprocess_wav(audio) #preprocess the audio for the encoder
        embedding = encoder.embed_utterance(wav) #get the voice embedding
        return embedding.tolist() #return the embedding as a list
    except Exception as e:
        st.error(f"Voice recognition error: {e}") #handle any errors during processing
        return None

def identify_speaker(new_embedding, candidates_dict, threshold = 0.65):
    if new_embedding is None or not candidates_dict:
        return None , 0.0 #return None if no embedding or candidates are available
    
    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding:
            similarity = np.dot(new_embedding, stored_embedding) #calculate cosine similarity between the new embedding and stored embeddings
            if similarity > best_score:
                best_score = similarity
                best_sid = sid
    
    if best_score >= threshold:
        return best_sid, best_score #return the speaker ID and similarity score if above threshold
    
    return None, best_score #return None if no match is found, along with the best score for reference

def process_bulk_audio(audio_bytes, candidates_dict, threshold = 0.65):

    try:
        encoder = load_voice_encoder() #get the loaded voice encoder

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000) #load the audio file and resample to 16kHz
        segments = librosa.effects.split(audio, top_db=30) #split the audio into segments based on silence

        identified_results = {}

        for start, end in segments:

            if(end - start )< sr *0.5: #skip segments shorter than 0.5 seconds
                continue
            segment_audio= audio[start:end] #get the audio segment
            wav = preprocess_wav(segment_audio) #preprocess the segment for the encoder
            embedding = encoder.embed_utterance(wav) #get the voice embedding for the segment

            sid, score = identify_speaker(embedding, candidates_dict, threshold) #identify the speaker for the segment

            if sid:
                if sid not in identified_results or score > identified_results[sid]: #update the result if this segment has a higher score for the same speaker
                    identified_results[sid] = score

        return identified_results #return the dictionary of identified speakers and their best scores
    except Exception as e:
        st.error(f"Bulk audio processing error: {e}") #handle any errors during processing
        return {}
    
"""
summary of each function:
1. load_voice_encoder: Loads and returns the voice encoder model, cached for efficiency.
2. get_voice_embedding: Takes audio bytes, processes it, and returns the voice embedding as a list. Handles errors gracefully.
3. identify_speaker: Compares a new voice embedding against stored candidate embeddings to identify the speaker based on cosine similarity, returning the speaker ID and score if above a threshold.
4. process_bulk_audio: Processes a longer audio file, splits it into segments, and identifies speakers for each segment, returning a dictionary of identified speakers and their best scores. Handles errors gracefully.
"""