# Diagram spec

```json
{
  "title": "Web app on AWS",
  "direction": "LR",
  "nodes": [
    {"id": "alb", "label": "Application\nLoad Balancer", "icon": "alb"},
    {"id": "api", "label": "ECS Fargate\nAPI", "icon": "fargate"}
  ],
  "groups": [
    {"id": "vpc", "label": "VPC", "members": ["alb", "api"]}
  ],
  "edges": [
    {"from": "alb", "to": "api", "label": "HTTP", "step": 1}
  ]
}
```

## Fields

| Field | Required | Notes |
|---|---|---|
| `title` | no | Shown above the diagram |
| `direction` | no | `LR` (default) or `TB` |
| `nodes[].id` | yes | Unique, no spaces |
| `nodes[].label` | yes | Short; `\n` for a second line |
| `nodes[].icon` | no | Alias (`alb`, `rds`, `s3`), a search phrase (`elastic container`), or a PNG path. No icon gives a plain rounded box |
| `nodes[].type` | no | Box colour when there is no icon: `client`, `network`, `compute`, `data`, `security` |
| `groups[]` | no | `id`, `label`, `members` (node ids). One group per node |
| `edges[].from`, `to` | yes | Node ids; arrow points from to `to` |
| `edges[].label` | no | Protocol or action |
| `edges[].step` | no | Integer from 1. Same step means animated together. Defaults to the edge's position in the list |

## Common aliases

user, users, client, mobile, internet, onprem, route53, cloudfront, apigateway,
alb, nlb, elb, vpc, igw, nat, waf, shield, cognito, iam, kms, secrets, ec2, ecs,
eks, fargate, lambda, ecr, batch, rds, aurora, dynamodb, elasticache, redis,
redshift, s3, efs, ebs, sqs, sns, eventbridge, stepfunctions, kinesis, athena,
glue, cloudwatch, cloudformation.

For anything else: `python scripts/list_icons.py <keyword>`.

## Step numbering patterns

- Request path: number along the path, 1, 2, 3 and so on.
- Fan-out: give parallel edges the same step.
- Async work: continue numbering after the synchronous path ends.
- Response path: either skip it (implied) or add it as later steps.
