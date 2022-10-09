# cf-postgres: CloudFormation custom resources to provision a Postgres database

CloudFormation lets easily you create a Postgres database server, be it RDS, Autora, or Redshift.
But creating a server is only the first step in deploying a database-centric application: you
also need to create users, databases, schemas, and tables. This project is a set of [custom
resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html)
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

   ```
   make deploy
   ```

3. The output from this command will include the function ARN. Copy that for the
   next step.

At this point, you can use the resource in your CloudFormation templates:

```
  User:
    Type:                               "Custom::CFPostgres"
    DependsOn:                          [ AdminSecretAttachment ]
    Properties:
      ServiceToken:                     !Ref LambdaArn
      Resource:                         "User"
      AdminSecretArn:                   !Ref AdminSecret
      UserSecretArn:                    !Ref UserSecret
```

All invocations require the following properties:

* `ServiceToken`

  This is the ARN of the deployed Lambda, and is required by CloudFormation.

  _Type_: _String_

* `Resource`

  Identifies the resource to create. See [below](#resources) for all implemented resources.

  _Type_: _String_

* `AdminSecretArn`

  A Secrets Manager secret that contains connection information for the database admin user.
  This secret must contain a JSON string as described
  [here](https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html#reference_secret_json_structure_rds-postgres).

  _Type_: _String_

Note the use of `DependsOn`: this is ensures that the database has been created
before you attempt to create resources in it.


# Resources

## User

Creates, updates, or deletes a Postgres user.

### Properties

* `Username`

  The name of the user. You may either specify this or `UserSecretArn`, not both.

  _Type_: String

  _Required_: No

* `Password`

  An optional password for the user. May only be specified with `Username`. If
  you do not specify a password, the user will not be able to login.

  _Type_: String

  _Required_: No

* `UserSecretArn`

  A secret that contains both username and password, following the standard RDS
  format linked above.

  _Type_: String

  _Required_: No

* `CreateDatabase`

  If this is "true" (case-insensitive), the user will be granted the permission
  to create new databases. Anything else, or missing, and they won't.

  _Type_: String

  _Required_: No

* `CreateRole`

  If this is "true" (case-insensitive), the user will be granted the permission
  to create new roles. Anything else, or missing, and they won't.

  _Type_: String

  _Required_: No


### Return values

The username.


### Notes

You cannot change the name of a user once created. Attempting to change the username
property (or secret value) will result in an error and no changes to the stack.

Updating the secret value _does not_ trigger a user update. Replacing the secret does.


### Examples

Create a user based on a secret.

```
UserSecret:
  Type:                               "AWS::SecretsManager::Secret"
  Properties:
    Name:                             !Sub "database/${AWS::StackName}-Application"
    Description:                      !Sub "Application user and password for database ${AWS::StackName}"
    GenerateSecretString:
      SecretStringTemplate:           !Sub |
                                      {
                                        "username": "example"
                                      }
      GenerateStringKey:              "password"
      ExcludePunctuation:             true
      PasswordLength:                 64


User:
  Type:                               "Custom::CFPostgres"
  DependsOn:                          [ AdminSecretAttachment ]
  Properties:
    Resource:                         "User"
    ServiceToken:                     !Ref ServiceToken
    AdminSecretArn:                   !Ref AdminSecret
    UserSecretArn:                    !Ref UserSecret
    CreateDatabase:                   true
    CreateRole:                       false
```



# Roadmap

`Database`: creates an additional, non-default database.

`Schema`: creates a schema within an existing database.

`Grant`: grants a user permission to perform some action.

`Restore`: restores a database from a dump stored on S3.

`Migrate`: applies migrations to a database.

