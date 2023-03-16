# AltTester-Instrumenter
Instruments Unity games with AltTester.

## Install
1. `pip3 install git+https://github.com/bigfishgames-external/AltTester-Instrumenter.git`
1. `python3 -m altins --version`

## Usage
`python3 -m altins --help`
```
options:
  -h, --help                    show this help message and exit
  --version                     show program's version number and exit
  --release     RELEASE         [required] The AltTester version to use.
  --assets      ASSETS          [required] The Assets folder path.
  --settings    SETTINGS        [required] The build settings file.
  --manifest    MANIFEST        [required] The manifest file to modify.
  --buildFile   BUILDFILE       [required] The build file to modify.
  --buildMethod BUILDMETHOD     [required] The build method to modify.
  --inputSystem INPUTSYSTEM     [required] Specify new or old.
```

### Example
`python3 -m altins --release="1.8.2" --assets="Assets" --settings="ProjectSettings/EditorBuildSettings.asset" --manifest="Packages/manifest.json" --buildFile="Assets/Editor/BundleAndBuild.cs" --buildMethod="Build()" --inputSystem="old"`

## Uninstall
`pip3 uninstall AltTester-Instrumenter`
