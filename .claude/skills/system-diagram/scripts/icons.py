"""Resolve a short service name (e.g. "alb", "rds", "s3") to an AWS icon PNG.

Icons come from the `diagrams` pip package (resources/ folder), so no
separate download is needed.
"""
import os
import re

import diagrams

ROOT = os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)), "resources")

# Short names -> "provider/category/file" relative to ROOT.
ALIASES = {
    "user": "aws/general/user.png",
    "users": "aws/general/users.png",
    "client": "aws/general/client.png",
    "mobile": "aws/general/mobile-client.png",
    "internet": "aws/general/internet-alt1.png",
    "onprem": "aws/general/office-building.png",
    "route53": "aws/network/route-53.png",
    "cloudfront": "aws/network/cloudfront.png",
    "cdn": "aws/network/cloudfront.png",
    "apigw": "aws/network/api-gateway.png",
    "apigateway": "aws/network/api-gateway.png",
    "alb": "aws/network/elb-application-load-balancer.png",
    "nlb": "aws/network/elb-network-load-balancer.png",
    "elb": "aws/network/elastic-load-balancing.png",
    "vpc": "aws/network/vpc.png",
    "igw": "aws/network/internet-gateway.png",
    "nat": "aws/network/nat-gateway.png",
    "privatelink": "aws/network/privatelink.png",
    "transitgateway": "aws/network/transit-gateway.png",
    "waf": "aws/security/waf.png",
    "shield": "aws/security/shield.png",
    "cognito": "aws/security/cognito.png",
    "iam": "aws/security/identity-and-access-management-iam.png",
    "kms": "aws/security/key-management-service.png",
    "secrets": "aws/security/secrets-manager.png",
    "ec2": "aws/compute/ec2.png",
    "ecs": "aws/compute/elastic-container-service.png",
    "eks": "aws/compute/elastic-kubernetes-service.png",
    "fargate": "aws/compute/fargate.png",
    "lambda": "aws/compute/lambda.png",
    "ecr": "aws/compute/elastic-container-registry.png",
    "batch": "aws/compute/batch.png",
    "rds": "aws/database/rds.png",
    "aurora": "aws/database/aurora.png",
    "dynamodb": "aws/database/dynamodb.png",
    "elasticache": "aws/database/elasticache.png",
    "redis": "aws/database/elasticache-for-redis.png",
    "redshift": "aws/database/redshift.png",
    "s3": "aws/storage/simple-storage-service-s3.png",
    "efs": "aws/storage/elastic-file-system-efs.png",
    "ebs": "aws/storage/elastic-block-store-ebs.png",
    "sqs": "aws/integration/simple-queue-service-sqs.png",
    "sns": "aws/integration/simple-notification-service-sns.png",
    "eventbridge": "aws/integration/eventbridge.png",
    "stepfunctions": "aws/integration/step-functions.png",
    "kinesis": "aws/analytics/kinesis.png",
    "athena": "aws/analytics/athena.png",
    "glue": "aws/analytics/glue.png",
    "cloudwatch": "aws/management/cloudwatch.png",
    "cloudformation": "aws/management/cloudformation.png",
}


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _all_icons():
    for dirpath, _, files in os.walk(os.path.join(ROOT, "aws")):
        for f in files:
            if f.endswith(".png"):
                yield os.path.join(dirpath, f)


def resolve(name):
    """Return an absolute icon path for `name`, or None.

    Order: explicit path -> alias -> fuzzy match on file names.
    """
    if not name:
        return None
    if os.path.isfile(name):
        return os.path.abspath(name)
    key = _norm(name)
    if key in ALIASES:
        return os.path.join(ROOT, ALIASES[key])
    tokens = [t for t in re.split(r"[\s_\-/]+", name.lower()) if t]
    hits = []
    for path in _all_icons():
        stem = os.path.basename(path)[:-4]
        if "rounded" in stem:
            continue
        if all(t in stem for t in tokens):
            hits.append(path)
    if hits:
        return min(hits, key=lambda p: len(os.path.basename(p)))
    return None


def search(query, limit=15):
    tokens = [t for t in re.split(r"[\s_\-/]+", query.lower()) if t]
    out = []
    for path in sorted(_all_icons()):
        stem = os.path.basename(path)[:-4]
        if "rounded" not in stem and all(t in stem for t in tokens):
            out.append(os.path.relpath(path, ROOT))
    return out[:limit]
