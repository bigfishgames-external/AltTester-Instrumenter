#!/usr/bin/env python3
import argparse
from glob import glob
from importlib.metadata import version
from zipfile import ZipFile
import shutil
import json
import os


def download_alttester(release):
    """
    Downloads the given version of AltTester from GitHub.
    Saves the file to the present working directory as "AltTester.zip".

    Args:
        `string` release: The AltTester version to use.
    """
    #print("download_alttester(release)") #DEBUGGING
    #print(f"  release: {release}") # DEBUGGING
    zip_url = f"https://github.com/alttester/AltTester-Unity-SDK/archive/refs/tags/{release}.zip"
    os.system(f"curl {zip_url} -o AltTester.zip -L")


def add_alttester_to_project(release, assets):
    """
    Unzips "AltTester.zip" to the given Assets directory.

    Args:
        `string` release: The AltTester version to use.
        `string` assets: The Assets folder path.
    """
    #print("add_alttester_to_project(release, assets)") #DEBUGGING
    #print(f"  release: {release}") #DEBUGGING
    #print(f"  assets: {assets}") #DEBUGGING
    with ZipFile("AltTester.zip", 'r') as zip:
        zip.extractall(f"{assets}/temp")
    if os.path.exists(f"{assets}/AltTester.meta"):
        os.remove(f"{assets}/AltTester.meta")
    if os.path.exists(f"{assets}/AltTester"):
        shutil.rmtree(f"{assets}/AltTester")
    shutil.move(f"{assets}/temp/AltTester-Unity-SDK-{release}/Assets/AltTester.meta", f"{assets}/AltTester.meta")
    shutil.move(f"{assets}/temp/AltTester-Unity-SDK-{release}/Assets/AltTester", f"{assets}/AltTester")
    shutil.rmtree(f"{assets}/temp")
    os.remove("AltTester.zip")


def modify_manifest(manifest, newt = "True"):
    """
    Modify's the given "manifest.json" to include new dependenciess.

    Args:
        `string` manifest: The manifest file to modify.
        `string` newt: [default='True'] Include newtonsoft in the main manifest.json.
    """
    newtonsoft = {"com.unity.nuget.newtonsoft-json": "3.0.1"}
    inputsystem = "com.unity.inputsystem"
    editorcoroutines = {"com.unity.editorcoroutines": "1.0.0"}
    with open(manifest,'r+') as file:
        file_data = json.load(file)
        if (newt == "True") and ("com.unity.nuget.newtonsoft-json" not in file_data):
            file_data["dependencies"].update(newtonsoft)
        if "com.unity.inputsystem" not in file_data:
            if "testables" in file_data:
                file_data["testables"].append(inputsystem)
            else:
                testables = {"testables":["com.unity.inputsystem"]}
                file_data.update(testables)
        if "com.unity.editorcoroutines" not in file_data:
            file_data["dependencies"].update(editorcoroutines)
        file.seek(0)
        json.dump(file_data, file, indent = 2)


def modify_build_file_usings(buildFile, release: str):
    """
    Modifies the given ".cs" file to include new using directives.

    Args:
        `string` buildFile: The build file to modify.
    """
    #print("modify_build_file_usings(buildFile)") #DEBUGGING
    #print(f"  buildFile: {buildFile}") #DEBUGGING
    buildUsingDirectives = ""

    if release.startswith("2."):
        buildUsingDirectives = """\
using AltTester.AltTesterUnitySDK;
using AltTester.AltTesterUnitySDK.Editor;"""
    else:
        buildUsingDirectives = """\
using Altom.AltUnityTesterEditor;
using Altom.AltUnityTester;"""

    with open(buildFile, "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(buildUsingDirectives + "\n" + content)


def modify_asmdef(assets):
    """
    Modifies any `.asmdef` files to include the AltTester and AltTesterEditor references.

    Args:
        `string` assets: The Assets folder path.
    """
    for filename in glob(f"/{assets}/**/*.asmdef", recursive=True):
        if "AltTester" not in filename and "Plugins" not in filename:
            with open(filename, mode='r+', encoding='utf-8-sig') as file:
                file_data = json.load(file)
                if "references" not in file_data:
                    file_data["references"] = []
                if "AltTester" not in file_data["references"]:
                    file_data["references"].append("AltTester")
                if "AltTesterEditor" not in file_data["references"]:
                    file_data["references"].append("AltTesterEditor")
                file.seek(0)
                json.dump(file_data, file, indent = 3)


def get_scenes_of_game(settings):
    """
    Gets a list of scenes from the given "EditorBuildSettings.asset" file.

    Args:
        `string` settings: The build settings file.
    Returns:
        `string[]` scenes: The scenes to be included in the build.
    """
    #print("get_scenes_of_game(settings)") #DEBUGGING
    #print(f"  settings: {settings}") #DEBUGGING
    scenes = []
    with open(settings, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "path" in line:
                scenes.append(line[line.rindex(" ")+1:].rstrip("\n"))
    return scenes


def modify_build_file_method(scenes, buildFile, buildMethod, target):
    """
    Modifies the given method in the given ".cs" file to add AltTester objects to the scenes.
    
    Args:
        `string[]` scenes: The scenes to be included in the build.
        `string` buildFile: The build file to modify.
        `string` buildMethod: The build method to modify.
        `string` target: The target to build ("Android" or "iOS").
    """
    #print("modify_build_file_method(scenes, buildFile, buildMethod)") #DEBUGGING
    #print(f"  scenes: {scenes}") #DEBUGGING
    #print(f"  buildFile: {buildFile}") #DEBUGGING
    #print(f"  buildMethod: {buildMethod}") #DEBUGGING
    buildMethodBody = f"""\
        var buildTargetGroup = BuildTargetGroup.{target};
        AltBuilder.AddAltTesterInScriptingDefineSymbolsGroup(buildTargetGroup);
        if (buildTargetGroup == UnityEditor.BuildTargetGroup.Standalone) {{
            AltBuilder.CreateJsonFileForInputMappingOfAxis();
        }}
        var instrumentationSettings = new AltInstrumentationSettings();"""
    i = 0
    for scene in scenes:
        buildMethodBody = buildMethodBody + f"""
            var scene{i} = "{scene}";
            AltBuilder.InsertAltInScene(scene{i}, instrumentationSettings);"""
        i+=1
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
    #print("delete_line_and_preceding (file_path, value)") #DEBUGGING
    #print(f"  file_path: {file_path}") #DEBUGGING
    #print(f"  value: {value}") #DEBUGGING
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


def delete_csharp_if(file_path, value):
    """
    Find C# conditional logic and make it unconditional.  

    Args:
        `string` file_path: The path to the file to modify.
        `string` value: String to search for.
    """
    #print("delete_csharp_if(file_path, value)") #DEBUGGING
    #print(f"  filePath: {file_path}") #DEBUGGING
    #print(f"  value: {value}") #DEBUGGING
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        fileOutBuffer = []
        for i in range(len(lines)):
            if ("if" in lines[i]) and (value in lines[i]):
                if "{" in lines[i]:
                    fileOutBuffer.append("if (true) {\n")
                else:
                    fileOutBuffer.append("if (true)\n")
            else:
                fileOutBuffer.append(lines[i])

    with open(file_path, 'w') as file:
        file.write("".join(fileOutBuffer))


def delete_using(file_path, value):
    """
    Delete library imports in C#.

    Args:
        `string` file_path : Path to the file to modify.
        `string` value : name of the package to remove.
    """
    #print("delete_using(file_path, value)") #DEBUGGING
    #print(f"  filePath: {file_path}") #DEBUGGING
    #print(f"  value: {value}") #DEBUGGING
    fileOutBuffer = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        linez_2_pop = []
        popped_count = 0
        for i in range(len(lines)):
            if ("using" in lines[i]) and (value in lines[i]):
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
    #print("remove_new_input_system(assets)") #DEBUGGING
    #print(f"  filePath: {assets}") #DEBUGGING
    os.remove(f"{assets}/AltTester/AltServer/NewInputSystem.cs")
    os.remove(f"{assets}/AltTester/AltServer/AltKeyMapping.cs")

    shutil.rmtree(f"{assets}/AltTester/Examples")
    os.remove(f"{assets}/AltTester/Examples.meta")

    alt_prefab_drag_path = f"{assets}/AltTester/AltServer/AltPrefabDrag.cs"
    delete_line_and_preceding(alt_prefab_drag_path, "UnityEngine.InputSystem")

    delete_csharp_if(f"{assets}/AltTester/AltServer/Input.cs", "InputSystemUIInputModule")
    delete_using(f"{assets}/AltTester/AltServer/Input.cs", "UnityEngine.InputSystem.UI")
    delete_csharp_if(f"{assets}/AltTester/AltServer/AltMockUpPointerInputModule.cs", "InputSystemUIInputModule")
    delete_using(f"{assets}/AltTester/AltServer/AltMockUpPointerInputModule.cs", "UnityEngine.InputSystem.UI")


# Main entry point.
if __name__ == "__main__":
    v = "unknown"
    try: v = version("AltTester-Instrumenter")
    except: pass
    parser=argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=f"{v}")
    parser.add_argument("--release", required=True, help="[required] The AltTester version to use.")
    parser.add_argument("--assets", required=True, help="[required] The Assets folder path.")
    parser.add_argument("--settings", required=True, help="[required] The build settings file.")
    parser.add_argument("--manifest", required=True, help="[required] The manifest file to modify.")
    parser.add_argument("--newt", required=False, help="[optional, default='True'] Include newtonsoft in the main manifest.json.")
    parser.add_argument("--buildFile", required=True, help="[required] The build file to modify.")
    parser.add_argument("--buildMethod", required=True, help="[required] The build method to modify.")
    parser.add_argument("--target", required=True, help="[required] The build target (Android or iOS).")
    parser.add_argument("--inputSystem", required=True, help="[default='old'] Specify new or old.")
    args=parser.parse_args()

    download_alttester(release=args.release)
    add_alttester_to_project(release=args.release, assets=args.assets)
    modify_manifest(manifest=args.manifest, newt=args.newt)
    modify_asmdef(assets=args.assets)
    modify_build_file_usings(buildFile=args.buildFile,release=args.release)
    scene_array = get_scenes_of_game(settings=args.settings)
    modify_build_file_method(scenes=scene_array, buildFile=args.buildFile, buildMethod=args.buildMethod, target=args.target)

    if "old" in args.inputSystem:
        if os.path.exists(f"{args.assets}/AltTester/AltServer/Input.cs"):
            remove_new_input_system(args.assets)
