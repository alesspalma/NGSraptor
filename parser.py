#!/usr/bin/python3
# usage:
# - python3 parser.py -q "query" --o1 table1.csv --o2 table2.csv -b backend.csv
# - python3 parser.py -i inputfile --o1 table1.csv --o2 table2.csv -b backend.csv
# - ./parser.py -q "query" --o1 table1.csv --o2 table2.csv -b backend.csv
# - ./parser.py -i inputfile --o1 table1.csv --o2 table2.csv -b backend.csv
import sys, getopt, math
from parsing_utilities import *
from downloaderRunner import *
from xml.dom import pulldom
# import os, psutil

BACKEND_NAME = ".backend.csv"


def xml_parser(inputFile, output1, output2):
    doc = pulldom.parse(inputFile)
    PRJNAs = []  # it will contain all the bioproject identifiers
    SAMIDs = []  # it will contain all the sample identifiers
    EXPIDs = []  # it will contain all the experiment identifiers
    run_sizes = []  # it will contain all run sizes for each experiment
    run_count_per_exps = []  # it will contain for each experiment its number of runs
    platforms = []  # it will contain all the platforms used
    layouts = []  # it will contain the layout used for each experiment
    library_sources = []  # it will contain the sources for each experiment
    library_strategies = []  # it will contain the strategies for each experiment
    organisms = []  # it will contain the organism studied for each experiment
    links = []      # it will contain all ref links to articles for each experiments
    sample_meta = []      # it will contain all the sample metadata for each experiment

    runs_to_write = []  # it will contain the runs of last experiment to write in the backend file

    f = open(BACKEND_NAME, 'w')  # just to truncate the backend file
    f.close()

    for event, node in doc:
        if event == pulldom.END_ELEMENT and node.tagName == "EXPERIMENT_PACKAGE":
            # if an experiment is ending, I dump the previous experiment in my backend file
            with open(BACKEND_NAME, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                for run in runs_to_write:
                    csvwriter.writerow([run[0], run[1], EXPIDs[-1], platforms[-1], layouts[-1], library_sources[-1],
                                        library_strategies[-1], PRJNAs[-1], links[-1], SAMIDs[-1], organisms[-1], dict(sample_meta[-1])])

        if event == pulldom.START_ELEMENT and not text_check(node):
            if node.tagName == "STUDY":
                study_node = node
                doc.expandNode(study_node)
                study_data = get_prjna(study_node)
                PRJNAs.append(study_data)
                # # takes all referral links of the experiment
                links.append(get_links(study_node.getElementsByTagName("STUDY_LINKS")))

            elif node.tagName == "EXPERIMENT":
                exp_node = node
                doc.expandNode(exp_node)
                # take the experiment ID
                EXPIDs.append(get_primary_id(exp_node))
                # researching layouts
                layouts.append(rec_search_tagname(exp_node, ["DESIGN", "LIBRARY_DESCRIPTOR", "LIBRARY_LAYOUT"]))
                # researching platforms
                platforms.append(get_tag_from_parentag(
                    exp_node.getElementsByTagName("PLATFORM")[0],
                    "INSTRUMENT_MODEL"))
                # takes sources used for this experiment
                library_sources.append(get_tag_from_parentag(
                    exp_node.getElementsByTagName("LIBRARY_DESCRIPTOR")[0],
                    "LIBRARY_SOURCE"))
                # takes strategies used for this experiment
                library_strategies.append(get_tag_from_parentag(
                    exp_node.getElementsByTagName("LIBRARY_DESCRIPTOR")[0],
                    "LIBRARY_STRATEGY"))

            elif node.tagName == "RUN_SET":
                run_node = node
                doc.expandNode(run_node)
                run_data = compute_runs(run_node)  # researching runs
                run_sizes.append(run_data[0])  # saving total size
                run_count_per_exps.append(run_data[1])  # count how many runs the experiment has
                runs_to_write = run_data[2]  # list of tuples (run_id, run_size)

            elif node.tagName == "SAMPLE":
                sample_node = node
                doc.expandNode(sample_node)
                # take the sample ID
                SAMIDs.append(get_sampleid(sample_node))
                # take organism used for this experiment
                organisms.append(get_tag_from_parentag(sample_node, "SCIENTIFIC_NAME"))
                # take all the metadata of the experiment, if there are any
                sample_attributes_nodelist = sample_node.getElementsByTagName("SAMPLE_ATTRIBUTES")
                if sample_attributes_nodelist:  # means if the nodelist is not empty
                    sample_meta.append(get_metadata(sample_attributes_nodelist[0]))
                else:
                    sample_meta.append(dict())

    # it'll store the data like that:
    # {project_id1: {data1: values, data2: values, ...},
    #  project_id2: {data1: values, data2, values, ...},
    #  ...
    # }
    # used for grouping data under the same BioProject
    dic = defaultdict(lambda: {"Platforms": set(), "#SRA_experiments": 0, "#Runs": 0,
                               "Size": 0, "Layouts": set(), "Sources": set(),
                               "Strategies": set(), "Organisms": set(), "Links": set(),
                               "Sample": dict()})

    for i in range(len(PRJNAs)):
        bioprj_id = PRJNAs[i]
        dic[bioprj_id]["Platforms"].add(platforms[i])
        dic[bioprj_id]["#SRA_experiments"] += 1
        dic[bioprj_id]["#Runs"] += run_count_per_exps[i]
        dic[bioprj_id]["Size"] = round(run_sizes[i]/math.pow(2, 30) + dic[bioprj_id]["Size"], 3)  # convertion to gibibytes
        dic[bioprj_id]["Layouts"].add(layouts[i])
        dic[bioprj_id]["Sources"].add(library_sources[i])
        dic[bioprj_id]["Strategies"].add(library_strategies[i])
        dic[bioprj_id]["Organisms"].add(organisms[i])
        dic[bioprj_id]["Links"].update(links[i])
        dic[bioprj_id]["Sample"] = mergeDict(dic[bioprj_id]["Sample"], sample_meta[i])
    
    create_tables(output1, output2, dic)
    print("Succesfully finished")

    # process = psutil.Process(os.getpid())
    # print(process.memory_info().rss, "bytes")  # in bytes


def main(argv):
    input1 = ""
    query = ""
    output1 = ""
    output2 = ""
    try:
        arguments, _ = getopt.getopt(argv, "i:q:b:", ["o1=", "o2="])
    except getopt.error:
        print('usage:\nparser.py -q "query" --o1 table1.csv --o2 table2.csv\nparser.py -i inputfile --o1 table1.csv --o2 table2.csv')
        sys.exit(2)
    for arg, val in arguments:
        if arg == "-i":
            input1 = val
        elif arg == "-q":
            query = val
        elif arg == "--o1":
            output1 = val
        elif arg == "--o2":
            output2 = val
        elif arg == "-b":
            global BACKEND_NAME
            BACKEND_NAME = val
            
    if (input1 and query) or (not output1) or (not output2) or (len(arguments) < 3):
        print('usage:\nparser.py -q "query" --o1 table1.csv --o2 table2.csv -b backend.csv'
               + '\nparser.py -i inputfile --o1 table1.csv --o2 table2.csv -b backend.csv')
        sys.exit(2)
    if input1:
        proc = subprocess.Popen(["sed", "-i", "3s/^/<root> \\n/", input1])
        proc.wait()
        with open(input1, 'a') as f:
            proc = subprocess.Popen(["printf", "</root>\n"], stdout=f)
            proc.wait()
        xml_parser(input1, output1, output2)
    else:
        inputName = query.replace(" ", "_")
        runScript(query, inputName)
        xml_parser(inputName + ".xml", output1, output2)


if __name__ == "__main__":
    main(sys.argv[1:])
