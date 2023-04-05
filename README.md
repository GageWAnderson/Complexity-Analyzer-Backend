# Python Lambda Function Repository for AWS

This repository contains Python code for AWS Lambda functions. 

## Getting Started

1. Clone this repository to your local machine.

2. Set up your AWS credentials on your local machine. You can use the AWS Command Line Interface (CLI) or set them as environment variables.

3. Create a new Lambda function in the AWS Management Console or using the AWS CLI.

4. Deploy your function code to the Lambda function. You can use the AWS Management Console or the AWS CLI to upload your code.

## Function Structure

Each function in this repository is contained in its own directory with the following structure:

- `__init__.py` is an empty file that indicates that the directory is a Python package.

- `main.py` contains the code for the Lambda function. 

- `requirements.txt` lists the dependencies required for the function. 

## Testing

You can test the function locally using the `aws-lambda-ric` (Runtime Interface Client) tool. This tool simulates the Lambda execution environment and allows you to test your function in a local environment.

To use `aws-lambda-ric`, you must first install it by running:

pip install aws-lambda-ric

Then, you can test your function by running:

lambda-ric main.handler < test_event.json

`test_event.json` should contain the event data that triggers your Lambda function.

## Deployment

To deploy your function code to AWS Lambda, you can use the AWS Management Console or the AWS CLI. You will need to package your code into a ZIP file and upload it to the Lambda function.

If your function has dependencies listed in `requirements.txt`, you can include them in the ZIP file or upload them separately as a layer. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
