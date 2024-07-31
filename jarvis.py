import io
import speech_recognition as sr
import whisper
import torch
import assist
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
import time
import tools

def main():
    #The last time a recording was recieved from queue
    phrase_time = None
    #Current raw audio bytes
    last_sample = bytes()
    #Thread safe Queue for passing data from the threaded recording callback
    data_queue = Queue()

    #We use speech recognizer to record audio
    recorder = sr.Recognizer()
    recorder.energy_threshold = 1000
    #Recorder energy threshold helps us with dynamic energy compensation and lowers energy threshold dramaticall
    recorder.dynamic_energy_threshold = False

    #Set the mic source
    source = sr.Microphone(sample_rate=16000, device_index=1)

    #Load the model
    audio_model = whisper.load_model("tiny.en")

    #Adjust for ambient noise
    with source:
        recorder.adjust_for_ambient_noise(source)

    
    #Function to collect audio data from microphone, then adds that data into our data queue(Main loop can continously grab data from the queue)
    def record_callback(_, audio:sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)
    
    #How realtime the recording is in seconds
    record_timeout = 2
    #How much empty space between recordings before we consider it a new line in the transcription
    phrase_timeout = 3

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    #Setup temp file
    temp_file = NamedTemporaryFile().name
    #Setup transcription variable
    transcription = ['']
    #Hot words
    hot_words = ["jarvis"]

    print("main loop starting")
    while True:
        now = datetime.utcnow()
        #Pull raw recorded audio from the queue
        if not data_queue.empty():
            phrase_complete = False
        
            if phrase_time and now - phrase_time > timedelta(seconds = phrase_timeout):
                last_sample = bytes()
                phrase_complete = True

            phrase_time = now

        #Concatenate our current audio data with the latest audio data
            while not data_queue.empty():
                data = data_queue.get()
                last_sample += data

        #Use AudioData to conver the raw data to wav data, create wav file object to get data how we want
            audio_data = sr.AudioData(last_sample , source.SAMPLE_RATE, source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())

            with open(temp_file, 'w+b') as f:
                f.write(wav_data.read())

            result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
            text = result['text'].strip()

            if phrase_complete:
                transcription.append(text)

                print("Checking for hotwords")
                if any(hot_word in text.lower() for hot_word in hot_words):
                    #make sure there is text
                    if text:
                        print("User: " + text)
                        response = assist.ask_question_memory(text)
                        done = assist.TTS(response)
                        if len(response.split('#')) > 1:
                            command = response.split('#')[1]
                            tools.parse_command(command)
                else:
                    print("Listening...")
            else:
                transcription[-1] = text
            print('', end='', flush=True)
            #Infinite loops are bad, this stops it
            time.sleep(0.25)


if __name__ == "__main__":
    main()