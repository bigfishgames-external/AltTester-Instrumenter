#!/usr/bin/env python3

import argparse
import urllib.request
from zipfile import ZipFile
import shutil
import json
import os

# Parse sys args
parser=argparse.ArgumentParser()
parser.add_argument("--version", help="The AltTester version to use.")
parser.add_argument("--assets", help="The Assests folder path.")
parser.add_argument("--settings", help="The build settings file.")
parser.add_argument("--manifest", help="The manifest file to modify.")
parser.add_argument("--buildFile", help="The build file to modify.")
parser.add_argument("--buildMethod", help="The build method to modify.")
parser.add_argument("--inputSystem", help="new or old")
args=parser.parse_args()

# Download AltTester
print(f"version: {args.version}")
zip_url = f"https://github.com/alttester/AltTester-Unity-SDK/archive/refs/tags/v.{args.version}.zip"
urllib.request.urlretrieve(zip_url, "AltTester.zip")

# Add AltTester to project
print(f"assets: {args.assets}")
with ZipFile("AltTester.zip", 'r') as zip:
    zip.extractall(f"{args.assets}/temp")
shutil.move(f"{args.assets}/temp/AltTester-Unity-SDK-v.{args.version}/Assets/AltTester", f"{args.assets}/AltTester") 
shutil.rmtree(f"{args.assets}/temp")

# Modify the manifest
print(f"version: {args.manifest}")
newtonsoft = {"com.unity.nuget.newtonsoft-json": "3.0.1"}
testables = {"testables":["com.unity.inputsystem"]}
editorcoroutines = {"com.unity.editorcoroutines": "1.0.0"}
with open(args.manifest,'r+') as file:
    file_data = json.load(file)
    # file_data["dependencies"].update(newtonsoft)
    file_data.update(testables)
    file_data["dependencies"].update(editorcoroutines)
    file.seek(0)
    json.dump(file_data, file, indent = 2)

# Modify the build file's using directive
print(f"buildFile: {args.buildFile}")
buildUsingDirectives = """\
using Altom.AltTesterEditor;
using Altom.AltTester;"""
with open(args.buildFile, "r+") as f:
    content = f.read()
    f.seek(0, 0)
    f.write(buildUsingDirectives + "\n" + content)
    
# Add scenes to instrumentation list
print(f"settings: {args.settings}")
scenes = []
with open(args.settings, "r") as f:
    lines = f.readlines()
    for line in lines:
        if "path" in line:
            scenes.append(line[line.rindex(" ")+1:].rstrip("\n"))

# Modify the build file's build method
print(f"buildMethod: {args.buildMethod}")
buildMethodBody = f"""\
        var buildTargetGroup = BuildTargetGroup.Android;
        AltBuilder.AddAltTesterInScriptingDefineSymbolsGroup(buildTargetGroup);
        if (buildTargetGroup == UnityEditor.BuildTargetGroup.Standalone) {{
            AltBuilder.CreateJsonFileForInputMappingOfAxis();
        }}
        var instrumentationSettings = new AltInstrumentationSettings();
        var FirstSceneOfTheGame = "{scenes[0]}";
        AltBuilder.InsertAltInScene(FirstSceneOfTheGame, instrumentationSettings);"""
with open(args.buildFile, 'r') as infile:
    data = infile.read()
rowData = data.split("\n")
outData = []
line_to_add_code = 0
for i in range(len(rowData)):
    outData.append(rowData[i])
    if args.buildMethod in rowData[i]:
        if "{" in rowData[i]:
            line_to_add_code = i+1
        else:
            line_to_add_code = i+2
if line_to_add_code > 0:
    outData.insert(line_to_add_code, buildMethodBody)
with open(args.buildFile, 'w') as outfile:
    outfile.write('\n'.join(outData))


def delete_line_and_preceding (file_path, target_string):
    """
    This is my comment.

    -----
    Args:
        file_path : The path to the file to modify.
        target_string : The path to the file to modify.
    """
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        fileOutBuffer = []
        for i in range(len(lines)):
            if target_string in lines[i]:
                fileOutBuffer.pop()
            else:
                fileOutBuffer.append(lines[i])
    with open(file_path, 'w') as file:
        file.write("\n".join(fileOutBuffer))


def delete_csharp_if(file_path, target_string):
    """
    Find c# conditional logic and make it unconditional.  

    -----
    Args:
        file_path : The path to the file to modify.
        target_string : String to search for
    """
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        lines_to_pop = []
        fileOutBuffer = []
        popped_count = 0
        brace_count = 0
        for i in range(len(lines)):
            if ("if" in lines[i]) and (target_string in lines[i]):
                lines_to_pop.append(i)
                # find the curly braces
                # 1. flow where the { is on the end of the if line
                if "{" in lines[i]:
                    brace_count = 1
                    current_line = i+1
                    while brace_count > 0: # this is dangerous, no other escape condition. could run forever
                        if "{" in lines[current_line]:
                            brace_count += 1
                        if "}" in lines[current_line]:
                            brace_count -= 1
                        current_line += 1
                    lines_to_pop.append(current_line)
                    
                # 2. flow where the { is on the next line
                else:
                    brace_count = 1
                    current_line = i+2
                    lines_to_pop.append(i+1)
                    while brace_count > 0: # this is dangerous, no other escape condition. could run forever
                        current_line += 1
                        if "{" in lines[current_line]:
                            brace_count += 1
                        if "}" in lines[current_line]:
                            brace_count -= 1
                    lines_to_pop.append(current_line)
            fileOutBuffer.append(lines[i])
        for badline in lines_to_pop:
            fileOutBuffer.pop(badline - popped_count)
            popped_count += 1


    with open(file_path, 'w') as file:
        file.write("".join(fileOutBuffer))


def delete_using (file_path, target_string):
    """
    Delete library imports in C#

    ----
    Args:
        - file_path : Path to the file to modify
        - target_string : name of the package to remove
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
        fileOutBuffer = []
        linez_2_pop = [] # POYZON
        popped_count = 0
        for i in range(len(lines)):
            if ("using" in lines[i]) and (target_string in lines[i]):
                linez_2_pop.append(i)
            fileOutBuffer.append(lines[i])
        for badline in linez_2_pop:
            fileOutBuffer.pop(badline - popped_count)
            popped_count += 1
    
    with open(file_path, 'w') as file:
        file.write("".join(fileOutBuffer))


# Remove references to NewInputSystem(NIS) if necessary
if "old" in args.inputSystem:
    # Adapt for old input system
    os.remove(f"{args.assets}/AltTester/AltServer/NewInputSystem.cs")
    os.remove(f"{args.assets}/AltTester/AltServer/AltKeyMapping.cs")

    # remove examples, which can contain references to NIS
    shutil.rmtree(f"{args.assets}/AltTester/Examples")
    os.remove(f"{args.assets}/AltTester/Examples.meta")


    alt_prefab_drag_path = f"{args.assets}/AltTester/AltServer/AltPrefabDrag.cs"
    line_to_target = "UnityEngine.InputSystem"
    delete_line_and_preceding(alt_prefab_drag_path, line_to_target)

    delete_csharp_if(f"{args.assets}/AltTester/AltServer/Input.cs", "InputSystemUIInputModule")
    delete_using(f"{args.assets}/AltTester/AltServer/Input.cs", "UnityEngine.InputSystem.UI")
    delete_csharp_if(f"{args.assets}/AltTester/AltServer/AltMockUpPointerInputModule.cs", "InputSystemUIInputModule")
    delete_using(f"{args.assets}/AltTester/AltServer/AltMockupPointerInputModule.cs", "UnityEngine.InputSystem.UI")
