import xbmcaddon
import xbmcgui
import xbmc
import os
import sys
import re
import json

from utils_xbmc import uni, ascii


class One(object):
    registered_plugins = []
    debug = False

    def __init__(self, plugins=None, use_xbmc=True):
        print '1 SEARCH -> init one'
        self.include_plugins = plugins or []
        self.results = list()
        self.plugins = list()
        self.init_plugins(use_xbmc)

    @staticmethod
    def register(P):
        print '1 SEARCH -> register %s' % P.id
        One.registered_plugins.append(P)

    def init_plugins(self, use_xbmc):
        for P in self.registered_plugins:
            #xbmc library is not a plugin
            if P.id == 'library.xbmc' and use_xbmc:
                exists = True
            elif P.id == 'library.xbmc' and not use_xbmc:
                exists = False
            else:
                exists = xbmcaddon.Addon(P.id)
            print '1 SEARCH -> %s exists: %s' % (P.id, exists)
            print '1 SEARCH -> self.include_plugins = %s' % self.include_plugins
            if exists and not self.include_plugins or P.id in self.include_plugins:
                print '1 SEARCH -> init %s' % P.id
                try:
                    p = P()
                    self.plugins.append(p)
                except Exception as e:
                    print '1 SEARCH -> ERROR %s FAILD TO INITIALIZE: %s' % (P.id.upper(), e)

    def search(self, search_str, media_type=None, plugin=None, pid=None):
        """ Unified search method.
        :param search_str: The string to search for.
        :param media_type: media type to search.
        :param plugin: Limit search to specified plugin id
        :param pid: The parent id if required to build a path
        :return: List of results
        """
        self.results = list()
        for p in self.plugins:
            if not plugin or p.id == plugin:
                results = p.search(search_str, media_type, pid=pid)
                self.results.extend(results)

        self.print_results(search_str, self.results, True)
        return self.results

    def print_results(self, query, results, overide=False):
        if self.debug or overide:
            total = 0
            sources = list()
            for r in results:
                total += int(r.get('limits', {}).get('total', 0))
                sources.append(r['one_meta']['source_id'])

            print '1 SEARCH RESULTS -->>> FOR: "%s" FOUND %s RESULTS FROM %s SOURCES: %s' \
                  % (query, total, len(sources), sources)
            for r in results:
                self.print_result(r)

    @staticmethod
    def print_result(response):
        print '- - - - - - - - - - - - - - - - - - - - - - - '
        result = response.get('result', None)
        if not result:
            result = response.get('result', response)
            print 'No "result" key found response = %s' % response
        result = result.copy()
        limits = result.pop('limits', None)
        one_meta = result.pop('one_meta', {})
        for k, v in one_meta.items():
            print '> %s: %s' % (k, v)
        print '> limits:  %s' % limits
        for k, v in result.items():
            if isinstance(v, list):
                print '> List key = %s:' % k
                One.print_list_of_dicts(v)
            else:
                print '  - %s:%s' % (k, v)

    @staticmethod
    def print_list_of_dicts(l):
        r = 1
        for i in l:
            label = i.get('label', None)
            print '  %s) %s' % (r, ascii(label) or i)
            for k, v in i.items():
                try:
                    print '   %s:%s' % (k, v)
                except UnicodeError as e:
                    print '   *%s' % e
                    print '   %s:%s' % (ascii(k), ascii(v))
            r += 1


class Plugin(object):
    id = None
    prfix = 'plugin://'
    debug = One.debug

    def __init__(self, id=None):
        self.id = self.id or id
        if self.id != 'library.xbmc':
            plugin = xbmcaddon.Addon(self.id)
            self.name = plugin.getAddonInfo('name')
            self.address = self.prfix+self.id
        else:
            self.name = 'XBMC'
            self.address = None

        # Temp cache for tree map results
        self.file_list = []
        self.directory_list = []

    def send_json(self, path=None, params=None, method=None):
        method = method or "Files.GetDirectory"
        json_query = {
            "jsonrpc":"2.0",
            "method": method,
            "params":{
                "properties": ["thumbnail"],
            },
            "id": 1}
        json_query['params'].update(params or {})

        if method == "Files.GetDirectory":
            if not path:
                raise Exception('send_json requires a path when the method is "Files.GetDirectory".')
            directory = self.address+self._get_query_path(path)
            json_query['params']["directory"] = directory

        # exicute server call
        json_query = json.dumps(json_query, ensure_ascii=False).encode('utf8')
        print '1 SEARCH -> Plugin.send_json to (%s):%s' % (self.id, json_query)
        try:
            data = xbmc.executeJSONRPC(uni(json_query))
        except UnicodeEncodeError:
            data = xbmc.executeJSONRPC(ascii(json_query))
        data = uni(data)
        json_obj = json.loads(data)

        # handle errors and debug
        self.print_response(json_obj, path)
        error = json_obj.get('error', None)
        if error:
            print '1 SEARCH -> JSONPRC ERROR: %s' % json_obj

        return json_obj

    def print_response(self, response, description='', overide=False):
        if self.debug or overide:
            print '-----------------------------------------------'
            print '> QUERY: %s' % description
            print '> plugin: %s' % self.name
            print '> response string:  %s' % response
            print '> response type:  %s' % type(response)
            # print dict and nested file list
            if isinstance(response, dict):
                One.print_result(response)
            # print list or string
            elif isinstance(response, list):
                for r in response:
                    One.print_result(r)

                One.print_list_of_dicts(response)
            print '-----------------------------------------------'

    def _map_filter(self, i, filters):
        path = self._get_query_path(i)
        filters = filters or []
        found = False
        for f in filters:
            if re.search(f, path):
                found = True
        if not found:
            path = ''
        if filters[-1] in path:
            self.directory_list.append(i)
        return path

    def _get_query_path(self, i):
        if isinstance(i, dict):
            path = i['file']
        else:
            path = i
        if path:
            path = path.replace(self.address, '')
            return path
        else:
            return None

    def map_tree(self, path, depth=1, filter=None, params=None, current_depth=0):
        """
        :param path: Path to query
        :param depth: Depth of tree to map
        :param filter: Only query file paths containing one of the key words in this list.
        :param current_depth:
        :param params:
        :return:
        """
        # TODO: Need to cache dirs & files and determine when to reset
        # TODO: Make dirs & files sets not lists
        if path:
            # set depth of this recursion
            current_depth += 1
            print '###### CURRENT DEPTH < DEPTH ####### = %s<%s' % (current_depth, depth)
            resp = self.send_json(path=path, params=params)
            results = resp.get('result', resp)
            items = results.get('files', [])
            for i in items:
                if isinstance(i, dict):
                    if i['filetype'] == "directory" and i not in self.directory_list:
                        if filter:
                            n_query = self._map_filter(i, filter)
                        else:
                            n_query = self._get_query_path(i)
                            self.directory_list.append(i)
                        # exicute recursion
                        if not depth or current_depth < depth:
                            print '# EXICUTE RECURSION current_depth < depth = %s<%s' % (current_depth ,depth)
                            self.map_tree(n_query, depth, filter, params, current_depth)
                    elif i['filetype'] == "file" and i not in self.file_list:
                        self.file_list.append(i)
        return (self.directory_list, self.file_list)

    # generic map queries
    def find_top_level(self):
        dirs, files = self.map_tree("/", depth=1)
        self.print_response(self.directory_list, 'get_top_level: directory list')
        return dirs

    def find_files(self):
        dirs, files = self.map_tree("/", depth=2, filter=['section', 'all'])
        self.print_response(self.file_list, 'get files: file list')
        return files

    def find_search_dirs(self):
        dirs, files = self.map_tree("/", depth=2, filter=['section', 'search'])
        self.print_response(dirs, 'get_search_dirs: directory list')
        return dirs

    def search_batch(self, batch):
        """ Exicute a search on a dictionary of paths.
        Currently this is the end method.

        :param batch:       List of search query dictionaries with keys:
                            'media_type', 'media_label', 'params', 'path', 'method'
        :return:
        """
        results = list()
        for search in batch:
            media_type = search.get('media_type')
            media_label = search.get('media_label', media_type.capitalize())
            print '1 SEARCH -----> START SEARCH %s / section:%s' % (media_type, media_label)
            search_path = search.get('path', None)
            params = search.get('params', None)
            method = search.get('method', None)
            pid = search.get('pid', None)
            print '1 SEARCH -----> search_batch got pid: %s' % pid

            # hit the server
            resp = self.send_json(path=search_path, params=params, method=method)
            result = resp.get('result', resp)
            result['one_meta'] = {'source_id': self.id,
                                  'source_name': self.name,
                                  'media_type': media_type,
                                  'media_label': media_label,
                                  'parent_path': search_path}

            # get items from key "files" or media_type
            items = result.pop('files', None) or result.pop(media_type, [])
            for i in items:
                i['id'] = self.get_item_id(i.get('file', None), i)
                i['pid'] = pid or self.get_item_id(search_path, i)
                i['file'] = self.get_file_path(media_type, i)
                self.modify_result_item(media_type, i)
                print '## 1 SEARCH ---PID--> %s for %s assigned pid: %s' % (self.id, media_type, ['pid'])

            result[media_type] = items
            results.append(result)

            self.print_response(results, '%s RESUlTS' % media_type.upper())
        return results

    def get_params(self, media_type, search_str=None, pid=None):
        """ Initiates search process for each plugin.
        """
        print '1 SEARCH -----> get_params got pid: %s' % pid
        if media_type == 'movies':
            params = {
                "properties": ["title", "streamdetails", "genre", "studio", "year", "tagline", "plot", "plotoutline", "runtime", "fanart", "thumbnail", "file", "trailer", "playcount", "rating", "mpaa", "director", "writer"],
                "sort": { "method": "label" },
                "filter": {"field":"title","operator":"contains","value": search_str}}

        elif media_type == 'actors':
            params = {
                "properties": ["title", "streamdetails", "genre", "studio", "year", "tagline", "plot", "plotoutline", "runtime", "fanart", "thumbnail", "file", "trailer", "playcount", "rating", "mpaa", "director", "writer"],
                "sort": { "method": "label" },
                "filter": {"field":"actor","operator":"contains","value": search_str}}

        elif media_type == 'tvshows':
            params = {
                "properties": ["title", "genre", "studio", "premiered", "plot", "fanart", "thumbnail", "playcount", "year", "mpaa", "episode", "rating", "art"],
                "sort": { "method": "label" },
                "filter": {"field": "title", "operator": "contains", "value": search_str}}

        elif media_type == 'seasons':
            params = {
                "properties": ["showtitle", "season", "fanart", "thumbnail", "playcount", "episode"],
                "sort": { "method": "label" },
                "filter": {"field": "season", "operator": "contains", "value": search_str}}
        elif media_type == 'episodes':
            params = {
                    "properties": ["title", "streamdetails", "plot", "firstaired", "runtime", "season", "episode", "showtitle", "thumbnail", "fanart", "file", "playcount", "director", "rating"],
                    "sort": { "method": "title" },
                    "filter": {"field": "title", "operator": "contains", "value": search_str}}
        elif media_type == 'musicvideos':
            params = {
                "properties": ["title", "streamdetails", "runtime", "genre", "studio", "artist", "album", "year", "plot", "fanart", "thumbnail", "file", "playcount", "director"],
                "sort": { "method": "label" },
                "filter": {"field": "title", "operator": "contains", "value": search_str}}

        elif media_type == 'artists':
            params = {
                "properties": ["genre", "description", "fanart", "thumbnail", "formed", "disbanded", "born", "yearsactive", "died", "mood", "style"],
                "sort": { "method": "label" },
                "filter": {"field": "artist", "operator": "contains", "value": search_str}}

        elif media_type == 'albums':
            params = {
                "properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "theme", "type", "mood", "style", "rating"],
                "sort": { "method": "label" },
                "filter": {"field": "album", "operator": "contains", "value": search_str}}
        elif media_type == 'songs':
            params = {
                "properties": ["title", "artist", "album", "genre", "duration", "year", "file", "thumbnail", "fanart", "comment", "rating", "track", "playcount"],
                "sort": { "method": "title" },
                "filter": {"field": "title", "operator": "contains", "value": search_str}}
        else:
            params = {}

        return params

    def search(self, search_str, media_type, pid=None):
        """ Initiates search process for each plugin.
        """
        print '1 SEARCH -----> %s for %s' % (self.id, 'make_%s_batch' % media_type)
        print '1 SEARCH -----> search got pid: %s' % pid
        # check if the plugin supports the media_type
        make_batch = getattr(self, 'make_%s_batch' % media_type, None)
        # provide a search object
        if make_batch:
            search = {
                'media_type': media_type,
                'media_label': media_type.capitalize(),
                'path': None,
                'method': None,
                'params': self.get_params(media_type, search_str, pid),
                'pid': pid
            }
            batch = make_batch(search_str, search)
            return self.search_batch(batch)
        return []

    def remove_properties(self, search, remove_list):
        properties = search['params']['properties']
        for r in remove_list:
            properties.remove(r)
        return properties

    def get_item_id(self, path, item):
        """ Hook to extract the item id
        """
        return None

    def get_file_path(self, path, item):
        return item['file']

    def modify_result_item(self, media_type, item):
        """ Provides a hook perform any required modifications to result items.
        """
        return item


class Youtube(Plugin):
    id = 'plugin.video.youtube'

    '''
    def search(self, search_str, media_types=None):
        # direct queries
        batch = list()
        batch.append({'media_type':'videos',
                      'path':'/kodion/search/query/?q=%s' % search_str})
        results = self.search_batch(batch, media_types)

        return results
    '''

    def make_videos_batch(self, search_str, search):
        batch = list()
        search['path'] = '/kodion/search/query/?q=%s' % search_str
        batch.append(search)
        return batch

One.register(Youtube)

class Xbmc(Plugin):
    id = 'library.xbmc'
    prefix = ''

    def make_movies_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetMovies"
        return [search]

    def make_tvshows_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetTVShows"
        return [search]

    def make_episodes_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetEpisodes"
        params = search['params']
        pid = search['pid']
        if pid:
            del params['filter']
            params['tvshowid'] = pid
        return [search]

    def make_seasons_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetSeasons"
        params = search['params']
        pid = search['pid']
        if pid:
            del params['filter']
            params['tvshowid'] = pid
        return [search]

    def make_actors_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetMovies"
        return [search]

    def make_musicvideos_batch(self, search_str, search):
        search['method'] = "VideoLibrary.GetMusicVideos"
        return [search]

    def make_artists_batch(self, search_str, search):
        search['method'] = "AudioLibrary.GetArtists"
        return [search]

    def make_albums_batch(self, search_str, search):
        search['method'] = "AudioLibrary.GetAlbums"
        params = search['params']
        pid = search['pid']
        if pid:
            del params['filter']
            params['artistid'] = pid
        return [search]

    def make_songs_batch(self, search_str, search):
        search['method'] = "AudioLibrary.GetSongs"
        params = search['params']
        pid = search['pid']
        if pid:
            del params['filter']
            params['artistid'] = pid
        return [search]

    def get_item_id(self, path, item):
        ids = ['tvshowid', 'artistid', 'albumid']
        for i in ids:
            id = item.get(i, None)
            if id:
                print '%s found item id: %s' % (self.id, id)
                return id
        return None

    def get_file_path(self, media_type, i):
        # for xbmc we must manually build a file path using the parent id
        if media_type == 'tvshows':
            tvshowid = i.get('tvshowid', '')
            path = 'videodb://tvshows/titles/' + str(tvshowid) + '/'

        elif media_type == 'seasons':
            # pid is tvshowid for xbmc
            tvshowid = i.get('pid', '') #TODO: Add tvshow id to each season result on search
            path =  'videodb://tvshows/titles/' + str(tvshowid) + '/' + str(i['season']) + '/'

        elif media_type == 'artists':
            artistid = i.get('artistid', None)
            path = 'musicdb://artists/' + str(artistid) + '/'

        elif media_type == 'albums':
            albumid = i.get('albumid', None)
            path = 'musicdb://albums/' + str(albumid) + '/'
        else:
            path = i['file']
        return path


One.register(Xbmc)

class Plexbmc(Plugin):
    id = 'plugin.video.plexbmc'

    def __init__(self):
        super(Plexbmc, self).__init__()
        self.sections = self.find_sections()

    def find_sections(self):
        dirs, files = self.map_tree("/", depth=1, filter=['section'])
        self.print_response(dirs, 'get sections')
        return dirs

    def make_search_path(self, s, s_type, query, mode=None):
        """ Convert a section path to search path.

        :param s: The section result
        :param s_type: The search type
        :param query: The search query string
        :param mode: The pexbmc result mode (seems not required for search)

        # s_type       section  search
        # -------    -------  ------
        # movies:    1        type=1
        # shows      2        type=2
        # episodes   2        type=4
        # tracks     4        type=10
        # albums     4        type=9
        # artists    4        type=8

        """
        file = s['file']
        if re.search('sections/\d&', file):
            path = re.sub('sections/(\d+)&', 'sections/\g<1>/search?type=%s&'% s_type, file)
            if mode:
                path = re.sub('mode=\d+', 'mode=%s' % mode, path)
            path = '%s&query=%s' % (path, query)
            path = self._get_query_path(path)
        else:
            path = ''
        return path

    def get_batch_from_sections(self, key_word, search, search_str, s_type):
        batch = list()
        # todo: test filter with plex
        # todo: test append pid to search path
        search['params'].pop('filter', None)
        for s in self.sections:
            media_label = s['label']
            label = media_label.lower()
            if key_word in label:
                search['media_label'] = media_label
                search['path'] = self.make_search_path(s, s_type=s_type, query=search_str)
                batch.append(search)
        return batch

    def make_movies_batch(self, search_str, search):
        # if params need to be altered modify search search['params'] here
        return self.get_batch_from_sections('movie', search, search_str, 1)

    def make_tvshows_batch(self, search_str, search):
        return self.get_batch_from_sections('show', search, search_str, 2)

    def make_episodes_batch(self, search_str, search):
        return self.get_batch_from_sections('show', search, search_str, 4)

    def make_artists_batch(self, search_str, search):
        remove = ["formed", "disbanded", "born", "yearsactive", "died", "mood", "style"]
        self.remove_properties(search, remove)
        return self.get_batch_from_sections('music', search, search_str, 8)

    def make_albums_batch(self, search_str, search):
        return self.get_batch_from_sections('music', search, search_str, 9)

    def make_songs_batch(self, search_str, search):
        return self.get_batch_from_sections('music', search, search_str, 10)

    def get_item_id(self, path, item):
        match = re.search('library/metadata/(\d+)[^\d].*', path)
        # return a tuple (path,id)
        if match:
            # path = match.group(0)
            return match.group(1)
        return '', None


One.register(Plexbmc)