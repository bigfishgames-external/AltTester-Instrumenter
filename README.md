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
  --target      INPUTSYSTEM     [required] The build target (Android or iOS).
  --newt        NEWTONSOFT      [required] Add newtonsoft to the manifest.
```

### Example
`python3 -m altins --release="2.0.2" --assets="Assets" --settings="ProjectSettings/EditorBuildSettings.asset" --manifest="Packages/manifest.json" --buildFile="Assets/Scripts/Editor/Build.cs" --buildMethod="BuildAndroid()" --inputSystem="old" --target="Android" --newt="True"`

## Uninstall
`pip3 uninstall AltTester-Instrumenter`

## CI/CD
BFG uses [Jenkins](https://www.jenkins.io/) for Continuous Integration and Continuous Delivery.

### JENKINS FILE
The following is an example of running AltTester-Instrumenter before a game build.

```
pipeline {
  parameters {
    booleanParam name: 'Test_Instrument', description: 'For E2E Test Builds', defaultValue: false
  }
  stages {
    stage('Android Build') {
      steps {
        script {
          if (params.Test_Instrument) {
            sh 'pip3 install git+https://github.com/bigfishgames-external/AltTester-Instrumenter.git'
            sh 'python3 -m altins --release="2.0.2" --assets="Assets" --settings="ProjectSettings/EditorBuildSettings.asset" --manifest="Packages/manifest.json" --buildFile="Assets/Scripts/Editor/Build.cs" --buildMethod="BuildAndroid()" --target=="Android" --inputSystem="old" --newt="True"'
          }
          sh '$UNITY_EXEC -buildTarget Android -executeMethod Build.BuildAndroid $UNITY_PARAMS'
        }
      }
    }
  }
}
```
