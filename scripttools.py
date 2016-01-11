#-------------------------------------------------------------------------------
# Script Tools - Argument and Config File Parser
#-------------------------------------------------------------------------------
import os
import ConfigParser
import argparse
import platform
import logging

LOGLEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

hdhr_args_list = ['--config','--autodelete','--interactive','--logfile','--loglevel']

hdhr_cfg_main = 'HDHR-DVR'
hdhr_cfg_path_dvr = 'dvrpath'
hdhr_cfg_path_plex = 'plexpath'
hdhr_cfg_skip_shows = 'skipshows'
hdhr_cfg_loglevel = 'loglevel'
hdhr_cfg_logfile = 'logfile'
hdhr_cfg_autodelete = 'autodelete'
hdhr_cfg_renameDir = 'renamedir'
hdhr_cfg_renameFile = 'renamefile'
hdhr_cfg_forceUpdate = 'forceupdate'
hdhr_cfg_linkToPlex = 'linkplex'

class ScriptTools:

    def __init__(self):
        self.interactive = False
        self.dvr_path = ''
        self.plex_path = ''
        self.renameDir = False
        self.renameFile = False
        self.force = False
        self.linkToPlex = False

        arg_parser = argparse.ArgumentParser(description='Process command line args')
        for n in hdhr_args_list:
            arg_parser.add_argument(n)
        self.args = arg_parser.parse_args()

        if self.args.config:
            if os.path.exists(self.args.config):
                self.parse_config_file(None)
            else:
                print "Config file specified not found - " + self.args.config
                self.interactive = True
        else:
            if os.path.exists('my.conf'):
                self.parse_config_file('my.conf')
            else:
                print "No config file found - reverting to interactive"
                self.interactive = True

        # user can always override the settings.
        if self.args.interactive:
            self.interactive = True

    def parse_config_file(self,config_file):
        global logging
        global dvr_path
        global plex_path

        config = ConfigParser.ConfigParser()
        if self.args.config:
            config.read(self.args.config)
        else:
            config.read(config_file)

        sections = {}

        # Parse out the config info from the config file
        for section_name in config.sections():
            sections[section_name] = {}
            for name, value in config.items(section_name):
                sections[section_name][name] = value

        if hdhr_cfg_main in sections.keys():
            if sections[hdhr_cfg_main][hdhr_cfg_path_dvr]:
                self.dvr_path = sections[hdhr_cfg_main][hdhr_cfg_path_dvr]
            #ensure we have trailing path seperator
            if not self.dvr_path.endswith(os.sep):
                self.dvr_path+=os.sep
            print 'Processing DVR files from: ', self.dvr_path

            if sections[hdhr_cfg_main][hdhr_cfg_path_plex]:
                self.plex_path = sections[hdhr_cfg_main][hdhr_cfg_path_plex]
            #ensure we have trailing path seperator
            if not self.plex_path.endswith(os.sep):
                self.plex_path+=os.sep
            print 'Processing Plex files from: ', self.plex_path

            # Load settings if present in config, otherise default to False
            if hasattr(sections[hdhr_cfg_main], hdhr_cfg_renameDir):
                self.renameDir = sections[hdhr_cfg_main][hdhr_cfg_renameDir]
            print 'Rename Directory to match TVDB show name: ', self.renameDir

            if hasattr(sections[hdhr_cfg_main], hdhr_cfg_renameFile):
                self.renameFile = sections[hdhr_cfg_main][hdhr_cfg_renameFile]
            print 'Rename Files Enabled: ', self.renameFile

            if hasattr(sections[hdhr_cfg_main], hdhr_cfg_forceUpdate):
                self.force = sections[hdhr_cfg_main][hdhr_cfg_forceUpdate]
            print 'Force Updates Enabled: ', self.force

            if hasattr(sections[hdhr_cfg_main], hdhr_cfg_linkToPlex):
                self.linkToPlex = sections[hdhr_cfg_main][hdhr_cfg_linkToPlex]
            print 'Symlink to Plex Enabled: ', self.linkToPlex

            if sections[hdhr_cfg_main][hdhr_cfg_skip_shows]:
                self.skip_list = sections[hdhr_cfg_main][hdhr_cfg_skip_shows]
                print 'Setting up Skip Shows: ', self.skip_list

            # Extract Logging Information
            loglevel = 'warning'
            if self.args.loglevel:
                loglevel = self.args.loglevel
            else:
                if sections[hdhr_cfg_main][hdhr_cfg_loglevel]:
                    loglevel = sections[hdhr_cfg_main][hdhr_cfg_loglevel]

            print 'Log Level is set to: ', loglevel

            if self.args.logfile:
                logfile = self.args.logfile
                logging.basicConfig(filename=logfile,
                                    level=LOGLEVELS.get(loglevel, logging.WARNING))
            else:
                if sections[hdhr_cfg_main][hdhr_cfg_logfile]:
                    logfile = sections[hdhr_cfg_main][hdhr_cfg_logfile]
                    logging.basicConfig(filename=logfile,
                                        level=LOGLEVELS.get(loglevel, logging.WARNING))
                else:
                    # Need to setup stdout error handler
                    logging.basicConfig(stream=sys.stdout,
                                        level=LOGLEVELS.get(loglevel, logging.WARNING))
            print 'Logging to: ', logfile

    def get_skip_shows(self):
        return self.skip_list

    def get_dvr_path(self):
        return self.dvr_path

    def get_plex_path(self):
        return self.plex_path

    def isInteractive(self):
        return self.interactive

    def fileRename(self):
        return self.renameFile

    def dirRename(self):
        return self.renameDir

    def forceEnabled(self):
        return self.force

    def linkToPlex(self):
        return self.linkToPlex
