import sys, datetime
import xbmc, xbmcgui
import contextmenu, infodialog
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = sys.modules[ "__main__" ].__addon__
__addonid__      = sys.modules[ "__main__" ].__addonid__
__addonversion__ = sys.modules[ "__main__" ].__addonversion__
__language__     = sys.modules[ "__main__" ].__language__
__cwd__          = sys.modules[ "__main__" ].__cwd__

ACTION_CANCEL_DIALOG = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_CONTEXT_MENU = ( 117, )
ACTION_OSD = ( 122, )
ACTION_SHOW_GUI = ( 18, )
ACTION_SHOW_INFO = ( 11, )

""" ROADMAP:

- Impliment IMDB or other indexers for initial search, user select, result, then search sources.
"""

# Results window
CTRL_RESULTS = 100
# Search.. label / new button
LABEL_SEARCH_STATUS = 190
# Search category label
LABEL_SEARCH_CATEGORY = 191
# New Search
BTN_NEW_SEARCH = 198
# Section container grouplist
GL_SECTION = 101

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'1 SEARCH (%s) DEBUG ->: %s ' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

from one import One
from utils_xbmc import ascii

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        print '1 SEARCH GUI -> GUI started'

        self.searchstring = kwargs[ "searchstring" ].replace('(', '[(]').replace(')', '[)]').replace('+', '[+]')
        log('script version %s started' % __addonversion__)

        self.source_order = ['xbmc.library', 'plugin.video.plexbmc']
        self.one = None
        self.results = dict()       # current search results todo: impliment store results here and add index to listitem for retrieval
        self.use_one_for_xbmc = True        # toggle xbmc search from one or gui
        self.selected_source = None # currently selected source
        self.tvshowid = None
        self.artistid = None

    def get_view_id(section, target=None):
        """ TODO: Not implimented yet
        """
        if target == 'container':
            target = 9
        elif target == 'count':
            target = 0
        elif target == 'list':
            target = 1
            
        if section == 'movies':
            section = 110
        elif section == 'shows':
            section = 120
        elif section == 'seasons':
            section = 130
        elif section == 'episodes':
            section = 140
        elif section == 'music_video':
            section = 150
        elif section == 'artists':
            section = 160
        elif section == 'albums':
            section = 170
        elif section == 'songs':
            section = 180
        elif section == 'actors':
            section = 210
            
        return section + target

    def onInit( self ):
        print '1 SEARCH GUI -> onInit'
        if self.searchstring == '':
            self._close()
            return

        self.window_id = xbmcgui.getCurrentWindowDialogId()
        xbmcgui.Window(self.window_id).setProperty('GlobalSearch.SearchString', self.searchstring)
        self.ACTORSUPPORT = True
        self._hide_controls()
        
        # Configure options for this search
        self._load_settings() # Get options from settings
        #self._parse_argv() 
            
                
        # since this is used after init we need to test for existence of self.one
        if not self.one:
            print '1 SEARCH GUI -> GUI init one'
            self.getControl( 190 ).setLabel( '[B]Discovering Plugins[/B]' )
            self.one = One(use_xbmc=self.use_one_for_xbmc)
            print '1 SEARCH GUI -> GUI end init one'
        self._reset_variables()
        self._init_variables()
        self._fetch_items()
        
    def getSearchType(self):
    
        pass

    def _fetch_items( self ):
        print '1 SEARCH GUI ->  _fetch_items'
        if self.movies == 'true':
            print '1 SEARCH GUI ->  before _fetch_movies'
            self._fetch_movies()
            print '1 SEARCH GUI ->  after _fetch_movies'
        if self.actors == 'true' and self.ACTORSUPPORT:
            self._fetch_actors()
        if self.tvshows == 'true':
            self._fetch_tvshows()
        if self.episodes == 'true':
            self._fetch_episodes()
        if self.musicvideos == 'true':
            self._fetch_musicvideos()
        if self.artists == 'true':
            self._fetch_artists()
        if self.albums == 'true':
            self._fetch_albums()
        if self.songs == 'true':
            self._fetch_songs()
        self._check_focus()

    def xbmc_send_json(self, json_query, media_type=None):
        """ Query xbmc directly (not needed after one's implimentation is fully tested)
        """
        json_resp = xbmc.executeJSONRPC(simplejson.dumps(json_query))
        json_resp = unicode(json_resp, 'utf-8', errors='ignore')
        print '1 SEARCH GUI -> xbmc %s response = %s' % (media_type, ascii(json_resp))
        json_obj = simplejson.loads(json_resp)
        items = json_obj.get('result', {}).get(media_type, [])

        # make sure 'file' is supplied for xbmc results
        for i in items:
            if media_type == 'tvshows':
                tvshowid = i.get('tvshowid', '')
                i['file'] = 'videodb://tvshows/titles/' + str(tvshowid) + '/'

            elif media_type == 'seasons':
                i['file'] = 'videodb://tvshows/titles/' + str(self.tvshowid) + '/' + str(i['season']) + '/'

            elif media_type == 'artists':
                artistid = i.get('artistid', None)
                i['file'] = 'musicdb://artists/' + str(artistid) + '/'

            elif media_type == 'albums':
                albumid = i.get('albumid', None)
                i['file'] = 'musicdb://albums/' + str(albumid) + '/'
        return json_obj

    def add_one_resp(self, xbmc_query, media_type, pid=None):
        print '1 SEARCH GUI -> ### start search for %s ### ' % media_type
        results = list()

        # start xbmc toggle
        if not self.use_one_for_xbmc:
            xbmc_response = self.xbmc_send_json(xbmc_query, media_type)
            results.append(xbmc_response.get('result', {}))
        # end xbmc toggle
        print '1 SEARCH GUI ->  selected source = %s' % self.selected_source
        print '1 SEARCH GUI ->  pid = %s' % pid
        one_results = self.one.search(self.searchstring, media_type, self.selected_source, pid=pid)
        results.extend(one_results)
        print '1 SEARCH GUI -> ### end result for %s ###' % media_type
        all_items = list()
        total = 0
        sources = list()
        # build top level meta and add meta to items
        # each r is a new source
        index = 0 # all items index used for fast retrieval
        for r in results:
            total += int(r.get('limits', {}).get('total', 0))
            items = r.get(media_type, [])
            source_data = r.get('one_meta', {'source_id': 'xbmc.library',
                                              'source_name': 'XBMC',
                                              'media_type': media_type,
                                              'media_label': media_type.capitalize()})
            source_name = source_data.get('source_name')
            source_id = source_data.pop('source_id')
            sources.append(source_name)

            for i in items:
                source_data['path'] = i.get('file')
                source_data['media_id'] = i['id']# Sources unique media id
                source_data['media_pid'] = i['pid'] # Sources unique media pid
                i['source_names'] = [source_name]
                i['source_ids'] = [source_name]
                i['source_data'] = {source_id: source_data}
                i['index'] = index

                # check for existing title match
                existing = False
                for ai in all_items:
                    # add sources as required
                    title = i.get('title', '') 
                    if title and title == ai['title']:
                        print '1 SEARCH GUI -> >>>>>> found existing match'
                        existing = True
                        ai['source_names'].append(source_name)
                        ai['source_data'].update({source_id: source_data})
                        print '1 SEARCH GUI -> >>>>>> new source data'
                        for k, v in ai['source_data'].items():
                            print '1 SEARCH GUI -> > %s : %s' % (k,v)

                # only add new items to all_items list and inc index
                if not existing:
                    all_items.append(i)
                    index += 1

        result = {
            'result': {
                media_type: all_items,
                'total': total,
                'sources': set(sources)}
        }
        # Item source_data is retrieved from self.results as follows:
        # source_data = self.results[media_type][index][source_id]
        self.results.update({media_type:result['result']})
        return result

    def add_one_listdata(self, item, listitem):
        """ Add data from one search to listitem.
        """
        print '1 SEARCH GUI -> # add_one_listdata for : %s' % item.get('title')
        source_names = item.get('source_names')
        print '1 SEARCH GUI -> source_names = %s' % source_names
        listitem.setProperty('source_names', ', '.join(source_names))
        source_data = item.get('source_data')
        print '1 SEARCH GUI -> source_data = %s' % source_data
        listitem.setProperty('source_data', simplejson.dumps(source_data))
        return listitem

    def _hide_controls( self ):
        self.getControl( 119 ).setVisible( False )
        self.getControl( 129 ).setVisible( False )
        self.getControl( 139 ).setVisible( False )
        self.getControl( 149 ).setVisible( False )
        self.getControl( 159 ).setVisible( False )
        self.getControl( 169 ).setVisible( False )
        self.getControl( 179 ).setVisible( False )
        self.getControl( 189 ).setVisible( False )
        try:
            self.getControl( 219 ).setVisible( False )
        except:
            self.ACTORSUPPORT = False
        self.getControl( 198 ).setVisible( False )
        self.getControl( 199 ).setVisible( False )

    def _reset_controls( self ):
        self.getControl( 111 ).reset()
        self.getControl( 121 ).reset()
        self.getControl( 131 ).reset()
        self.getControl( 141 ).reset()
        self.getControl( 151 ).reset()
        self.getControl( 161 ).reset()
        self.getControl( 171 ).reset()
        self.getControl( 181 ).reset()
        if self.ACTORSUPPORT:
            self.getControl( 211 ).reset()

    def _parse_argv( self ):
        try:
            self.params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
            print "1 SEARCH GUI -> Got params %s" % self.params
        except:
            self.params = {}
        self.movies = self.params.get( "movies", "" )
        self.tvshows = self.params.get( "tvshows", "" )
        self.episodes = self.params.get( "episodes", "" )
        self.musicvideos = self.params.get( "musicvideos", "" )
        self.artists = self.params.get( "artists", "" )
        self.albums = self.params.get( "albums", "" )
        self.songs = self.params.get( "songs", "" )
        self.actors = self.params.get( "actors", "" )

    def _load_settings( self ):
        self.movies = __addon__.getSetting( "movies" )
        self.tvshows = __addon__.getSetting( "tvshows" )
        self.episodes = __addon__.getSetting( "episodes" )
        self.musicvideos = __addon__.getSetting( "musicvideos" )
        self.artists = __addon__.getSetting( "artists" )
        self.albums = __addon__.getSetting( "albums" )
        self.songs = __addon__.getSetting( "songs" )
        self.actors = __addon__.getSetting( "actors" )

    def _reset_variables( self ):
        self.focusset= 'false'
        self.getControl( 190 ).setLabel( '[B]' + xbmc.getLocalizedString(194) + '[/B]' )

    def _init_variables( self ):
        self.selected_source = None
        self.tvshowid = None
        self.artistid = None
        self.fetch_seasonepisodes = 'false'
        self.fetch_albumssongs = 'false'
        self.fetch_songalbum = 'false'
        self.playingtrailer = 'false'
        self.getControl( 198 ).setLabel( '[B]' + __language__(32299) + '[/B]' ) #new search button
        self.Player = MyPlayer()
        self.Player.gui = self

    def _fetch_movies( self):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(342) + '[/B]' )
        json_query = {"jsonrpc": "2.0",
                      "method": "VideoLibrary.GetMovies",
                      "params": {"properties": ["title", "streamdetails", "genre", "studio", "year", "tagline", "plot", "plotoutline", "runtime", "fanart", "thumbnail", "file", "trailer", "playcount", "rating", "mpaa", "director", "writer"],
                                 "sort": { "method": "label" },
                                 "filter": {"field":"title","operator":"contains","value":self.searchstring} },
                      "id": 1}
        json_response = self.add_one_resp(json_query, 'movies')

        if (json_response['result'] != None) and (json_response['result'].has_key('movies')):
            for item in json_response['result']['movies']:
                movie = item['title']
                count = count + 1
                director = " / ".join(item['director'])
                writer = " / ".join(item['writer'])
                fanart = item['fanart']
                path = item['file']
                genre = " / ".join(item['genre'])
                mpaa = item['mpaa']
                playcount = str(item['playcount'])
                plot = item['plot']
                outline = item['plotoutline']
                rating = str(round(float(item['rating']),1))
                starrating = 'rating%.1d.png' % round(float(rating)/2)
                runtime = str(int((item['runtime'] / 60.0) + 0.5))
                studio = " / ".join(item['studio'])
                tagline = item['tagline']
                thumb = item['thumbnail']
                trailer = item['trailer']
                year = str(item['year'])
                if item['streamdetails']['audio'] != []:
                    audiochannels = str(item['streamdetails']['audio'][0]['channels'])
                    audiocodec = str(item['streamdetails']['audio'][0]['codec'])
                else:
                    audiochannels = ''
                    audiocodec = ''
                if item['streamdetails']['video'] != []:
                    videocodec = str(item['streamdetails']['video'][0]['codec'])
                    videoaspect = float(item['streamdetails']['video'][0]['aspect'])
                    if videoaspect <= 1.4859:
                        videoaspect = '1.33'
                    elif videoaspect <= 1.7190:
                        videoaspect = '1.66'
                    elif videoaspect <= 1.8147:
                        videoaspect = '1.78'
                    elif videoaspect <= 2.0174:
                        videoaspect = '1.85'
                    elif videoaspect <= 2.2738:
                        videoaspect = '2.20'
                    else:
                        videoaspect = '2.35'
                    videowidth = item['streamdetails']['video'][0]['width']
                    videoheight = item['streamdetails']['video'][0]['height']
                    if videowidth <= 720 and videoheight <= 480:
                        videoresolution = '480'
                    elif videowidth <= 768 and videoheight <= 576:
                        videoresolution = '576'
                    elif videowidth <= 960 and videoheight <= 544:
                        videoresolution = '540'
                    elif videowidth <= 1280 and videoheight <= 720:
                        videoresolution = '720'
                    else:
                        videoresolution = '1080'
                else:
                    videocodec = ''
                    videoaspect = ''
                    videoresolution = ''
                listitem = xbmcgui.ListItem(label=movie, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "plot", plot )
                listitem.setProperty( "plotoutline", outline )
                listitem.setProperty( "duration", runtime )
                listitem.setProperty( "studio", studio )
                listitem.setProperty( "tagline", tagline )
                listitem.setProperty( "year", year )
                listitem.setProperty( "trailer", trailer )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "mpaa", mpaa )
                listitem.setProperty( "writer", writer )
                listitem.setProperty( "director", director )
                listitem.setProperty( "videoresolution", videoresolution )
                listitem.setProperty( "videocodec", videocodec )
                listitem.setProperty( "videoaspect", videoaspect )
                listitem.setProperty( "audiocodec", audiocodec )
                listitem.setProperty( "audiochannels", audiochannels )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 111 ).addItems( listitems )
        if count > 0:
            self.getControl( 110 ).setLabel( str(count) )
            self.getControl( 119 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 111 ) )
                self.focusset = 'true'

    def _fetch_tvshows( self ):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(20343) + '[/B]' )
        json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows",
                      "params": {
                          "properties": ["title", "genre", "studio", "premiered", "plot", "fanart", "thumbnail", "playcount", "year", "mpaa", "episode", "rating", "art"],
                          "sort": { "method": "label" },
                          "filter": {"field": "title", "operator": "contains", "value": self.searchstring} },
                      "id": 1}

        json_response = self.add_one_resp(json_query, 'tvshows')

        if (json_response['result'] != None) and (json_response['result'].has_key('tvshows')):
            for item in json_response['result']['tvshows']:
                tvshow = item['title']
                count = count + 1
                episode = str(item['episode'])
                fanart = item['fanart']
                genre = " / ".join(item['genre'])
                mpaa = item['mpaa']
                playcount = str(item['playcount'])
                plot = item['plot']
                premiered = item['premiered']
                rating = str(round(float(item['rating']),1))
                starrating = 'rating%.1d.png' % round(float(rating)/2)
                studio = " / ".join(item['studio'])
                thumb = item['thumbnail']
                banner = item['art'].get('banner', '')
                poster = item['art'].get('poster', '')
                path = item.get('file', None)
                tvshowid = str(item.get('tvshowid', ''))
                #if not path:
                    #path = 'videodb://tvshows/titles/' + tvshowid + '/'
                year = str(item['year'])
                listitem = xbmcgui.ListItem(label=tvshow, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "art(banner)", banner )
                listitem.setProperty( "art(poster)", poster )
                listitem.setProperty( "episode", episode )
                listitem.setProperty( "mpaa", mpaa )
                listitem.setProperty( "year", year )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "plot", plot )
                listitem.setProperty( "premiered", premiered )
                listitem.setProperty( "studio", studio )
                listitem.setProperty( "rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "path", path )
                listitem.setProperty( "id", tvshowid or item.get('id', None))
                listitem = self.add_one_listdata(item, listitem)
                listitems.append(listitem)
        self.getControl( 121 ).addItems( listitems )
        if count > 0:
            self.getControl( 120 ).setLabel( str(count) )
            self.getControl( 129 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 121 ) )
                self.focusset = 'true'

    def _fetch_seasons( self ):
        listitems = []
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(20343) + '[/B]' )
        count = 0
        json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons",
                  "params": {
                      "properties": ["showtitle", "season", "fanart", "thumbnail", "playcount", "episode"],
                      "sort": { "method": "label" },
                      "tvshowid":self.tvshowid },
                  "id": 1}

        json_response = self.add_one_resp(json_query, 'seasons')

        if (json_response['result'] != None) and (json_response['result'].has_key('seasons')):
            for item in json_response['result']['seasons']:
                tvshow = item['showtitle']
                count = count + 1
                episode = str(item['episode'])
                fanart = item['fanart']
                path = item.get('file', None)
                #if not path:
                    #path = 'videodb://tvshows/titles/' + str(self.tvshowid) + '/' + str(item['season']) + '/'
                season = item['label']
                playcount = str(item['playcount'])
                thumb = item['thumbnail']
                listitem = xbmcgui.ListItem(label=season, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "episode", episode )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "tvshowtitle", tvshow )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 131 ).addItems( listitems )
        if count > 0:
            self.foundseasons= 'true'
            self.getControl( 130 ).setLabel( str(count) )
            self.getControl( 139 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 131 ) )
                self.focusset = 'true'

    def _fetch_episodes( self ):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(20360) + '[/B]' )
        if self.tvshowid:
            json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                          "params": {
                              "properties": ["title", "streamdetails", "plot", "firstaired", "runtime", "season", "episode", "showtitle", "thumbnail", "fanart", "file", "playcount", "director", "rating"],
                              "sort": { "method": "title" },
                              "tvshowid":self.tvshowid },
                          "id": 1}
        else:
            json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                              "params": {
                                  "properties": ["title", "streamdetails", "plot", "firstaired", "runtime", "season", "episode", "showtitle", "thumbnail", "fanart", "file", "playcount", "director", "rating"],
                                  "sort": { "method": "title" },
                                  "filter": {"field": "title", "operator": "contains", "value": self.searchstring} },
                              "id": 1}

        print '1 SEARCH GUI -> fetch episodes tvshowid=%s' % self.tvshowid
        json_response = self.add_one_resp(json_query, 'episodes', self.tvshowid)

        if (json_response['result'] != None) and (json_response['result'].has_key('episodes')):
            for item in json_response['result']['episodes']:
                if self.fetch_seasonepisodes == 'true':
                    episode = item['showtitle']
                else:
                    episode = item['title']
                count = count + 1
                if self.fetch_seasonepisodes == 'true':
                    tvshowname = episode
                    episode = item['title']
                else:
                    tvshowname = item['showtitle']
                director = " / ".join(item['director'])
                fanart = item['fanart']
                episodenumber = "%.2d" % float(item['episode'])
                path = item['file']
                plot = item['plot']
                runtime = str(int((item['runtime'] / 60.0) + 0.5))
                premiered = item['firstaired']
                rating = str(round(float(item['rating']),1))
                starrating = 'rating%.1d.png' % round(float(rating)/2)
                seasonnumber = '%.2d' % float(item['season'])
                playcount = str(item['playcount'])
                thumb = item['thumbnail']
                fanart = item['fanart']
                if item['streamdetails']['audio'] != []:
                    audiochannels = str(item['streamdetails']['audio'][0]['channels'])
                    audiocodec = str(item['streamdetails']['audio'][0]['codec'])
                else:
                    audiochannels = ''
                    audiocodec = ''
                if item['streamdetails']['video'] != []:
                    videocodec = str(item['streamdetails']['video'][0]['codec'])
                    videoaspect = float(item['streamdetails']['video'][0]['aspect'])
                    if videoaspect <= 1.4859:
                        videoaspect = '1.33'
                    elif videoaspect <= 1.7190:
                        videoaspect = '1.66'
                    elif videoaspect <= 1.8147:
                        videoaspect = '1.78'
                    elif videoaspect <= 2.0174:
                        videoaspect = '1.85'
                    elif videoaspect <= 2.2738:
                        videoaspect = '2.20'
                    else:
                        videoaspect = '2.35'
                    videowidth = item['streamdetails']['video'][0]['width']
                    videoheight = item['streamdetails']['video'][0]['height']
                    if videowidth <= 720 and videoheight <= 480:
                        videoresolution = '480'
                    elif videowidth <= 768 and videoheight <= 576:
                        videoresolution = '576'
                    elif videowidth <= 960 and videoheight <= 544:
                        videoresolution = '540'
                    elif videowidth <= 1280 and videoheight <= 720:
                        videoresolution = '720'
                    else:
                        videoresolution = '1080'
                else:
                    videocodec = ''
                    videoaspect = ''
                    videoresolution = ''
                listitem = xbmcgui.ListItem(label=episode, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "episode", episodenumber )
                listitem.setProperty( "plot", plot )
                listitem.setProperty( "rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "director", director )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "season", seasonnumber )
                listitem.setProperty( "duration", runtime )
                listitem.setProperty( "tvshowtitle", tvshowname )
                listitem.setProperty( "premiered", premiered )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "videoresolution", videoresolution )
                listitem.setProperty( "videocodec", videocodec )
                listitem.setProperty( "videoaspect", videoaspect )
                listitem.setProperty( "audiocodec", audiocodec )
                listitem.setProperty( "audiochannels", audiochannels )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 141 ).addItems( listitems )
        if count > 0:
            self.getControl( 140 ).setLabel( str(count) )
            self.getControl( 149 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 141 ) )
                self.focusset = 'true'

    def _fetch_musicvideos( self ):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(20389) + '[/B]' )
        json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos",
                      "params": {
                          "properties": ["title", "streamdetails", "runtime", "genre", "studio", "artist", "album", "year", "plot", "fanart", "thumbnail", "file", "playcount", "director"],
                          "sort": { "method": "label" },
                          "filter": {"field": "title", "operator": "contains", "value": self.searchstring} },
                      "id": 1}

        json_response = self.add_one_resp(json_query, 'musicvideos')

        if (json_response['result'] != None) and (json_response['result'].has_key('musicvideos')):
            for item in json_response['result']['musicvideos']:
                musicvideo = item['title']
                count = count + 1
                album = item['album']
                artist = " / ".join(item['artist'])
                director = " / ".join(item['director'])
                fanart = item['fanart']
                path = item['file']
                genre = " / ".join(item['genre'])
                plot = item['plot']
                studio = " / ".join(item['studio'])
                thumb = item['thumbnail']
                playcount = str(item['playcount'])
                year = str(item['year'])
                if year == '0':
                    year = ''
                if item['streamdetails']['audio'] != []:
                    audiochannels = str(item['streamdetails']['audio'][0]['channels'])
                    audiocodec = str(item['streamdetails']['audio'][0]['codec'])
                else:
                    audiochannels = ''
                    audiocodec = ''
                if item['streamdetails']['video'] != []:
                    videocodec = str(item['streamdetails']['video'][0]['codec'])
                    videoaspect = float(item['streamdetails']['video'][0]['aspect'])
                    if videoaspect <= 1.4859:
                        videoaspect = '1.33'
                    elif videoaspect <= 1.7190:
                        videoaspect = '1.66'
                    elif videoaspect <= 1.8147:
                        videoaspect = '1.78'
                    elif videoaspect <= 2.0174:
                        videoaspect = '1.85'
                    elif videoaspect <= 2.2738:
                        videoaspect = '2.20'
                    else:
                        videoaspect = '2.35'
                    videowidth = item['streamdetails']['video'][0]['width']
                    videoheight = item['streamdetails']['video'][0]['height']
                    if videowidth <= 720 and videoheight <= 480:
                        videoresolution = '480'
                    elif videowidth <= 768 and videoheight <= 576:
                        videoresolution = '576'
                    elif videowidth <= 960 and videoheight <= 544:
                        videoresolution = '540'
                    elif videowidth <= 1280 and videoheight <= 720:
                        videoresolution = '720'
                    else:
                        videoresolution = '1080'
                    duration = str(datetime.timedelta(seconds=int(item['streamdetails']['video'][0]['duration'])))
                    if duration[0] == '0':
                        duration = duration[2:]
                else:
                    videocodec = ''
                    videoaspect = ''
                    videoresolution = ''
                    duration = ''
                listitem = xbmcgui.ListItem(label=musicvideo, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "album", album )
                listitem.setProperty( "artist", artist )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "director", director )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "plot", plot )
                listitem.setProperty( "duration", duration )
                listitem.setProperty( "studio", studio )
                listitem.setProperty( "year", year )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "videoresolution", videoresolution )
                listitem.setProperty( "videocodec", videocodec )
                listitem.setProperty( "videoaspect", videoaspect )
                listitem.setProperty( "audiocodec", audiocodec )
                listitem.setProperty( "audiochannels", audiochannels )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 151 ).addItems( listitems )
        if count > 0:
            self.getControl( 150 ).setLabel( str(count) )
            self.getControl( 159 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 151 ) )
                self.focusset = 'true'

    def _fetch_artists( self ):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(133) + '[/B]' )
        json_query = {"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists",
                      "params": {
                          "properties": ["genre", "description", "fanart", "thumbnail", "formed", "disbanded", "born", "yearsactive", "died", "mood", "style"],
                          "sort": { "method": "label" },
                          "filter": {"field": "artist", "operator": "contains", "value": self.searchstring} },
                      "id": 1}

        json_response = self.add_one_resp(json_query, 'artists')

        if (json_response['result'] != None) and (json_response['result'].has_key('artists')):
            for item in json_response['result']['artists']:
                artist = item['label']
                count = count + 1
                path = item.get('file', None)
                artistid = item.get('artistid', None)
                #if not path:
                #    path = 'musicdb://artists/' + str(artistid) + '/'
                born = item.get('born', '')
                description = item.get('description', '')
                died = item.get('died', '')
                disbanded = item.get('disbanded', '')
                fanart = item.get('fanart', '')
                formed = item.get('formed', '')
                genre = " / ".join(item.get('genre', ''))
                mood = " / ".join(item.get('mood', ''))
                style = " / ".join(item.get('style', ''))
                thumb = item.get('thumbnail', '')
                yearsactive = " / ".join(item.get('yearsactive', ''))
                listitem = xbmcgui.ListItem(label=artist, iconImage='DefaultArtist.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "artist_born", born )
                listitem.setProperty( "artist_died", died )
                listitem.setProperty( "artist_formed", formed )
                listitem.setProperty( "artist_disbanded", disbanded )
                listitem.setProperty( "artist_yearsactive", yearsactive )
                listitem.setProperty( "artist_mood", mood )
                listitem.setProperty( "artist_style", style )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "artist_genre", genre )
                listitem.setProperty( "artist_description", description )
                listitem.setProperty( "path", path )
                listitem.setProperty( "id", str(artistid) or item.get('id', None))
                listitems.append(listitem)
        self.getControl( 161 ).addItems( listitems )
        if count > 0:
            self.getControl( 160 ).setLabel( str(count) )
            self.getControl( 169 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 161 ) )
                self.focusset = 'true'

    def _fetch_albums( self):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(132) + '[/B]' )
        if self.fetch_albumssongs == 'true':
            json_query = {"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums",
                          "params": {
                              "properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "theme", "type", "mood", "style", "rating"],
                              "sort": { "method": "label" },
                              "filter": {"artistid": self.artistid} }, "id": 1}
        else:
            json_query = {"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums",
                          "params": {
                              "properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "theme", "type", "mood", "style", "rating"],
                              "sort": { "method": "label" },
                              "filter": {"field": "album", "operator": "contains", "value": self.searchstring} },
                          "id": 1}

        json_response = self.add_one_resp(json_query, 'albums')

        if (json_response['result'] != None) and (json_response['result'].has_key('albums')):
            for item in json_response['result']['albums']:
                if self.fetch_albumssongs == 'true':
                    album = " / ".join(item['artist'])
                else:
                    album = item['title']
                count = count + 1
                if self.fetch_albumssongs == 'true':
                    artist = album
                    album = item['title']
                else:
                    artist = " / ".join(item['artist'])
                    if self.fetch_songalbum == 'true':
                        if not artist == self.artistname:
                            count = count - 1
                            return
                path = item.get('file', None)
                albumid = item.get('albumid', None)
                #if not path:
                #    path = 'musicdb://albums/' + str(albumid) + '/'
                label = item['albumlabel']
                description = item['description']
                fanart = item['fanart']
                genre = " / ".join(item['genre'])
                mood = " / ".join(item['mood'])
                rating = str(item['rating'])
                if rating == '48':
                    rating = ''
                if rating != '':
                    starrating = 'rating%.1d.png' % round(float(int(rating))/2)
                else:
                    starrating = 'rating0.png'
                style = " / ".join(item['style'])
                theme = " / ".join(item['theme'])
                albumtype = item['type']
                thumb = item['thumbnail']
                year = str(item['year'])
                listitem = xbmcgui.ListItem(label=album, iconImage='DefaultAlbumCover.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "artist", artist )
                listitem.setProperty( "album_label", label )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "album_description", description )
                listitem.setProperty( "album_theme", theme )
                listitem.setProperty( "album_style", style )
                listitem.setProperty( "album_rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "album_type", albumtype )
                listitem.setProperty( "album_mood", mood )
                listitem.setProperty( "year", year )
                listitem.setProperty( "path", path )
                listitem.setProperty( "id", str(albumid) or item.get('id', None))
                listitems.append(listitem)
        self.getControl( 171 ).addItems( listitems )
        if count > 0:
            self.getControl( 170 ).setLabel( str(count) )
            self.getControl( 179 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 171 ) )
                self.focusset = 'true'

    def _fetch_songs( self):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(134) + '[/B]' )
        if self.fetch_albumssongs == 'true':
            json_query = {"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs",
                          "params": {
                              "properties": ["title", "artist", "album", "genre", "duration", "year", "file", "thumbnail", "fanart", "comment", "rating", "track", "playcount"],
                              "sort": { "method": "title" },
                              "filter": {"artistid": self.artistid} },
                          "id": 1}
        else:
            json_query = {"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs",
                          "params":
                              {"properties": ["title", "artist", "album", "genre", "duration", "year", "file", "thumbnail", "fanart", "comment", "rating", "track", "playcount"],
                               "sort": { "method": "title" },
                               "filter": {"field": "title", "operator": "contains", "value": self.searchstring}},
                          "id": 1}

        json_response = self.add_one_resp(json_query, 'songs')

        if (json_response['result'] != None) and (json_response['result'].has_key('songs')):
            for item in json_response['result']['songs']:
                if self.fetch_albumssongs == 'true':
                    song = " / ".join(item['artist'])
                else:
                    song = item['title']
                count = count + 1
                if self.fetch_albumssongs == 'true':
                    artist = song
                    song = item['label']
                else:
                    artist = " / ".join(item['artist'])
                album = item['album']
                comment = item['comment']
                duration = str(datetime.timedelta(seconds=int(item['duration'])))
                if duration[0] == '0':
                    duration = duration[2:]
                fanart = item['fanart']
                path = item['file']
                genre = " / ".join(item['genre'])
                thumb = item['thumbnail']
                track = str(item['track'])
                playcount = str(item['playcount'])
                rating = str(int(item['rating'])-48)
                starrating = 'rating%.1d.png' % int(rating)
                year = str(item['year'])
                listitem = xbmcgui.ListItem(label=song, iconImage='DefaultAlbumCover.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "artist", artist )
                listitem.setProperty( "album", album )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "comment", comment )
                listitem.setProperty( "track", track )
                listitem.setProperty( "rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "duration", duration )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "year", year )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 181 ).addItems( listitems )
        if count > 0:
            self.getControl( 180 ).setLabel( str(count) )
            self.getControl( 189 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 181 ) )
                self.focusset = 'true'

    def _fetch_actors( self,  ):
        listitems = []
        count = 0
        self.getControl( 191 ).setLabel( '[B]' + xbmc.getLocalizedString(344) + '[/B]' )
        json_query = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                      "params": {
                          "properties": ["title", "streamdetails", "genre", "studio", "year", "tagline", "plot", "plotoutline", "runtime", "fanart", "thumbnail", "file", "trailer", "playcount", "rating", "mpaa", "director", "writer"],
                          "sort": { "method": "label" },
                          "filter": {"field":"actor","operator":"contains","value":self.searchstring} },
                      "id": 1}

        json_response = self.add_one_resp(json_query, 'actors')

        if (json_response['result'] != None) and (json_response['result'].has_key('movies')):
            for item in json_response['result']['movies']:
                movie = item['title']
                count = count + 1
                director = " / ".join(item['director'])
                writer = " / ".join(item['writer'])
                fanart = item['fanart']
                path = item['file']
                genre = " / ".join(item['genre'])
                mpaa = item['mpaa']
                playcount = str(item['playcount'])
                plot = item['plot']
                outline = item['plotoutline']
                rating = str(round(float(item['rating']),1))
                starrating = 'rating%.1d.png' % round(float(rating)/2)
                runtime = str(int((item['runtime'] / 60.0) + 0.5))
                studio = " / ".join(item['studio'])
                tagline = item['tagline']
                thumb = item['thumbnail']
                trailer = item['trailer']
                year = str(item['year'])
                if item['streamdetails']['audio'] != []:
                    audiochannels = str(item['streamdetails']['audio'][0]['channels'])
                    audiocodec = str(item['streamdetails']['audio'][0]['codec'])
                else:
                    audiochannels = ''
                    audiocodec = ''
                if item['streamdetails']['video'] != []:
                    videocodec = str(item['streamdetails']['video'][0]['codec'])
                    videoaspect = float(item['streamdetails']['video'][0]['aspect'])
                    if videoaspect <= 1.4859:
                        videoaspect = '1.33'
                    elif videoaspect <= 1.7190:
                        videoaspect = '1.66'
                    elif videoaspect <= 1.8147:
                        videoaspect = '1.78'
                    elif videoaspect <= 2.0174:
                        videoaspect = '1.85'
                    elif videoaspect <= 2.2738:
                        videoaspect = '2.20'
                    else:
                        videoaspect = '2.35'
                    videowidth = item['streamdetails']['video'][0]['width']
                    videoheight = item['streamdetails']['video'][0]['height']
                    if videowidth <= 720 and videoheight <= 480:
                        videoresolution = '480'
                    elif videowidth <= 768 and videoheight <= 576:
                        videoresolution = '576'
                    elif videowidth <= 960 and videoheight <= 544:
                        videoresolution = '540'
                    elif videowidth <= 1280 and videoheight <= 720:
                        videoresolution = '720'
                    else:
                        videoresolution = '1080'
                else:
                    videocodec = ''
                    videoaspect = ''
                    videoresolution = ''
                listitem = xbmcgui.ListItem(label=movie, iconImage='DefaultVideo.png', thumbnailImage=thumb)
                listitem.setProperty( "icon", thumb )
                listitem.setProperty( "fanart", fanart )
                listitem.setProperty( "genre", genre )
                listitem.setProperty( "plot", plot )
                listitem.setProperty( "plotoutline", outline )
                listitem.setProperty( "duration", runtime )
                listitem.setProperty( "studio", studio )
                listitem.setProperty( "tagline", tagline )
                listitem.setProperty( "year", year )
                listitem.setProperty( "trailer", trailer )
                listitem.setProperty( "playcount", playcount )
                listitem.setProperty( "rating", rating )
                listitem.setProperty( "starrating", starrating )
                listitem.setProperty( "mpaa", mpaa )
                listitem.setProperty( "writer", writer )
                listitem.setProperty( "director", director )
                listitem.setProperty( "videoresolution", videoresolution )
                listitem.setProperty( "videocodec", videocodec )
                listitem.setProperty( "videoaspect", videoaspect )
                listitem.setProperty( "audiocodec", audiocodec )
                listitem.setProperty( "audiochannels", audiochannels )
                listitem.setProperty( "path", path )
                listitems.append(listitem)
        self.getControl( 211 ).addItems( listitems )
        if count > 0:
            self.getControl( 210 ).setLabel( str(count) )
            self.getControl( 219 ).setVisible( True )
            if self.focusset == 'false':
                xbmc.sleep(100)
                self.setFocus( self.getControl( 211 ) )
                self.focusset = 'true'

    def _getTvshow_Seasons( self ):
        self.fetch_seasonepisodes = 'true'
        listitem = self.getControl( 121 ).getSelectedItem()
        self.tvshowid = int(listitem.getProperty('id'))
        print '1 SEARCH GUI -> get seasons tvshowid=%s' % self.tvshowid
        self.searchstring = listitem.getLabel().replace('(','[(]').replace(')','[)]').replace('+','[+]')
        self._reset_variables()
        self._hide_controls()
        self._reset_controls()
        self._fetch_seasons()
        self._check_focus()
        self.fetch_seasonepisodes = 'false'

    def _getTvshow_Episodes( self ):
        #self.fetch_seasonepisodes = 'true'
        source = self.select_source(121)
        self.tvshowid = int(source['media_id'])
        self.searchstring = source['searchstring']
        #listitem = self.getControl( 121 ).getSelectedItem()
        #self.tvshowid = int(listitem.getProperty('id'))
        #self.searchstring = listitem.getLabel().replace('(','[(]').replace(')','[)]').replace('+','[+]')
        self._reset_variables()
        self._hide_controls()
        self._reset_controls()
        self._fetch_episodes()
        self._check_focus()
        #self.fetch_seasonepisodes = 'false'

    def _getArtist_Albums( self ):
        self.fetch_albumssongs = 'true'
        listitem = self.getControl( 161 ).getSelectedItem()
        self.artistid = int(listitem.getProperty('id'))
        self.searchstring = listitem.getLabel().replace('(','[(]').replace(')','[)]').replace('+','[+]')
        self._reset_variables()
        self._hide_controls()
        self._reset_controls()
        self._fetch_albums()
        self._check_focus()
        self.fetch_albumssongs = 'false'

    def _getArtist_Songs( self ):
        self.fetch_albumssongs = 'true'
        listitem = self.getControl( 161 ).getSelectedItem()
        self.artistid = int(listitem.getProperty('id'))
        self.searchstring = listitem.getLabel().replace('(','[(]').replace(')','[)]').replace('+','[+]')
        self._reset_variables()
        self._hide_controls()
        self._reset_controls()
        self._fetch_songs()
        self._check_focus()
        self.fetch_albumssongs = 'false'

    def _getSong_Album( self ):
        self.fetch_songalbum = 'true'
        listitem = self.getControl( 181 ).getSelectedItem()
        self.artistname = listitem.getProperty('artist')
        self.searchstring = listitem.getProperty('album').replace('(','[(]').replace(')','[)]').replace('+','[+]')
        self._reset_variables()
        self._hide_controls()
        self._reset_controls()
        self._fetch_albums()
        self._check_focus()
        self.fetch_songalbum = 'false'

    def _play_video( self, path ):
        self._close()
        xbmc.Player().play( path )

    def _play_audio( self, path, listitem ):
        self._close()
        xbmc.Player().play( path, listitem )

    def _play_trailer( self ):
        self.playingtrailer = 'true'
        self.getControl( 100 ).setVisible( False )
        self.Player.play( self.trailer )

    def _trailerstopped( self ):
        self.getControl( 100 ).setVisible( True )
        self.playingtrailer = 'false'

    def _play_album( self ):
        self._close()
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "albumid": %d } }, "id": 1 }' % int(self.albumid))

    def _browse_video( self, path ):
        self._close()
        xbmc.executebuiltin('ActivateWindow(Videos,' + path + ',return)')

    def _browse_audio( self, path ):
        self._close()
        xbmc.executebuiltin('ActivateWindow(MusicLibrary,' + path + ',return)')

    def _browse_album( self ):
        listitem = self.getControl( 171 ).getSelectedItem()
        path = listitem.getProperty('path')
        self._close()
        xbmc.executebuiltin('ActivateWindow(MusicLibrary,' + path + ',return)')

    def _check_focus( self ):
        self.getControl( 190 ).setLabel( '' )
        self.getControl( 191 ).setLabel( '' )
        if self.focusset == 'false':
            self.getControl( 199 ).setVisible( True )
            self.setFocus( self.getControl( 198 ) )
        self.getControl( 198 ).setVisible( True )

    def _showContextMenu( self ):
        labels = ()
        functions = ()
        controlId = self.getFocusId()
        print '1 SEARCH GUI -> _showContextMenu controlId=%s' % controlId
        x, y = self.getControl( controlId ).getPosition()
        w = self.getControl( controlId ).getWidth()
        h = self.getControl( controlId ).getHeight()
        if controlId == 111:
            labels += ( xbmc.getLocalizedString(13346), )
            functions += ( self._showInfo, )
            listitem = self.getControl( 111 ).getSelectedItem()
            self.trailer = listitem.getProperty('trailer')
            if self.trailer:
                labels += ( __language__(32205), )
                functions += ( self._play_trailer, )
        elif controlId == 121:
            labels += ( xbmc.getLocalizedString(20351), __language__(32207), __language__(32208), )
            functions += ( self._showInfo, self._getTvshow_Seasons, self._getTvshow_Episodes, )
        elif controlId == 131:
            labels += ( __language__(32204), )
            functions += ( self._showInfo, )
        elif controlId == 141:
            labels += ( xbmc.getLocalizedString(20352), )
            functions += ( self._showInfo, )
        elif controlId == 151:
            labels += ( xbmc.getLocalizedString(20393), )
            functions += ( self._showInfo, )
        elif controlId == 161:
            labels += ( xbmc.getLocalizedString(21891), __language__(32209), __language__(32210), )
            functions += ( self._showInfo, self._getArtist_Albums, self._getArtist_Songs, )
        elif controlId == 171:
            labels += ( xbmc.getLocalizedString(13351), __language__(32203), )
            functions += ( self._showInfo, self._browse_album, )
        elif controlId == 181:
            labels += ( xbmc.getLocalizedString(658), __language__(32206), )
            functions += ( self._showInfo, self._getSong_Album, )
        elif controlId == 211:
            labels += ( xbmc.getLocalizedString(13346), )
            functions += ( self._showInfo, )
            listitem = self.getControl( 211 ).getSelectedItem()
            self.trailer = listitem.getProperty('trailer')
            if self.trailer:
                labels += ( __language__(32205), )
                functions += ( self._play_trailer, )
        context_menu = contextmenu.GUI( "script-globalsearch-contextmenu.xml" , __cwd__, "Default", labels=labels )
        context_menu.doModal()
        print '1 SEARCH GUI -> context_menu.selection = %s' % context_menu.selection
        if context_menu.selection is not None:
            functions[ context_menu.selection ]()
        del context_menu

    def _showInfo( self ):
        items = []
        controlId = self.getFocusId()
        print '1 SEARCH GUI -> controlId=%s' % controlId
        if controlId == 111:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "movies"
        elif controlId == 121:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "tvshows"
        elif controlId == 131:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "seasons"
        elif controlId == 141:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "episodes"
        elif controlId == 151:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "musicvideos"
        elif controlId == 161:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "artists"
        elif controlId == 171:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "albums"
        elif controlId == 181:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "songs"
        elif controlId == 211:
            listitem = self.getControl( controlId ).getSelectedItem()
            content = "actors"
        info_dialog = infodialog.GUI( "script-globalsearch-infodialog.xml" , __cwd__, "Default", listitem=listitem, content=content )
        info_dialog.doModal()
        if info_dialog.action is not None:
            actions = info_dialog.action
            self.selected_source = info_dialog.selected_source
            if info_dialog.action == 'play_movie':
                path = self.select_source_path(111)
                self._play_video(path)
            elif info_dialog.action == 'play_trailer':
                listitem = self.getControl( 111 ).getSelectedItem()
                self.trailer = listitem.getProperty('trailer')
                self._play_trailer()
            elif info_dialog.action == 'browse_tvshow':
                path = self.select_source_path(121)
                self._browse_video(path)
            elif info_dialog.action == 'browse_season':
                path = self.select_source_path(131)
                self._browse_video(path)
            elif info_dialog.action == 'play_episode':
                path = self.select_source_path(141)
                self._play_video(path)
            elif info_dialog.action == 'play_musicvideo':
                path = self.select_source_path(151)
                self._play_video(path)
            elif info_dialog.action == 'browse_artist':
                path = self.select_source_path(161)
                self._browse_audio(path)
            elif info_dialog.action == 'play_album':
                listitem = self.getControl( 171 ).getSelectedItem()
                self.albumid = int(listitem.getProperty('id'))
                self._play_album()
            elif info_dialog.action == 'browse_album':
                listitem = self.getControl( 171 ).getSelectedItem()
                path = listitem.getProperty('path')
                self._browse_audio(path)
            elif info_dialog.action == 'play_song':
                listitem = self.getControl( 181 ).getSelectedItem()
                path = listitem.getProperty('path')
            elif info_dialog.action == 'play_movie_actors':
                listitem = self.getControl( 211 ).getSelectedItem()
                path = listitem.getProperty('path')
                self._play_video(path)
                self._play_audio(path, listitem)
            elif info_dialog.action == 'play_trailer_actors':
                listitem = self.getControl( 211 ).getSelectedItem()
                self.trailer = listitem.getProperty('trailer')
                self._play_trailer()
        del info_dialog

    def _newSearch( self ):
        print '1 SEARCH GUI -> _newSearch'
        keyboard = xbmc.Keyboard( '', __language__(32101), False )
        keyboard.doModal()
        if ( keyboard.isConfirmed() ):
            self.searchstring = keyboard.getText()
            self._reset_controls()
            self.onInit()

    def onClick( self, controlId ):
        print '1 SEARCH GUI -> +++++++++++ onClick controlID = %s' % controlId
        if controlId == 111:
            path = self.select_source_path(controlId)
            self._play_video(path)
        elif controlId == 121:
            path = self.select_source_path(controlId)
            self._browse_video(path)
        elif controlId == 131:
            path = self.select_source_path(controlId)
            self._browse_video(path)
        elif controlId == 141:
            path = self.select_source_path(controlId)
            self._play_video(path)
        elif controlId == 151:
            path = self.select_source_path(controlId)
            self._play_video(path)
        elif controlId == 161:
            path = self.select_source_path(controlId)
            self._browse_audio(path)
        elif controlId == 171:
            listitem = self.getControl( 171 ).getSelectedItem()
            self.albumid = int(listitem.getProperty('id'))
            self._play_album()
        elif controlId == 181:
            listitem = self.getControl( 181 ).getSelectedItem()
            path = self.select_source_path(controlId)
            self._play_audio(path, listitem)
        elif controlId == 211:
            path = self.select_source_path(controlId)
            self._play_video(path)
        elif controlId == 198:
            self._newSearch()


    def select_source_path(self, controlId):
        source = self.select_source(controlId)
        return source.get('path')

    def select_source(self, controlId):
        """ Controlls the source selcted for playback.
        """
        listitem = self.getControl( controlId ).getSelectedItem()
        source_data = listitem.getProperty('source_data')
        source_data = simplejson.loads(source_data)
        source = None

        # use first source in order if non has been specified
        if self.selected_source is None:
            self.selected_source = self.source_order[0]
        
        # convert selected_source numeric key to valid source key
        if isinstance( int(self.selected_source), int ):
            source_keys = source_data.keys()
            self.selected_source = source_keys[self.selected_source]
            
        source = source_data.get(self.selected_source, None)
        if source is None:
            raise KeyError('The selected source (%s) is not valid.' % self.selected_source)
        
        print '1 SEARCH GUI ->  source selected: %s' % self.selected_source
        source['searchstring'] = listitem.getLabel().replace('(','[(]').replace(')','[)]').replace('+','[+]')
        return source

    # TODO; need to
    def select_source_manual(self):
        """ Used for manual selection of source.
        :return:
        """
        pass


    def onAction( self, action ):
        if action.getId() in ACTION_CANCEL_DIALOG:
            if self.playingtrailer == 'false':
                self._close()
            else:
                self.Player.stop()
                self._trailerstopped()
        elif action.getId() in ACTION_CONTEXT_MENU:
            self._showContextMenu()
        elif action.getId() in ACTION_OSD:
            if self.playingtrailer == 'true' and xbmc.getCondVisibility('videoplayer.isfullscreen'):
                xbmc.executebuiltin("ActivateWindow(12901)")
        elif action.getId() in ACTION_SHOW_GUI:
            if self.playingtrailer == 'true':
                self.Player.stop()
                self._trailerstopped()
        elif action.getId() in ACTION_SHOW_INFO:
            if self.playingtrailer == 'true' and xbmc.getCondVisibility('videoplayer.isfullscreen'):
                xbmc.executebuiltin("ActivateWindow(142)")
            else:
                self._showInfo()

    def _close( self ):
            log('script stopped')
            self.close()
            xbmc.sleep(300)
            xbmcgui.Window(self.window_id).clearProperty('GlobalSearch.SearchString')

class MyPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__( self )

    def onPlayBackEnded( self ):
        self.gui._trailerstopped()

    def onPlayBackStopped( self ):
        self.gui._trailerstopped()
