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
  --buildFile   BUILDFILE       [required] The build file to modify.
  --buildMethod BUILDMETHOD     [required] The build method to modify.
  --target      TARGET          [required] The build target (Android or iOS).
  --assets      ASSETS          [optional, default='Assets'] Specify if there is a different Assets folder
  --settings    SETTINGS        [optional, default='ProjectSettings/EditorBuildSettings.asset'] Specify if there is a different EditorBuildSettings.asset file
  --manifest    MANIFEST        [optional, default='Packages/manifest.json'] Specify if there is a different manifest.json file to modify.
  --newt        NEWTONSOFT      [optional, default='True'] Add newtonsoft to the manifest.
  --inputSystem INPUTSYSTEM     [optional, default='old'] Specify new or old.

```

### Example
`python3 -m altins --release="2.1.0" --buildFile="Assets/Editor/Build/ProjectBuilderAndroid.cs" --buildMethod="Build" --target=="Android"`

For Evermerge, build file is either "Assets/Editor/Build/ProjectBuilderAndroid.cs" or "Assets/Editor/Build/ProjectBuilderIos.cs", and buildMethod should just be "Build"


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
            sh 'python3 -m altins --release="2.1.0" --buildFile="Assets/Editor/Build/ProjectBuilderAndroid.cs" --buildMethod="Build" --target=="Android"'
          }
          sh '$UNITY_EXEC -buildTarget Android -executeMethod Build.BuildAndroid $UNITY_PARAMS'
        }
      }
    }
  }
}
```
