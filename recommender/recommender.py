import os
import json

from kubernetes import client, config

from utils.recommenderUtils import get_response, resource2str, get_endpoint
import utils.recommenderConstants as recommenderConstants

# This function fetches latest recommendations from Kruize for a given VPA
def get_recommendations(vpa, containers):
    print("Generating recommendations - ")
    recommendations_for_vpa = []

    # Check if Kruize experiment exists with vpa name
    experiment_name = vpa['metadata']['name'].strip()
    # Calling listExperiment endpoint to check if experiment with vpa name exist or not
    print(get_endpoint(recommenderConstants.LIST_EXPERIMENT_ENDPOINT) + experiment_name)
    response = get_response("", get_endpoint(recommenderConstants.LIST_EXPERIMENT_ENDPOINT) + experiment_name, recommenderConstants.GET)

    if response.ok:
        # Experiment for VPA exists.
        print("Experiment for VPA exists.")

        # Calling generateRecommendations endpoint to get latest recommendations from Kruize
        print(get_endpoint(recommenderConstants.GENERATE_RECOMMENDATIONS_ENDPOINT) + experiment_name)
        response = get_response("", get_endpoint(recommenderConstants.GENERATE_RECOMMENDATIONS_ENDPOINT) + experiment_name, recommenderConstants.POST)

        if response.ok:
            print("Fetched latest recommendations.")
            recommendations = response.json()

            # Checking container policies to know which container to update
            container_recommendations = recommendations[0]['kubernetes_objects'][0]['containers']
            container_policy = vpa['spec']['resourcePolicy']['containerPolicies'][0]
            selected_containers_vpa = []

            if container_policy['containerName'] == '*':
                # Use all fetched containers
                selected_containers_vpa = containers
            else:
                # Filter for specific container if defined
                for c in containers:
                    if c['container_name'] == container_policy['containerName']:
                        selected_containers_vpa.append(c)


            print("Selected containers to update - ")
            print(selected_containers_vpa)

            # Get recommendations for each container
            for c in selected_containers_vpa:
                # Fetch Recommendations for specified container from API response
                for cr in container_recommendations:
                    if cr['container_name'] == c['container_name']:
                        # Check if recommendations are present and data is not empty
                        if cr['recommendations']['data']:
                            for timestamp, content in cr['recommendations']['data'].items():
                                # Get short term cost profile recommendations
                                short_term_cpu = content["recommendation_terms"]["short_term"]["recommendation_engines"]["cost"]["config"]["requests"]["cpu"]["amount"]
                                short_term_memory = float(content["recommendation_terms"]["short_term"]["recommendation_engines"]["cost"]["config"]["requests"]["memory"]["amount"])

                                print("CPU Recommendations: " + str(short_term_cpu))
                                print("Memory Recommendations: " + str(short_term_memory))

                                # Convert recommendations to desired format
                                short_term_cpu_conv = resource2str("cpu", short_term_cpu)
                                short_term_memory_conv = resource2str("memory", int(short_term_memory))

                                # Generate recommendations object
                                recomObject = {
                                    "containerName": c['container_name'],
                                    "lowerBound": {"cpu": short_term_cpu_conv, "memory": short_term_memory_conv},
                                    "target": {"cpu": short_term_cpu_conv, "memory": short_term_memory_conv},
                                    "upperBound": {"cpu": short_term_cpu_conv, "memory": short_term_memory_conv}
                                }
                                recommendations_for_vpa.append(recomObject)
                        else:
                            print("Recommendation data is not available. Please wait sometime.")
        else:
            print("Generate Recommendations Failed. Will retry again.")
            print(response.json())

    else:
        print("Experiment not registered with kruize. Please register experiment with name - {}.".format(experiment_name))
        print("Experiment not found. Creating New Experiment - {}".format(experiment_name))
        generate_create_exp_from_vpa(vpa, containers)

    return recommendations_for_vpa


# This function generates json and creates experiment for Kruize for a given VPA
def generate_create_exp_from_vpa(vpa, containers):
    vpa_name = vpa['metadata']['name'].strip()
    namespace = vpa['metadata'].get('namespace', 'default').strip()
    target_deployment = vpa['spec']['targetRef']['name'].strip()
    container_policy = vpa['spec']['resourcePolicy']['containerPolicies'][0]

    selected_containers = []

    if container_policy['containerName'] == '*':
        # Use all fetched containers
        selected_containers = containers
    else:
        # Filter for specific container if defined
        selected_containers = []
        for c in containers:
            if c['container_name'] == container_policy['containerName']:
                selected_containers.append(c)

    # default json format
    json_output = '''[{
        "version": "v2.0",
        "experiment_name": "experiment_name",
        "cluster_name": "default",
        "performance_profile": "resource-optimization-local-monitoring",
        "mode": "monitor",
        "target_cluster": "local",
        "kubernetes_objects": [{
            "type": "deployment",
            "name": "name",
            "namespace": "namespace",
            "containers": []
        }],
        "trial_settings": {
            "measurement_duration": "15min"
        },
        "recommendation_settings": {
            "threshold": "0.1"
        },
        "datasource": "prometheus-1"
    }]'''

    data = json.loads(json_output)
    # Update the fields
    data[0]['experiment_name'] = vpa_name
    data[0]['kubernetes_objects'][0]['name'] = target_deployment
    data[0]['kubernetes_objects'][0]['namespace'] = namespace
    data[0]['kubernetes_objects'][0]['containers'] = selected_containers

    modified_json = json.dumps(data, indent=4)

    # Creating an experiment on Kruize
    print(get_endpoint(recommenderConstants.CREATE_EXPERIMENT_ENDPOINT))
    res = get_response(modified_json, get_endpoint(recommenderConstants.CREATE_EXPERIMENT_ENDPOINT), recommenderConstants.POST)
    if res.ok:
        print("Experiment registered!")
    else:
        print("Failed to register experiment!")
