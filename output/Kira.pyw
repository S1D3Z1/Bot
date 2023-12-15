import pyaudio
import wave
import grpc
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
import g4f
import pyttsx3
from googletrans import Translator

API_KEY="aje0nu6adfas7s356osq"

# Настройки потокового распознавания.
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 8000
CHUNK = 4096
RECORD_SECONDS = 60000
WAVE_OUTPUT_FILENAME = "audio.wav"

audio = pyaudio.PyAudio()


def asker(ar:str):
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": ar}],
            stream=True,
        )
        try:
            li=list(response)
            a=''
            for el in li:
                a+=str(el)
            translator = Translator()
            translation = translator.translate(a, dest="ru")
            tts = pyttsx3.init()
            tts.say(translation.text)
            tts.runAndWait()
        except:
            tts = pyttsx3.init()
            tts.say("Не получилось распознать речь")
            tts.runAndWait()
            
        


def gen():
   # Задайте настройки распознавания.
   recognize_options = stt_pb2.StreamingOptions(
      eou_classifier=stt_pb2.EouClassifierOptions(
          default_classifier=stt_pb2.DefaultEouClassifier(
             max_pause_between_words_hint_ms=2500
          )
      ),
      recognition_model=stt_pb2.RecognitionModelOptions(
         audio_format=stt_pb2.AudioFormatOptions(
            raw_audio=stt_pb2.RawAudio(
               audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
               sample_rate_hertz=8000,
               audio_channel_count=1
            )
         ),
         text_normalization=stt_pb2.TextNormalizationOptions(
            text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
            profanity_filter=True,
            literature_text=False
         ),
         language_restriction=stt_pb2.LanguageRestrictionOptions(
            restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
            language_code=['ru-RU']
         ),
         audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
      )
   )

   # Отправьте сообщение с настройками распознавания.
   yield stt_pb2.StreamingRequest(session_options=recognize_options)

   # Начните запись голоса.
   stream = audio.open(format=FORMAT, channels=CHANNELS,
               rate=RATE, input=True,
               frames_per_buffer=CHUNK)
   print("recording")
   frames = []

   # Распознайте речь по порциям.
   for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
      data = stream.read(CHUNK)
      yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
      frames.append(data)
   print("finished")

   # Остановите запись.
   stream.stop_stream()
   stream.close()
   audio.terminate()

   # Создайте файл WAV с записанным голосом.
   waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
   waveFile.setnchannels(CHANNELS)
   waveFile.setsampwidth(audio.get_sample_size(FORMAT))
   waveFile.setframerate(RATE)
   waveFile.writeframes(b''.join(frames))
   waveFile.close()

def run():
   # Установите соединение с сервером.
   cred = grpc.ssl_channel_credentials()
   channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
   stub = stt_service_pb2_grpc.RecognizerStub(channel)

   # Отправьте данные для распознавания.
   it = stub.RecognizeStreaming(gen(), metadata=(
      ('authorization', f'Api-Key {"AQVN0zICodW1BySszgFQrpJILp6OPV8pYcsjyWCy"}'),

   ))

   # Обработайте ответы сервера и выведите результат в консоль.
   try:
      for r in it:
         event_type, alternatives = r.WhichOneof('Event'), None
         if event_type == 'partial' and len(r.partial.alternatives) > 0:
            alternatives = [a.text for a in r.partial.alternatives]

         if event_type == 'final':
            alternatives = [a.text for a in r.final.alternatives]
            tmp = str(alternatives).upper()
            if 'КИРА' in tmp:
               asker(tmp.replace('КИРА','').lower())
         if event_type == 'final_refinement':
            alternatives = [a.text for a in r.final_refinement.normalized_text.alternatives]
         
   except grpc._channel._Rendezvous as err:
      print(f'Error code {err._state.code}, message: {err._state.details}')
      raise err

if __name__ == '__main__':
   run()
