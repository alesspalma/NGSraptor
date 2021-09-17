from collections import defaultdict
import math

class BioProject:
    def __init__(self, prjID, links):
        self.id = prjID
        self.links = links or "-"
        self.experiments = []

    def add(self, experiment):
        self.experiments.append(experiment)
    
    def get_runs_number(self):
        return sum([len(x) for x in self.experiments])

    def get_runs_size(self):
        return round(sum([x.get_runs_size() for x in self.experiments]), 3)

    def get_platforms(self):
        return {x.platform for x in self.experiments}

    def get_layouts(self):
        return {x.layout for x in self.experiments}

    def get_sources(self):
        return {x.source for x in self.experiments}

    def get_strategies(self):
        return {x.strategy for x in self.experiments}

    def get_organisms(self):
        return {x.sample.organism for x in self.experiments}

    def get_metadata(self):
        result_dic = {metaname : set() for exp in self.experiments for metaname in exp.sample.metadata.keys()}
        for exp in self.experiments:
            for key,val in exp.sample.metadata.items():
                for item in val:
                    result_dic[key].add(item)
        return result_dic

    def __len__(self):
        return len(self.experiments)

    def __repr__(self):
        return self.id


class Experiment:
    def __init__(self, expID, platform, layout, source, strategy, sample):
        self.id = expID
        self.platform = platform
        self.layout = layout
        self.source = source
        self.strategy = strategy
        self.sample = sample
        self.runs = []
    
    def add(self, run):
        self.runs.append(run)

    def get_runs_size(self):
        return sum([x.size for x in self.runs])

    def __len__(self):
        return len(self.runs)

    def __repr__(self):
        return self.id


class BioSample:
    def __init__(self, samID, organism, metadata):
        self.id = samID
        self.organism = organism
        self.metadata = metadata

    def __repr__(self):
        return self.id
    

class Run:
    def __init__(self, runID, size):
        self.id = runID
        self.size = round(size/math.pow(2,30), 3)

    def __repr__(self):
        return self.id