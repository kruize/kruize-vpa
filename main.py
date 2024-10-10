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

import os
import sys
import time
from kubernetes import config, client
from kubernetes.client import ApiException

import utils.recommenderConstants as recommenderConstants
import utils.recommenderUtils as recommenderUtils
from recommender.recommender import get_recommendations


# Loads Kubernetes configuration
def load_kubernetes_config():
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()


def start_recommender():
    # Load kubernetes configuration
    load_kubernetes_config()

    # Get the api instance and custom resources to interact with the cluster
    api_client = client.api_client.ApiClient()
    v1 = client.ApiextensionsV1Api(api_client)
    corev1 = client.CoreV1Api(api_client)
    crds = client.CustomObjectsApi(api_client)
    apps_v1 = client.AppsV1Api(api_client)

    # Check for VerticalPodAutoscaler CRD presence
    current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
    if recommenderConstants.VPA_NAME not in current_crds:
        print(recommenderConstants.VPA_CRD_NOT_CREATED)
        exit(-1)
    else:
        print(recommenderConstants.VPA_CRD_FOUND)

    # Continuously check for recommendations and update VPA managed by Kruize vpa
    while True:
        # Fetch VPAs managed by the Kruize recommender
        vpas = crds.list_cluster_custom_object(group=recommenderConstants.DOMAIN,
                                               version="v1",
                                               plural=recommenderConstants.VPA_PLURAL)

        selected_vpas = recommenderUtils.selects_vpas_for_current_recommender(vpas, recommenderConstants.RECOMMENDER_NAME)

        for vpa in selected_vpas:
            vpa_name = vpa["metadata"]["name"]
            vpa_namespace = vpa["metadata"]["namespace"]
            target_deployment = vpa['spec']['targetRef']['name']

            print("Selected VPA {} in namespace {} and deployment {}.".format(vpa_name, vpa_namespace, target_deployment))

            # Getting all the containers in current deployment
            containers_in_deployment = recommenderUtils.get_containers_in_deployment(target_deployment, vpa_namespace, apps_v1)

            # Generating recommendations
            recom = get_recommendations(vpa, containers_in_deployment)
            if recom is None:
                print("No Recommendations found. Skipping to update VPA.")
            else:
                print(recom)
                print("Patching vpa object with available recommendations.")

                # Prepare the body to patch the VPA object
                patched_vpa = {
                    "status": {
                        "recommendation": {
                            "containerRecommendations": recom
                        }
                    }
                }

                # Update the VPA object
                try:
                    vpa_updated = crds.patch_namespaced_custom_object_status(
                        group=recommenderConstants.DOMAIN,
                        version="v1",
                        plural=recommenderConstants.VPA_PLURAL,
                        namespace=vpa_namespace,
                        name=vpa_name,
                        body=patched_vpa
                    )
                    print("VPA has been patched to apply recommendations.")
                except ApiException as e:
                    print(f"Exception when updating VPA '{vpa_name}': {e}")


            print("Sleeping for {} seconds ...".format(recommenderConstants.SLEEP_WINDOW))
            print("\n******************************************************************\n")
            sys.stdout.flush()
            time.sleep(recommenderConstants.SLEEP_WINDOW)


# Starting the Kruize vpa recommender
start_recommender()