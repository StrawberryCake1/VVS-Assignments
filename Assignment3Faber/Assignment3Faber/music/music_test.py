from Application.music.play import *

#set_volume(100) # quiet at 0 maximal volume at 32768
#playsong(melody[2])  # actually start playing the melody

def play(melodyNumber, volume_intensity):
    set_volume(volume_intensity)
    playsong(playsong(melody[melodyNumber]))
