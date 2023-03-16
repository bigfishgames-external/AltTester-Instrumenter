#!/usr/bin/env python3
import argparse
from importlib.metadata import version
import urllib.request
from zipfile import ZipFile
import shutil
import json
import os
import logging

def download_alttester(release):
    """
    Downloads the given version of AltTester from GitHub.
    Saves the file to the present working directory as "AltTester.zip".

    Args:
        `string` release: The AltTester version to use.
    """
    zip_url = f"https://github.com/alttester/AltTester-Unity-SDK/archive/refs/tags/v.{release}.zip"
    urllib.request.urlretrieve(zip_url, "AltTester.zip")


def add_alttester_to_project(release, assets):
    """
    Unzips "AltTester.zip" to the given Assets directory.

    Args:
        `string` release: The AltTester version to use.
        `string` assets: The Assets folder path.
    """
    with ZipFile("AltTester.zip", 'r') as zip:
        zip.extractall(f"{assets}/temp")
    if os.path.exists(f"{assets}/AltTester"):
        shutil.rmtree(f"{assets}/AltTester")
    shutil.move(f"{assets}/temp/AltTester-Unity-SDK-v.{release}/Assets/AltTester", f"{assets}/AltTester") 
    shutil.rmtree(f"{assets}/temp")


def modify_manifest(manifest):
    """
    Modify's the given "manifest.json" to include new dependenciess.

    Args:
        `string` manifest: The manifest file to modify.
    """
    newtonsoft = {"com.unity.nuget.newtonsoft-json": "3.0.1"}
    testables = {"testables":["com.unity.inputsystem"]}
    editorcoroutines = {"com.unity.editorcoroutines": "1.0.0"}
    with open(manifest,'r+') as file:
        file_data = json.load(file)
        file_data["dependencies"].update(newtonsoft)
        file_data.update(testables)
        file_data["dependencies"].update(editorcoroutines)
        file.seek(0)
        json.dump(file_data, file, indent = 2)


def modify_build_file_usings(buildFile):
    """
    Modifies the given ".cs" file to include new using directives.

    Args:
        `string` buildFile: The build file to modify.
    """
    buildUsingDirectives = """\
using Altom.AltTesterEditor;
using Altom.AltTester;"""
    with open(buildFile, "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(buildUsingDirectives + "\n" + content)


def get_scenes_of_game(settings):
    """
    Gets a list of scenes from the given "EditorBuildSettings.asset" file.

    Args:
        `string` settings: The build settings file.
    Returns:
        `string[]` scenes: The scenes to be included in the build.
    """
    scenes = []
    with open(settings, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "path" in line:
                scenes.append(line[line.rindex(" ")+1:].rstrip("\n"))
    return scenes


def modify_build_file_method(scenes, buildFile, buildMethod):
    """
    Modifies the given method in the given ".cs" file to add AltTester objects to the scenes.
    
    Args:
        `string[]` scenes: The scenes to be included in the build.
        `string` buildFile: The build file to modify.
        `string` buildMethod: The build method to modify.
    """
    buildMethodBody = f"""\
        var buildTargetGroup = BuildTargetGroup.Android;
        AltBuilder.AddAltTesterInScriptingDefineSymbolsGroup(buildTargetGroup);
        if (buildTargetGroup == UnityEditor.BuildTargetGroup.Standalone) {{
            AltBuilder.CreateJsonFileForInputMappingOfAxis();
        }}
        var instrumentationSettings = new AltInstrumentationSettings();
        var FirstSceneOfTheGame = "{scenes[0]}";
        AltBuilder.InsertAltInScene(FirstSceneOfTheGame, instrumentationSettings);"""
    with open(buildFile, 'r') as infile:
        data = infile.read()
    rowData = data.split("\n")
    outData = []
    line_to_add_code = 0
    for i in range(len(rowData)):
        outData.append(rowData[i])
        if buildMethod in rowData[i]:
            if "{" in rowData[i]:
                line_to_add_code = i+1
            else:
                line_to_add_code = i+2
    if line_to_add_code > 0:
        outData.insert(line_to_add_code, buildMethodBody)
    with open(buildFile, 'w') as outfile:
        outfile.write('\n'.join(outData))


def delete_line_and_preceding (file_path, value):
    """
    Removes the line of code that contains the given sting and the line preceeding it from the returned data.

    Args:
        `string` file_path: The path to the file to modify.
        `string` value: The path to the file to modify.
    """
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        fileOutBuffer = []
        for i in range(len(lines)):
            if value in lines[i]:
                fileOutBuffer.pop()
            else:
                fileOutBuffer.append(lines[i])
    with open(file_path, 'w') as file:
        file.write("".join(fileOutBuffer))


def delete_csharp_if(file_path, target_string):
    """
    Find C# conditional logic and make it unconditional.  

    Args:
        `string` file_path: The path to the file to modify.
        `string` target_string: String to search for.
    """
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        fileOutBuffer = []
        for i in range(len(lines)):
            if ("if" in lines[i]) and (target_string in lines[i]):
                if "{" in lines[i]:
                    fileOutBuffer.append("if (true) {\n")
                else:
                    fileOutBuffer.append("if (true)\n")
            else:
                fileOutBuffer.append(lines[i])

    with open(file_path, 'w') as file:
        file.write("".join(fileOutBuffer))


def delete_using (file_path, target_string):
    """
    Delete library imports in C#.

    Args:
        `string` file_path : Path to the file to modify.
        `string` target_string : name of the package to remove.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
        fileOutBuffer = []
        linez_2_pop = []
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


def remove_new_input_system(assets):
    """
    Removes all references to the new input system.

    Args:
        `string` assets: The Assets folder path.
    """
    os.remove(f"{assets}/AltTester/AltServer/NewInputSystem.cs")
    os.remove(f"{assets}/AltTester/AltServer/AltKeyMapping.cs")

    shutil.rmtree(f"{assets}/AltTester/Examples")
    os.remove(f"{assets}/AltTester/Examples.meta")

    alt_prefab_drag_path = f"{assets}/AltTester/AltServer/AltPrefabDrag.cs"
    delete_line_and_preceding(alt_prefab_drag_path, "UnityEngine.InputSystem")

    delete_csharp_if(f"{assets}/AltTester/AltServer/Input.cs", "InputSystemUIInputModule")
    delete_using(f"{assets}/AltTester/AltServer/Input.cs", "UnityEngine.InputSystem.UI")
    delete_csharp_if(f"{assets}/AltTester/AltServer/AltMockUpPointerInputModule.cs", "InputSystemUIInputModule")
    delete_using(f"{assets}/AltTester/AltServer/AltMockupPointerInputModule.cs", "UnityEngine.InputSystem.UI")


# Main entry point.
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=version("AltTester-Instrumenter"))
    parser.add_argument("--release", required=True, help="[required] The AltTester version to use.")
    parser.add_argument("--assets", required=True, help="[required] The Assets folder path.")
    parser.add_argument("--settings", required=True, help="[required] The build settings file.")
    parser.add_argument("--manifest", required=True, help="[required] The manifest file to modify.")
    parser.add_argument("--buildFile", required=True, help="[required] The build file to modify.")
    parser.add_argument("--buildMethod", required=True, help="[required] The build method to modify.")
    parser.add_argument("--inputSystem", required=True, help="[default='old'] Specify new or old.")
    args=parser.parse_args()

    logging.info(f"release: {args.release}")
    logging.info(f"assets: {args.assets}")
    logging.info(f"release: {args.release}")
    logging.info(f"settings: {args.settings}")
    logging.info(f"manifest: {args.manifest}")
    logging.info(f"buildFile: {args.buildFile}")
    logging.info(f"buildMethod: {args.buildMethod}")
    logging.info(f"inputSystem: {args.inputSystem}")

    download_alttester(release=args.release)
    add_alttester_to_project(release=args.release, assets=args.assets)
    modify_manifest(manifest=args.manifest)
    modify_build_file_usings(buildFile=args.buildFile)
    scene_array = get_scenes_of_game(settings=args.settings)
    modify_build_file_method(scenes=scene_array, buildFile=args.buildFile, buildMethod=args.buildMethod)

    if str(args.inputSystem).lower == "old":
            remove_new_input_system(args.assets)
