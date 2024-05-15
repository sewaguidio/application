# -*- coding: utf-8 -*-
"""
!pip install --quiet ipython-autotime
# %load_ext autotime
!pip install moviepy
!pip install deep_translator
!pip install streamlit
!pip install numpy
"""
import tempfile
import os
import requests
from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as  np
from deep_translator import GoogleTranslator
import streamlit as st
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip



def extraire_audio(chemin_video):

    video = VideoFileClip(chemin_video)
    audio = video.audio
    sortie_audio = "sortie_audio.mp3"
    audio.write_audiofile(sortie_audio)
    return sortie_audio

def getDeepgramTranscription(file_path, lang ):
    # Use this to get subtitles in English
    if lang == "fr" : 
        url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=fr&punctuate=true&diarize=true&smart_format=true"
        
    else:
        url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=en&punctuate=true&diarize=true&smart_format=true"

    # Use this to get subtitles in the same language as the audio/video
    #url = "https://api.deepgram.com/v1/listen?model=whisper-large&detect_language=true"

    headers = {
        "Authorization": 'Token ' + "cb011716c36c35506d18ba9ce382f30355055be1",
    }

    with open(file_path, 'rb') as audio_file:
        response = requests.post(url, headers=headers, data=audio_file)

    output = response.json()
    return output





def translate_text(text, langue):
    # Initialiser le traducteur
    translator = GoogleTranslator(source='auto', target = langue)
    # Traduire le texte en ewe
    translation = translator.translate(text)
    return translation

def convert_to_srt(datas, output_filename, lang):
    def format_time(seconds):
        # Convert seconds to hours, minutes, seconds, milliseconds format
        hours, remainder = divmod(seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds, milliseconds = divmod(remainder, 1)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"

    with open(output_filename, 'w',encoding="utf-8") as f:
      for para in range(len(datas)):
        data = datas[para]['sentences']
        for i, entry in enumerate(data, start=1):
            start_time = format_time(entry['start'])
            end_time = format_time(entry['end'])
            
            if lang == "ee" or lang == "yo":
                subtitle_text = translate_text(entry['text'], lang)
            else:
                subtitle_text = entry['text']
                
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{subtitle_text}\n\n")


# Liste des langues disponibles
langues = [ "Anglais (en)", "Ewe (ee)", "Yoruba (yo)"]

st.title("Générer des sous-titres pour une vidéo")

# Télécharger la vidéo
video_file = st.file_uploader("Choisir une vidéo", type=["mp4"])

# Saisir la clé DeepGram
#cle = st.text_input("Entrez votre clé DeepGram")

# Sélectionner la langue
langue_selectionnee = st.selectbox("Sélectionnez une langue", langues)

# Extraire le code de langue
lang = langue_selectionnee.split("(")[1].split(")")[0]

if st.button("Générer les sous-titres"):
    if video_file is not None  and lang:
        # 1. Extraction de l'audio
        mp3url = extraire_audio(video_file.name)

        # 2. Transcription de l'audio
        output1 = getDeepgramTranscription(mp3url, lang)

        # 3. Extraction de la partie de la transcription pour le sous-titrage
        subtitle_data1 = output1['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']

        # Extraction du nom de fichier
        filename = os.path.basename(mp3url)
        name, extension = os.path.splitext(filename)
        output_filename = name + ".srt"

        # Écriture d'un fichier de sous-titres (.srt) avec les timestamps mot par mot
        convert_to_srt(subtitle_data1, output_filename, lang)
        srtfilename = output_filename

        # Fonction pour générer les clips de texte à partir des sous-titres
        generator = lambda txt: TextClip(txt, fontsize=18, color='white')

        # Charger le fichier de sous-titres avec l'encodage spécifié
        subtitles = SubtitlesClip(output_filename, generator, encoding='utf-8')

        # Charger la vidéo
        video = VideoFileClip(video_file.name)

        # Positionner les sous-titres en bas au milieu
        subtitles = subtitles.set_position(('center', 'bottom'))

        # Combiner la vidéo et les sous-titres
        result = CompositeVideoClip([video, subtitles])

        # Écrire la nouvelle vidéo avec les sous-titres
        out_file = f"{name}_with_subtitles.mp4"
        result.write_videofile(out_file)

        # Afficher la vidéo avec sous-titres
        st.video(out_file)
    else:
        st.warning("Veuillez télécharger une vidéo, entrer une clé DeepGram et sélectionner une langue.")
