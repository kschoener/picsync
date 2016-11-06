import sys
import os
from pydub import AudioSegment
import random
import subprocess

#echo nest -- through spotify

songpath = None
picpaths = None

fastest = False
'''
*TODO:
rewrite it to find the locations where it is between the threshold
then use greedy stay ahead algo to fill out the song
'''

'''
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
def main():
    initialize()

    #if there are two channels, the even values are left channel and odd are the right in the array of samples
    sound = AudioSegment.from_file(songpath, format="mp3")
    (songTimeSeconds, samples, pointsPerMillisecond, sizeOfSamp) = soundValues(sound)

    numberOfPictures = len(picpaths)

    minDisplayTime = 1000 #milliseconds
    # minDisplayTime = (songTimeSeconds*1000)/(numberOfPictures*1.5)
    #prefer to show all pictures and not the whole song than the whole song and not all pics
    maxDisplayTime = 5000 #5 seconds hard maximum

    loudest = max(samples)
    print("The loudest is: "+str(loudest))
    #quietest will be (-1 * loudest)
    print("the number of milliseconds is: "+str(pointsPerMillisecond*sizeOfSamp))

    picInsertionsSeconds = changeLogic(loudest, minDisplayTime, maxDisplayTime,
        numberOfPictures, songTimeSeconds, samples, pointsPerMillisecond
    )

    myPath = os.path.dirname(os.path.realpath(__file__))
    outPath = "tempoutput/"

    setUpPictureVideos(myPath, outPath, picInsertionsSeconds, maxDisplayTime)


    # put all of the little picture videos together into one video
    concatCommand = [FFMPEG_BIN, "-y", "-auto_convert", "1", "-f", "concat", "-i", myPath+"/"+outPath+"input.txt",
        "-i", "/"+os.path.relpath(songpath, "/"), "-vcodec", "copy", "-acodec", "copy", myPath+"/finalVideoNoAudio.mp4"]
    print("\n\n\nCommand: "+str(concatCommand))
    (subprocess.Popen(concatCommand, cwd=myPath)).wait()

    # ffmpeg -i finalVideoNoAudio.mp4 -i song.mp3 -vcodec copy -acodec copy -shortest finalWithAudio.mp4
    # mergeCommand = [FFMPEG_BIN, "-i", myPath+"/finalVideoNoAudio.mp4", "-i", myPath+"/"+songpath, "-vcodec", "copy",
    #     "-acodec", "copy", "-shortest", myPath+"/video.mp4"]
    # add the music to the video
    mergeCommand = [FFMPEG_BIN, "-y", "-i", myPath+"/finalVideoNoAudio.mp4", "-i", "/"+os.path.relpath(songpath, "/"),
        "-vcodec", "copy", "-c:a", "aac", "-strict", "experimental",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", os.path.join(os.getcwd(),"video.mp4")]
    print("\n\n\nCommand: "+str(mergeCommand))
    (subprocess.Popen(mergeCommand, cwd=myPath)).wait()

    #ffmpeg -i input_file.mp4 -acodec copy -vcodec copy -f mov output_file.mov
    # convert the mp4 to mov for viewing on mac
    toMovCommand = [FFMPEG_BIN, "-y", "-i", os.path.join(os.getcwd(),"video.mp4"),
        "-acodec", "copy", "-vcodec", "copy", "-f", "mov", os.path.join(os.getcwd(),"video.mov")]
    print("\n\n\nCommand: "+str(toMovCommand))
    (subprocess.Popen(toMovCommand, cwd=myPath)).wait()

    # remove all temp files, only keep video.mov
    os.remove(myPath+"/finalVideoNoAudio.mp4")
    # os.remove(os.path.join(os.getcwd(),"video.mp4"))
    for item in os.listdir(myPath+"/"+outPath):
        os.remove(myPath+"/"+outPath+item)
#enddef main



def initialize():
    global songpath
    global picpaths
    global fastest
    picpaths = []
    #python3 picsync.py path/to/pics path/to/song.mp3
    for item in os.listdir(sys.argv[1]):
        if(os.path.isfile(os.path.join(sys.argv[1],item)) and str(item).endswith('.JPG')):
            picpaths.append(str(os.path.join(sys.argv[1],item)))
        #endif
    #endfor
    print("pic paths: "+str(picpaths))
    random.shuffle(picpaths)
    print("after shuffle: "+str(picpaths))
    songpath = sys.argv[2]

    fastest = "fastest" in sys.argv[1:]
#enddef initialize



def soundValues(sound):
    print("Number of channels: "+str(sound.channels))

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

    return (songTimeSeconds, samples, pointsPerMillisecond, len(samples))
#enddef soundValues



def changeLogic(loudest, minDisplayTime, maxDisplayTime,
    numberOfPictures, songTimeSeconds, samples, pointsPerMillisecond):
    picInsertions = [0]
    minVol = loudest
    while(len(picInsertions) < numberOfPictures and picInsertions[-1] <= songTimeSeconds*1000):# and minDisplayTime > 100):
        picInsertions = []
        picInsertions.append(0)
        minVol /= 1.1
        i = 0
        for val in samples:
            currentTimeInMilli = float(i / pointsPerMillisecond)
            if((val >= minVol and (currentTimeInMilli-picInsertions[-1]) >= minDisplayTime) or currentTimeInMilli-picInsertions[-1] >= maxDisplayTime):
                picInsertions.append(currentTimeInMilli)
            #endif
            if(len(picInsertions) >= numberOfPictures):
                break
            i += 1
        #endfor
        # minDisplayTime /= 2
        print("Insert times at end of loop = "+str(picInsertions))
    #endwhile

    print("\n\nFinal insertion points are: "+str(picInsertions))

    picInsertionsSeconds = [float(x/1000) for x in picInsertions]
    print("\n\nInsertion points in seconds: "+str(picInsertionsSeconds))
    return picInsertionsSeconds
#enddef changeLogic



def setUpPictureVideos(myPath, outPath, picInsertionsSeconds, maxDisplayTime):
    try:
        os.mkdir(myPath+"/"+outPath)
    except:
        print(outPath+" already created!")

    ppIndex = 0
    writeString = ''
    for j in range(len(picInsertionsSeconds)):
        duration = None
        if(j == len(picInsertionsSeconds)-1):
            duration = maxDisplayTime/1000
        else:
            duration = picInsertionsSeconds[j+1]-picInsertionsSeconds[j]
        #endif
        path = "/"+os.path.relpath(picpaths[ppIndex], "/")

        name = str(path.split('.')[0].split('/')[-1])

        tempOutPath = myPath + "/" + outPath + name + ".mp4"
        #ffmpeg -framerate 1/3 -i DSC_0251.JPG -c:v libx264 -acodec copy -vcodec copy DSC_0251.mp4
        #ffmpeg -loop_input -i test.jpg -t 10 test.mp4
        command = None
        if(not fastest):
            # fairly slow -- very small file size though -- 29.2MB for 75s (with 5mb photos)
            command = [FFMPEG_BIN, "-y", "-loop", "1", "-i", path,
                "-t", str(duration), "-c:v", "libx264", "-preset", "medium",
                "-vf", "scale=-2:1440,format=yuv420p", "-c:a", "libfdk_aac", tempOutPath]
        else:
            # stupid fast - normal size (HUGE) --  takes a lot of space -- 8.2GB for 75s (with 5mb photos)
            command = [FFMPEG_BIN, "-y", "-loop", "1", "-i", path, "-t",
                str(duration), "-c:v", "libx264", "-codec", "copy", tempOutPath]

        try:
            print("\n\n\ncommand called: "+str(command))
            (subprocess.Popen(command, cwd=myPath)).wait()
            writeString += ("file '"+name+".mp4"+"'\n")

            # command = [FFMPEG_BIN, "-y", "-i", tempOutPath, "-t", str(duration), "-codec", "copy", tempOutPath]
            # (subprocess.Popen(command, cwd=myPath)).wait()
        except:
            print("Couldn't complete command")
        ppIndex += 1
    #endfor

    #save filenames to text file for concat later
    print("\n\n\n WriteString = "+writeString)
    with open(myPath+"/"+outPath+"input.txt", "w") as handle:
        handle.write(writeString)
    #end with
    handle.close()
#enddef setUpPictureVideos
























if __name__ == '__main__':
    main()
