# Python Lambda Function Repository for AWS

This repository contains Python code for AWS Lambda functions that implement the backend logic for a code complexity analyzer.

## Getting Started

1. Clone this repository to your local machine.

2. Develop you code locally on a feature branch. Make a pull request once done.

3. On merge of Pull Requests into `main` AWS CodePipeline will pull from the GitHub repository and deploy the new code to the Lambda functions.

## Function Structure

Each function in this repository is contained in its own directory with the following structure:

- `xxx.py` contains the code for the Lambda function. 

- `requirements.txt` lists the dependencies required for the function. This is deprecated, since the functions use Lambda layers to access their dependencies once deployed to the cloud.

## Testing

You can test the function locally using the `aws-lambda-ric` (Runtime Interface Client) tool. This tool simulates the Lambda execution environment and allows you to test your function in a local environment.

To use `aws-lambda-ric`, you must first install it by running:

pip install aws-lambda-ric

Then, you can test your function by running:

lambda-ric main.handler < test_event.json

`test_event.json` should contain the event data that triggers your Lambda function.

## Deployment

The reccomended deployment method is to merge the changes to your code into `main` via a PR. This will kick off an AWS CodePipeline build script that wil automatically deploy all the code to your lambda functions.

To deploy your function code to AWS Lambda, you can use the AWS Management Console or the AWS CLI. You will need to package your code into a ZIP file and upload it to the Lambda function.

If your function has dependencies listed in `requirements.txt`, you can include them in the ZIP file or upload them separately as a layer. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
