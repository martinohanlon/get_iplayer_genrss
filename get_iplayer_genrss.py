#!/usr/bin/env python

# import libraries
import os
import sys
import datetime
import time
import argparse

# import constants from stat library
from stat import * # ST_SIZE ST_MTIME

# format date method
def formatDate(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

# get the item/@type based on file extension
def getItemType(fileExtension):
    if fileExtension == "aac":
         mediaType = "audio/mp4"
    elif fileExtension == "m4a":
         mediaType = "audio/mp4"
    elif fileExtension == "mp4":
         mediaType = "video/mp4" 
    else:
         mediaType = "audio/mpeg" 
    return mediaType

# encode xml escape characters
def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text

# get_iplayer download_history fields
dhPID = 0
dhName = 1
dhEpisode = 2
dhType = 3
dhTimeAdded = 4
dhMode = 5
dhFileName = 6
dhVersions = 7
dhDuration = 8
dhDescription = 9
dhChannel = 10
dhCategories = 11
dhThumbnail = 12
dhGuidance = 13
dhWeb = 14
dhEpisodeNum = 15
dhSeriesNum = 16

# command line options
parser = argparse.ArgumentParser(description="Create RSS feed (podcast)  from get_iplayer's download history")
parser.add_argument("outputRSSFilename", help="The location to output the RSS file")
parser.add_argument("numberOfPastDays", help="The number of days in the past to include in the RSS")
parser.add_argument("rssTitle", help="Title of the rss feed")
parser.add_argument("rssDescription", help="Description of the rss feed")
parser.add_argument("rssHTMLPageURL", help="URL to the rss feed HTML page www.example.com/rss/index.html")
parser.add_argument("rssDownloadsURL", help="URL where the downloads will be located, wwww.example.com/rss/downloads/")
parser.add_argument("rssImageURL", help="URL of the rss image")
parser.add_argument("rssTTL", help="Time to live in minutes for the rss feed e.g 60 minutes")
parser.add_argument("rssWebMaster", help="RSS feed web master contact details e.g. me@me.com")
parser.add_argument("-a", "--altDownloadDir", help="An alternative download directory as apposed to that in the download_history, useful if the downloads have been copied to another location; specify multiple by seperating with a comma /path1,path2")
parser.add_argument("-m", "--mediaType", help="Filter by get_iplayer media type (tv,radio) ; specify multile values by seperating with a comma tv,radio")
parser.add_argument("-v", "--verbose", action="store_true", help="Output verbose statements")
args = parser.parse_args()

if args.verbose:
	print "Parameters:"
	print "  OutputRSSFilename - " + args.outputRSSFilename
	print "  NumberOfPastDays - " + args.numberOfPastDays
	print "  RssTitle - " + args.rssTitle
	print "  RssDecription - " + args.rssDescription
	print "  RssHTMLPageURL - " + args.rssHTMLPageURL
	print "  RssDownloadsURL - " + args.rssDownloadsURL
	print "  RssImageURL - " + args.rssImageURL
	print "  RssTTL - " + args.rssTTL
	print "  RssWebMaster = " + args.rssWebMaster
	if args.altDownloadDir != None: print "  AltDownloadDir = " + args.altDownloadDir
	if args.mediaType != None: print "  MediaType = " + args.mediaType


# podcast values
# the podcast name
rssTitle = args.rssTitle
# the podcast description
rssDescription = args.rssDescription
# the url of the folder where the items will be stored
rssItemURL = args.rssDownloadsURL
# the url to the podcast html file
rssLink = args.rssHTMLPageURL
# the url to the podcast image
rssImageUrl = args.rssImageURL
# the time to live (in minutes)
rssTtl = args.rssTTL
# contact details of the web master
rssWebMaster = args.rssWebMaster

# get_iplayer download history file location
get_iplayerDownloadHistoryFile = os.getenv("HOME") + "/.get_iplayer/download_history"
if args.verbose: print "Using get_iplayer download history file = " + get_iplayerDownloadHistoryFile 

# - output RSS filename
outputFilename = args.outputRSSFilename

# - number of days in the past
numberOfDays = 30
now = datetime.datetime.now()
fromDate = now-datetime.timedelta(days=numberOfDays)

# Main program

# open get_iplayer download history and read into list
GIPHistoryFile = open(get_iplayerDownloadHistoryFile) 
downloadHistory = GIPHistoryFile.readlines() 
GIPHistoryFile.close()

# open rss file
outputFile = open(outputFilename, "w")

# write rss header
outputFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" + "\n")
outputFile.write("<rss version=\"2.0\">" + "\n")
outputFile.write("<channel>\n")
outputFile.write("<title>" + rssTitle + "</title>\n")
outputFile.write("<description>" + rssDescription + "</description>\n")
outputFile.write("<link>" + rssLink + "</link>\n")
outputFile.write("<ttl>" + rssTtl + "</ttl>\n")
outputFile.write("<image><url>" + rssImageUrl + "</url><title>" + rssTitle + "</title><link>" + rssLink +"</link></image>\n")
outputFile.write("<copyright>www.stuffaboutcode.com (2012)</copyright>\n")
outputFile.write("<lastBuildDate>" + formatDate(now) + "</lastBuildDate>\n")
outputFile.write("<pubDate>" + formatDate(now) + "</pubDate>\n")
outputFile.write("<webMaster>" + rssWebMaster + "</webMaster>\n")

# go through the download history 
for download in downloadHistory:
	
	# split download history into data
	downloadData = download.split("|")

	# apply rules to see whether download should be included?
	includeDownload = False

	# get the full path of the file
        fullPath = downloadData[dhFileName]

	# Check whether this download should be included due to the date range
	downloadDate = datetime.datetime.fromtimestamp(int(downloadData[dhTimeAdded]))
	if downloadDate > fromDate:
		includeDownload = True
	#end if

	if includeDownload == True:
		# check to see its the right media type
		if args.mediaType != None:
			# media types
			mediaTypes = args.mediaType.split(",")
			foundMediaType = False
			for mediaType in mediaTypes: 
				if mediaType == downloadData[dhType]: foundMediaType = True
			if foundMediaType == False : includeDownload = False
		# end if
	#end if 

	if includeDownload == True:
		# Check to see whether the file exists

		# process the file path
		fullPathData = fullPath.split("/")
		# find the file name
		fileName = fullPathData[len(fullPathData)-1]
		# split the file based on "."
		fileNameBits = fileName.split(".")
		# get the file extension
		fileExtension = fileNameBits[len(fileNameBits)-1]

		# Work out whether a sub directory was used as part of the download and add it to the download
		if len(fullPathData) > 1:
			subFolder = fullPathData[len(fullPathData)-2]
			if subFolder == downloadData[dhName].replace(" ", "_").replace(":", "").replace("'", ""):
				fileName = subFolder + "/" + fileName
			#end if
		#end if

		# try and find the file
		if os.path.exists(fullPath) == False:
			includeDownload = False
			# is there is an alternative download dir
			if args.altDownloadDir != None:
				# alt download directories
				altDownloadDirs = args.altDownloadDir.split(",")

				for altDownloadDir in altDownloadDirs:
					if len(altDownloadDir) > 0:
						# tidy up parameter
						if altDownloadDir[-1:] != "/": altDownloadDir = altDownloadDir + "/"
						altFullPath = altDownloadDir + fileName
						if os.path.exists(altFullPath) == True: 
							fullPath = altFullPath
							includeDownload = True
					#end if
				#end for
			# end if
		else:
			includeDownload = True
		#end if
		if args.verbose and includeDownload == False: print "Warning: file '" + fullPath + "' in download_history doesnt exist in download location or alternatives"
	#end if	

	if includeDownload == True:

		# get the stats for the file
		fileStat = os.stat(fullPath)

        	# write rss item
        	outputFile.write("<item>\n")
      		outputFile.write("<title>" + encodeXMLText(downloadData[dhName] + " " + downloadData[dhEpisode]) + "</title>\n")
		outputFile.write("<description>" + encodeXMLText(downloadData[dhDescription]) + "</description>\n")
		outputFile.write("<link>" + rssItemURL + fileName + "</link>\n")
		outputFile.write("<guid>" + rssItemURL + fileName + "</guid>\n")
		outputFile.write("<pubDate>" + formatDate(datetime.datetime.fromtimestamp(int(downloadData[dhTimeAdded]))) + "</pubDate>\n")
        	outputFile.write("<enclosure url=\"" + rssItemURL + fileName + "\" length=\"" + str(fileStat[ST_SIZE]) + "\" type=\"" + getItemType(fileNameBits[len(fileNameBits)-1]) + "\" />\n")
		outputFile.write("</item>\n")
	#end if

#end for loop

# write rss footer
outputFile.write("</channel>\n")
outputFile.write("</rss>")
outputFile.close()
print "RSS/podcast create : " + outputFilename
