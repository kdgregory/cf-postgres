# cf-postgres: CloudFormation custom resources to provision a Postgres database

CloudFormation will easily let you create a Postgres database server, be it RDS, Autora, or Redshift.
But creating a server is only the first step: you also need to create users, databases, schemas, and
tables. This project is a set of [custom resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html)
to provide that functionality.


# Usage

To use, you must first build and deploy the Lambda. This is a two-step process:

1. Create the Lambda resources, using [CloudFormation](cloudformation/deploy.yml).

   By default, the Lambda is named `cf_postgres`. This CloudFormation script lets
   you provide another name, but you must use that name in the next step.

   **Note:** the template grants the Lambda the ability to retrieve all secrets.
   For security, you should implement a tagging strategy, and use a condition that
   restricts those secrets to the specified tag. The template provides one such
   implementation, commented-out.

2. Build and deploy the Lambda, using the provided [Makefile](Makefile).

At this point, you can use the resource in your CloudFormation templates:

```
```

All invocations require the `SecretArn` property, which specifies a Secrets Manager
secret that contains [database connection information](https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html#reference_secret_json_structure_rds-postgres).

They also require the `Action` property, which specifies the action to take, along
with any properties required by that action. See below for more information.


# Actions


# Roadmap

`Database`: creates an additional, non-default database.

`Schema`: creates a schema within an existing database.

`User`: creates a database user with username, password, and a default database.

`Grant`: grants a user permission to perform some action.

`Restore`: restores a database from a dump stored on S3.

`Migrate`: applies migrations to a database.
