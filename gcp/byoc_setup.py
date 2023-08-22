#!/bin/env python

import argparse
import json
import subprocess
import yaml


def run_cmd(cmd: str) -> str:
    return subprocess.check_output(cmd.split()).decode().strip()


def set_project(args):
    run_cmd(f"gcloud config set project {args.project}")


def grant_dm_permissions():
    project_name = run_cmd("gcloud config get project")
    project_number = run_cmd(f"gcloud projects list --filter {project_name} --format value(PROJECT_NUMBER)")
    run_cmd(f"gcloud projects add-iam-policy-binding {project_name} --member serviceAccount:{project_number}@cloudservices.gserviceaccount.com --role roles/owner")


def create_deployment(args):
    run_cmd(f"gcloud deployment-manager deployments create {args.name} "
            "--template deployment.py "
            f"--properties region:'{args.region}',cidr:'{args.cidr}',name:'{args.name}'"
            )


def get_output(args) -> dict:
    manifest_name = json.loads(run_cmd(f"gcloud deployment-manager deployments describe {args.name} --format json"))['deployment']['manifest'].split('/')[-1]
    manifest = run_cmd(f"gcloud deployment-manager manifests describe --deployment {args.name} {manifest_name} --format json")
    return {
        x["name"]: x["finalValue"]
        for x in yaml.load(json.loads(manifest)["layout"], yaml.SafeLoader)["resources"][0]["outputs"]
    }


def delete(args):
    run_cmd(f"gcloud deployment-manager deployments delete {args.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', help="GCP Project ID")
    parser.add_argument('-n', '--name', help="Name of BYOC installation")
    parser.add_argument('-r', '--region', help="GCP region")
    parser.add_argument('-c', '--cidr', help="IPv4 CIDR", default="10.0.0.0/16")
    parser.add_argument('-o', '--output-only', action='store_true', help="Get the output from previously created resources", dest='output')
    parser.add_argument('-d', '--delete', action='store_true', help="Delete previously created resources")
    args = parser.parse_args()

    set_project(args)

    if args.delete:
        delete(args)
        return

    if not args.output:
        grant_dm_permissions()
        create_deployment(args)

    print(json.dumps(get_output(args)))


if __name__ == '__main__':
    main()
