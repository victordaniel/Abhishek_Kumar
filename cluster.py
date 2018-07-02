"""
cluster.py

Read data from previous.
Create a graph for users and their follows.
Cluster users into communities.
"""


from collections import Counter, defaultdict, deque
import matplotlib.pyplot as plt
import networkx as nx
import sys
import pickle
import math
from itertools import chain, combinations


def get_user_info(name):
    """
    load stored user info, list of dicts
    (screen_name, id, friends_id)
    """
    
    with open(name + '.pkl', 'rb') as val:
        return pickle.load(val)


def print_num_friends(users):
    """
    Print the number of friends of each user, sorted by candidate name.
    
    Args:
        users....The list of user dicts.
    Returns:
        Nothing
    """
    
    for usern in users:
        num_friends = str(len(usern['friends_id']))
        print (usern['screen_name'] + ' ' + num_friends)


def count_friends(users):
    """
    Count how often each friend is followed.
    
    Args:
        users: a list of user dicts
    Returns:
        a Counter object mapping each friend to the number of candidates who follow them.
        Counter documentation: https://docs.python.org/dev/library/collections.html#collections.Counter
    """
    friends = []

    upd = Counter()
    for user in users:
        #list of friends of each user
        friends.append(user['friends_id'])
    for friend in friends:
        #count each friend in friends[] and update the counter
        upd.update(friend)
        
    return upd


def create_graph(users, friend_counts, min_common):
    """
    Create a networkx undirected Graph, adding each user and their friends
    as a node.
    Note: while all users should be added to the graph,
    Each user in the Graph will be represented by their screen_name,
    while each friend will be represented by their user id.

    Args:
      users...........The list of user dicts.
      friend_counts...The Counter dict mapping each friend to the number of candidates that follow them.
      min_common......Add friends to the graph if they are followed by more than min_common users.
    Returns:
      A networkx Graph
    """

    follow = [x for x in friend_counts if friend_counts[x] > min_common]
    
    graph = nx.Graph()
    for x in follow:
        graph.add_node(x)
    #add users nodes
    for user in users:
        graph.add_node(user['id'])
        #list of friends should be plotted
        fndlst = set(user['friends_id']) & set(follow)
        #add edges for each node
        for fnd in fndlst:
            graph.add_edge(fnd, user['id'])

    nx.draw_networkx(graph, with_labels=True)
    
    return graph


def draw_network(graph, users, filename):
    """
    Draw the network to a file.
    Only label the candidate nodes; the friend
    nodes should have no labels (to reduce clutter).

    params:
        graph...........the undirected graph created
        users...........list of dicts
        filename........the name of the saved network figure
    """

    #only users have lables
    label = {}
    for n in graph.nodes():
        for u in users:
            if n in u['id']:
                label[n] = u['screen_name']
    
    plt.figure(figsize=(15, 15))
    plt.axis('off')

    nx.draw_networkx(graph, labels=label, alpha=.5, node_size=100, width=.5)
    plt.savefig(filename)


def get_subgraph(graph, min_degree):
    """
    Return a subgraph containing nodes whose degree is
    greater than or equal to min_degree.
    To prune the original graph.

    Params:
      graph........a networkx graph
      min_degree...degree threshold
    Returns:
      a networkx graph, filtered as defined above.
    """
    
    sub_nodes = []
    node_list = graph.nodes()
    for node in node_list:
        if graph.degree(node) >= min_degree:
            sub_nodes.append(node)
    subgraph = graph.subgraph(sub_nodes)

    return subgraph


def bfs(graph, root, max_depth):
    """
    Perform breadth-first search to compute the shortest paths from a root node to all
    other nodes in the graph. To reduce running time, the max_depth parameter ends
    the search after the specified depth.

    Params:
      graph.......A networkx Graph
      root........The root node in the search graph (a string). We are computing
                  shortest paths from this node to all others.
      max_depth...An integer representing the maximum depth to search.

    Returns:
      node2distances...dict from each node to the length of the shortest path from
                       the root node
      node2num_paths...dict from each node to the number of shortest paths from the
                       root node that pass through this node.
      node2parents.....dict from each node to the list of its parents in the search
                       tree
    """

    node2parents = {}
    node2distances = {}
    node2num_paths = {}
    visiting = deque()
    visited = deque()
    
    nodes = graph.nodes()
    visited={x:"No" for x in nodes}
    visiting.append(root)
    distance= {x:float("inf") for x in nodes}
    distance[root] = 0
    parents = {x:[] for x in nodes} 
    parents[root] = root
  
    while(len(visiting) > 0):
        c = visiting.popleft()
        child = graph.neighbors(c)
            
        for node in child:
            if(distance[c] > max_depth):
                break
            if(visited[node] == "No"):
                if(distance[node] < distance[c]):
                    break
                elif(distance[node] > distance[c] ):
                    distance[node] = distance[c] + 1
                    parents[node].append(c)
                    visiting.append(node)

        visited[c] = "Yes"
        
    for node in visited:
        if(visited[node] == "Yes"):
            node2distances[node] = distance[node]
            node2num_paths[node] = len(parents[node])
            if(node != root):
                node2parents[node] = parents[node]

    return node2distances, node2num_paths, node2parents
    
def friend_overlap(users):
    """
    Compute the number of common friends of each pair of users.

    Args:
        users...The list of user dicts.

    Return:
        A list of tuples containing (user1, user2, N), where N is the
        number of friends that both user1 and user2 follow.
        This list shouldbe sorted in descending order of N.
        Ties are broken first by user1's screen_name, then by
        user2's screen_name (sorted in ascending alphabetical order).
    """

    pointer = 0
    friend_overlap = []
    overlap = tuple()
    
    for i in range(0, len(users)):
        for j in range(i+1, len(users)):
            for m in range(0, len(users[i]['friends_id'])):
                for n in range(0, len(users[j]['friends_id'])):
                    if users[i]['friends_id'][m] == users[j]['friends_id'][n]:
                        pointer += 1
            overlap = (users[i]['screen_name'], users[j]['screen_name'], pointer)
            friend_overlap.append(overlap)
            pointer = 0

    friend_overlap = sorted(friend_overlap, key=lambda tup: (-tup[2], tup[0], tup[1]))

    return friend_overlap



def bottom_up(root, node2distances, node2num_paths, node2parents):
    """
    Compute the final step of the Girvan-Newman algorithm.

    Params:
      root.............The root node in the search graph (a string). We are computing
                       shortest paths from this node to all others.
      node2distances...dict from each node to the length of the shortest path from
                       the root node
      node2num_paths...dict from each node to the number of shortest paths from the
                       root node that pass through this node.
      node2parents.....dict from each node to the list of its parents in the search
                       tree
    Returns:
      A dict mapping edges to credit value. Each key is a tuple of two strings
      representing an edge (e.g., ('A', 'B')).
    """

    result = defaultdict()
    edge_value = deque()
    node_value = {}
    
    for n in node2distances:
        node_value[n] = 1
    
    for nv in node_value:
        nv = {k:1 for k in node2distances.keys()}
     
    for key in sorted(node2distances, key=node2distances.get,reverse=True):
        if(key != root):
            for parent in node2parents[key]:
                nv[parent] = nv[parent] + (nv[key]/len(node2parents[key]))
                if(key > parent):
                    edge_value.append((parent, key))
                elif(key < parent):
                    edge_value.append((key, parent))
   
    for ev in edge_value:
        if( root in ev):
            root_index = ev.index(root)
            if(root_index > 0):
                result[ev] = (nv[ev[0]]/len(node2parents[ev[0]]))
            else:
                result[ev] = (nv[ev[1]]/len(node2parents[ev[1]]))
        elif(ev[0] in node2parents[ev[1]]):
            result[ev] = (nv[ev[1]]/len(node2parents[ev[1]]))
        else:
            result[ev] = (nv[ev[0]]/len(node2parents[ev[0]]))

    return result


def approximate_betweenness(graph, max_depth):
    """
    Compute the approximate betweenness of each edge, using max_depth to reduce
    computation time in breadth-first search.
    Only leave the original users nodes and corresponding edges and betweenness for future analysis.

    Params:
      graph.......A networkx Graph
      max_depth...An integer representing the maximum depth to search.

    Returns:
      A dict mapping edges to betweenness. Each key is a tuple of two strings
      representing an edge (e.g., ('A', 'B')). Make sure each of these tuples
      are sorted alphabetically (so, it's ('A', 'B'), not ('B', 'A')).
    """

    result = defaultdict(float)
    
    for n in graph.nodes():
        node2distances, node2num_paths, node2parents = bfs(graph, n, max_depth)
        edge2score = bottom_up(n, node2distances, node2num_paths, node2parents)
      
        for a,b in edge2score.items():
            result[a] += b/2
   

    return dict(sorted(result.items()))


def partition_girvan_newman(graph, max_depth, num_clusters):
    """
    Use the approximate_betweenness implementation to partition a graph.
    Unlike in class, here you will not implement this recursively. Instead,
    just remove edges until more than one component is created, then return
    those components.
    That is, compute the approximate betweenness of all edges, and remove
    them until multiple comonents are created.

    Note: the original graph variable should not be modified. Instead,
    make a copy of the original graph prior to removing edges.

    Params:
      graph..........A networkx Graph created before
      max_depth......An integer representing the maximum depth to search.
      num_clusters...number of clusters want

    Returns:
      clusters...........A list of networkx Graph objects, one per partition.
      users_graph........the partitioned users graph.
    """
 
    clusters = []

    partition_edge = list(sorted(approximate_betweenness(graph, max_depth).items(), key=lambda x:(-x[1], x[0])))
    
    for i in range(0, len(partition_edge)):
        graph.remove_edge(*partition_edge[i][0])
        clusters = list(nx.connected_component_subgraphs(graph))
        if len(clusters) >= num_clusters:
            break

    new_clusters = [cluster for cluster in clusters if len(cluster.nodes()) > 1]

    return new_clusters, graph


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f)


def main():
    users = get_user_info('twit_user')
    print("Fetched user data.")
    print('Number of friends of each user:')
    print_num_friends(users)
    friend_counts = count_friends(users)
    print('Most common friends:\n%s' % str(friend_counts.most_common(5)))
    print('Friend Overlap:\n%s' % str(friend_overlap(users)))
    
    graph = create_graph(users, friend_counts, 0)
    print('graph has %s nodes and %s edges' % (len(graph.nodes()), len(graph.edges())))
    draw_network(graph, users, 'Network1.png')
    print('network drawn to Network1.png')

    subgraph = create_graph(users, friend_counts, 1)
    print('subgraph has %s nodes and %s edges' % (len(subgraph.nodes()), len(subgraph.edges())))
    draw_network(subgraph, users, 'Network2.png')
    print('network drawn to network2.png')
    
    clusters, partitioned_graph = partition_girvan_newman(subgraph, 5, 100)
    save_obj(clusters, 'clusters')

    print('cluster 1 has %d nodes, cluster 2 has %d nodes, cluster 3 has %d nodes' %
          (len(clusters[0].nodes()), len(clusters[1].nodes()), len(clusters[2].nodes())))

    draw_network(partitioned_graph, users, 'Network3.png')
    print('network drawn to Network3.png')


if __name__ == '__main__':
    main()



    
