#!/usr/bin/python3
# usage:
# - python3 filter.py -b backend.csv --o1 filtered_table1.csv --o2 filtered_table2.csv
# - ./filter.py -b backend.csv --o1 filtered_table1.csv --o2 filtered_table2.csv
from classes import *
from parser import BACKEND_NAME
from filtering_utilities import *
import sys, getopt

HEADER = ["Platforms", "#SRA_experiments", "#Runs", "BioProject_size", "Layouts", "Sources", "Strategies", "Organisms", "Links"]
CHOICES = {x:[] for x in HEADER}

def get_max_min(choice, prj_dict):
    if choice == 1:
        ls = [len(prj) for prj in prj_dict.values()]
        max_size = max(ls)
        min_size = min(ls)
    elif choice == 2:
        ls = [prj.get_runs_number() for prj in prj_dict.values()]
        max_size = max(ls)
        min_size = min(ls)
    else:
        ls = [prj.get_runs_size() for prj in prj_dict.values()]
        max_size = max(ls)
        min_size = min(ls)

    return min_size, max_size


def start_filtering(output1, output2, backend_file=""):
    prj_dict = dict()
    exp_dict = dict()

    backend_file = BACKEND_NAME if not backend_file else backend_file

    with open(backend_file) as backend:
        csv_reader = csv.reader(backend, delimiter=',')
        for line in csv_reader:
            run = Run(line[0], int(line[1]))
            exp_id = line[2]
            if exp_id in exp_dict:
                exp_dict[exp_id].add(run)
            else:
                sample = BioSample(line[9], line[10], eval(line[11]))
                experiment = Experiment(exp_id, line[3], line[4], line[5], line[6], sample)
                experiment.add(run)
                exp_dict[exp_id] = experiment
            prj_id = line[7]
            if prj_id in prj_dict:
                if exp_id not in [x.id for x in prj_dict[prj_id].experiments]:
                    prj_dict[prj_id].add(experiment)
            else:
                project = BioProject(prj_id, eval(line[8]))
                project.add(experiment)
                prj_dict[prj_id] = project

    choice = 0
    while choice != "q":
        if not prj_dict:
            print("\nYour filters led to an empty file")
            sys.exit(2)
        # main menu
        print("\nYou can filter on these attributes:")

        for i in range(len(HEADER)):
            print("Select " + str(i) + " to show filters for the attribute: " + HEADER[i])
        print("Select 9 to switch to metadata filtering")

        print("Current size of dataset is:", get_current_size(prj_dict), "GB")
        print("Type p to print the choices you made")
        print("Type q to end selection")

        choice = input("\nEnter your choice: ")  # wait for user input
        if choice != "q":
            try:
                choice = int(choice)
            except ValueError:
                if choice == "p":
                    # print user choices
                    for k in CHOICES:
                        if CHOICES[k]:
                            if k in {"#SRA_experiments", "#Runs", "BioProject_Size"}: print("For the attribute " + k + " you have selected this range: " + str(CHOICES[k]))
                            elif k == "Links": print("You have selected to take only projects that " + ("don't have" if CHOICES[k]=="NO" else "have") + " scientific publications")
                            else: print("For the attribute " + k + " you have selected this filters: " + str(CHOICES[k]))
                else:
                    print("This attribute doesn't exist, retry")
                choice = -1
                continue

            if choice in {1, 2, 3}:
                tup = get_max_min(choice, prj_dict)
                if choice in {1, 2}:    
                    print("\nThe minimum value for " + HEADER[choice] + " is: " + str(tup[0]))
                    print("The maximum value for " + HEADER[choice] + " is: " + str(tup[1]))
                else:
                    print("\nThe minimum BioProject size is: " + str(tup[0]))
                    print("The maximum BioProject size is: " + str(tup[1]))
                print("Type q to end selection")
                wanted = numeric_input()
                CHOICES[HEADER[choice]] = list(wanted)
                if wanted:
                    prj_dict = {prj: prj_dict[prj] for prj in prj_dict if filter_project(choice, wanted, prj_dict[prj])}
                    create_tables(output1, output2, prj_dict)

            elif choice in {0, 4, 5, 6, 7}:
                print("\nChoose the value you want: ")
                wanted, prj_dict = filters_for_lists(choice, prj_dict)
                CHOICES[HEADER[choice]] += list(wanted)
                if wanted: create_tables(output1, output2, prj_dict)
            
            elif choice == 8:
                wanted = links_selection()
                if wanted:
                    CHOICES[HEADER[choice]] = wanted
                    prj_dict = {prj: prj_dict[prj] for prj in prj_dict if filter_project(choice, wanted, prj_dict[prj])}
                    create_tables(output1, output2, prj_dict)

            elif choice == 9:
                prj_dict = show_metadata(output1, output2, prj_dict, CHOICES)
                
            else:
                print("This attribute doesn't exist, retry")

    return


def main(argv):
    output1 = ""
    output2 = ""
    backend = ""
    try:
        arguments, _ = getopt.getopt(argv, "b:", ["o1=", "o2="])
    except getopt.error:
        print('usage: filter.py -b backend.csv --o1 filtered_table1.csv --o2 filtered_table2.csv')
        sys.exit(2)
    if len(arguments) < 2 or len(arguments) > 3:
        print('usage: filter.py -b backend.csv --o1 filtered_table1.csv --o2 filtered_table2.csv')
        sys.exit(2)
    for arg, val in arguments:
        if arg == "--o1":
            output1 = val
        elif arg == "--o2":
            output2 = val
        elif arg == "-b":
            backend = val
    start_filtering(output1, output2, backend_file=backend)


if __name__ == "__main__":
    main(sys.argv[1:])
