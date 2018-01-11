import datetime
import json
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

from urllib import FancyURLopener
from simplecache import SimpleCache

ADDON        = xbmcaddon.Addon()
ADDON_ID     = ADDON.getAddonInfo('id')
ADDON_NAME   = ADDON.getAddonInfo('name')
ADDON_BASE   = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ICON         = ADDON.getAddonInfo('icon')
LANGUAGE     = ADDON.getLocalizedString

url = ADDON.getSetting('url')

def log(msg, level=xbmc.LOGNOTICE):
#    level=xbmc.LOGERROR
    xbmc.log(ADDON_ID + ' - ' + msg, level)

def parseArgs():
    args = urlparse.parse_qs(sys.argv[2][1:])
    # args is a dictionary with the values in lists
    series = args.get('series', None)
    if series:
        series = int(series[0])
    season = args.get('season', None)
    if season:
        season = int(season[0])
    view = args.get('view', None)
    # 1: episodes, 2: seasons
    if view:
        view = int(view[0])
    return series, season, view

def retrieveCatalog():
    try:
        cache = SimpleCache()
        catalog = cache.get(ADDON_NAME + '.catalog')
        if catalog:
            log("using cached catalog")
        if not catalog:
            log("downloading catalog")
            opener = FancyURLopener()
            f = opener.open(url)
            catalog = json.load(f)
            cache.set(ADDON_NAME + '.catalog', catalog,
                      expiration=datetime.timedelta(hours=12))
        return catalog
    except Exception as e:
        log("error retrieving catalog - " + str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)

def getValue(dic, key1, key2=None, key3=None):
    try:
        if key3:
            return dic[key1][key2][key3]
        if key2:
            return dic[key1][key2]
        else:
            return dic[key1]
    # return empty string if there is a KeyError
    except:
        return ''

def listSeries():
    xbmcplugin.setContent(ADDON_HANDLE, 'tvshows')
    try:
        for i,d in enumerate(data):
            li = xbmcgui.ListItem(getValue(d, 'title'), getValue(d, 'tagline'))
            li.setArt({
                'thumb'    : getValue(d, 'cover', 'path'),
                'poster'   : getValue(d, 'cover', 'path'),
                'fanart'   : getValue(d, 'cover_image', 'path'),
                'clearart' : getValue(d, 'logo', 'path'),
                'clearlogo': getValue(d, 'logo', 'path')
            })
            li.setInfo('video', {
                'plot':        getValue(d, 'plot'),
                'plotoutline': getValue(d, 'tagline'),
                'trailer':     getValue(d, 'cover_video', 'path')
            })
            url = ADDON_BASE + '?series=' + str(i) + '&view=1'
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, url=url, listitem=li,
                                        isFolder=True)
    except Exception as e:
        log("error showing series list - " + str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(series, season=0):
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    try:
        xbmcplugin.setPluginCategory(ADDON_HANDLE,
                                     getValue(data, series, 'title'))
        xbmcplugin.setPluginFanart(ADDON_HANDLE,
                                   getValue(data, series, 'cover_image',
                                            'path'))
        episodes = data[series]['seasons']['data'][season]['episodes']['data']
        for ep in episodes:
            li = xbmcgui.ListItem(getValue(ep, 'title'),
                                  getValue(ep, 'tagline'))
            li.setArt({
                'thumb' : getValue(ep, 'videos', 'screenshots', 'path'),
                'poster': getValue(ep, 'cover', 'path')
            })
            li.setInfo('video', {
                'episode'    : getValue(ep, 'number'),
                'season'     : str(season + 1),
                'plot'       : getValue(ep, 'synopsis', 'long'),
                'plotoutline': getValue(ep, 'synopsis', 'short'),
                'title'      : getValue(ep, 'title'),
                'tagline'    : getValue(ep, 'tagline')
            })
            xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                        getValue(ep, 'videos', 'hls', 'path'),
                                        listitem=li)
    except Exception as e:
        log("error showing episode list - " + str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def setViewMode(mode):
    skin = xbmc.getSkinDir()
    modes = {
        'infowall': {
            'skin.estuary': 54
        },
        'poster': {
            'skin.estuary': 51
        }
    }
    if mode in modes and skin in modes[mode]:
        xbmc.executebuiltin('Container.SetViewMode(%d)' % modes[mode][skin])

# if url not set, exit and show addon settings
if not url:
    log("No source URL set. Exiting.", xbmc.LOGWARNING)
    xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
    xbmc.executebuiltin('Action(PreviousMenu)')
    xbmc.executebuiltin('Addon.OpenSettings(%s)' % ADDON_ID)
    sys.exit(0)

catalog = retrieveCatalog()
data = catalog['data']
meta = catalog['__meta']

series, season, view = parseArgs()
if (view == 1):
    listEpisodes(series)
    setViewMode('infowall')
else:
    listSeries()
    setViewMode('poster')
