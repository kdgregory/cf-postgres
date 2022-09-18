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

   **Note:** the template grants the Lambda the ability to retrieve all secrets
   that begin with "database/". Alternatively, implement a tagging strategy and
   use a condition on the policy.

2. Build and deploy the Lambda, using the provided [Makefile](Makefile).

At this point, you can use the resource in your CloudFormation templates:

```
  User:
    Type:                               "Custom::CFPostgres"
    Properties:
      Resource:                         "User"
      ServiceToken:                     !Ref ServiceToken
      AdminSecretArn:                   !Ref AdminSecret
      UserSecretArn:                    !Ref UserSecret
```

All invocations require a `Resource` property, which specifies the type of
resource to create.  See [below](#actions) for all implemented actions.

You must also specify the `AdminSecretArn` property, which specifies a Secrets Manager
secret that contains [database connection information](https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html#reference_secret_json_structure_rds-postgres)
for the database administrator account.


# Resources

## User

Creates or deletes a Postgres user; update is a no-op.

### Configuration properties

| Property        | Description
|-----------------|-------------
| `Username`      | The name of the user.
| `Password`      | A password for the user.
| `UserSecretArn` | A secret that contains both username and password.

You must specify either `Username` or `UserSecretArn` (with the latter preferred).

`Password` is only used if `Username` is specified. If omitted, then you must manually set the password at a later point to enable login.

### Return values

None.


# Roadmap

`Database`: creates an additional, non-default database.

`Schema`: creates a schema within an existing database.

`Grant`: grants a user permission to perform some action.

`Restore`: restores a database from a dump stored on S3.

`Migrate`: applies migrations to a database.
