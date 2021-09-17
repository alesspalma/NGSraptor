import csv
from collections import defaultdict


# ----------------- PARSING UTILITIES ----------------- #

# xml tags are divided in text nodes and element nodes, text nodes haven't children so it's mandatory to check type
def text_check(node): return node.nodeType == node.TEXT_NODE


# merges two dictionaries into one
def mergeDict(dict1, dict2):
    resultDic = defaultdict(set)
    for key in dict1:
        resultDic[key].update(dict1[key])
    for key in dict2:
        resultDic[key].update(dict2[key])
    return resultDic


def rec_search_tagname(start_node, lista):
    if not lista:   # if lista is empty, this is the tag of which we want the text
        child_nodes_not_text = [ch for ch in start_node.childNodes if not text_check(ch)]
        return child_nodes_not_text[0].tagName    # returns the element tag name
    else:           # if lista is not empty, then we'have to find some other children yet
        for child in start_node.childNodes:     # for each child in child nodes
            # ruling out text nodes and see if the tag we're pointing at it's in the list of the wanted ones
            if not text_check(child) and child.tagName in lista:
                # continuing the research in child
                return rec_search_tagname(child, [lista[x] for x in range(1, len(lista))])


def compute_runs(start_node):
    total_size = 0  # total size of runs for current experiment
    counter = 0  # number of runs for current experiment
    runs = []
    for child in start_node.childNodes:     # for each child in child nodes
        # ruling out text nodes and see if the tag we're pointing at it's a run tag
        if not text_check(child) and child.tagName == "RUN":
            counter += 1
            size = child.getAttribute("size")
            if size: total_size += int(size)  # if size attribute is not specified then move on
            else: size = 0
            run_id = get_primary_id(child)
            runs.append((run_id, size))
    return total_size, counter, runs


# returns the PRJ******* identifier if it exists, otherwise it returns the SRP******* identifier 
def get_prjna(start_node):
    id_list = start_node.getElementsByTagName("IDENTIFIERS")[0].getElementsByTagName("EXTERNAL_ID")
    for id in id_list:
        if id.getAttribute("namespace") == "BioProject": return ''.join(t.data for t in id.childNodes if text_check(t))
    return get_primary_id(start_node)


# returns the SAM******* identifier if it exists, otherwise it returns the SRS******* identifier 
def get_sampleid(start_node):
    id_list = start_node.getElementsByTagName("IDENTIFIERS")[0].getElementsByTagName("EXTERNAL_ID")
    for id in id_list:
        if id.getAttribute("namespace") == "BioSample": return ''.join(t.data for t in id.childNodes if text_check(t))
    return get_primary_id(start_node)


# returns the primary identifier, used especially for experiments and runs
def get_primary_id(start_node):
    primary_id = start_node.getElementsByTagName("IDENTIFIERS")[0].getElementsByTagName("PRIMARY_ID")[0]
    return ''.join(t.data for t in primary_id.childNodes if text_check(t))


# returns text inside wanted_tag, child of parent_node
def get_tag_from_parentag(parent_node, wanted_tag):
    child = parent_node.getElementsByTagName(wanted_tag)[0]
    return ''.join(t.data for t in child.childNodes if text_check(t))


# get all metadata of a sample and store it in a dictionary { key: [value, value, ...] }
def get_metadata(sample_attributes):
    dic = defaultdict(set) # every key will be matched for the first time with an empty list
    for attr in sample_attributes.childNodes: # for every sample attribute
        if not text_check(attr):
            tag = attr.getElementsByTagName("TAG")[0]
            tag = ''.join(t.data for t in tag.childNodes if text_check(t))
            value_nodelist = attr.getElementsByTagName("VALUE")
            if value_nodelist:  # if it is not empty
                dic[tag].add(''.join(t.data for t in value_nodelist[0].childNodes if text_check(t)))
    return dic


# get all scientific publication links in a study tag
def get_links(nodes):
    links = set()
    for node in nodes:
        children = node.getElementsByTagName("XREF_LINK")
        for ch in children:
            db = ch.getElementsByTagName("DB")[0]
            db = ''.join(t.data for t in db.childNodes if text_check(t))
            if db == "pubmed":
                link_id = ch.getElementsByTagName("ID")[0]
                link_id = ''.join(t.data for t in link_id.childNodes if text_check(t))
                link = "https://pubmed.ncbi.nlm.nih.gov/" + link_id
                links.add(link)
            else:
                link_id = ch.getElementsByTagName("ID")[0]
                link_id = ''.join(t.data for t in link_id.childNodes if text_check(t))
                links.add(db+"/"+link_id)

        children = node.getElementsByTagName("URL_LINK")
        for ch in children:
            link = ch.getElementsByTagName("URL")[0]
            link = ''.join(t.data for t in link.childNodes if text_check(t))
            links.add(link)

    return links


# write both the csv files
def create_tables(output1, output2, dic):
    # first table
    with open(output1, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(["BioProject"] + list(dic[next(iter(dic))].keys())[:-1])
        for prj in dic:  # writes each project infos on different row
            values = list(dic[prj].values())[:-2]  # exclude the sample metadata
            values.append(dic[prj]["Links"] if dic[prj]["Links"] else "-")
            csvwriter.writerow([prj] + values)

    # second table
    header = defaultdict(lambda: 0)
    for prj in dic:
        for key in dic[prj]["Sample"]:
            header[key] += 1  # count the occurrencies of every metadata in all the projects
    header = sorted(list(header.keys()), key=lambda x: -header[x])  # sort on metadata popularity

    with open(output2, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(["BioProject"] + list(header))
        for prj in dic:  # writes each project metadata on different row
            if not dic[prj]["Sample"]: continue  # if the dictionary is empty we will not write that row
            row = [prj]
            for column in header:
                row.append(dic[prj]["Sample"].get(column, "-"))
            csvwriter.writerow(row)

    print("Current size of dataset is:", get_current_size(dic), "GB")


def get_current_size(prj_dict):
    return round(sum([prj_dict[prj]["Size"] for prj in prj_dict]), 3)
