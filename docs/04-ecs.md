# ECS

## In this lab …

- Use Elastic Container Registry (ECR) to store Images
- Use CDK to automatically pack images
- Create an Elastic Container Service (ECS) cluster
- Run tasks and services

## Setup Lab
As this lab is more or less disconnected from the previous labs, it makes sense to create a new project.

1. Just create a new folder `ecs-workshop` next to your `workshop` root folder.

1. Then go to the folder and initialize a new cdk project:
```bash
cd ecs-workshop
npx cdk init app --language=python
```

1. Open `./app.py` and rename your stack again, i.e., change `EcsWorkshopStack(app, "EcsWorkshopStack",` to something different, e.g., append your name.

1. Now there is one last thing to do. As we will also need a VPC setup for this lab, open `./ecs_workshop/ecs_workshop_stack.py`
   and copy over the VPC setup code from the previous lab.\
\
The file should look like this:

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
   repository = ecr.Repository(
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
   and save it as
   ```python
   ecs_workshop/ecs_workshop_cdk_assets_stack.py
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

Create ECS service and run public nginx in a service.

### 🔎 Hints
- [What are ECS services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html)
- [CDK ECS patterns documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs_patterns/README.html)

### 🗺 Step-by-Step Guide
1. Open
   ```bash
   ecs_workshop/ecs_workshop_cdk_assets_stack.py
   ```
   
1. Import `aws_ecs` and `aws_ecs_patterns`:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
       aws_ecr as ecr,
       aws_ecs as ecs,
       aws_ecs_patterns as ecs_patterns
   )
   ```
1. Now we have to create an ECS Cluster, where our application will run in:
   ```python
   cluster = ecs.Cluster(
         self,
         "WorkshopCluster",
         vpc=vpc,
   )
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
