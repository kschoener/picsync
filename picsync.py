import sys
import os
from pydub import AudioSegment
import random
import subprocess

songpath = None
picpaths = None

'''
rewrite it to find the locations where it is between the threshold

then use greedy stay ahead algo to fill out the song
'''

'''
this works for multiple pictures -- stops either when we're out of pictures or the song ends

ffmpeg -framerate 2 -pattern_type glob -i 'pics/small/*.JPG' -i songs/Bashy.mp3 -c:v libx264 -c:a aac -strict experimental -b:a 192k -shortest -acodec copy -vcodec copy -f mov output_file.mov

mp4 to mov:
ffmpeg -i input_file.mp4 -acodec copy -vcodec copy -f mov output_file.mov
********
to make a mp4 out of image:
ffmpeg -framerate 1/3 -i DSC_0251.JPG -c:v libx264 -acodec copy -vcodec copy DSC_0251.mp4
this is 3 seconds, decimals are allowed

then add all pictures to a file name input.txt in the format:
file 'path/to/file'

then concat the videos together:
ffmpeg -f concat -i input.txt -codec copy finalVideoNoAudio.mp4

finally add the song to finalVideoNoAudio.mp4
ffmpeg -i finalVideoNoAudio.mp4 -i song.mp3 -vcodec copy -acodec copy -shortest finalWithAudio.mp4
'''
FFMPEG_BIN = "/usr/local/bin/ffmpeg"

#start with one audio file as input, and a folder of pictures
# min framerate = 2 (image displayed for 1/2 of a second)
def main():
    global songpath
    global picpaths
    songpath = []
    picpaths = []
    #python3 picsync.py path/to/pics path/to/song.mp3
    for item in os.listdir(sys.argv[1]):
        if(os.path.isfile(os.path.join(sys.argv[1],item)) and str(item).endswith('.JPG')):
            picpaths.append(str(os.path.join(sys.argv[1],item)))
        #endif
    #endfor
    print("pic paths: "+str(picpaths))
    # random.shuffle(picpaths)
    print("after shuffle: "+str(picpaths))

    #if there are two channels, the even values are left channel and odd are the right in the array of samples
    songpath = sys.argv[2]
    sound = AudioSegment.from_file(songpath, format="mp3")

    channels = sound.channels
    print("Number of channels: "+str(channels))

    print("Sample width (1 == 8 bits, 2 == 16bits, etc): "+str(sound.sample_width))
    print("Frame rate: "+str(sound.frame_rate))

    songTimeSeconds = sound.duration_seconds
    print("Duration in seconds: "+str(songTimeSeconds))

    print("Frame count in 400ms of sound: "+str(sound.frame_count(ms=400)))
    # print("Raw data: "+str(sound.raw_data))
    # print("Array of samples: "+str(sound.get_array_of_samples()))
    samples = list(sound.get_array_of_samples())
    print("Length of sample array = "+str(len(samples)))

    pointsPerMillisecond = float(len(samples)/(songTimeSeconds*1000))
    print("Data points per millisecond: "+str(pointsPerMillisecond))

    sizeOfSamp = len(samples)

    numberOfPictures = len(picpaths)
    # minDisplayTime = float(0.5) #30 seconds, 1/2 minute
    # minDisplayTime = 400 #milliseconds
    minDisplayTime = (songTimeSeconds*1000)/(numberOfPictures*1.5)
    #prefer to show all pictures and not the whole song than the whole song and not all pics
    maxDisplayTime = 5000 #5 seconds hard maximum
    if(minDisplayTime > 1000):
        minDisplayTime = 1000
    #endif

    loudest = max(samples)
    print("The loudest is: "+str(loudest))
    #quietest will be (-1 * loudest)

    print("the number of milliseconds is: "+str(pointsPerMillisecond*sizeOfSamp))

    picInsertions = []
    minVol = loudest
    while(len(picInsertions) < numberOfPictures):
        picInsertions = [0]
        minVol /= 1.25
        i = 0
        for val in samples:
            currentTimeInMilli = float(i / pointsPerMillisecond)
            if((currentTimeInMilli-picInsertions[-1]) >= minDisplayTime and val >= minVol):
                picInsertions.append(currentTimeInMilli)
            #endif
            if(len(picInsertions) >= numberOfPictures or currentTimeInMilli-picInsertions[-1] >= maxDisplayTime):
                break
            i += 1
        #endfor
        minDisplayTime /= 2
        print("Insert times at end of loop = "+str(picInsertions))
    #endwhile

    print("\n\nFinal insertion points are: "+str(picInsertions))

    picInsertionsSeconds = [float(x/1000) for x in picInsertions]
    print("\n\nInsertion points in seconds: "+str(picInsertionsSeconds))

    myPath = os.path.dirname(os.path.realpath(__file__))

    outPath = "tempoutput/"
    ppIndex = 0
    writeString = ''
    for j in range(len(picInsertionsSeconds)):
        duration = None
        if(j == len(picInsertionsSeconds)-1):
            duration = maxDisplayTime/1000
        else:
            duration = picInsertionsSeconds[j+1]-picInsertionsSeconds[j]
        #endif
        path = picpaths[ppIndex]

        name = str(path.split('.')[0].split('/')[-1])

        tempOutPath = myPath + "/" + outPath + name + ".mp4"
        # tempOutPath = outPath + name + ".mp4"
        #ffmpeg -framerate 1/3 -i DSC_0251.JPG -c:v libx264 -acodec copy -vcodec copy DSC_0251.mp4
        command = [FFMPEG_BIN, "-framerate", "1/"+str(duration)[:4], "-i", myPath+"/"+path,
            "-c:v", "libx264", "-acodec", "copy", "-vcodec", "copy", tempOutPath]
        try:
            print("\n\n\ncommand called: "+str(command))
            # subprocess.call(command)
            pipe = subprocess.Popen(command, cwd=myPath)
            pipe.wait()
            # handle.write("file '"+name+".mp4"+"'\n")
            # writeString += ("file '"+myPath+"/"+name+".mp4"+"'\n")
            writeString += ("file '"+name+".mp4"+"'\n")
        except:
            print("Couldn't complete command")
        ppIndex += 1
    #endfor
    path = picpaths[-1]
    name = "filler"
    tempOutPath = myPath + "/" + outPath + name + ".mp4"
    # tempOutPath = outPath + name + ".mp4"
    #ffmpeg -framerate 1/3 -i DSC_0251.JPG -c:v libx264 -acodec copy -vcodec copy DSC_0251.mp4
    command = [FFMPEG_BIN, "-framerate", "1/"+str(.001), "-i", myPath+"/"+path,
        "-c:v", "libx264", "-acodec", "copy", "-vcodec", "copy", tempOutPath]
    try:
        print("\n\n\ncommand called: "+str(command))
        # subprocess.call(command)
        pipe = subprocess.Popen(command, cwd=myPath)
        pipe.wait()
        # handle.write("file '"+name+".mp4"+"'\n")
        # writeString += ("file '"+myPath+"/"+name+".mp4"+"'\n")
        writeString += ("file '"+name+".mp4"+"'\n")
    except:
        print("Couldn't complete command")
    print("\n\n\n WriteString = "+writeString)

    with open(outPath+"input.txt", "w") as handle:
        handle.write(writeString)
    #end with
    handle.close()
    #ffmpeg -f concat -i input.txt -codec copy finalVideoNoAudio.mp4
    concatCommand = [FFMPEG_BIN, "-f", "concat", "-i", myPath+"/"+outPath+"input.txt", "-codec", "copy", myPath+"/finalVideoNoAudio.mp4"]
    # subprocess.call(concatCommand)
    (subprocess.Popen(concatCommand, cwd=myPath)).wait()

    #ffmpeg -i finalVideoNoAudio.mp4 -i song.mp3 -vcodec copy -acodec copy -shortest finalWithAudio.mp4
    mergeCommand = [FFMPEG_BIN, "-i", myPath+"/finalVideoNoAudio.mp4", "-i", myPath+"/"+songpath, "-vcodec", "copy",
        "-acodec", "copy", "-shortest", myPath+"/video.mp4"]
    # subprocess.call(mergeCommand)
    (subprocess.Popen(mergeCommand, cwd=myPath)).wait()

    #ffmpeg -i input_file.mp4 -acodec copy -vcodec copy -f mov output_file.mov
    toMovCommand = [FFMPEG_BIN, "-i", myPath+"/video.mp4", "-acodec", "copy", "-vcodec", "copy", "-f", "mov", myPath+"/video.mov"]
    # subprocess.call(toMovCommand)
    (subprocess.Popen(toMovCommand, cwd=myPath)).wait()

    # subprocess.call("open", "video.mov")
    # subprocess.Popen(["open", myPath+"/video.mov"], cwd=myPath)
#enddef main



































if __name__ == '__main__':
    main()
