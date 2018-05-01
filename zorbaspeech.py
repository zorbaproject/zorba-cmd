#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://cmusphinx.sourceforge.net/wiki/tutorialadapt
# http://cmusphinx.sourceforge.net/wiki/tutorialtuning

# you probably need the file /acoustic-model/mixture_weights to get better results in adaptation. Just check that you have it.


import time
from os import path
import speech_recognition as sr
import sys
import shutil
import os
import select
import subprocess
import datetime

import pyaudio
import wave


class ZorbaSpeech(object):
    
    def __init__(self, lang = "en-US", afile = ""):
        self.language = lang
    
        self.inst_dir = "/usr/local/lib/python3.5/dist-packages/speech_recognition/pocketsphinx-data/"
    
        self.libdir = "/usr/lib/"
        self.bindir = "/usr/bin/"
    
    
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        
        
        self.AUDIO_FILE = afile
        
        self.chooseVoice()
    
    
    
    
    #for (i, item) in enumerate(sys.argv):
    def help(self):
            print("Options:\n -l specify self.language\n -f specify file to recognize\n -t tune speech recognition voice model \n -r do recognize audio     input (from microphone or file)")
        
    def setLanguage(self, lang = "en-US"):
            self.language = lang
            print("language: " + self.language)
        
    def setAudioFile(self, afile):
            self.AUDIO_FILE = afile
            
    def recognize(self):
            r = sr.Recognizer()
            #m = sr.Microphone()
            try:
                m = sr.Microphone()
                print("Noise calibration. A moment of silence, please...")
                with m as source: r.adjust_for_ambient_noise(source)
                print("Set minimum energy threshold to {}".format(r.energy_threshold))
            except:
                print("No microphone")
            try:
                runrecognition = True
                while runrecognition:
                    if self.AUDIO_FILE!="":
                        with sr.AudioFile(self.AUDIO_FILE) as fsource:
                            audio = r.record(fsource)  # read the entire audio file
                    else:
                            #m = sr.Microphone()
                            #print("Noise calibration. A moment of silence, please...")
                            #with m as source: r.adjust_for_ambient_noise(source)
                            #print("Set minimum energy threshold to {}".format(r.energy_threshold))
                            print("Listening...") #Please, try to speak with you usual voice: if you talk too slow sphinx will not identify words boundaries
                            with m as source: audio = r.listen(source)
                    print("Wait...")
                    try:
                        # recognize speech using Google Speech Recognition
                        #value = r.recognize_google(audio) #https://cloud.google.com/speech/pricing
                        value = r.recognize_sphinx(audio, self.language)
                        #print("You: {}".format(value))
                        if self.AUDIO_FILE!="":
                            runrecognition = False
                        #os.system(os.path.abspath(os.path.dirname(sys.argv[0])) + "/zorba-cmd.py -p \"" + value + "\"")
                        return value
                    except sr.UnknownValueError:
                        print("???")
                    except sr.RequestError as e:
                        print("Error; {0}".format(e))
            except KeyboardInterrupt:
                pass
            
            
    def chooseVoice(self):
            mblang = ""
            #load settings from file
            #mblang = "mb-it4"
            vfile = os.path.abspath(os.path.dirname(sys.argv[0])) + '/lang/' + self.language + '/sphinxadapt.txt'
            if os.path.isfile(vfile):
                text_file = open(vfile, "r")
                lines = text_file.read()
                text_file.close()
                if lines != "":
                    mblang = lines.split(",")[0]
            self.espeaklang = self.language.split("-")[0]
            mbfolder = "/usr/share/mbrola/"
            
            if mblang == "" or os.path.isdir(mbfolder + mblang[3:]) == False:
                if os.path.isdir(mbfolder):
                    entities = os.listdir(mbfolder)
                    for entity in entities:
                        if os.path.isdir(mbfolder + entity) and entity[:len(self.espeaklang)]==str(self.espeaklang) :
                            mblang = "mb-" + entity
                            break
            if (mblang != ""):
                self.espeaklang = mblang
            return self.espeaklang
            
    def speak(self, answer = "", chat_id = ""):
            tmpfile = str(datetime.datetime.now()).replace(" ","_").replace(":","_")
            newFileW = "/tmp/voice" + tmpfile + "_" + str(chat_id) + ".wav"
            #http://telepot.readthedocs.io/en/latest/reference.html
            if self.espeaklang == "":
                self.chooseVoice()
            if self.espeaklang != "":
                os.system('espeak -v ' + self.espeaklang + ' -s 150 -p 50 -w ' + newFileW + ' "' + str(answer) + '"')
            else:
                return str("")
            #wave is massive, even if this feature is not designed for long messages, we should think about using OGG instead of WAV
            
            #if chat_id is empty, we should just play the file
            return newFileW
        
    def train(self, choice = "no"):
            #TODO: -copy immediately original self.language model in current_pwd and work only on the copy -edit if needed the feat.params file on the copy
            
            #we start to adapt the model
            current_pwd = os.getcwd() + "/training" #os.getcwd is probably a directory we can write without root permission, while this script folder probably not
            shutil.rmtree(current_pwd, ignore_errors=True)
            os.makedirs(current_pwd)
            
            fparams = self.inst_dir + self.language + "/acoustic-model/feat.params"
            params = open(fparams, 'r')
            paramscont = params.readlines()
            params.close()
            found = False
            for line in paramscont:
                if "-cmn current" in line:
                    print("Found '-cmn current' in feat.params file. Good.")
                    found = True
    
            if not found:
                print("Please take note that training MAY FAIL, since the file " + fparams + " does not contain the '-cmn current' line.")
            

            ph = []
            f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + '/lang/' + self.language + '/sphinxadapt.txt','r')
            for line in f:
                ph.append(line.strip())
            f.close()
            
            audio = pyaudio.PyAudio()
            f1 = open(current_pwd + "/test.fileids", 'w')
            f2 = open(current_pwd + "/test.transcription", 'w')
            for (n, itemn) in enumerate(ph):
                f1.write("test" + str(n) + "\n")
                f2.write(itemn + " (test" + str(n) + ")\n")
                
                stream = audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
                print("Please say: " + itemn + " And press ENTER.")
                frames = []
     
                runrecord = True
                while runrecord:
                    data = stream.read(self.CHUNK)
                    frames.append(data)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = input()
                        runrecord = False
                
                stream.stop_stream()
                stream.close()
    
                waveFile = wave.open(current_pwd + "/test" + str(n) +".wav", 'wb')
                waveFile.setnchannels(self.CHANNELS)
                waveFile.setsampwidth(audio.get_sample_size(self.FORMAT))
                waveFile.setframerate(self.RATE)
                waveFile.writeframes(b''.join(frames))
                waveFile.close()
                
            f1.close()
            f2.close()
            audio.terminate()
            
            # verify accuracy
            command = self.bindir + "pocketsphinx_batch -adcin yes -cepdir " + current_pwd + " -cepext .wav -ctl " + current_pwd + "/test.fileids -lm " + self.inst_dir + self.language + "/language-model.lm.bin -dict " + self.inst_dir + self.language + "/pronounciation-dictionary.dict -hmm " + self.inst_dir + self.language + "/acoustic-model -hyp " + current_pwd + "/test.hyp"
            os.system(command)
        
            command = self.libdir + "sphinxtrain/scripts/decode/word_align.pl " + current_pwd + "/test.transcription " + current_pwd + "/test.hyp"
            os.system(command)
            ##
            
            #now build new self.language model
            shutil.copytree(self.inst_dir + self.language, current_pwd + "/" + self.language)
    
            command = self.bindir + "sphinx_fe -argfile " + current_pwd + "/" + self.language + "/acoustic-model/feat.params -samprate 16000 -c " + current_pwd + "/test.fileids -di " + current_pwd + " -do " + current_pwd + " -ei wav -eo mfc -mswav yes"
            os.system(command)
        
            command = self.bindir + "pocketsphinx_mdef_convert -text " + current_pwd + "/" + self.language + "/acoustic-model/mdef " + current_pwd + "/" + self.language + "/acoustic-model/mdef.txt"
            os.system(command)
        
            command = self.libdir + "sphinxtrain/bw -hmmdir " + self.inst_dir + self.language + "/acoustic-model -moddeffn " + current_pwd + "/" + self.language + "/acoustic-model/mdef.txt -ts2cbfn .cont. -feat 1s_c_d_dd -cmn current -agc none -dictfn " + self.inst_dir + self.language + "/pronounciation-dictionary.dict -ctlfn " + current_pwd + "/test.fileids -lsnfn " + current_pwd + "/test.transcription -accumdir" + current_pwd + " -lda " + current_pwd + "/" + self.language + "/acoustic-model/feature_transform"
            os.system(command)
        
            command = self.libdir + "sphinxtrain/mllr_solve -meanfn " + current_pwd + "/" + self.language + "/acoustic-model/means -varfn " + current_pwd + "/" + self.language + "/acoustic-model/variances -outmllrfn mllr_matrix -accumdir" + current_pwd
            os.system(command)
        
            shutil.copytree(current_pwd + "/" + self.language, current_pwd + "/" + self.language + "-adapt")
        
            command = self.libdir + "sphinxtrain/map_adapt -moddeffn " + current_pwd + "/" + self.language + "/acoustic-model/mdef.txt -ts2cbfn .cont. -meanfn " + current_pwd + "/" + self.language + "/acoustic-model/means -varfn " + current_pwd + "/" + self.language + "/acoustic-model/variances -mixwfn " + current_pwd + "/" + self.language + "/acoustic-model/mixture_weights -tmatfn " + current_pwd + "/" + self.language + "/acoustic-model/transition_matrices -accumdir" + current_pwd + " -mapmeanfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/means -mapvarfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/variances -mapmixwfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/mixture_weights -maptmatfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/transition_matrices"
            os.system(command)
        
            command = self.libdir + "sphinxtrain/mk_s2sendump -pocketsphinx yes -moddeffn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/mdef.txt -mixwfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/mixture_weights -sendumpfn " + current_pwd + "/" + self.language + "-adapt/acoustic-model/sendump"
            os.system(command)
        
            # verify accuracy of new model
            command = self.bindir + "pocketsphinx_batch -adcin yes -cepdir " + current_pwd + " -cepext .wav -ctl " + current_pwd + "/test.fileids -lm " + self.inst_dir + self.language + "-adapt/language-model.lm.bin -dict " + self.inst_dir + self.language + "-adapt/pronounciation-dictionary.dict -hmm " + self.inst_dir + self.language + "-adapt/acoustic-model -hyp " + current_pwd + "/test-adapt.hyp"
            os.system(command)
        
            command = self.libdir + "sphinxtrain/scripts/decode/word_align.pl " + current_pwd + "/test.transcription " + current_pwd + "/test-adapt.hyp"
            os.system(command)
            ##
        
        
       
            yes = set(['yes','y', 'ye'])
            no = set(['no','n', ''])

            #choice = ''
            if choice == '' and "linux" in sys.platform:
                print("Do you want to INSTALL the new voice model? [y/N]")
                choice = input().lower()
                #if you are not on a GNU/Linux system, you may install manually the new voice model
       
            if choice in yes:
                subprocess.call(['sudo','/bin/rm','-r', self.inst_dir + self.language + '-adapt'])
                subprocess.call(['sudo','/bin/cp','-r', current_pwd + '/' + self.language + '-adapt', self.inst_dir + self.language + '-adapt'])
                print("Installed in " + self.inst_dir + self.language + '-adapt')
                print("To use the new model just run this program with the following option: -l " + self.language + '-adapt')
            else:
                print("You can find the new model files in " + current_pwd + '/' + self.language + '-adapt')
