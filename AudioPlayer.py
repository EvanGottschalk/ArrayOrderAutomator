# PURPOSE - This program is for easily adding sound effects to other programs

import pathlib

from playsound import playsound

class AudioPlayer:
    def __init__(self):
        self.audio_file_location = str(pathlib.Path().absolute()) + '/_Python_SFX/'

    def playSound(self, sound_title):
        if '.mp3' in sound_title:
            sound_title = sound_title.split('.mp3')[0]
        if sound_title == 'Navi Hey' or sound_title == 'Hey':
            print('Audio : "Hey!"')
            playsound(self.audio_file_location + 'Navi Hey.mp3')
        elif sound_title == 'Navi Hey Listen' or sound_title == 'Hey Listen':
            print('Audio : "Hey! Listen"')
            playsound(self.audio_file_location + 'Navi Hey Listen.mp3')
        elif sound_title == 'Tim Allen Huh' or sound_title == 'Tim Allen' or sound_title == 'Home Improvement' or sound_title == 'Huh':
            print('Audio : "AEUHHH????"')
            playsound(self.audio_file_location + 'Tim Allen Huh.mp3')
        elif sound_title == 'Kill Bill Siren' or sound_title == 'Kill Bill Sirens' or sound_title == 'Kill Bill' or sound_title == 'Siren' or sound_title == 'Sirens':
            print('Audio : *Kill Bill Sirens*')
            playsound(self.audio_file_location + 'Kill Bill Siren.mp3')
        elif sound_title == 'Buffy Theme Song Ending Drumroll TRIMMED' or sound_title == 'Buffy Theme Song' or \
             sound_title == 'Buffy Drumroll' or sound_title == 'Buffy':
            print('Audio : *Buffy Drumroll*')
            playsound(self.audio_file_location + 'Buffy Theme Song Ending Drumroll TRIMMED.mp3')
            print('        .............grrr...argggh.................')
