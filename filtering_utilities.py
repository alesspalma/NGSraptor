import csv
from collections import defaultdict
from filter import HEADER

# ---------------- FILTERING UTILITIES ---------------- #

# print the selection list for metadata filtering
def show_metadata(output1, output2, prj_dict, CHOICES):
    choice = -1
    while choice != "q":
        header = defaultdict(lambda: 0)
        for prj in prj_dict.values():
            for key in prj.get_metadata():
                header[key] += 1  # count the occurrencies of every metadata in all the projects
        header = sorted(list(header.keys()), key=lambda x: -header[x])  # sort on metadata popularity
        # main menu for metadata
        print("\nYou can filter on these attributes:")

        for i in range(len(header)):
            print("Select " + str(i) + " to show filters for the attribute: " + header[i])
        
        print("Type q to go back to previous menu")
        choice = input("\nEnter your choice: ")  # wait for user input
        if choice != "q":
            try:
                choice = int(choice)
            except ValueError:
                print("This attribute doesn't exist, retry")
                choice = -1
                continue

            if 0 <= choice <= len(header) - 1:
                print("\nChoose the value you want: ")
                wanted, prj_dict = filters_for_lists(header[choice], prj_dict, metachoice=True)

                if wanted: 
                    if header[choice] in CHOICES:
	                    CHOICES[header[choice]] += list(wanted)
                    else:
	                    CHOICES[header[choice]] = list(wanted)
                    create_tables(output1, output2, prj_dict)

            else:
                print("This attribute doesn't exist, retry")
    return prj_dict


# handles numeric range user input
def numeric_input():
    while True:
        _min = input("\nEnter the minimum value you want to accept: ")
        try:
            _min = float(_min)
            break
        except ValueError:
            if _min == "q": return ()
            print("This attribute doesn't exist, retry")

    while True:
        _max = input("Enter the maximum value you want to accept: ")
        try:
            _max = float(_max)
            break
        except ValueError:
            if _max == "q": return ()
            print("This attribute doesn't exist, retry")

    return _min, _max


# handles the user choice about projects with or without scientific publications
def links_selection():
    print("\nSelect 1 to take only projects that have scientific publications")
    print("Select 2 to take only projects that don't have scientific publications")
    print("Type q to end selection")
    selection = -1
    while selection not in {1, 2, "q"}:
        selection = input("\nEnter your choice: ")
        try:
            selection = int(selection)
            if selection < 1 or selection > 2: raise ValueError
        except ValueError:
            if selection != "q":
                print("This attribute doesn't exist, retry")

    if selection == 1:
        return "YES"
    elif selection == 2:
        return "NO"
    else: return False


# removes trash characters from a line and splits it
def clean_set_line(line):
    li = line.replace("{", "").replace("}", "").replace("'", "")
    values = set(li.split(", "))
    return values


def filter_project(choice, data, prj, metachoice=False):
    # if metachoice is true, then we are passing choice as a string (the metadata selected)
    if metachoice:
        return any([searched in prj.get_metadata().get(choice, set()) for searched in data])
    # if metachoice is false, then we are passing choice as a numeric index that tells us the getter to call
    else:
        # select on numeric filters
        if choice == 1:
            return data[0] <= len(prj) <= data[1]
        elif choice == 2:
            return data[0] <= prj.get_runs_number() <= data[1]
        elif choice == 3:
            return data[0] <= prj.get_runs_size() <= data[1]

        # select on non numeric filters
        elif choice == 0:
            return any([searched in prj.get_platforms() for searched in data])
        elif choice == 4:
            return any([searched in prj.get_layouts() for searched in data])
        elif choice == 5:
            return any([searched in prj.get_sources() for searched in data])
        elif choice == 6:
            return any([searched in prj.get_strategies() for searched in data])
        elif choice == 7:
            return any([searched in prj.get_organisms() for searched in data])
        
        # select on link filter
        else:
            return (data == "YES" and prj.links != "-") or (data == "NO" and prj.links == "-")


def filters_for_lists(index, prj_dict, metachoice=False):  # star=False):
    option_set = set()
    # if metachoice is true, then we are passing index as a string (the metadata selected)
    if metachoice:
        for prj in prj_dict.values(): option_set.update(prj.get_metadata().get(index, set()))
    # if metachoice is false, then we are passing index as a numeric index that tells us the getter to call
    else:
        if index == 0:
            for prj in prj_dict.values(): option_set.update(prj.get_platforms())
        elif index == 4:
            for prj in prj_dict.values(): option_set.update(prj.get_layouts())
        elif index == 5:
            for prj in prj_dict.values(): option_set.update(prj.get_sources())
        elif index == 6:
            for prj in prj_dict.values(): option_set.update(prj.get_strategies())
        else:
            for prj in prj_dict.values(): option_set.update(prj.get_organisms())

    option_set = list(option_set)
    ind = 0

    for v in option_set:  # print all the values that we have on that metadata
        print("Select " + str(ind) + " to filter by " + v)
        ind += 1
    # if star: print("Type * to select all valid values")
    print("Type q to end selection")

    wanted = set()
    _choice = input("\nEnter your choice: ")
    while _choice != "q":
        try:
            _choice = int(_choice)
        except ValueError:
            _choice = -1

        # if _choice == "*":  # if the user selected all values
        #     _wanted.update(filters_map[index])
        #     _choice = "q"
        #     continue
        if 0 <= _choice <= ind-1:  # if it is a valid choice
            wanted.add(option_set[_choice])
        else:
            print("This attribute doesn't exist, retry")
            _choice = input("\nEnter your choice: ")
            continue
        print("You can put more than one filter, type q if you're good to go")
        _choice = input("\nEnter your choice: ")

    # if the user didn't select anything
    if not wanted: return wanted, prj_dict

    if metachoice: prj_dict = {prj: prj_dict[prj] for prj in prj_dict if filter_project(index, wanted, prj_dict[prj], metachoice=True)}
    else: prj_dict = {prj: prj_dict[prj] for prj in prj_dict if filter_project(index, wanted, prj_dict[prj])}

    for prj in prj_dict.values():
        if metachoice:
            prj.experiments = [exp for exp in prj.experiments if any([attr in wanted for attr in exp.sample.metadata.get(index, set())])]
        else:
            if index == 0:
                prj.experiments = [exp for exp in prj.experiments if exp.platform in wanted]
            elif index == 4:
                prj.experiments = [exp for exp in prj.experiments if exp.layout in wanted]
            elif index == 5:
                prj.experiments = [exp for exp in prj.experiments if exp.source in wanted]
            elif index == 6:
                prj.experiments = [exp for exp in prj.experiments if exp.strategy in wanted]
            else:
                prj.experiments = [exp for exp in prj.experiments if exp.sample.organism in wanted]

    return wanted, prj_dict


# write both the csv files
def create_tables(output1, output2, prj_dict):
    # first table
    with open(output1, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(["BioProject"] + HEADER)
        for prj in prj_dict.values():  # writes each project infos on different row
            csvwriter.writerow([prj.id, prj.get_platforms(), len(prj), prj.get_runs_number(), prj.get_runs_size(),
                                prj.get_layouts(), prj.get_sources(), prj.get_strategies(), prj.get_organisms(), prj.links])

    # second table
    header = defaultdict(lambda: 0)
    for prj in prj_dict.values():
        for key in prj.get_metadata():
            header[key] += 1  # count the occurrencies of every metadata in all the projects
    header = sorted(list(header.keys()), key=lambda x: -header[x])  # sort on metadata popularity

    with open(output2, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(["BioProject"] + header)
        for prj in prj_dict.values():  # writes each project metadata on different row
            prj_meta = prj.get_metadata()
            if not prj_meta: continue  # if the dictionary is empty we will not write that row
            row = [prj.id]
            for column in header:
                row.append(prj_meta.get(column, "-"))
            csvwriter.writerow(row)


def get_current_size(prj_dict):
    return round(sum([prj.get_runs_size() for prj in prj_dict.values()]), 3)

