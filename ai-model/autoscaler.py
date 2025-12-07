import time
import math
import logging
from datetime import datetime, timedelta
import pandas as pd
from prophet import Prophet
from prometheus_api_client import PrometheusConnect
from kubernetes import client, config

DEPLOYMENT_NAME = "fake-app"
NAMESPACE = "default"
TARGET_CPU_PER_POD = 0.05
MIN_REPLICAS = 1
MAX_REPLICAS = 10
PROMETHEUS_URL = "http://localhost:9090"

try:
    config.load_kube_config()
    k8s_apps = client.AppsV1Api()
    
    prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
except Exception as e:
    exit()

def get_predicted_load():
    duration = 30
    start_time = datetime.now() - timedelta(minutes=duration)
    end_time = datetime.now()
    
    query = 'sum(rate(container_cpu_usage_seconds_total{pod=~"fake-app.*", container!="POD"}[1m]))'
    
    data = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step="15s"
    )
    
    if not data:
        return None

    metric_data = data[0]['values']
    df = pd.DataFrame(metric_data, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'], unit='s')
    df['y'] = df['y'].astype(float)
    
    m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False, changepoint_prior_scale=0.5)
    m.add_seasonality(name='traffic_wave', period=300/86400, fourier_order=10)
    m.fit(df)
    
    future = m.make_future_dataframe(periods=4, freq='15s')
    forecast = m.predict(future)
    
    future_load = forecast.tail(4)['yhat'].max()
    return max(0, future_load)

def scale_deployment(replicas):
    """Envoie l'ordre à Kubernetes"""
    current_deployment = k8s_apps.read_namespaced_deployment_scale(DEPLOYMENT_NAME, NAMESPACE)
    current_replicas = current_deployment.spec.replicas
    
    if current_replicas == replicas:
        print(f"zzz Rien à faire. Replicas actuels ({current_replicas}) suffisants.")
        return

    print(f"ACTION : Scaling de {current_replicas} -> {replicas} replicas.")
    
    body = {"spec": {"replicas": replicas}}
    k8s_apps.patch_namespaced_deployment_scale(DEPLOYMENT_NAME, NAMESPACE, body)


while True:
    start_loop = time.time()
    
    predicted_cpu = get_predicted_load()
    
    if predicted_cpu is not None:
        required_replicas = math.ceil(predicted_cpu / TARGET_CPU_PER_POD)
        
        required_replicas = max(MIN_REPLICAS, min(required_replicas, MAX_REPLICAS))
        
        print(f"Charge Prévue: {predicted_cpu:.3f} CPU | Replicas Requis: {required_replicas}")
        
        scale_deployment(required_replicas)
    else:
        print("Pas de données. En attente...")

    time.sleep(15)