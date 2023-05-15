# Batch

## In this lab …

- Create an AWS Batch compute environment and job queue
- Create and submit a job defition
- Use advanced features of AWS Batch, such as Array jobs and job dependencies

## Setup Lab
As this lab is more or less disconnected from the previous labs, it makes sense to create a new project.

1. Just create a new folder `batch-workshop` next to your `workshop` root folder.

1. Then go to the folder and initialize a new cdk project:
```bash
cd batch-workshop
npx cdk init app --language=python
```

1. Open `./app.py` and rename your stack again, i.e., change `BatchWorkshopStack(app, "BatchWorkshopStack",` to something different, e.g., append your name.

1. Now there is one last thing to do. As we will also need a VPC setup for this lab, open './batch_workshop/batch_workshop_stack.py'
   and create a VPC with a public and a private with egress subnet:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
   )
   from constructs import Construct


   class BatchWorkshopStack(Stack):
       def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
           super().__init__(scope, construct_id, **kwargs)
           vpc = ec2.Vpc(
               self,
               "WorkshopVPC",
               max_azs=2,
               ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
               subnet_configuration=[
                   ec2.SubnetConfiguration(
                       name="Private",
                       subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                       cidr_mask=20
                   ),
                   ec2.SubnetConfiguration(
                       name="Public",
                       subnet_type=ec2.SubnetType.PUBLIC,
                       cidr_mask=20
                   )
               ]
           )
   ```

## Batch compute environment and job queue

### 📝 Task

Create a Batch compute environment and a job queue.

### 🔎 Hints

- [What is Batch?](https://docs.aws.amazon.com/batch/latest/userguide/what-is-batch.html)
- [Batch experimental CDK documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_batch_alpha/README.html)

### 🗺  Step-by-Step Guide

1. Open
   ```bash
   batch_workshop/batch_workshop_stack.py
   ```

1. Install `aws_batch_alpha`via:
   ```bash
   pip install aws-cdk.aws-batch-alpha
   ```

   Now call `pip freeze`and copy the line containing `aws-cdk.aws-batch-alpha` into your `requirements.txt`.

1. Import `aws_batch_alpha`:
   ```python
   from aws_cdk import (
       Stack,
       aws_batch_alpha as batch,
       aws_ec2 as ec2,
   )
   ```

1. Create a Batch compute environment:
   ```python
   compute_env = batch.ManagedEc2EcsComputeEnvironment(
       self,
       "BatchComputeEnvironment",
       vpc=vpc,
   )
   ```
   as well as a job queue:
   ```python
   job_queue = batch.JobQueue(
       self,
       "BatchJobQueue",
       compute_environments=[
           batch.OrderedComputeEnvironment(
               compute_environment=compute_env,
               order=1
           )
       ]
   )
   ```

1. Deploy the project via
   ```bash
   npx cdk deploy
   ```

1. Open the web console and take a look at [your Batch resources](
   https://eu-west-1.console.aws.amazon.com/batch/home) and [your ECS cluster](https://eu-west-1.console.aws.amazon.com/ecs/home)

## Job Definition

### 📝 Task
Add a job definition and run a job.

### 🔎 Hints
- [What are Job Definitions?](https://docs.aws.amazon.com/batch/latest/userguide/job_definitions.html)
- [What are Jobs?](https://docs.aws.amazon.com/batch/latest/userguide/jobs.html)
- [Job Definiton CDK documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_batch_alpha/EcsJobDefinition.html)

### 🗺 Step-by-Step Guide
1. Open
   ```bash
   batch_workshop/batch_workshop_stack.py
   ```

1. Import `aws_ecs`, `aws_logs` and `Size`:
   ```python
   from aws_cdk import (
       Size,
       Stack,
       aws_batch_alpha as batch,
       aws_ec2 as ec2,
       aws_ecs as ecs,
       aws_logs as logs,
   )
   ```

1. Create a job definition:
   ```python
   job_definition = batch.EcsJobDefinition(
       self,
       "BatchJobDefinition",
       container=batch.EcsEc2ContainerDefinition(
           self,
           "BatchContainerDefinition",
           image=ecs.ContainerImage.from_registry("amazonlinux"),
           command=["echo", "hello world"],
           memory=Size.mebibytes(512),
           cpu=1,
           logging=ecs.LogDriver.aws_logs(
               stream_prefix="batch",
               log_retention=logs.RetentionDays.ONE_WEEK
           )
       )
   )
   ```

1. Deploy the project via
   ```bash
   npx cdk deploy
   ```

1. Open the [batch console](https://eu-west-1.console.aws.amazon.com/batch/home?#job-definition)
















1. You can remove remove your repository and the `CfnOutput`, CDK will manage this for you.

1. Now add the `DockerImageAsset` with a corresponding output:
   ```python
   asset = ecr_assets.DockerImageAsset(
       self,
       "ECRAsset",
       directory=path.join(path.dirname(__file__), "..", "docker")
   )

   CfnOutput(
       self,
       "ECRRepository",
       value=asset.repository.repository_uri_for_tag(asset.image_uri),
   )
   ```

1. Deploy your changes. You will see that the image is also pushed:
   ```
   [0%] start: Publishing 036bbda8ccada264b693ac2003d4e6ebb1f08f87daa34fd2c4b44ab1051fcd19:current_account-current_region
   [50%] success: Published 63cebb1acf8865f17d67d1934c3677face55fc27d9af8370bc0a2b81f70709f3:current_account-current_region
   The push refers to repository [<your account id>.dkr.ecr.eu-west-1.amazonaws.com/cdk-hnb659fds-container-assets-<your account id>-eu-west-1]
   b7e0fa7bfe7f: Preparing
   b7e0fa7bfe7f: Pushed
   ```

1. 1. Deploy your changes and go to the [ECS console task definitions](https://eu-west-1.console.aws.amazon.com/ecs/v2/task-definitions).
   Lets deploy our task. Select the task definition you just created and click "Deploy" -> "Run task". Choose your ECS cluster,
   then select "Launch type". You can now select "FARGATE" from the drop-down. Other options would be EC2 or EXTERNAL (ECS Anywhere).
   We do not have any EC2 instances or external servers registered to our cluster, so we go with FARGATE.
   The default configuration for the deployment options will do, but we have to configure some networking. Here you
   should select the VPC you created. Options:
   * You can remove the private subnets and leave public IP turned on
   * You could also remove the public subnets and turn off public IP assignment, but since the cluster is pulling images from ECR,
     and the tasks interacts with ECS, logs to CloudWatch and pulls image layers from S3 you would need
     interface/gateway endpoints for these services (ECR, ECR docker, ECS, CloudWatch Logs, and S3). If you want to do
     this, you can add this code below your VPC initialization:
     ```python
     vpc.add_interface_endpoint(
         "ECS",
         service=ec2.InterfaceVpcEndpointAwsService.ECS,
     )
     vpc.add_interface_endpoint(
         "ECR",
         service=ec2.InterfaceVpcEndpointAwsService.ECR,
     )
     vpc.add_interface_endpoint(
         "ECRDocker",
         service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
     )
     vpc.add_interface_endpoint(
         "CloudWatchLogs",
         service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
     )
     vpc.add_gateway_endpoint(
         "S3",
         service=ec2.GatewayVpcEndpointAwsService.S3,
     )
     ```
     and deploy before continuing to run your task.
   Now click "Create" at the bottom.

1. From the list of tasks in the cluster, you can now click on your task to see more details. Hit refresh a couple of
   times at the top right of the page. You can observe the task's last status and also its desired status. When the task
   stopped, check the logs in the "Logs" tab. There should be "Hello, world!" printed to the logs.\

### Questions
1. Where did your image go?

## Using Amazon Elastic Container Service (ECS)

### 📝 Task

Create ECS service and run public nginx in a service.

### 🔎 Hints
- [What are ECS services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html)
- [CDK ECS patterns documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs_patterns/README.html)

### 🗺 Step-by-Step Guide
1. Open
   ```bash
   ecs_workshop/ecs_workshop_cdk_assets_stack.py
   ```
1. We can now use the ECS pattern library to create a load balanced Fargate service. Add this at the end of your
   constructor:
   ```python
   nginx_task_definition = ecs.FargateTaskDefinition(
       self,
       "NginxTask",
       cpu=256,
       memory_limit_mib=512,
   )
   nginx_container = nginx_task_definition.add_container(
       "NginxContainer",
       image=ecs.ContainerImage.from_registry(
           "public.ecr.aws/nginx/nginx:stable"
       ),
       logging=ecs.LogDrivers.aws_logs(
           stream_prefix="NginxContainer",
       ),
   )
   ```
   This will generate a task definition for running an nginx server.

1. As the server also provides ports to which the load balancer needs to map, you also need to add port mappings:
   ```python
   nginx_container.add_port_mappings(
       ecs.PortMapping(
           container_port=80,
       )
   )
   ```

1. We can now bundle all of this into a load balanced Fargate service:
   ```python
   ecs_patterns.ApplicationLoadBalancedFargateService(
       self,
       "WorkshopService",
       cluster=cluster,
       task_definition=nginx_task_definition,
       desired_count=2,
       public_load_balancer=True,
       listener_port=80,
       task_subnets=ec2.SubnetSelection(
           subnet_type=ec2.SubnetType.PUBLIC,
       ),
       assign_public_ip=True,
   )
   ```
   We have to pick public subnets here, as we are using an image from the ECR public gallery. Normally, you would create
   a new image on deploy and upload it to your private repository, but for this example, we keep it simple.

1. Deploy your changes via
   ```bash
   npx cdk deploy
   ```

1. Go to the [ECS console](https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters) and select your cluster. In the
   services tab you will be greeted by the service you just defined in code. There should be 2 of 2 tasks running (or
   pending, if you are a fast clicker). Go to your service and check the "Networking" tab. There should be a load balancer
   configured with a public DNS name. Open this in your browser and check that the web server you just deployed responds
   to requests properly.

   You can also go to the tasks tab of your cluster and verify that there are 2 tasks running. Their health status is
   unknown, though. This is because the nginx image does not provide a docker `HEALTHCHECK` on their side ([more about
   health checks here](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_HealthCheck.html)).

1. As for many other resources on AWS, we can also configure auto-scaling. In this example the auto-scaling engine will
   try to achieve a CPU utilization of ~50%:
   ```python
   service.service.auto_scale_task_count(
       max_capacity=4,
       min_capacity=2,
   ).scale_on_cpu_utilization(
       "CpuScaling",
       target_utilization_percent=50,
   )
   ```
   Add this to your code and deploy again.

1. You can inspect the auto scaling settings in your service in your "Configuration and tasks" tab.

1. Questions:
   * What happens, if you terminate one of the tasks belonging to the service?
   * What happens, if your CPU utilization on one task would hit 100% and on the other 0%? Can you imagine a scenario
     where this could happen?

---

You can find the complete implementation of this lab [here](https://github.com/superluminar-io/compute-basics-workshop/tree/main/packages/lab4).
