import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import numpy as np

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
 


def random_walk(graph, parent, n_steps, query_limit=10, album_type='single'):
    """
    """
    artist_node = search_artist(parent)
    add_artist(graph, artist_node)
    random_walk = []

    while len(random_walk) < n_steps:
        singles = get_albums(graph.nodes[parent], type=album_type, limit=query_limit)
        random_walk.append(parent)
        neighbors = []
        # add edges
        for single in singles['items']:
            for artist in single['artists']:
                if artist['name'] not in graph and artist['name']!=parent:
                    add_artist(graph, artist)
                    add_song(parent, artist['name'], single)
                    neighbors.append(artist['name'])
        # pick next node
        # allow backtracking
        neighbors.append(parent)
        parent = np.random.choice(list(neighbors), 1)[0]

    print(list(graph.nodes))
    print(list(graph.edges))
    return random_walk


graph = nx.Graph()
random_walk(graph, 'Drake', 10)

nx.draw(graph, with_labels = True)

# Set margins for the axes so that nodes aren't clipped
ax = plt.gca()
ax.margins(0.20)
plt.axis("off")
plt.show()