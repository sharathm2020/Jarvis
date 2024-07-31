from openai import OpenAI
import time
from pygame import mixer
import os

#Initialize the client
client = OpenAI(api_key='api-key')

#Initialize the mixer
mixer.init()

assistant_id = "asst_sYUKRiL3YmusbdLVN1EnxFA9"
thread_id = "thread_Byu3jf0IA1dvnyPuJzyYLSaw"

#Retrieve Assistant
assistant = client.beta.assistants.retrieve(assistant_id)

#Retrieve thread
thread = client.beta.threads.retrieve(thread_id)

#Function to ask questions
def ask_question_memory(question):
    global thread

    client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=question,
    )

    #create run for thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id = assistant.id
    )

    #Check run status
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id = run.id
        )

        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            return "The run has failed"
        time.sleep(0.5)

        #get the messages
        messages = client.beta.threads.messages.list(
        thread_id = thread.id
    )

    return messages.data[0].content[0].text.value


# Function to generate TTS and return speech file path
def generate_tts(sentence, speech_file_path):
    # Get a response
    response = client.audio.speech.create(
        model = "tts-1",
        voice="echo",
        input = sentence,
    ) 
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)

def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

# Function for generating TTS
def TTS(text):
    speech_file_path = "speech.mp3"
    speech_file_path = generate_tts(text, speech_file_path)

    #play sound somehow
    play_sound(speech_file_path)
    while mixer.music.get_busy():
        time.sleep(1)
    mixer.music.unload()
    os.remove(speech_file_path)
    return "done"

    #Method for playing sound

    
response = ask_question_memory("Provide me with the weather for Philadelphia today")
print(response)
TTS(response)