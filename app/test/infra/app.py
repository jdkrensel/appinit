import aws_cdk as cdk
# from aws_cdk import Environment
# from stacks.service_stack import ServiceStack
# from config import load_config

app = cdk.App()

# staging_cfg = load_config("staging")
# ServiceStack(
#     app,
#     "staging",
#     config=staging_cfg,
#     env=Environment(
#         account=staging_cfg["account"],
#         region=staging_cfg["region"]
#     ),
# )

# prod_cfg = load_config("prod")
# ServiceStack(
#     app,
#     "prod",
#     config=prod_cfg,
#     env=Environment(
#         account=prod_cfg["account"],
#         region=prod_cfg["region"]
#     ),
# )

app.synth()
