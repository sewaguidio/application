import tempfile
import os
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
import streamlit as st
from deep_translator import GoogleTranslator

#cmd = "cat /etc/ImageMagick-6/policy.xml | sed 's/none/read,write/g' > /etc/ImageMagick-6/policy.xml"
cmd = "sed -i 's/none/read,write/g'/ etc/ImageMagick-6/policy.xml"
os.system(cmd)

def extraire_audio(chemin_video):
    video = VideoFileClip(chemin_video)
    audio = video.audio
    sortie_audio = "sortie_audio.mp3"
    audio.write_audiofile(sortie_audio)
    return sortie_audio

def getDeepgramTranscription(file_path, lang):
    if lang == "fr":
        url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=fr&punctuate=true&diarize=true&smart_format=true"
    else:
        url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=en&punctuate=true&diarize=true&smart_format=true"

    headers = {
        "Authorization": 'Token ' + "20e4d0f5d789e83cc750c3db664f8bbfb464b558",
    }

    with open(file_path, 'rb') as audio_file:
        response = requests.post(url, headers=headers, data=audio_file)
        output = response.json()

    return output

def translate_text(text, langue):
    translator = GoogleTranslator(source='auto', target=langue)
    translation = translator.translate(text)
    return translation

def convert_to_srt(datas, output_filename, lang):
    def format_time(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds, milliseconds = divmod(remainder, 1)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"

    with open(output_filename, 'w', encoding="utf-8") as f:
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

def main():
    # Liste des langues disponibles
    langues = ["Yoruba (yo)", "Ewe (ee)", "Français (fr)", "Anglais (en)"]

    st.title("Générer des sous-titres pour une vidéo")

    # Télécharger la vidéo
    video_file = st.file_uploader("Choisir une vidéo", type=["mp4"])

    # Sélectionner la langue
    langue_selectionnee = st.selectbox("Sélectionnez une langue", langues)

    # Extraire le code de langue
    lang = langue_selectionnee.split("(")[1].split(")")[0]

    if st.button("Générer les sous-titres"):
        if video_file is not None and lang:
            try:
                with st.spinner("Génération des sous-titres en cours..."):
                    tfile = tempfile.NamedTemporaryFile(delete=False)
                    tfile.write(video_file.read())
                    video_path = tfile.name

                    mp3url = extraire_audio(video_path)
                    transcription = getDeepgramTranscription(mp3url, lang)

                    subtitle_data = transcription['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']

                    filename = os.path.basename(mp3url)
                    name, extension = os.path.splitext(filename)
                    output_filename = name + ".srt"

                    convert_to_srt(subtitle_data, output_filename, lang)

                    srtfilename = output_filename

                    generator = lambda txt: TextClip(txt, font='Arial', fontsize=18, color='white')
                    subtitles = SubtitlesClip(output_filename, generator, encoding='utf-8')

                    video = VideoFileClip(video_path)
                    subtitles = subtitles.set_position(('center', 'bottom'))

                    result = CompositeVideoClip([video, subtitles])

                    out_file = "sortie.mp4"
                    result.write_videofile(out_file)

                st.success("Vidéo avec sous-titres générée avec succès !")
                st.video(out_file)
            except Exception as e:
                st.error(f"Une erreur s'est produite lors de la génération des sous-titres : {e}")
        else:
            st.warning("Veuillez sélectionner une vidéo et une langue avant de générer les sous-titres.")

if __name__ == "__main__":
    main()
