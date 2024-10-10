# *******************************************************************************
# Copyright (c) 2024 Red Hat, IBM Corporation and others.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#  *******************************************************************************/
from http.client import responses

import requests
import utils.recommenderConstants as recommenderConstants

# This file holds various utility functions used in recommender

# Select the VPAs that choose the current recommender as Kruize
def selects_vpas_for_current_recommender(vpas, recommender_name):
    selected_vpas = []
    for vpa in vpas["items"]:
        vpa_spec = vpa["spec"]
        if "recommenders" not in vpa_spec.keys():
            continue
        else:
            for recommender in vpa_spec["recommenders"]:
                if recommender["name"] == recommender_name:
                    selected_vpas.append(vpa)
                    print("VPA {} has chosen {} recommender.".format(vpa["metadata"]["name"], recommenderConstants.RECOMMENDER_NAME))

    return selected_vpas


# This function calls the APIs
def get_response(json_data, api_url, api_method):
    headers = {'Content-Type': 'application/json'}
    response = None

    if api_method == recommenderConstants.POST:
        response = requests.post(api_url, data=json_data, headers=headers)
    if api_method == recommenderConstants.GET:
        response = requests.get(api_url, data=json_data, headers=headers)

    return response


# This function returns list of all containers in deployment
def get_containers_in_deployment(deployment_name, namespace, apps_v1_client):
    # Fetch the deployment
    deployment = apps_v1_client.read_namespaced_deployment(deployment_name, namespace)

    # Extract container names and images
    containers = []
    for container in deployment.spec.template.spec.containers:
        containers.append({
            'container_image_name': container.image,
            'container_name': container.name
        })
    return containers


# resource2str converts a resource (CPU, Memory) value to a string
def resource2str(resource, value):
    if resource.lower() == "cpu":
        if value < 1:
            return str(int(value * 1000)) + "m"
        else:
            return str(value)
    # Memory is in bytes
    else:
        if value < 1024:
            return str(value) + "B"
        elif value < 1024 * 1024:
            return str(int(value / 1024)) + "k"
        elif value < 1024 * 1024 * 1024:
            return str(int(value / 1024 / 1024)) + "Mi"
        else:
            return str(int(value / 1024 / 1024 / 1024)) + "Gi"