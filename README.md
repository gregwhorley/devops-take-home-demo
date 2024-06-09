# devops-take-home-demo
Artifacts from devops take home assignment

## Summary
This project contains a combination of IaC, deployment, and app code to deploy and manage a simple http server and S3 bucket.
Specifics are detailed below.

## Prerequisites
* An AWS account with valid authc/authz
* Python 3 with pip
* Docker engine latest
* Terraform 1.x latest
* Terragrunt
* Skaffold 2.x latest
* Minikube latest
* Helm 3.x latest

## Terraform
An S3 bucket is configured with a bucket policy that only allows traffic over Secure Transport. AWS provides SSE with S3
managed key by default.

### Reasoning
I chose to use a remote S3 backend with DynamoDB locking for Terraform state management to keep the state centrally located
and to prevent consistency issues. The Terraform code for the S3 bucket is located under the `tf/modules/s3` directory to
keep it DRY. A note about the S3 bucket definition: the assignment required S3 encryption, but did not specify how the
encryption is configured. AWS enables SSE by default, so all S3 bucket objects are encrypted with the S3 managed keys. I
originally set up KMS managed encryption for bucket objects in a SSE config, but backed out of it since I thought it might
be overkill. I chose Terragrunt because it is a convenient tool that allows users to keep their Terraform code, backend
config, and variable inputs DRY, but also provides several other nifty features that I didn't use here.

### Managing Terraform state
This project has configured the backend such that remote state is stored in S3 with state locking via DynamoDB. A companion
Python CLI tool `tf_state_mgr.py` is provided that creates a state bucket and a DynamoDB table with the same name.
Run `python tf_state_mgr.py -h` to get a list of options.

#### Example
`python tf_state_mgr.py --profile aws-profile-name --name my-tf-state-identifier`

### Terraform operations
This project uses Terragrunt to manage the IaC. All operations will be performed through the `terragrunt` binary. All the
code is stored in the `tf` directory and contains:
* Main `terragrunt.hcl` configuration with AWS provider and S3 backend configuration
* A single Terraform module with the S3 bucket definition
* A `dev` working directory that contains a Terragrunt config that sources the S3 module and provides inputs

It is assumed that an AWS profile with valid credentials is set up in your environment prior to running Terragrunt. The
commands below include the `AWS_PROFILE` environment variable on the command line, but you can export it instead, so it
can be omitted from the commands.

Use `terragrunt run-all` for all Terraform commands. This project only contains one environment in the "stack", so using
the `--terragrunt-working-dir` flag is not necessary in this case. However, the following examples include the flag with
the assumption that additional environments will be added to the stack.

Run `terragrunt run-all plan --terragrunt-working-dir dev` to initialize and output a plan with the S3 bucket definition.
Run `terragrunt run-all apply --terragrunt-working-dir dev` to apply the S3 IaC

## Docker
This project uses Skaffold to manage build operations of the simple Flask app `hello_evolve.py`. A `Dockerfile`
contains the build directives for the app. Skaffold is configured to use Kaniko as the builder in a local Minikube cluster.

### Reasoning
I chose to use Skaffold for managing building and deployment operations because it keeps all the configuration in one place,
has support for a variety of build and deploy tools, and has a debugging feature--`skaffold dev`--that has been proven to be
very helpful for local development. I chose Kaniko as the builder because it does not require a Docker daemon and can operate
securely within a Kubernetes cluster, given that RBAC and security context are set up. I am using Minikube simply because
it was the quickest, easiest way to get a k8s cluster off the ground, but this should not be used in production capacity.

### Setup
The setup is barebones, requiring a `kaniko` namespace that contains an Opaque k8s secret named `docker-config-secret`.
The secret requires one data entry that is keyed on `config.json` whose value is a base64 encoded Docker config that looks
like the following:
```json
{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "BASE64-ENCODED-CREDENTIALS"
    }
  }
}
```
The credentials hash can be created by running `echo USERNAME:PASSWORD | base64`.

Also, I used my personal Docker account for both authentication and image storage to a remote registry so that I could test
this before turning the assignment in. **NOTE**: Change the image name on line 12 of `skaffold.yaml` to a remote registry
URL that you have access to if you are testing this yourself.

### Build operation
Once you have Minikube running and the k8s resources mentioned above applied to the local cluster, simply run `skaffold build`
to spin up a kaniko executor pod that builds and pushes the image.

## Helm
This project uses Skaffold to manage deployment operations of the Docker image artifact for the simple Flask app `hello_evolve.py`.
A Helm release is defined within the Skaffold config that sets value overrides for the deployment resource's image repo
and tag via templating support.

### Reasoning
I chose to use Skaffold for managing deployment operations for the same reasons mentioned in the Docker section above. I
was able to test a deployment of the Flask app using `skaffold dev`, which incidentally exposed a bug in Minikube's Kong
ingress controller addon that I created an issue about: https://github.com/kubernetes/minikube/issues/19043 . I chose Kong
ingress controller because it is one of the few ingress controllers that has API Gateway support in General Availability.
While I did not include a `HTTPRoute` resource for the Flask app, at least the stage is set to do so at a later time. I set
a replica set in the Deployment so two copies of the app are running, but it would be better to deploy an auto-scaling
solution and enable the HPA resource. I enabled a security context for the Deployment but adding enforcement of Pod Security
Standards would also be advised if this is run in production.

### Setup
The setup for this was solely within the scope of Minikube. I installed the Kong addon for ingress support, the metrics-server
addon for k8s metrics collection, and the dashboard addon for a GUI view of the cluster.

### Deploy operation
If you followed this readme from beginning to end, you likely already have all of the prerequisites installed and Minikube
running. By this point, you could either run `skaffold dev` or `skaffold run` to build the image for the Flask app and deploy
it to the local cluster.

If you are testing this out, make sure to add the cluster role permission I mentioned in the github issue above so that Kong
ingress controller will run. Run `minikube tunnel` and provide a password so that traffic from the ingress controller and
resources will be exposed, then run `curl -i localhost -H "Host: evolve-app.hello"` to make a request to the Flask app.
