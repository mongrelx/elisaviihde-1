# Elisa Viihde API Python implementation usage demo
# Creates vlc xspf playlist file containing all recordings
# (first page only, 10 per page) from all folders recursively

import getopt, sys, cgi, datetime, getpass, elisaviihde
import xml.etree.ElementTree as et

def getxmlheader():
  return """<?xml version="1.0" encoding="UTF-8"?>
            <playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
            <title>Elisa Viihde</title><trackList>
         """

def getxmlfooter():
  return """</trackList><extension application="http://www.videolan.org/vlc/playlist/0"><vlc:item tid="0"/>
            </extension></playlist>
         """

def getxmltrack(folder, recording, uri):
  return """<track><location>%s</location><title>%s</title><creator>%s</creator>
            <album>%s</album><annotation>%s</annotation><duration>%d</duration>
            <image>%s</image>
            <extension application="http://www.videolan.org/vlc/playlist/0"><vlc:id>%d</vlc:id>
            <vlc:option>network-caching=1000</vlc:option></extension></track>
         """ % (cgi.escape(uri),
                cgi.escape(recording["name"]),
                cgi.escape(datetime.datetime.fromtimestamp(recording["startTimeUTC"]/1000).strftime('%Y-%m-%d %H:%M:%S')
                             + " " + recording["serviceName"]),
                cgi.escape(folder["name"]) if folder and "name" in folder else "",
                cgi.escape(recording["description"]) if "description" in recording else "",
                ((recording["endTimeUTC"]) - (recording["startTimeUTC"])),
                cgi.escape(recording["thumbnail"]) if "thumbnail" in recording else "",
                recording["programId"])

def main():
  # Parse command line args
  if len(sys.argv[1:]) < 2:
    print "ERROR: Usage:", sys.argv[0], "[-u username] [-f outputfile]" 
    sys.exit(2)
  try:
    opts, args = getopt.getopt(sys.argv[1:], "u:f:v", ["username", "outputfile"])
  except getopt.GetoptError as err:
    print "ERROR:", str(err)
    sys.exit(2)
  
  # Init args
  username = ""
  outputfile = "playlist.xspf"
  verbose = False
  
  # Read arg data
  for o, a in opts:
    if o == "-v":
      verbose = True
    elif o in ("-u", "--username"):
      username = a
    elif o in ("-f", "--outputfile"):
      outputfile = a
    else:
      assert False, "unhandled option"
  
  # Ask password securely on command line
  password = getpass.getpass('Password: ')
  
  # Init elisa session
  try:
    elisa = elisaviihde.elisaviihde(verbose)
  except Exception as exp:
    print "ERROR: Could not create elisa session"
    sys.exit(1)
  
  # Login
  try:
    elisa.login(username, password)
  except Exception as exp:
    print "ERROR: Login failed, check username and password"
    sys.exit(1)
  
  filehandle = open(outputfile, 'w')
  filehandle.write(getxmlheader())
  
  # Read top directory and persist to a file
  recordings = elisa.getrecordings(0, 0)
  for recording in recordings:
    streamuri = elisa.getstreamuri(recording["programId"])
    filehandle.write(getxmltrack(None, recording, streamuri).encode('utf8'))

  # Walk sub-directories recursively and persist to a file
  folders = elisa.getfolders()
  for folder in folders:
    recordings = elisa.getrecordings(folder["id"], 0)
    for recording in recordings:
      streamuri = elisa.getstreamuri(recording["programId"])
      filehandle.write(getxmltrack(folder, recording, streamuri).encode('utf8'))
  
  filehandle.write(getxmlfooter())
  filehandle.close()
  
  # Close session
  elisa.close()

if __name__ == "__main__":
  main()

