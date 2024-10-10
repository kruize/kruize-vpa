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


# This file holds constants used in recommender

# name of the custom recommender
RECOMMENDER_NAME = "kruize"
SLEEP_WINDOW=60
KRUIZE_URL="http://kruize-openshift-tuning.apps.kruize-lm.4zhx.p1.openshiftapps.com/"
LIST_EXPERIMENT_ENDPOINT=KRUIZE_URL + "listExperiments?experiment_name="
CREATE_EXPERIMENT_ENDPOINT=KRUIZE_URL + "createExperiment"
GENERATE_RECOMMENDATIONS_ENDPOINT=KRUIZE_URL + "generateRecommendations?experiment_name="

# vpa object related constants
DOMAIN = "autoscaling.k8s.io"
VPA_NAME = "verticalpodautoscaler"
VPA_PLURAL = "verticalpodautoscalers"
NAMESPACE = "namespace"
DEFAULT_NAMESPACE = "default"


# status related constants
VPA_CRD_FOUND = "VerticalPodAutoscaler CRD is present!"
SUCCESS="SUCCESS"

# error related constants
VPA_CRD_NOT_CREATED = "VerticalPodAutoscaler CRD is not created!"
ERROR="ERROR"


# api related
POST="post"
GET="get"