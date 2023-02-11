#!/usr/bin/env python3.11

# import libraries
import argparse
import datetime
import json
import os
import sys
import time
import urllib.request

# import constants from stat library
from stat import * # ST_SIZE ST_MTIME

EXPECTED_SEPARATOR_COUNT = 17
FIELD_SEPARATOR = '|'

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

default_histfile = os.getenv("HOME") + "/.get_iplayer/download_history"

# ------------------------------------------------------------------------------
# handle command line options

def get_args():
    parser = argparse.ArgumentParser(description="Create RSS feed (podcast)  from get_iplayer's download history")
    parser.add_argument("outputRSSFilename", help="The location to output the RSS file")
    parser.add_argument("numberOfPastDays", type=int, help="The number of days in the past to include in the RSS")
    parser.add_argument("rssTitle", help="Title of the rss feed")
    parser.add_argument("rssDescription", help="Description of the rss feed")
    parser.add_argument("rssHTMLPageURL", help="URL to the rss feed HTML page www.example.com/rss/index.html")
    parser.add_argument("rssDownloadsURL", help="URL where the downloads will be located, wwww.example.com/rss/downloads/")
    parser.add_argument("rssImageURL", help="URL of the rss image")
    parser.add_argument("rssTTL", help="Time to live in minutes for the rss feed e.g 60 minutes")
    parser.add_argument("rssWebMaster", help="RSS feed web master contact details e.g. me@me.com")
    parser.add_argument("-a", "--altDownloadDir", help="An alternative download directory as apposed to that in the download_history, useful if the downloads have been copied to another location; specify multiple by seperating with a comma /path1,path2")
    parser.add_argument( "--force-audio-mp3", action='store_true', help="Audio has been externally converted to MP3")
    parser.add_argument("-f", "--histfile", help=f"iplayer history file (default: {default_histfile})", default=default_histfile)
    parser.add_argument("-j", "--json", action='store_true', help=f"Retrieve extended (better) data from the BBC website. The get_iplayer history data is limited and the date downloaded isn't necessarily the date of first broadcast.")
    parser.add_argument("-m", "--mediaType", help="Filter by get_iplayer media type (tv,radio) ; specify multile values by seperating with a comma tv,radio")
    parser.add_argument("-v", "--verbose", action="store_true", help="Output verbose statements")
    args = parser.parse_args()

    if args.verbose:
        print("Parameters:")
        print(f"  OutputRSSFilename: {args.outputRSSFilename}")
        print(f"  NumberOfPastDays: {args.numberOfPastDays}")
        print(f"  RssTitle: {args.rssTitle}")
        print(f"  RssDecription: {args.rssDescription}")
        print(f"  RssHTMLPageURL: {args.rssHTMLPageURL}")
        print(f"  RssDownloadsURL: {args.rssDownloadsURL}")
        print(f"  RssImageURL: {args.rssImageURL}")
        print(f"  RssTTL: {args.rssTTL}")
        print(f"  RssWebMaster: {args.rssWebMaster}")
        if args.altDownloadDir != None:
            print(f"  AltDownloadDir: {args.altDownloadDir}")
        if args.mediaType != None:
            print(f"  MediaType: {args.mediaType}")

    return args

# ------------------------------------------------------------------------------
# Convert datetime to required format

def formatDate(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

# ------------------------------------------------------------------------------
# Convert datetime from BBC to required format

def reformat_bbc_pubdate(pubdate):
    return formatDate(datetime.datetime.fromisoformat(pubdate))

# ------------------------------------------------------------------------------
# get the item/@type based on file extension

def getItemType(fileExtension, force_mp3):
    audioType = "audio/mp4"
    if force_mp3:
        audioType = "audio/mp3"
    if fileExtension == "aac":
         mediaType = audioType
    elif fileExtension == "m4a":
         mediaType = audioType
    elif fileExtension == "mp4":
         mediaType = "video/mp4"
    else:
         mediaType = "audio/mpeg"
    return mediaType

# ------------------------------------------------------------------------------
# encode xml escape characters

def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text

# ------------------------------------------------------------------------------
# retrieve programme JSON from BBC

def get_json_from_bbc(ippid):
    j = None
    url = f"https://www.bbc.co.uk/programmes/{ippid}.json"
    with urllib.request.urlopen(url, timeout=30) as response:
        j = response.read()
        if j:
            j = j.decode("utf-8")
            j = json.loads(j)
        else:
            raise Exception("Failed to retrieve JSON from '{url}' : {response.status}")
    return j

# ------------------------------------------------------------------------------
# retrieve JSON and extract and return data

def extra_data_from_bbc(ippid):
   j = get_json_from_bbc(ippid)

   title = j['programme']['long_synopsis']
   description = j['programme']['parent']['programme']['short_synopsis'] + "\n\n" + j['programme']['long_synopsis']

   # Target format: Sat, 11 Feb 2023 18:21:03 +0000
   # Retrieved format: 2022-12-30T18:15:00Z
   pubdate = j['programme']['first_broadcast_date']
   pubdate = reformat_bbc_pubdate(pubdate)

   return title, description, pubdate

# ------------------------------------------------------------------------------
# handle an individual programme download history record

def process_download(download):
    # split download history into data
    downloadData = download.split("|")

    # apply rules to see whether download should be included?
    includeDownload = False

    # get the full path of the file
    fullPath = downloadData[dhFileName]

    # munge series name from potentially inconsisent text given
    series, *subtitle = downloadData[dhName].split(':')

    # Check whether this download should be included due to the date range
    downloadDate = datetime.datetime.fromtimestamp(int(downloadData[dhTimeAdded]))
    if downloadDate >= config.fromDate:
        includeDownload = True

    if includeDownload == True:
        # check to see its the right media type
        if config.mediaType != None:
            # media types
            mediaTypes = config.mediaType.split(",")
            foundMediaType = False
            for mediaType in mediaTypes:
                if mediaType == downloadData[dhType]:
                    foundMediaType = True
            if foundMediaType == False :
                includeDownload = False

    if includeDownload == True:
        # Check to see whether the file exists

        # process the file path
        fullPathData = fullPath.split("/")

        # find the file name
        fileName = fullPathData[len(fullPathData)-1]

        # split the file based on "."
        fileNameBits = fileName.split(".")

        # get the file extension
        fileExtension = fileNameBits[-1]

        if config.force_audio_mp3 and fileExtension == "m4a":
            fileExtension = "mp3"
            fileName = fileName[0: -3] + fileExtension

        # Work out whether a sub directory was used as part of the download and add it to the download
        if len(fullPathData) > 1:
            subFolder = fullPathData[len(fullPathData)-2]
            if subFolder == downloadData[dhName].replace(" &", "").replace(" ", "_").replace(":", "").replace("'", ""):
                fileName = subFolder + "/" + fileName

        # try and find the file
        if os.path.exists(fullPath) == False:
            includeDownload = False
            # is there is an alternative download dir
            if config.altDownloadDir != None:
                # alt download directories
                altDownloadDirs = config.altDownloadDir.split(",")

                for altDownloadDir in altDownloadDirs:
                    if len(altDownloadDir) > 0:
                        # tidy up parameter
                        if altDownloadDir[-1:] != "/": altDownloadDir = altDownloadDir + "/"
                        altFullPath = altDownloadDir + fileName
                        if os.path.exists(altFullPath) == True:
                            fullPath = altFullPath
                            includeDownload = True
        else:
            includeDownload = True

        if config.verbose and includeDownload == False:
            print("Warning: file '" + fullPath + "' in download_history doesnt exist in download location or alternatives")

    if includeDownload == True:

        # get the stats for the file
        fileStat = os.stat(fullPath)

        title = None
        description = None
        pubdate = None

        # pull extra info from BBC if requested to do so
        if config.json:
            try:
                title, description, pubdate = extra_data_from_bbc(downloadData[dhPID])
            except Exception as e:
                if config.verbose:
                    print(f"Failed to retrieve JSON for {downloadData[dhPID]} : '{e}'")

        if not title:
            title = series
            if downloadData[dhSeriesNum]:
                title += f" : S{downloadData[dhSeriesNum]}"
            elif downloadData[dhEpisodeNum]:
                title += " : "
            if downloadData[dhEpisodeNum]:
                title += f"E{downloadData[dhEpisodeNum]}"
            if subtitle:
                title += f" : {subtitle}"
            if downloadData[dhEpisode]:
                title += f" : {downloadData[dhEpisode]}"
            description = downloadData[dhDescription]
            pubdate = formatDate(datetime.datetime.fromtimestamp(int(downloadData[dhTimeAdded])))

        media_url = f"{config.rssDownloadsURL}{fileName}"

        # write rss item
        text = "<item>\n"
        text += f"<title>{encodeXMLText(title)}</title>\n"
        text += f"<description>{encodeXMLText(description)}\n{downloadData[dhWeb]}</description>\n"
        text += f"<link>{media_url}</link>\n"
        text += f"<guid>{downloadData[dhPID]}</guid>\n"
        text += f"<itunes:image href=\"{downloadData[dhThumbnail]}\" />\n"
        text += f"<itunes:duration>{downloadData[dhDuration]}</itunes:duration>\n"
        text += f"<pubDate>{pubdate}</pubDate>\n"
        text += f"<enclosure url=\"{media_url}\" length=\"{str(fileStat[ST_SIZE])}\" type=\"{getItemType(fileNameBits[len(fileNameBits)-1], config.force_audio_mp3)}\" />\n"
        text += "</item>\n"

        return (series, text)

    # Not handling this episode
    return (None, None)

# ------------------------------------------------------------------------------
# Parse history data in to channels (think programme-as-series)

def get_channels(downloadHistory):
    channels={}

    prev = None

    # go through the download history
    for (i, download) in enumerate(downloadHistory):

        # Try to reconstruct malformed lines by guessing that they may have embedded newline(s)
        # Not foolproof against corner cases where field separators occur inside strings.
        # On the plus side it should self correct if a previous line was badly corrupt, but the following one is good
        if download.count('|') < EXPECTED_SEPARATOR_COUNT:
            if prev:
                download = prev + download
                # Still not enough fields?
                if download.count('|') < EXPECTED_SEPARATOR_COUNT:
                    prev = download
                    continue
            else:
                prev = download
                continue

        prev = None

        try:
            (channel, item) = process_download(download)

            if channel and item:
                if channel not in channels:
                    channels[channel]=[]
                channels[channel].append(item)

        except Exception as e:
            print(f"Gah, data buggered ({e}), skipping line {i}:\n  {download}", file=sys.stderr)

    return channels

# ------------------------------------------------------------------------------
# Main programme

config = get_args()

if config.verbose:
    print("Using get_iplayer download history file = " + config.histfile)

now = datetime.datetime.now()
config.now = formatDate(now)
config.fromDate = now - datetime.timedelta(days=config.numberOfPastDays)

# open get_iplayer download history and read into list
with open(config.histfile) as f:
    downloadHistory = f.readlines()

    channels = get_channels(downloadHistory)

    # output RSS file
    with open(config.outputRSSFilename, "w") as outputFile:

        # write rss header
        outputFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" + "\n")
        outputFile.write("<rss xmlns:itunes=\"http://www.itunes.com/dtds/podcast-1.0.dtd\" version=\"2.0\">\n")

        # cycle over channels (programmes as series)
        for channel, items in channels.items():
            # Write channel header
            outputFile.write("<channel>\n")
            outputFile.write(f"<title>{config.rssTitle} - {channel}</title>\n")
            outputFile.write(f"<description>{config.rssDescription}</description>\n")
            outputFile.write(f"<link>{config.rssHTMLPageURL}</link>\n")
            outputFile.write(f"<ttl>{config.rssTTL}</ttl>\n")
            outputFile.write(f"<image><url>{config.rssImageURL}</url><title>{config.rssTitle}</title><link>{config.rssHTMLPageURL}</link></image>\n")
            outputFile.write(f"<lastBuildDate>{config.now}</lastBuildDate>\n")
            outputFile.write(f"<pubDate>{config.now}</pubDate>\n")
            outputFile.write(f"<webMaster>{config.rssWebMaster}</webMaster>\n")

            for item in items:
                outputFile.write(item)

            outputFile.write("</channel>\n")

        # write rss footer
        outputFile.write("</rss>")

        if config.verbose:
            print("RSS/podcast created : " + config.outputRSSFilename)

# ------------------------------------------------------------------------------
