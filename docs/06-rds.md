# RDS

<!-- Plan:
- Backup aufsetzen
- Cluster runternehmen + vom Backup wiederherstellen -->

## In this lab …

- Create a RDS Aurora database cluster
- Launch ECS service that connects to the database
- Backup your database cluster and restore it

## Setup Lab
As this lab is more or less disconnected from the previous labs, it makes sense to create a new project.

1. Just create a new folder `rds_workshop` next to your `workshop` root folder.

1. Then go to the folder and initialize a new cdk project:
```bash
cd rds_workshop
npx cdk init app --language=python
```

1. Open `./app.py` and rename your stack again, i.e., change `RdsWorkshopStack(app, "RdsWorkshopStack",` to something different, e.g., append your name.

1. Now there is one last thing to do. As we will also need a VPC setup for this lab, open `./rds_workshop/rds_workshop_stack.py`
   and create a VPC with a public and a private with egress subnet:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
   )
   from constructs import Construct

   class RdsWorkshopStack(Stack):
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

## RDS Aurora cluster

### 📝 Task

Create a RDS Aurora database cluster.

### 🔎 Hints

- [What is RDS?](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html)
- [RDS CDK documentation](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/README.html)

### 🗺  Step-by-Step Guide

1. Open
   ```bash
   rds_workshop/rds_workshop_stack.py
   ```

1. Import `aws_rds`:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
       aws_rds as rds,
   )
   ```

1. Create a RDS Aurora database cluster:
   ```python
   mysql_cluster = rds.DatabaseCluster(
       self,
       "WorkshopDatabase",
       engine=rds.DatabaseClusterEngine.aurora_mysql(
           version=rds.AuroraMysqlEngineVersion.VER_3_03_0
       ),
       instance_props=rds.InstanceProps(
           vpc_subnets=ec2.SubnetSelection(
               subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
           ),
           vpc=vpc
       ),
       default_database_name="workshop",
   )
   ```

1. Deploy the project via
   ```bash
   npx cdk deploy
   ```

1. Open the web console and take a look at [the RDS Dashboard](https://eu-west-1.console.aws.amazon.com/rds/home?r#databases:), then
   click "Databases" to check on your cluster.

1. Reboot the writer instance via "Actions", refresh a couple of times and observe what happens.

### Questions
- After rebooting, which instance is the writer instance, now?

## Connect from ECS Service

### 📝 Task

Connect to your RDS database cluster from phpMyAdmin running on ECS.

### 🔎 Hints
- [pmpMyAdmin image](https://gallery.ecr.aws/bitnami/phpmyadmin)

### 🗺 Step-by-Step Guide

1. Open
   ```bash
   rds_workshop/rds_workshop_stack.py
   ```

1. Import `aws_ecs`, `aws_ecs_patterns` and `aws_secretsmanager`:
   ```python
   from aws_cdk import (
       Stack,
       aws_ec2 as ec2,
       aws_ecs as ecs,
       aws_ecs_patterns as ecs_patterns,
       aws_rds as rds,
       aws_secretsmanager as secret,
   )
   ```

1. Add the following code to create an ECS cluster, ECS service, and connect the service to your database:
   ```python
   ecs_cluster = ecs.Cluster(
       self,
       "WorkshopCluster",
       vpc=vpc,
   )

   phpmyadmin_task_definition = ecs.FargateTaskDefinition(
       self,
       "PhpMyAdminTask",
       cpu=256,
       memory_limit_mib=512,
   )

   mysql_secret = cast(secret.ISecret, mysql_cluster.secret)
   CfnOutput(self, "SecretArn", value=mysql_secret.secret_arn)

   phpmyadmin_container = phpmyadmin_task_definition.add_container(
       "PhpMyAdminContainer",
       image=ecs.ContainerImage.from_registry(
           "public.ecr.aws/bitnami/phpmyadmin:latest"
       ),
       logging=ecs.LogDrivers.aws_logs(
           stream_prefix="phpmyadmin",
       ),
       secrets={
           "DATABASE_HOST": ecs.Secret.from_secrets_manager(
               mysql_secret,
               field="host",
           ),
           "DATABASE_USER": ecs.Secret.from_secrets_manager(
               mysql_secret,
               field="username",
           ),
           "DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
               mysql_secret,
               field="password",
           ),
       },
       environment={
           "DATABASE_ENABLE_SSL": "yes",
       }
   )

   phpmyadmin_container.add_port_mappings(
       ecs.PortMapping(
           container_port=8080,
       )
   )

   service = ecs_patterns.ApplicationLoadBalancedFargateService(
       self,
       "PhpMyAdminService",
       cluster=ecs_cluster,
       task_definition=phpmyadmin_task_definition,
       desired_count=1,
       public_load_balancer=True,
       listener_port=80,
       task_subnets=ec2.SubnetSelection(
           subnet_type=ec2.SubnetType.PUBLIC,
       ),
       assign_public_ip=True,
   )

   mysql_cluster.connections.allow_default_port_from(service.service)
   ```
   Setting the deletion policy is not required, but we will reuse the secret in the next step and need to retain it.

1. Deploy your changes.

1. Find your cluster in the [ECS console](https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters) and select it. Then
   select the service and wait until there are no pending tasks anymore. Go to the networking tab - on the right side you will
   find load balancer's properties. Find "DNS names" and open the address. You now see the phpMyAdmin Dashboard.

1. For our next lab, create a table in the database `workshop` and populate it with a couple of rows.

## Backup and restore

### 📝 Task

Add data to your database, create a snapshot from your RDS cluster and create a new database from your snapshot.

### 🔎 Hints
- [How to create a DB snapshot](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_CreateSnapshot.html)
- [CDK `DatabaseClusterFromSnapshot`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseClusterFromSnapshot.html)

### 🗺 Step-by-Step Guide

__Disclaimer: this lab will include a lot of waiting time for destroying and setting up RDS__

1. Open the web console and take a look at [the RDS Dashboard](https://eu-west-1.console.aws.amazon.com/rds/home?r#databases:),
   select your cluster. Choose "Take snapshot" from the "Actions" menu, give it a meaningful name and click on "Take snapshot".

1. Wait for the snapshot to complete

1. Destroy the stack you deployed before via `npx cdk destroy`. This will take some time.

1. Go to [your snapshots](https://eu-west-1.console.aws.amazon.com/rds/home?#snapshots-list:). You could now select the snapshot and restore it.
   This would create a new database. But we want to do this via CDK to be able to track changes in code.

1. First create a new file next to the workshop stack and name it `rds_workshop/rds_workshop_restore_stack.py`. Copy the contents of
   `rds_workshop/rds_workshop_stack.py`.

1. Now find the `DatabaseCluster` initialization and replace it by the `DatabaseClusterFromSnapshot` construct. You will need the ARN of the
   snapshot for this, or at least the name. In out example we use the name to demonstrate the constructions of ARNs in CDK:
   ```python
   mysql_cluster = rds.DatabaseClusterFromSnapshot(
       self,
       "WorkshopDatabaseFromSnapshot",
       engine=rds.DatabaseClusterEngine.aurora_mysql(
           version=rds.AuroraMysqlEngineVersion.VER_3_01_0
       ),
       instance_props=rds.InstanceProps(
           vpc_subnets=ec2.SubnetSelection(
               subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
           ),
           vpc=vpc
       ),
       default_database_name="workshop",
       snapshot_identifier=Arn.format(
           components={
               "service": "rds",
               "resource": "cluster-snapshot",
               "resourceName": <Your snapshot name here>,
               "arnFormat": ArnFormat.COLON_RESOURCE_NAME,
           },
           stack=Stack.of(self),
       ),
       snapshot_credentials=rds.SnapshotCredentials.from_generated_secret(
           "admin",
       ),
   )
   ```
   Note that you cannot change the username for the database. It is taken from the snapshot. A new password and other connection info will
   be generated into a secret like in the previous section, though.

1. In `app.py` you can now change the import to reference the new stack. The class name is the same, as you copied it.
   ```python
   from rds_workshop.rds_workshop_restore_stack as RdsWorkshopStack
   ```

1. Now go ahead and deploy via `npx cdk deploy`. This will also take some time, as it will recreate all of the network. We didn't separate this
   out or used any other technique of speeding this up.

1. When the stack is finally deployed, go find the load balancer's DNS name as done before. You should now be able to open phpMyAdmin again
   and see all the tables and data you created before you took the snapshot.

---

You can find the complete implementation of this lab [here](https://github.com/superluminar-io/compute-basics-workshop/tree/main/packages/lab6).
