import os

import spotipy
import spotipy.util as util
from wavelink.ext import spotify

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI') 
spotify_scope = 'user-library-read playlist-read-private user-modify-playback-state'

username = os.getenv('SPOTIFY_USERNAME')
token = util.prompt_for_user_token(
    username=username, 
    scope=spotify_scope, 
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET, 
    redirect_uri=redirect_uri
    )

sp = spotipy.Spotify(auth=token)
sp_wavelink = spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)


# The below is not implemented and proven difficult to work with in current versions, hopeful to be revisited
# @bot.command(name='splay')
# async def splay(ctx: commands.Context, query: str):
#     """Play type of playlist from Spotify"""
#     if not getattr(ctx.author.voice, "channel", None):
#         ctx.send('Sorry, I can only play in voice channels!')
#     vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)
#     results = sp.search(q='bardic-inspiration:combat', type='playlist')
#     playlist = next((p for p in results['playlists']['items'] if p['owner']['display_name'] == 'Landon Turner'))
#     tracks = sp.playlist_tracks(playlist_id=playlist.get('id'), fields='items',additional_types=('track',))
#     # print(tracks['items'][0]['track']['external_urls']['spotify'])
#     track_url = tracks['items'][0]['track']['external_urls']['spotify']
#     decoded = spotify.decode_url(track_url)
#     if not decoded or decoded['type'] is not spotify.SpotifySearchType.track:
#         await ctx.send('Sorry, I had an issue finding the lyrics to a song.')
#         return
#     try:
#         vc.autoplay = True
#         track = find_track(track_url)
#         # track = await spotify.SpotifyTrack.search(track_url)
#         if vc.queue.is_empty and not vc.is_playing():
#             print('evry ting ire')
#             await vc.play(track, populate=True)
#             print('everyting still ire')
#             await ctx.send(f'Playing `{tracks.title}`')
#         else:
#             await vc.queue.put_wait(track)
#     except Exception as e:
#         print('damn', e)
#         print(traceback.print_exc())
       
#         return await ctx.send("oops")

# # @tasks.loop(seconds=5)
# async def find_track(query):
#     """Finds the track using the wavelink Spotify extensions. Has to run in it's own async function."""
#     track = await spotify.SpotifyTrack.search(query)
#     print('track', track)
#     return track