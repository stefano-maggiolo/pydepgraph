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

import dircache
import sys
import os
import colorsys
import argparse


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


def color_label(names, start=0.0, stop=1.0):
    """Assign a color to each package name in names in such a way that
    'near' packages have similar colors.

    names ([str]): a list of package names to assign colors to.
    start (float): smallest assignable hue.
    stop (float): largest assignable hue.

    return (dict): a dictionary assigning to every name in names a
                   color as a hex string.

    """
    damping = 2
    if len(names) == 1:
        return {names[0]: rgb(start)}

    names_split = [x.split(".") for x in names]
    first_level = sorted(list(set([x[0] for x in names_split])))
    step = 0.0 if names == [] else (stop - start) / (len(names) * damping)
    ret = {}
    cur = start
    for word in first_level:
        to_recur = [".".join(x[1:]) for x in names_split if x[0] == word]
        tmp = color_label(to_recur,
                          cur,
                          cur + step * len(to_recur))
        cur += step * len(to_recur) * damping
        for name in tmp:
            package = word
            if name != "":
                package = "%s.%s" % (word, name)
            ret[package] = tmp[name]

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


## Escaping functions. ##

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
        list_ = dircache.listdir(complete_path)
    except OSError:
        sys.stderr.write("Warning: cannot open path %s.\n" % complete_path)
        return [], []
    for name in list_:
        if name in [".", ".."] or name in exclude:
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
    graph_clusters = dict((cluster, []) for cluster in clusters)
    for name in graph:
        source = find_best_cluster(name, clusters)
        if source is None:
            continue
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

def do_graph(paths,
             exclude=None,
             clusters=None,
             draw_mode="CLUSTERS",
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
    graph_clusters = build_graph_clusters(
        graph,
        [cluster[0] for cluster in clusters],
        self_edges=(draw_mode == "ONLY_CLUSTERS_WITH_SELF_EDGES"))

    all_names = list(set([adjust(x[0]) for x in files + clusters]))
    colors = color_label(sorted(all_names))

    clusters = [[x, "Not opened", i] for i, x in enumerate(clusters)]

    string = "digraph G {\n" \
             "ranksep=1.0\n" \
             "node [style=filled,fontname=Helvetica,fontsize=10];\n"

    for name in sorted(graph):
        for c_name, idx in [(x[0], x[2])
                            for x in clusters
                            if not in_package(name, x[0][0])
                                and x[1] == "Opened"]:
            if draw_mode == "CLUSTERS":
                string += "}\n\n"
            clusters[idx][1] = "Closed"
        for c_name, idx in [(x[0][0], x[2])
                            for x in clusters
                            if in_package(name, x[0][0])
                                and x[1] == "Not opened"]:
            if draw_mode == "CLUSTERS":
                string += "\nsubgraph cluster_%s {\n" % escape(c_name)
            elif draw_mode in ["ONLY_CLUSTERS",
                               "ONLY_CLUSTERS_WITH_SELF_EDGES"]:
                string += '%s [label="%s",fillcolor="#%s"];\n' % (
                    escape(c_name), label(c_name), colors[c_name])
            clusters[idx][1] = "Opened"

        if draw_mode in ["NO_CLUSTERS", "CLUSTERS"]:
            string += '%s [label="%s",fillcolor="#%s"];\n' % (
                escape(name), label(name), colors[name])

    if draw_mode == "CLUSTERS":
        for i in [x for x in clusters if x[1] == "Opened"]:
            string += "}\n\n"

    max_dist = get_max_dist(graph)
    if draw_mode in ["NO_CLUSTERS", "CLUSTERS"]:
        for name in graph:
            for name_ in graph[name]:
                if name_ in graph:
                    string += '%s -> %s [weight=%d];\n' % (
                        escape(name), escape(name_),
                        1 + max_dist - distance(name, name_))
    elif draw_mode in ["ONLY_CLUSTERS", "ONLY_CLUSTERS_WITH_SELF_EDGES"]:
        for name in graph_clusters:
            for name_ in graph_clusters[name]:
                if name_ in graph_clusters:
                    string += '%s -> %s [weight=%d];\n' % (
                        escape(name), escape(name_),
                        max(1, max_dist - distance(name, name_)))

    string += "}\n"
    sys.stdout.write(string)


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

    args = parser.parse_args()
    path = args.path.split(",")
    clusters = args.clusters.split(",") if args.clusters is not None else None
    exclude = args.exclude.split(",") if args.exclude is not None else None
    try:
        draw_mode = DRAW_MODES[args.graph]
    except KeyError:
        print >> sys.stderr, parser.usage
        sys.exit(1)

    do_graph(path,
             exclude=exclude,
             clusters=clusters,
             draw_mode=draw_mode,
             recursive=not args.no_recursive)

if __name__ == "__main__":
    main()
