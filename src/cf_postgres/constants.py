''' Constants that are useful in multiple places.
    '''

# standard request elements

REQ_REQUEST_ID      = 'RequestId'
REQ_STACK_ID        = 'StackId'
REQ_LOGICAL_ID      = 'LogicalResourceId'
REQ_PHYSICAL_ID     = 'PhysicalResourceId'
REQ_REQUEST_TYPE    = 'RequestType'
REQ_PROPERTIES      = 'ResourceProperties'
REQ_RESPONSE_URL    = 'ResponseURL'

REQ_RESOURCE_TYPE   = 'Resource'
REQ_ADMIN_SECRET    = 'AdminSecretArn'

# standard response elements

RSP_REQUEST_ID      = 'RequestId'
RSP_STACK_ID        = 'StackId'
RSP_LOGICAL_ID      = 'LogicalResourceId'
RSP_PHYSICAL_ID     = 'PhysicalResourceId'
RSP_STATUS          = 'Status'
RSP_REASON          = 'Reason'
RSP_DATA            = 'Data'

# response status code

RSP_SUCCESS         = 'SUCCESS'
RSP_FAILURE         = 'FAILED'

# actions that a resource handler needs to process

ACTION_CREATE       = 'Create'
ACTION_UPDATE       = 'Update'
ACTION_DELETE       = 'Delete'

# components of the standard RDS secret

DB_SECRET_USERNAME  = 'username'
DB_SECRET_PASSWORD  = 'password'
DB_SECRET_HOSTNAME  = 'host'
DB_SECRET_PORT      = 'port'
DB_SECRET_DATABASE  = 'dbname'
