import * as cdk from "@aws-cdk/core";
import * as s3 from "@aws-cdk/aws-s3";
import * as lambda from "@aws-cdk/aws-lambda";
import * as apiGateway from "@aws-cdk/aws-apigateway";

export class CacheTwitterCdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const methodResponse: apiGateway.MethodResponse = {
      statusCode: "200",
      responseParameters: {
        "method.response.header.Access-Control-Allow-Headers": true,
        "method.response.header.Access-Control-Allow-Methods": true,
        "method.response.header.Access-Control-Allow-Credentials": true,
        "method.response.header.Access-Control-Allow-Origin": true,
      },
    };

    const defaultCorsOptions: apiGateway.CorsOptions = {
      allowCredentials: true,
      allowMethods: ["POST", "OPTIONS"],
      statusCode: 200,
      allowOrigins: ["http://localhost:8080"],
    };

    const bucketName = "alngyn-twitter-archive";

    const twitterArchiveBucket = new s3.Bucket(this, "TwitterArchive", {
      bucketName: bucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const twitterPythonLayer = new lambda.LayerVersion(this, "LambdaLayer", {
      code: new lambda.AssetCode("lib/twitterVenv/lib/python3.7/python.zip"),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_8],
    });

    const twitterCacheLambda = new lambda.Function(this, "TwitterCacheLambda", {
      code: new lambda.AssetCode("lib/lambda"),
      handler: "cache_twitter_lambda.handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(30),
      reservedConcurrentExecutions: 1,
      layers: [twitterPythonLayer],
      environment: {
        CONSUMER_KEY: "",
        CONSUMER_SECRET: "",
        ACCESS_TOKEN: "",
        ACCESS_TOKEN_SECRET: "",
      },
    });
    if (!twitterCacheLambda.role) {
      throw new Error("This should not happen. Exiting.");
    }
    twitterArchiveBucket.grantPut(twitterCacheLambda.role);

    const twitterGetLambda = new lambda.Function(this, "TwitterGetLambda", {
      code: new lambda.AssetCode("lib/lambda"),
      handler: "retrieve_twitter_lambda.handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(30),
      reservedConcurrentExecutions: 1,
    });

    if (!twitterGetLambda.role) {
      throw new Error("This should not happen. Exiting.");
    }
    twitterArchiveBucket.grantRead(twitterGetLambda.role);

    const restApiGateway = new apiGateway.LambdaRestApi(this, "ApiGateway", {
      proxy: true,
      handler: twitterGetLambda,
      defaultMethodOptions: {
        // default already none. just making this explicit
        // to call out the preflight call needs 'NONE' auth
        authorizationType: apiGateway.AuthorizationType.NONE,
        methodResponses: [methodResponse],
      },
      restApiName: "TwitterCacheAPIGateway",
      description: "Gets the latest tweets of a person",
      defaultCorsPreflightOptions: defaultCorsOptions,
    });
  }
}
