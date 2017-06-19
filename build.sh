#!/bin/bash

# Copyright 2017 Google Inc. All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

local=0 # Should run using local Docker daemon instead of GCR?

# Note that $gcloud_cmd has spaces in it
gcloud_cmd="gcloud beta container builds submit ."
local_gcloud_cmd="../python-runtime/scripts/local_cloudbuild.py"

# Helper functions
function fatal() {
  echo "$1" >&2
  exit 1
}

function usage {
  fatal "Usage: $0 [OPTION]...
Build and test artifacts in this repository

Options:
  --local: Build images using local Docker daemon
"
}
  
# Read environment variables
if [ -z "${DOCKER_NAMESPACE+set}" ] ; then
  fatal 'Error: $DOCKER_NAMESPACE is not set; invoke with something like DOCKER_NAMESPACE=gcr.io/YOUR-PROJECT-NAME'
fi

if [ -z "${TAG+set}" ] ; then
  export TAG=`date +%Y-%m-%d-%H%M%S`
fi

substitutions="_DOCKER_NAMESPACE=${DOCKER_NAMESPACE},_TAG=${TAG}"

# Read command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --local)
      local=1
      shift
      ;;
    *)
      usage
      ;;
  esac
done

# Running build local or remote?
if [ "${local}" -eq 1 ]; then 
  gcloud_cmd="${local_gcloud_cmd}"
fi

# Build images and push to GCR
echo "Building images"
${gcloud_cmd} --config cloudbuild.yaml --substitutions "${substitutions}"
