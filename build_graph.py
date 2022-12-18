import os
from dotenv import load_dotenv
from typing import Dict, List

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc


def add_artist(graph: nx.Graph, artist: Dict) -> None:
    """ Adds new artist node to graph
    Args:
        graph: graph object to add new artist node to
        artist: artist data from Spotify API, must have uri, name, id, and href
    """
    graph.add_node(
        artist['name'],
        uri=artist['uri'],
        id=artist['id'],
        href=artist['href']
    )

def add_song(graph, artist_parent, artist_child, song_data) -> None:
    """ Adds new collaboration edge between two artist nodes
    Args:
        graph: graph object to add new collaboration edge to
        artist_parent: source node
        artist_child: target node
        song_data: song data from Spotify API
    """
    graph.add_edge(
        artist_parent,
        artist_child,
        name=song_data['name'],
        uri=song_data['uri'],
        id=song_data['id']
    )

def search_artist(artist_name: str, sp) -> Dict:
    """
    Args:
        artist_name: string name used to search for artist on Spotify API
        sp:
    Returns: 

    """
    artist_query_result = sp.search(
        q='artist:' + artist_name, 
        type='artist', 
        limit=1
    )
    return artist_query_result['artists']['items'][0]

def get_albums(artist: nx.Graph, sp, type: str='single', limit: int=20, country:str='US') -> Dict:
    """ Retrieves a set number of albums from spotify. 
    There is no guarantee each album or single will have features.
    This function can be used to query albums or singles.
    Args:
        artist: artist node to use in search for albums
        sp:
        type: 'single' or 'album'
        limit: number of albums 
        country: data availability
    Returns:
        Dictionary of results from API query, dict of songs
    """
    album_query_result = sp.artist_albums(
        artist['id'],
        album_type=type, 
        limit=limit,
        country=country
    )
    return album_query_result
 


def random_walk(graph: nx.Graph, sp, parent: str, n_steps: int, query_limit: int=20, album_type: str='single') -> List:
    """ Using artist name as seed for random walk of Spotify API calls.
    Retrieves song and features (if found) from Spotify call and adds 
    new neighbor nodes and edges to graph.
    Args:
        graph: network graph to add nodes to
        sp:
        parent: seed for first step in random walk
        n_steps: number of steps in random walk
        query_limit: maximum number of songs to return from Spotify
        album_type: 'single' or 'album'
    Returns:    
        List of nodes visited during random walk
    """
    # adding first node in random walk to graph 
    artist_node = search_artist(parent, sp)
    add_artist(graph, artist_node)

    random_walk = []
    while len(random_walk) <= n_steps:
        singles = get_albums(graph.nodes[parent], sp, type=album_type, limit=query_limit)
        random_walk.append(parent)
        neighbors = []
        # add edges between parent node and new neighbors
        for single in singles['items']:
            for artist in single['artists']:
                if artist['name'] not in graph and artist['name']!=parent:
                    add_artist(graph, artist)
                    add_song(graph, parent, artist['name'], single)
                    neighbors.append(artist['name'])
        # pick next random node, allow backtracking
        neighbors.append(parent)
        parent = np.random.choice(list(neighbors), 1)[0]

    return random_walk

def networkx_to_cyto(graph, path):
    """ Converts NetworkX graph data to format accepted by Dash Cytoscape.
    Ability to highlight random walk path may be moved elsewhere...
    Args:
        graph: graph with artist and song data, represented as nodes and edges, respectively.
        path: List of nodes visited during random walk. Different styling applied by default
    Returns:
        node data and edge data represented in format accepted by Dash Cytoscape graph

    """
    nodes = []
    nx_node_data = list(graph.nodes)
    n_steps = len(nx_node_data)
    for i, node in enumerate(nx_node_data):
        data = {'data':{'id': node, 'label': node}}
        # highlight all path nodes and edges
        if node in path:
            data['classes']='path'
            # highlight start and end of random walk
            if i==0 or i==(n_steps-1):
                data['classes']='anchor'
        else:
            data['classes']='basic'
        nodes.append(data)

    edges = []
    for edge in list(graph.edges):
        data = {'data':{'source': edge[0], 'target': edge[1], 'label':'single'}}
        if edge[0] in path and edge[1] in path:
            data['classes']='path'
        else:
            data['classes']='basic'
        edges.append(data)

    return nodes, edges

def main():

    load_dotenv('../featuring_network.env')
    client = os.getenv('SPOTIFY_CLIENT', 'client')
    secret = os.getenv('SPOTIFY_SECRET', 'secret')

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client, client_secret=secret))

    graph = nx.Graph()
    path = random_walk(graph, sp, 'Elton John', 20)

    nodes, edges = networkx_to_cyto(graph, path)

    data = nodes
    data.extend(edges)

    # dash app
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Collaboration Network", style={'textAlign': 'center'})
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(['Drake', 'Snoop Dogg', 'Elton John', 'Kendrick Lamar', 'Britney Spears'], 'Drake', id='artist-dropdown'),
            ], width=4),
            dbc.Col(
                html.Div(children=[
                    cyto.Cytoscape(
                        id='cytoscape',
                        elements=[],
                        layout={'name': 'cose'},
                        responsive=True,
                        stylesheet=[
                            # Group selectors
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'color': '#000000',
                                    'background-color': '#d8d8d8'  
                                }
                            },
                            # Class selectors
                            {
                                'selector': '.path',
                                'style': {
                                    'background-color': '#ffa600',
                                    'line-color': '#ffa600'
                                }
                            },
                            {
                                'selector': '.basic',
                                'style': {
                                    'background-color': '#2f4b7c',
                                    'line-color': '#2f4b7c'
                                }
                            },
                            {
                                'selector': '.anchor',
                                'style': {
                                    'background-color': '#f95d6a',
                                    'line-color': '#f95d6a'
                                }
                            }
                        ]
                    )
                ]), width=8)
        ])
    ]
    
    # style={
    # 'background-color': '#1E1E1E',
    # 'color': '#d8d8d8',
    # 'margin': 0,
    # 'padding': 0
    # }
    )




    @app.callback(
        Output("cytoscape", "elements"),
        Input('artist-dropdown', 'value'),
        State("cytoscape", "elements"),

    )
    def update_output(value, el):
        #https://community.plotly.com/t/remove-all-elements-in-cytoscape/51810/5
        client = os.getenv('SPOTIFY_CLIENT', 'client')
        secret = os.getenv('SPOTIFY_SECRET', 'secret')

        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client, client_secret=secret))
        graph = nx.Graph()
        path = random_walk(graph, sp, value, 20)

        nodes, edges = networkx_to_cyto(graph, path)

        data = nodes
        data.extend(edges)
        elements = data
        return elements #if el == [] else []








    app.run_server(debug=True)


main()