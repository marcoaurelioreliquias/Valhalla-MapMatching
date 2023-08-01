import pandas as pd
import geopandas as gpd
import json
import requests
from shapely.geometry.linestring import LineString
from decode_functions import decode
from arcgis.features import GeoAccessor, GeoSeriesAccessor

# Função para verificar a existência da chave 'shape' em uma ramificação do JSON
def check_shape(json_data, lista_saida):            
    if isinstance(json_data, dict):
        if 'shape' in json_data:
            lista_saida.append(decode(json_data['shape']))
            print("Chave 'shape' encontrada!")
        else:
            for value in json_data.values():
                check_shape(value, lista_saida)
    elif isinstance(json_data, list):
        for item in json_data:
            check_shape(item, lista_saida)

# for i in range(1,8):
i = 7
print(f"rodando rota {i}")
in_track     = fr"D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados_Apresentacao\Dados_Apresentacao.gdb\Track{i}\track_{i}"
fc_saida     = fr'D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados_Apresentacao\Dados_Apresentacao.gdb\teste_{i}'

track = gpd.GeoDataFrame.spatial.from_featureclass(in_track)
track_gdf = gpd.GeoDataFrame(track, crs=29192, geometry=track['SHAPE'])
track_gdf.to_crs(4326, inplace=True)

track_gdf['longitude'] = track_gdf.geometry.x
track_gdf['latitude'] = track_gdf.geometry.y

track_gdf['rta_data'] = pd.to_datetime(track_gdf['rta_data'])
track_gdf = track_gdf.sort_values(by=['rta_data'])

df_trip_for_meili = track_gdf[['longitude', 'latitude', 'rta_data']].copy()
df_trip_for_meili.columns = ['lon', 'lat', 'rta_data']

meili_coordinates = df_trip_for_meili.to_json(orient='records')
meili_head = '{"shape":'
meili_tail = ""","search_radius": 150, "shape_match":"map_snap", "costing":"auto", "format":"json"}"""
meili_request_body = meili_head + meili_coordinates + meili_tail

url = "http://localhost:8002/trace_route"
headers = {'Content-type': 'application/json'}
data = str(meili_request_body)

r = requests.post(url, data=data, headers=headers)
lista_trechos = []
saida = []
if r.status_code == 200:
    response_text = json.loads(r.text)
    check_shape(response_text, lista_trechos)
    for item in lista_trechos:
    #     check_shape()
        saida.extend(item)
    
    lst_MapMatchingRoute = LineString(saida)
    gdf_MapMatchingRoute_linestring = gpd.GeoDataFrame(geometry=[lst_MapMatchingRoute], crs=4326)
    routes = GeoAccessor.from_geodataframe(geo_df=gdf_MapMatchingRoute_linestring)
    routes.spatial.to_featureclass(location=fc_saida, overwrite=True, 
                                has_z=False, has_m=False, sanitize_columns=True)

