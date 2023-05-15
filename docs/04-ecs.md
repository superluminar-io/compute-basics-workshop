# ECS

## In this lab …

- Use Elastic Container Registry (ECR) to store Images
- Use CDK to automatically pack images
- Create an Elastic Container Service (ECS) cluster

## Setup Lab
As this lab is more or less disconnected from the previous labs, it makes sense to create a new project.

1. Just create a new folder `ecs-workshop` next to your `workshop` root folder.

1. Then go to the folder and initialize a new cdk project:
```bash
cd ecs-workshop
npx cdk init app --language=python
```

1. Open `./app.py` and rename your stack again, i.e., change `EcsWorkshopStack(app, "EcsWorkshopStack",` to something different, e.g., append your name.

1. Now there is one last thing to do. As we will also need a VPC setup for this lab, open './ecs_workshop/ecs_workshop_stack.py'
   and copy over the VPC setup code from the previous lab. The file should look like this:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
   )
   from constructs import Construct


   class EcsWorkshopStack(Stack):

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
                       subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
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


## Create an ECR repository

### 📝 Task

Create an ECR repository and upload an image.

### 🔎 Hints

- [What is ECR?](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [ECR CDK documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecr.html)

### 🗺  Step-by-Step Guide

1. Open
   ```bash
   ecs_workshop/ecs_workshop_stack.py
   ```

1. Import `aws_ecr`:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
       aws_ecr as ecr,
   )
   ```

1. Create an ECR repository with a custom name to avoid conflicts with other participants:
   ```python
   ecr.Repository(
       self,
       "WorkshopECR",
       repository_name="workshop-ecr"  # please rename this to avoid conflict with others in the workshop # noqa E501
   )
   ```
   and for convenience, also create an output:
   ```python
   CfnOutput(
       self,
       "ECRRepository",
       value=repository.repository_uri
   )
   ```

1. Deploy the project via
   ```bash
   npx cdk deploy
   ```

1. Open the web console and take a look at [the repository that you created](
   https://eu-west-1.console.aws.amazon.com/ecr/repositories)

1. Lets upload an image. Create a folder for your docker image in the workshop and switch into it:
   ```bash
   mkdir docker
   cd docker
   ```

1. Create a `Dockerfile` with some dummy content:
   ```Dockerfile
   FROM ubuntu:18.04

   CMD ["echo", "Hello World!"]
   ```

1. Build and tag your image:
   ```bash
   docker build ./docker -t workshop-ecr
   docker tag workshop-ecr:latest <your account id>.dkr.ecr.eu-west-1.amazonaws.com/<your repo name>:latest
   ```

1. Now login to the docker registry:
   ```bash
   aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <your account id>.dkr.ecr.eu-west-1.amazonaws.com
   ```

1. And finally push your image:
   ```bash
   docker push <your account id>.dkr.ecr.eu-west-1.amazonaws.com/<your repo name>:latest
   ```

1. If you take a look at your repository now, you should find your image.


## Using CDK DockerImageAsset

### 📝 Task
Use a CDK `DockerImageAsset` to let CDK manage the bundling.

### 🔎 Hints
- [What are Assets?](https://docs.aws.amazon.com/cdk/v2/guide/assets.html)
- [CDK `DockerImageAsset` documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecr_assets/DockerImageAsset.html)

### 🗺 Step-by-Step Guide
1. Open
   ```bash
   ecs_workshop/ecs_workshop_stack.py
   ```

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

### Questions
1. Where did your image go?

## Using Amazon Elastic Container Service (ECS)

### 📝 Task

Create an ECR cluster with Fargate support.

### 🔎 Hints
- [What is Fargate?](https://docs.aws.amazon.com/AmazonECS/latest/userguide/what-is-fargate.html)
- [CDK ECS documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/README.html)

### 🗺 Step-by-Step Guide
1. Open
   ```bash
   ecs_workshop/ecs_workshop_stack.py
   ```

1. Create an ECS cluster:
   ```python
   cluster = ecs.Cluster(
       self,
       "WorkshopCluster",
       vpc=vpc,
   )
   ```
   This cluster will have the capability to run Fargate tasks.

1. Deploy your changes via
   ```bash
   npx cdk deploy
   ```

1. You can now check what you deployed in the [ECS web console](https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters).

1. So we have a cluster now, but we would also like to run some application on it. Lets start by running the container
   that you just build. For this we need a task definition that specifies resources needed, networking and some more
   properties.
   ```python
   ```
   <!-- TODO: Is there code missing? -->

1. Deploy your changes and go to the [ECS console task definitions](https://eu-west-1.console.aws.amazon.com/ecs/v2/task-definitions).
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
   stopped, check the logs in the "Logs" tab. There should be "Hello, world!" printed to the logs.

### Questions
1. Which permissions did you just grant and why?

## Playing with Versioning

### 📝 Task

Delete and restore your object using bucket versioning.

### 🔎 Hints
- [What is object versioning?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)

### 🗺 Step-by-Step Guide

1. Go to the [S3 console](https://s3.console.aws.amazon.com/s3/buckets) and select your bucket. Find the file you just overwrote and select it.

1. You will now see several properties of the file like the file ARN, its S3 URI (which you need for the high level aws cli s3 api), or an
   object URL, which you would use to access the object via HTTPs. Since the bucket is not public, you will not be able to use this, though.
   Also, there is a tab called "Versions" at the top. Click this to inspect all version of the given object. This feature can be very useful
   to prevent files from being deleted accidentally.

1. Now lets try this out. Go back to your bucket objects overview. Select your test object and delete it. You will be prompted to confirm the
   deletion and you have to enter *delete*. If the console prompts you to enter *permanently delete* there ist something *wrong*.

1. Now find the "Show versions" toggle next to the search bar and enable it. You will see, your object is
   not gone but instead a delete marker has been created. To restore your object, you can select the delete marker and delete it 🤪.
   This time you will be prompted to confirm with *permanently delete*. As a rule of thumb: if you delete a version of an object, it is gone for
   good, therefore you should only do this if absolutely necessary (e.g., when you need to clean up a bucket completely before deleting it).

1. Switch of the "Show versions" toggle and your file should re-appear.

---

You can find the complete implementation of this lab [here](https://github.com/superluminar-io/compute-basics-workshop/tree/main/packages/lab4).
