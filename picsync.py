import sys

if __name__ == '__main__':
    main()

songpaths = None
picpaths = None
#-s for songs, -p for pictures
# def main():
#     global songpaths
#     global picpaths
#     songpaths = []
#     picpaths = []
#     songTag = '-s'
#     picTag = '-p'
#     if(songTag in sys.argv[1:] and picTag in sys.argv[1:]):
#         songIndex = sys.argv[1:].index(songTag)
#         picIndex = sys.argv[1:].index(picTag)
#         start = songIndex if songIndex < picIndex else picIndex
#         current = songTag if songIndex < picIndex else picTag
#         for i in range(len(sys.argv[start:])):
#             if(sys.argv[i] == songTag or sys.argv[i] == picTag):
#                 current = sys.argv[i]
#                 continue
#             elif(current == songTag):
#                 songpaths.append(sys.argv[i])
#             elif(current == picTag):
#                 picpaths.append(sys.argv[i])
#             #endif
#         #endfor
#     else:
#         print('Error, must use %s and %s to define the songs and pictures')
#     #endif
#
# #enddf main

#start with one audio file as input, and a folder of pictures
def main():
    pass

#enddef main
