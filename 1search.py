import xbmcaddon
import xbmcgui
import xbmc
import os
import sys
import re
import json


__addon__ = xbmcaddon.Addon()
__plugin__ = __addon__.getAddonInfo('name')
__addonid__ = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__     = __addon__.getLocalizedString
__icon__ = __addon__.getAddonInfo('icon')
__cachedir__ = __addon__.getAddonInfo('profile')
__settings__ = xbmcaddon.Addon(id='plugin.program.1.search')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8')

BASE_RESOURCE_PATH = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
PLUGINPATH = xbmc.translatePath(os.path.join(__cwd__))
sys.path.append(BASE_RESOURCE_PATH)
PLEX_CACHEDATA = __cachedir__
ONE_VERSION = __addonversion__

'''
# test for plexbmc
try:
    plexbmc_addon = xbmcaddon.Addon ('plugin.video.plexbmc')
except:
    plexbmc_addon = False

# add plex to path
if plexbmc_addon:
    plexbmc_path = plexbmc_addon.getAddonInfo('path')
    print 'plexbmc_path = %s' % plexbmc_path
    sys.path.append (xbmc.translatePath( os.path.join( plexbmc_path,'resources', 'lib' ) ))
    from plexgdm import plexgdm

    print 'plexbmc server list=%s' % plexgdm().getServerList()

    plexbmc_profile = plexbmc_addon.getAddonInfo('profile')
    print 'plexbmc_profile=%s' % plexbmc_profile
'''




#ustv now directory
#ustv_files = get_search_dirs("plugin.video.ustvnow/live?mode=live")
'''
from one import Plexbmc
plexbmc = Plexbmc()
params = {"properties":["art", "genre", "plot", "title", "originaltitle", "year", "rating", "thumbnail", "playcount", "file", "fanart"],
          "sort": { "method": "label"}
}
resp = plexbmc.send_json('?url=http%3A//192.168.1.102%3A32400/library/metadata/8958/&mode=1', params)
plexbmc.print_response(resp, 'TEST query', True)
#youtube = Youtube()
'''

# get top level directories
print '1 SEARCH -> STARTED'
#one = One()
#one.search('saul')

# all path
#plugin://plugin.video.plexbmc/?url=http%3A//192.168.1.102%3A32400/library/sections/2/all&mode=0
# search path
#plugin://plugin.video.plexbmc/?url=http%3A//192.168.1.102%3A32400/library/sections/2/search%3Ftype%3D4&mode=0


if ( __name__ == "__main__" ):
    searchstring = ''
    try:
        params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        searchstring = params.get("searchstring")
        searchstring = urllib.unquote_plus(searchstring)
    except:
        keyboard = xbmc.Keyboard( '', __language__(32101), False )
        print '1 SEARCH -> D0 MODAL for KEYBOARD'
        keyboard.setDefault(searchstring)
        keyboard.doModal()
        if ( keyboard.isConfirmed() ):
            searchstring = keyboard.getText()
    if searchstring:
        print '1 SEARCH ->  START GUI'
        import gui
        ui = gui.GUI( "script-globalsearch-main.xml", __cwd__, "Default", searchstring=searchstring )
        print '1 SEARCH -> D0 MODAL for GUI'
        ui.doModal()
        del ui
print '1 SEARCH -> ENDED'

''' this is good!
# get all video plugins
json_query = uni('{"jsonrpc":"2.0","method":"Addons.GetAddons","params":{"type":"xbmc.addon.video","content":"video","enabled":true,"properties":["path","name"]}, "id": 1 }')
plugins_files = get_files(json_query)
'''

#xbmcgui.Dialog().ok(addonname, str(plex), line2, line3)

'''
#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
class ListDiag(xbmcgui.Window):
  def __init__(self):
    self.strActionInfo = xbmcgui.ControlLabel(250, 80, 200, 200, '', 'font14', '0xFFBBBBFF')
    self.addControl(self.strActionInfo)
    self.strActionInfo.setLabel('Push BACK to quit')
    self.list = xbmcgui.ControlList(200, 150, 800, 400)
    self.addControl(self.list)
    self.setFocus(self.list)

  def onAction(self, action):
    if action == ACTION_PREVIOUS_MENU:
      self.close()

  def onControl(self, control):
    if control == self.list:
      item = self.list.getSelectedItem()
      self.message('You selected : ' + item.getLabel())

  def message(self, message):
    dialog = xbmcgui.Dialog()
    dialog.ok(" My message title", message)

  def add_items(self, lc):
      for i in lc:
        self.list.addItem(str(i))


print 'plex_files', plex_files
mydisplay = ListDiag()
mydisplay.add_items(plex_files)
mydisplay.doModal()
del mydisplay
'''