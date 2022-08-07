# cf-postgres: CloudFormation custom resources to provision a Postgres database

CloudFormation will easily let you create a Postgres database server, be it RDS, Autora, or Redshift.
But creating a server is only the first step: you also need to create users, databases, schemas, and
tables. This project is a set of [custom resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html)
to provide that functionality.


# Usage


# Features


# Roadmap

`Database`: creates an additional, non-default database.

`Schema`: creates a schema within an existing database.

`User`: creates a database user with username, password, and a default database.

`Grant`: grants a user permission to perform some action.

`Restore`: restores a database from a dump stored on S3.

`Migrate`: applies migrations to a database.
