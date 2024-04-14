# Copyright (c) 2023, Xgrid Inc, https://xgrid.co

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os

import boto3

try:
    iam = boto3.client("iam")
except Exception as e:
    logging.error("Error creating boto3 client: " + str(e))
try:
    lambda_client = boto3.client("lambda")
except Exception as e:
    logging.error("Error creating boto3 client: " + str(e))

# try:
#     ecs_client = boto3.client("ecs")
# except Exception as e:
#     logging.error("Error creating boto3 client: " + str(e))

def handle_fargate_tasks(role_name, role_region, service_mapping):
    """
    Identifies Fargate tasks associated with a given IAM role and region,
    and appends detailed information to the service mapping list.
    """
    # if role_region == "None":
    #     # Skip if the role region is not identified
    #     return
    # ecs_client = boto3.client("ecs", region_name=role_region)

    # print("**** AAA ECS Client DONE ****")

    # # List clusters to identify tasks across all clusters
    # clusters = ecs_client.list_clusters()["clusterArns"]
    # for cluster_arn in clusters:
    #     # List tasks for each cluster
    #     task_arns = ecs_client.list_tasks(cluster=cluster_arn, launchType='FARGATE')["taskArns"]
    #     if task_arns:
    #         # Describe tasks to get detailed information including the task definition
    #         tasks = ecs_client.describe_tasks(cluster=cluster_arn, tasks=task_arns)["tasks"]
    #         for task in tasks:
    #             # Check if the task role ARN matches the current role being processed
    #             task_def_arn = task["taskDefinitionArn"]
    #             task_id = task["id"]
    #             task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)["taskDefinition"]
    #             if "executionRoleArn" in task_def and task_def["executionRoleArn"].endswith(role_name):
    #                 # Append Fargate task details to the service mapping
    #                 task_detail = {
    #                     "Service": "Fargate",
    #                     "Cluster": cluster_arn,
    #                     "Task" : task_id,
    #                     "TaskArn": task["taskArn"],
    #                     "TaskDefinition": task_def_arn
    #                 }
    #                 service_mapping.append(task_detail)

    # Dummy [s]
    task_detail_1 = {
        "Service": "Fargate",
        "Cluster": "Auninda_Cluster_01",
        "Task": "arn:aws:ecs:ap-southeast-2:767398022717:task:task01",
        "TaskDefinition": "Auninda_Task_Definition_01"
    }
    task_detail_2 = {
        "Service": "Fargate",
        "Cluster": "Auninda_Cluster_01",
        "Task": "arn:aws:ecs:ap-southeast-2:767398022717:task:task02",
        "TaskDefinition": "Auninda_Task_Definition_02"
    }
    task_detail_3 = {
        "Service": "Fargate",
        "Cluster": "Auninda_Cluster_01",
        "Task": "arn:aws:ecs:ap-southeast-2:767398022717:task:task03",
        "TaskDefinition": "Auninda_Task_Definition_03"
    }
    service_mapping.append(task_detail_1)
    service_mapping.append(task_detail_2)
    service_mapping.append(task_detail_3)

    print("**** AAA handle_fargate_tasks DONE ****")
    # Dummy [e]



def lambda_handler(event, context):

    """
    List Services Association with IAM Roles.

    Args:
        resource file: It takes resources.json file of IAM role Details.

    Returns:
        It return List of IAM role and its associated services to another
        lambda function.

    Raises:
        EC2 instance details: Raise error if ec2 describe_instances
        api not execute
    """

    function_name = os.environ["function_name_iamroleservice"]
    resource_file_content = event
    resource_mapping = []

    # parsing iam role detail
    for iterator in range(len(resource_file_content)):
        service_mapping = []
        role_arn = resource_file_content[iterator]["Arn"]
        role_name = resource_file_content[iterator]["RoleName"]
        if len(resource_file_content[iterator]["RoleLastUsed"]) != 0:
            role_region = resource_file_content[iterator]["RoleLastUsed"]["Region"]
        else:
            role_region = "None"
        statement_service = resource_file_content[iterator]["AssumeRolePolicyDocument"][
            "Statement"
        ]
        # parsing services attached to IAM role
        for service_iterator in range(len(statement_service)):
            service_list = []
            data_principal = statement_service[service_iterator]["Principal"]
            for key in data_principal.keys():
                if key == "Service":
                    service = statement_service[service_iterator]["Principal"][
                        "Service"
                    ]
                    if isinstance(service, list):
                        for item in service:
                            # getting service name for boto3 client
                            service_name = item.split(".")[0]
                            service_list.append(service_name)
                    else:
                        # getting service name for boto3 client
                        service_name = service.split(".")[0]
                        service_list.append(service_name)
                else:
                    # skipping AWS User and federated User
                    continue
            try:
                for resource in service_list:

                    # handling ecs services here
                    if resource == "ecs-tasks":
                        handle_fargate_tasks(role_name, role_region, service_mapping)


                    # handling ec2 service here
                    elif resource == "ec2":
                        if role_region == "None":
                            # role is not in use
                            continue
                        else:
                            service_client = boto3.client(
                                resource, region_name=role_region
                            )
                        try:
                            instance_profile_detail = (
                                iam.list_instance_profiles_for_role(RoleName=role_name)
                            )
                        except Exception as e:
                            logging.error("Error getting IAM Instance profile" + str(e))
                            return {
                                "statusCode": 500,
                                "body": json.dumps({"Error": str(e)}),
                            }

                        # getting instance profile from iam role
                        profile_iterator = instance_profile_detail["InstanceProfiles"]
                        for profile in range(len(profile_iterator)):
                            instance_profile = instance_profile_detail[
                                "InstanceProfiles"
                            ][profile]["Arn"]
                            ec2 = service_client.describe_instances(
                                Filters=[
                                    {
                                        "Name": "iam-instance-profile.arn",
                                        "Values": [instance_profile],
                                    }
                                ]
                            )
                            for reservation in ec2["Reservations"]:
                                for instance in reservation["Instances"]:
                                    instance_id = instance["InstanceId"]
                                    instance_region = instance["Placement"][
                                        "AvailabilityZone"
                                    ][:-1]
                                    instance_detail = {
                                        "Service": "ec2",
                                        "Instance_Region": instance_region,
                                        "Instance": instance_id,
                                    }
                                    service_mapping.append(instance_detail)
                    elif resource == "lambda":
                        if role_region == "None":
                            # role is not in use
                            continue
                        else:
                            service_client = boto3.client(
                                resource
                            )
                        try:
                            list_of_lambdas = service_client.list_functions()
                        except Exception as e:
                            logging.error("Error getting list of lambdas" + str(e))
                            return {
                                "statusCode": 500,
                                "body": json.dumps({"Error": str(e)}),
                            }

                        # getting lambdas description from the above list
                        lambdas_iterator = list_of_lambdas["Functions"]
                        for function in lambdas_iterator:
                            function_arn = function["FunctionArn"]
                            function_region = function["FunctionArn"].split(':')[3]
                            function_role_arn = function["Role"]
                            if function_role_arn != role_arn:
                                # if the lambda is not assuming this role
                                continue
                            else:
                                function_detail = {
                                    "Service": "lambda",
                                    "Function_Region": function_region,
                                    "Function": function_arn
                                }
                                service_mapping.append(function_detail)
                    else:
                        # adding other services
                        service_mapping.append(resource)
            except Exception as e:
                logging.error("Error getting EC2 instances details" + str(e))
                return {"statusCode": 500, "body": json.dumps({"Error": str(e)})}

        # creating json object for cost and usage api call
        role_mapping = {
            "Role": role_arn,
            "Role_Region": role_region,
            "Service Details": service_mapping,
        }
        resource_mapping.append(role_mapping)

        try:
            invoker = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="Event",
                Payload=json.dumps(resource_mapping),
            )
            # Extract the status code from the response
            status_code = invoker["StatusCode"]
            if status_code != 202:
                # Handle unexpected status code
                logging.error(
                    f"Unexpected status code {status_code} returned from iamroleservice_lambda"
                )
        except Exception as e:
            logging.error("Error in invoking lambda function: " + str(e))
            return {
                "statusCode": 500,
                "body": "Error invoking iamroleservice_lambda",
            }

    return {"statusCode": 200, "body": json.dumps(resource_mapping)}
#EOF