import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iot from 'aws-cdk-lib/aws-iot';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as alexa from 'aws-cdk-lib/alexa-ask';
import { Duration } from 'aws-cdk-lib';

export class CdkSkillBackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);


    const user_table = new dynamodb.Table(this, 'user-selected-vin', {
      tableName: "user_table",
      partitionKey: { name: 'email_address', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    const car_status_table = new dynamodb.Table(this, 'car_status_table', {
      tableName: "car_status_table",
      partitionKey: { name: 'vin', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    
    const write_to_ddb_policy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['dynamoDB:PutItem'],
      resources: [user_table.tableArn, car_status_table.tableArn]
    });

    
    // const iotrule_role = new iam.Role(this, 'iotrulerole', {
    //   roleName: "iotrulerole",
    //   assumedBy: new iam.ServicePrincipal('iot.amazonaws.com'),
    // });

    // iotrule_role.addToPolicy(write_to_ddb_policy);

    // const queue = new sqs.Queue(this, 'CdkSkillBackendQueue', {
    //   queueName: "event_queue",
    //   retentionPeriod: cdk.Duration.days(14),
    // });

    // const write_to_sqs_policy = new iam.PolicyStatement({
    //   effect: iam.Effect.ALLOW,
    //   actions: ['sqs:SendMessage', 'sqs:ReceiveMessage', 'sqs:DeleteMessage'],
    //   resources: [queue.queueArn]
    // });

    // iotrule_role.addToPolicy(write_to_sqs_policy);

    // const iot_rule = new iot.CfnTopicRule(this, 'writetoddbrule', {
    //   ruleName: 'writetoddbrule',
    //   topicRulePayload: {
    //     actions: [
    //       {
    //         dynamoDBv2: {
    //           roleArn: iotrule_role.roleArn,
    //           putItem: {
    //             tableName: car_status_table.tableName,
    //           },
    //         }
    //       },
    //       {
    //         sqs: {
    //           roleArn: iotrule_role.roleArn,
    //           queueUrl: queue.queueUrl,
    //           useBase64: false,
    //         },
    //       }
    //     ],
    //     sql: 'SELECT * FROM "car/status"',
    //   },
    // });

    const lambda_execution_role = new iam.Role(this, 'lambdaexecutionrole', {
      roleName: "lambda_execution_role",
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });

    lambda_execution_role.addToPolicy(write_to_ddb_policy);


    const skill_function = new lambda.Function(this, 'skillFunction', {
      functionName: "skill_function",
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'lambda_function.handler',
      code: lambda.Code.fromAsset('./resources/skill'),
      timeout: Duration.minutes(15)
    });
  }
}
