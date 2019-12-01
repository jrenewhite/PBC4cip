import arff
import os
import pickle
import csv
from tqdm import tqdm
from io import StringIO, BytesIO


def ReadARFF(file):
    return arff.loads(open(file))


def ReadAndDeleteARFF(file):
    dataset = ReadARFF(file)
    if os.path.exists(file):
        # We should check if file exists or not not before deleting them
        os.remove(file)
    else:
        print(f"Can not delete the file '{file}' as it doesn't exists")
    return dataset


def ReadDAT(file):
    f = open(file).readlines()
    new_f = str(file+'.arff')
    with open(new_f, 'w') as new_file:
        for line in f:
            if line != '\n':
                newline = line
                if newline.split()[0] == '@inputs' or newline.split()[0] == '@output':
                    continue
                elif newline.split()[0] == '@attribute':
                    newline = newline.replace(
                        'real', 'real ').replace(
                        'REAL', 'REAL ').replace('  ', ' ')
                    if newline.split()[2].lower() in ['numeric', 'real', 'integer', 'string']:
                        newline = newline.split(
                        )[0]+' '+newline.split()[1]+' '+newline.split()[2]+'\n'
                new_file.write(newline)
    return ReadAndDeleteARFF(new_f)


def ReadPatternsBinary(originalFile, outputDirectory, suffix=None):
    patterns = list()

    if not suffix:
        suffix = ""

    name = os.path.splitext(os.path.basename(originalFile))[0]
    name = os.path.join(
        outputDirectory, name[:len(name)-len(suffix)]+'.pypatterns')

    if os.path.exists(name):
        input_file = open(name, "rb")
        patternCount = pickle.load(input_file)
        # Read the data
        for pattern in tqdm(range(patternCount), desc=f"Reading patterns from {name}", unit="pat", leave=False):
            try:
                pattern_in = pickle.load(input_file)
                patterns.append(pattern_in)
            except EOFError:
                break
        # while True:
        #     try:
        #         pattern_in = pickle.load(input_file)
        #         patterns.append(pattern_in)
        #     except EOFError:
        #         break
    else:
        raise Exception(
            f"File '{name}'' not found! Please extract patterns first!")
    return patterns


def WritePatternsBinary(patterns, originalFile, outputDirectory, suffix=None):
    if not patterns or len(patterns) == 0:
        return ""
    if not suffix:
        suffix = ""
    if not os.path.exists(outputDirectory):
        print(f"Creating output directory: {outputDirectory}")
        os.makedirs(outputDirectory)

    name = os.path.splitext(os.path.basename(originalFile))[0]
    name = os.path.join(
        outputDirectory, name[:len(name)-len(suffix)]+'.pypatterns')

    action = "Writing"
    if os.path.exists(name):
        action = "Overwriting"
        os.remove(name)

    patterns_out = open(name, "wb")
    pickle.dump(len(patterns), patterns_out)
    for pattern in tqdm(patterns, desc=f"{action} patterns to {name}...", unit="pattern", leave=False):
        pickle.dump(pattern, patterns_out)
        patterns_out.flush()
    patterns_out.close()

    return name


def WritePatternsCSV(patterns, originalFile, outputDirectory, suffix=None):
    if not patterns or len(patterns) == 0:
        return ""
    if not suffix:
        suffix = ""
    if not os.path.exists(outputDirectory):
        print(f"Creating output directory: {outputDirectory}")
        os.makedirs(outputDirectory)

    name = os.path.splitext(os.path.basename(originalFile))[0]
    name = os.path.join(outputDirectory, name[:len(name)-len(suffix)]+'.csv')

    action = "Writing"
    if os.path.exists(name):
        action = "Overwriting"
        os.remove(name)

    patterns_out = open(name, "w", newline='\n', encoding='utf-8')
    fields = list(patterns[0].ToDictionary().keys())
    pattern_writer = csv.DictWriter(patterns_out, fieldnames=fields)
    pattern_writer.writeheader()
    for pattern in tqdm(patterns, desc=f"{action} patterns to {name}...", unit="pattern", leave=False):
        pattern_writer.writerow(pattern.ToDictionary())

    patterns_out.close()

    return name


def WriteClassificationResults(evaluation, originalFile, outputDirectory, suffix=None):
    if not evaluation:
        return ""
    if not suffix:
        suffix = ""
    if not os.path.exists(outputDirectory):
        print(f"Creating output directory: {outputDirectory}")
        os.makedirs(outputDirectory)

    name = os.path.splitext(os.path.basename(originalFile))[0]
    basename = name[:len(name)-len(suffix)]
    name = os.path.join(
        outputDirectory, name[:len(name)-len(suffix)]+'_results.md')

    if os.path.exists(name):
        os.remove(name)

    results_out = open(name, "a", newline='\n', encoding='utf-8')
    results_out.write(f"# Results for the testing dataset [{basename}]")
    results_out.write(f"\r\n\r\n")
    results_out.write(f"## Confusion Matrix \r\n\r\n")
    results_out.write(f"{evaluation.ConfusionMatrix.__repr__()}")
    results_out.write(f"## Measures per class")
    for classValue in range(len(evaluation.ConfusionMatrix.Classes)):
        auc = evaluation.ConfusionMatrix.AUCMeasure(classValue)
        basicEvaluation = evaluation.ConfusionMatrix.ComputeBasicEvaluation(
            classValue)
        classLabel = evaluation.ConfusionMatrix.Classes[classValue]
        results_out.write(f"\r\n\r\n")
        results_out.write(f"### [{classLabel}]\r\n\r\n")
        results_out.write(f"- TP Rate: {basicEvaluation.TPrate}\r\n\r\n")
        results_out.write(f"- FP Rate: {basicEvaluation.FPrate}\r\n\r\n")
        results_out.write(f"- AUC: {auc}")
    results_out.close()

    return name


def WriteResultsCSV(evaluation, originalFile, outputDirectory, resultsId):
    if not evaluation:
        return ""
    if not os.path.exists(outputDirectory):
        print(f"Creating output directory: {outputDirectory}")
        os.makedirs(outputDirectory)

    datasetName = os.path.splitext(os.path.basename(originalFile))[0]
    name = os.path.join(outputDirectory, f"TestsResults{resultsId}.csv")

    action = "Writing"
    if os.path.exists(name):
        action = "Appending"
        results_out = open(name, "a+", newline='\n', encoding='utf-8')
    else:
        results_out = open(name, "w+", newline='\n', encoding='utf-8')
        results_out.write(f"File,AUC\n")

    auc = evaluation.ConfusionMatrix.AUCMeasure(0)

    results_out.write(f"{datasetName},{str(auc)}\n")

    results_out.close()

    return name
