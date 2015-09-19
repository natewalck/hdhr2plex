#-------------------------------------------------------------------------------
# This is an automated python script to parse out the metadata from MPEG-TS
# files created by the HDHomeRun DVR record engine.
#-------------------------------------------------------------------------------
import getpass
import os
import platform
import logging
import sys
import time
from time import strftime
import hdhr_tsparser
import plextools
import hdhr_md
import scripttools

HDHR_TS_METADATA_PID = 0x1FFA

# QNAP NAS adds thumbnails with it's media scanner - so will skip that dir
# TODO: Make skip dirs configurable
def get_shows_in_dir(path):
    return [os.path.join(path,f) for f in os.listdir(path) \
           if (not ".@__thumb" in f) & os.path.isdir(os.path.join(path,f))]

def get_episodes_in_show(path):
    return [os.path.join(path,f) for f in os.listdir(path) \
           if (not os.path.islink(os.path.join(path,f))) & os.path.isfile(os.path.join(path,f)) \
              & f.endswith('.mpg')]

def parse_file_for_data(filename):
    parser = hdhr_tsparser.TSParser(filename)
    payloads = 0
    tempMD = []
    pid_found = False
    for b in parser.read_next_section():
        payloads+=1
        header = parser.parse_ts_header(b)
        if parser.header_contains_pid(header,HDHR_TS_METADATA_PID):
            # found a matching program ID - need to reconstruct the payload
            tempMD += parser.extract_payload(b)
            pid_found = True
        else:
            # Didn't find HDHR MetaData PID.. so break if we found already
            if pid_found == True:
                break
    return parser.extract_metadata(tempMD)

def extract_metadata(metadata):
    md = hdhr_md.HDHomeRunMD(metadata)
    md.print_metaData()

    show = md.extract_show()
    epNumber = md.extract_epNumber()
    epAirDate = md.extract_epAirDate()
    epTitle = md.extract_epTitle()
    season = md.get_season_string(show,epNumber,epAirDate,epTitle)
    episode = md.get_episode_string(show,epNumber,epAirDate,epTitle)

    logging.info('=== Extracted: show [' + show + '] Season [' + season + '] Episode: [' + episode +']')
    return {'show':show, 'season':season, 'epnum':episode, 'eptitle':epTitle}

def fix_filename(show, season, episode, epTitle):
    if epTitle == '':
        return show + '-S' + season + 'E' + episode + '.mpg'
    else:
        return show + '-S' + season + 'E' + episode + '-' + epTitle + '.mpg'

def is_already_fixed(filename):
    # Checking file is form of    <show>-S<season number>E<episode number>[- title]
    # where title is optional, but must have show, season and episode numbers
    show_file, file_ext = os.path.splitext(filename)
    base_name = os.path.basename(show_file)
    parts = base_name.split('-')
    if len(parts) >= 2:
        logging.debug(base_name + 'contains 2 or greater parts, might be fixed')
        if parts[1][0] == 'S':
            logging.debug(base_name + 'Contains an S indicator for season - looking good')
            if parts[1][3] == 'E':
                logging.debug(base_name + 'Contains an E indicator for episode - looking like it is fixed already')
                return True
    return False

def rename_episode(filename, show, season, episode, epTitle):
    if not epTitle:
        epTitle = ''
    logging.info('Renaming '+ filename + ' to ' + show + '-S' + season + 'E' + episode + '-' + epTitle)
    base_name = os.path.basename(filename)
    # shouldn't need to recheck, but may as well..
    if base_name == fix_filename(show, season, episode, epTitle):
        logging.warn('Filename '+ base_name + ' already fixed')
    else:
        dir_name = os.path.dirname(filename)
        new_name = os.path.join(dir_name, fix_filename(show, season, episode, epTitle))
        logging.debug('replacing ' + filename + ' with ' + new_name)
        os.rename(filename,new_name)

if __name__ == "__main__":
    files = []
    episodes = []
    tools = scripttools.ScriptTools()
    if tools.isInteractive():
        print 'Interactive mode not supported at this time... exiting...'
        sys.exit(0)

    logging.info('------------------------------------------------------------')
    logging.info('-                  HDHR TS MetaData Tool                   -')
    logging.info('-                   '+strftime("%Y-%m-%d %H:%M:%S")+'                    -')
    logging.info('------------------------------------------------------------')
    shows = get_shows_in_dir(tools.get_dvr_path())
    for show in shows:
        episodes = get_episodes_in_show(show)
        files.extend(episodes)
    
    for f in files:
        if is_already_fixed(f):
            logging.info('SKIPPING: Already fixed ' + f)
            continue
        metaData = []
        logging.info('-----------------------------------------------')
        logging.info('Parsing: ' + f)
        metaData = parse_file_for_data(f)
        md = extract_metadata(metaData)
        rename_episode(f,md['show'],md['season'],md['epnum'],md['eptitle'])
        logging.info('Completed for : ' + f)

    logging.info('------------------------------------------------------------')
    logging.info('-              HDHR TS MetaData Tool Complete              -')
    logging.info('-                   '+strftime("%Y-%m-%d %H:%M:%S")+'                    -')
    logging.info('------------------------------------------------------------')
