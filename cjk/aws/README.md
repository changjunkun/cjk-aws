### Project Architecture
![ProjectArchitecture](docs/architecture.png)


### Prerequisite
1. A Linux machine to deploy CDK codes, with AWS IAM user's AK/SK configured.

2. Python3.8 and NodeJS are installed on the Linux machine.


### To deploy
1. Ensure CDK is installed
```
$ npm install -g aws-cdk
```

2. Create a Python virtual environment
```
$ python3 -m venv .venv
```

3. Activate virtual environment

_On MacOS or Linux_
```
$ source .venv/bin/activate
```

_On Windows_
```
% .venv\Scripts\activate.bat
```

4. Install the required dependencies.

```
$ pip install -r requirements.txt
```

5. Bootstrapping cdk environment.

```
$ cdk bootstrap
```

6. Synthesize (`cdk synth`) or deploy (`cdk deploy`) the example, use --parameters to pass additional parameters, use --require-approval to run without being prompted for approval, Please replace your own tags to the tags parameter.

```
$ cdk deploy --require-approval never --parameters tags='{"TagName1": "TagValue1","TagName2": "TagValue2"}'
```

(Optional) You can also choose to disable the Identity Recording feature by definening the `identityRecording` parameter to false. This feature is enabled by default.

```
$ cdk deploy --require-approval never --parameters tags='{"TagName1": "TagValue1","TagName2": "TagValue2"}' --parameters identityRecording='false'
```