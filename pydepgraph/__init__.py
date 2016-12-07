#!/usr/bin/python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2012 Stefano Maggiolo <s.maggiolo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""The program is all here.

"""

import argparse
import colorsys
import sys
import os

xrange = range

DRAW_MODES = ["NO_CLUSTERS",
              "CLUSTERS",
              "ONLY_CLUSTERS",
              "ONLY_CLUSTERS_WITH_SELF_EDGES"]


## Color hashing functions. ##

def rgb(hue):
    """Return a RGB value from a hue value.

    hue (float): a hue value, between 0.0 and 1.0.

    return (str): corresponding RGB value as a hex string.

    """
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.6, 0.8)
    return '%02x%02x%02x' % (red * 256, green * 256, blue * 256)


def color_label(names, start=0.0, stop=1.0, damping=3.0):
    """Assign a color to each package name in names in such a way that
    'near' packages have similar colors.

    names ([str]): a sorted list of package names to assign colors to.
    start (float): smallest assignable hue.
    stop (float): largest assignable hue.
    damping (float): describe how we want to distribute the
                     discrimination power of the colors amongst the
                     levels: a high damping (> 3) means we strongly
                     prefer to separate nodes differing in the small
                     level (in particular in the first); a low damping
                     (1 <= damping <= 3) means we prefer to separate
                     nodes more uniformly, regardless of the level in
                     which they differ.
                     Hence, if damping is low, the nodes will be very
                     well spread in the hue circle; if damping is
                     high, nodes' colors will form clusters depending
                     on the value of the first level.

    return (dict): a dictionary assigning to every name in names a
                   color as a hex string.

    """
    if names == []:
        return {}
    elif len(names) == 1:
        return {names[0]: rgb(start)}

    ret = {}
    names = [x.split(".") for x in names]
    first_level = sorted(list(set([x[0] for x in names])))

    if len(first_level) == 1:
        for name, color in color_label([".".join(x[1:]) for x in names],
                                       start,
                                       stop,
                                       damping).items():
            ret[cat(first_level[0], name)] = color
        return ret

    step = ((stop - start) / len(names)) / damping
    infra_dist = (damping - 1.0) * (stop - start) / len(first_level) / damping
    cur = start
    for word in first_level:
        to_recur = [".".join(x[1:]) for x in names if x[0] == word]
        for name, color in color_label(to_recur,
                                       cur,
                                       cur + step * len(to_recur),
                                       damping).items():
            ret[cat(word, name)] = color
        cur += step * len(to_recur) + infra_dist

    return ret


## Distance between packages. ##

def in_package(mod, pkg):
    """Return if mod is a subpackage of pkg.

    mod (str): a module name.
    pkg (str): a package name.

    return (bool): True if mod is a subpackage of pkg.

    """
    if mod == pkg:
        return True
    else:
        return mod.startswith("%s." % pkg)


def distance(pkg1, pkg2):
    """Return the distance between two packages.

    pkg1 (str): a package name.
    pkg2 (str): a package name.

    return (int): the distance in hops between pkg1 and pkg2.

    """

    split1 = pkg1.split(".")
    split2 = pkg2.split(".")
    dist = 0
    for i in xrange(len(split2), 0, -1):
        if in_package(pkg1, ".".join(split2[:i])):
            break
        dist += 1
    for i in xrange(len(split1), 0, -1):
        if in_package(pkg2, ".".join(split1[:i])):
            break
        dist += 1
    return dist


def get_max_dist(graph):
    """Return the maximum length of an edge in graph.

    graph ({str: [str]}): a graph of packages as an adjacency matrix.

    return (int): maximum length (in hops) of an edge.

    """
    max_dist = 0
    for name in graph:
        for name_ in graph[name]:
            if name_ in graph:
                max_dist = max(max_dist, distance(name, name_))
    return max_dist


## Names utility functions. ##

def adjust(name):
    """Return name formatted as a package name.

    name (str): a path of a package.

    return (str): name formatted as a package.

    """
    name = name.replace("/", ".")
    if name.endswith(".py"):
        name = name[:-3]
    if name.endswith(".__init__"):
        name = name[:-9]
    return name


def escape(name):
    """Return name suitable for being used as a node name in DOT.

    name (str): a package name.

    return (str): name formatted as a DOT node name.

    """
    return name.replace(".", "_").replace("-", "_")


def label(name):
    """Return name formatted as a node label.

    name (str): a package name.

    return (str): name formatted as a node label.

    """
    return name.replace(".", ".\\n")


def cat(package, name):
    """Return the concatenation of package and name handling the
    special cases in which one is empty.

    package (str): the prefix.
    name (str): the suffix.

    return (str): the concatenation.

    """
    if name == "":
        return package
    elif package == "":
        return name
    else:
        return "%s.%s" % (package, name)


## File searching functions. ##

def compute_list(path, additional_path="", exclude=None, recursive=True):
    """Return all Python files and clusters (read: subdirectory)
    starting from a path in paths, not crossing directories or files
    whose name is in exclude (and recurring if recursive is True).

    path (str): starting path to check.
    exclude ([str]): list of directory of file names to exclude.
    recursive (bool): whether we descend into subdirectories.

    return ([str], [str]): a list of Python files and of clusters.

    """
    if exclude is None:
        exclude = []
    ret = []
    clusters = [(adjust(additional_path), path)]
    complete_path = os.path.join(path, additional_path)
    try:
        list_ = os.listdir(complete_path)
    except OSError:
        sys.stderr.write("Warning: cannot open path %s.\n" % complete_path)
        return [], []
    for name in list_:
        if name.startswith(".") or name in exclude:
            continue

        partial_name = os.path.join(additional_path, name)
        complete_name = os.path.join(path, partial_name)
        if os.path.isdir(complete_name):
            if recursive:
                tmp_ret, tmp_clusters = compute_list(path,
                                                     partial_name,
                                                     exclude,
                                                     recursive)
                ret += tmp_ret
                clusters += tmp_clusters
        elif name.endswith(".py"):
            ret.append((partial_name, path))

    return ret, clusters


## Graph creation functions. ##

def find_best_cluster(name, clusters):
    """Return the cluster in clusters which is nearest to name.

    name (str): a package name.
    clusters ([str]): a list of cluster names.

    return (str): the nearest cluster to name.

    """
    best = None
    for cluster in clusters:
        if in_package(name, cluster):
            if best is None:
                best = cluster
            elif in_package(cluster, best):
                best = cluster
    return best


def build_graph_clusters(graph, clusters, self_edges=False):
    """Given a graph of packages, build a graph of clusters.

    graph ({str: [str]}): a graph of packages as an adjacency matrix.
    clusters ([str]): a list of cluster names.
    self_edges (bool): if True, draw also self edges.

    return ({str: [str]}) a graph of clusters as an adjacency matrix.

    """
    graph_clusters = {}
    for name in graph:
        source = find_best_cluster(name, clusters)
        if source is None:
            continue
        if source not in graph_clusters:
            graph_clusters[source] = []
        for name_ in graph[name]:
            target = find_best_cluster(name_, clusters)
            if target is not None:
                if self_edges or target != source:
                    if target not in graph_clusters[source]:
                        graph_clusters[source].append(target)
    return graph_clusters


def build_graph(files):
    """Given a list of Python files, build a graph of
    dependencies. Dependencies are computed statically, analyzing
    import and from statements. Unusual code may not give the expected
    results.

    files ([str]): a list of Python file names to analyze.

    return ({str: [str]}): a graph of packages as an adjacency matrix.

    """
    graph = {}
    for file_, path in files:
        content = open(os.path.join(path, file_)).read().replace("\\\n", "")
        file_display = adjust(file_)
        graph[file_display] = []
        for line in content.split("\n"):
            line = line.split()
            if "import" not in line:
                continue
            if "import" == line[0]:
                tmp = " ".join(line[1:]).split(",")
                for name in tmp:
                    name = name.strip().split(" ")[0]
                    if adjust(name) not in [x for x in graph[file_display]]:
                        graph[file_display].append(adjust(name))
            elif "from" == line[0]:
                if adjust(line[1]) not in [x for x in graph[file_display]]:
                    graph[file_display].append(adjust(line[1]))
    return graph


## Main functions. ##

def draw_begin_graph(concentrate):
    """Return the initial part of the graph definition.

    return (str): initial part of the graph definition.

    """
    string = "digraph G {\n"
    if concentrate:
        string += "concentrate=true\n"
    string += "node [style=filled,fontname=Helvetica,fontsize=16];\n"
    return string


def draw_graph(graph, clusters, colors, draw_mode):
    """Return the definition of the nodes and of the clusters.

    graph ({str: [str]}): the graph to draw.
    clusters ([(str, str)]): the clusters definition.
    colors ({str: str}): the color assignment.
    draw_mode (int): the draw mode (cf. DRAW_MODES).

    return (str): the definition of the nodes and of the clusters.

    """
    c_opened = []
    string = ""

    for name in sorted(graph):
        for cluster in [x for x in c_opened
                        if not in_package(name, x[0])]:
            if draw_mode == "CLUSTERS":
                string += "}\n\n"
            c_opened.remove(cluster)

        for cluster in [x for x in clusters
                        if in_package(name, x[0])]:
            if draw_mode == "CLUSTERS":
                string += "\nsubgraph cluster_%s {\n" % escape(cluster[0])
            elif draw_mode in ["ONLY_CLUSTERS",
                               "ONLY_CLUSTERS_WITH_SELF_EDGES"]:
                if cluster[0] in colors:
                    string += '%s [label="%s",fillcolor="#%s"];\n' % (
                        escape(cluster[0]),
                        label(cluster[0]),
                        colors[cluster[0]])
            c_opened.append(cluster)
            clusters.remove(cluster)

        if draw_mode in ["NO_CLUSTERS", "CLUSTERS"]:
            string += '%s [label="%s",fillcolor="#%s"];\n' % (
                escape(name), label(name), colors[name])

    if draw_mode == "CLUSTERS":
        string += "}\n\n" * len(c_opened)

    return string


def draw_arrows(graph):
    """Draw all arrows of the graph using the usual distance function.

    graph ({str: [str]}): the graph.

    return (str): the string representing the arrows in dot format.

    """
    string = ""
    max_dist = get_max_dist(graph)
    for name in graph:
        for name_ in graph[name]:
            if name_ in graph:
                string += '%s -> %s [weight=%d];\n' % (
                    escape(name), escape(name_),
                    2 ** (max_dist - distance(name, name_)))
    return string


def draw_end_graph():
    """Return the final part of the graph definition.

    return (str): final part of the graph definition.

    """
    return "}\n"


def do_graph(paths,
             exclude=None,
             clusters=None,
             draw_mode="CLUSTERS",
             concentrate=False,
             recursive=True):
    """Main function.

    paths ([str]): list of paths to analyze.
    exclude ([str]): list of directory or file names to exclude.
    clusters ([str]): list of clusters.
    draw_mode (str): how to draw the graph (see DRAW_MODES).
    recursive (bool): whether we want to analyze subdirectories.

    """
    if exclude is None:
        exclude = []
    files = []
    autoclusters = []
    for path in paths:
        tmp_files, tmp_autoclusters = compute_list(path,
                                                   exclude=exclude,
                                                   recursive=recursive)
        files += tmp_files
        autoclusters += tmp_autoclusters
    if clusters is None:
        clusters = autoclusters
    else:
        clusters = [(x, "") for x in clusters]
    clusters.sort()

    graph = build_graph(files)

    if draw_mode in ["NO_CLUSTERS", "CLUSTERS"]:
        colors = color_label(sorted(graph.keys()))

    elif draw_mode in ["ONLY_CLUSTERS", "ONLY_CLUSTERS_WITH_SELF_EDGES"]:
        graph_clusters = build_graph_clusters(
            graph,
            [cluster[0] for cluster in clusters],
            self_edges=(draw_mode == "ONLY_CLUSTERS_WITH_SELF_EDGES"))
        colors = color_label(sorted(graph_clusters.keys()))

    sys.stdout.write(draw_begin_graph(concentrate))

    sys.stdout.write(draw_graph(graph, clusters, colors, draw_mode))

    if draw_mode in ["NO_CLUSTERS", "CLUSTERS"]:
        sys.stdout.write(draw_arrows(graph))
    elif draw_mode in ["ONLY_CLUSTERS", "ONLY_CLUSTERS_WITH_SELF_EDGES"]:
        sys.stdout.write(draw_arrows(graph_clusters))

    sys.stdout.write(draw_end_graph())


def main():
    """Analyze command line arguments and call the main function.

    """
    parser = argparse.ArgumentParser(
        description="Draw the dependency graph of a Python project.")
    parser.add_argument("-p", "--path", default=".",
                        help="comma separated list of paths to include")
    parser.add_argument("-e", "--exclude",
                        help="comma separated list of paths to exclude")
    parser.add_argument("-c", "--clusters",
                        help="comma separated list of clusters")
    parser.add_argument("-r", "--no-recursive", action="store_true",
                        help="do not descend into subdirectories")
    parser.add_argument("-g", "--graph", type=int, default=0,
                        help="type of graph: 0 (without clusters), "
                        "1 (with clusters), 2 (only clusters), "
                        "3 (only clusters, drawing also self edges")
    parser.add_argument("-C", "--concentrate", action="store_true",
                        help="merge common path of different edges")

    args = parser.parse_args()
    path = args.path.split(",")
    clusters = args.clusters.split(",") if args.clusters is not None else None
    exclude = args.exclude.split(",") if args.exclude is not None else None
    try:
        draw_mode = DRAW_MODES[args.graph]
    except IndexError:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    do_graph(path,
             exclude=exclude,
             clusters=clusters,
             draw_mode=draw_mode,
             concentrate=args.concentrate,
             recursive=not args.no_recursive)

if __name__ == "__main__":
    main()
