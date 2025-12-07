from prometheus_api_client import PrometheusConnect
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging

prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

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
    exit()

metric_data = data[0]['values']
df = pd.DataFrame(metric_data, columns=['ds', 'y'])

df['ds'] = pd.to_datetime(df['ds'], unit='s')
df['y'] = df['y'].astype(float)

m = Prophet(
    daily_seasonality=False, 
    weekly_seasonality=False, 
    yearly_seasonality=False,
    changepoint_prior_scale=0.5
)

m.add_seasonality(name='traffic_wave', period=300/86400, fourier_order=10)

m.fit(df)

future = m.make_future_dataframe(periods=20, freq='15s') 
forecast = m.predict(future)

print("Affichage du résultat...")
fig = m.plot(forecast)
plt.title("Prédiction Autoscaling (Points Noirs = Réel, Bleu = Futur)")
plt.xlabel("Temps")
plt.ylabel("Charge CPU")
plt.show()