import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import networkx as nx


load_dotenv('../featuring_network.env')
client = os.getenv('SPOTIFY_CLIENT', 'client')
secret = os.getenv('SPOTIFY_SECRET', 'secret')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client, client_secret=secret))

def add_artist(graph, artist):
    """
    """
    graph.add_node(
        artist['name'],
        uri=artist['uri'],
        id=artist['id'],
        href=artist['href']
    )


def add_song(artist_parent, artist_child, song_data):
    """
    """
    graph.add_edge(
        artist_parent,
        artist_child,
        name=song_data['name'],
        uri=song_data['uri'],
        id=song_data['id']
    )

def search_artist(artist_name):
    """
    """
    artist_query_result = sp.search(
        q='artist:' + artist_name, 
        type='artist', 
        limit=1
    )
    return artist_query_result['artists']['items'][0]

def get_albums(artist, type='single', limit=20, country='US'):

    album_query_result = sp.artist_albums(
        artist['id'],
        album_type=type, 
        limit=limit,
        country=country
    )
    return album_query_result
 


graph = nx.Graph()
seed = 'Drake'
drake = search_artist(seed)
print(drake)
add_artist(graph, drake)
print(list(graph.nodes))
singles = get_albums(graph.nodes[seed], type='single', limit=30)

for single in singles['items']:
    for artist in single['artists']:
        if artist['name'] not in graph and artist['name']!=seed:
            add_artist(graph, artist)
            add_song(seed, artist['name'], single)


print(list(graph.nodes))
print(list(graph.edges))
