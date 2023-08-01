#%% IMPORT LIBRARIES
import pandas as pd
import geopandas as gpd
import json
import requests
from shapely.geometry.linestring import LineString
from pyproj import Geod
from decode_functions import decode
from arcgis.features import GeoAccessor, GeoSeriesAccessor

#%% READ & FORMAT GPS INFO
in_route     = r"D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados Rota\Projeto_Roteirizacao\Projeto_Roteirizacao.gdb\rota_2443_030822_RotaASE"
in_track     = r"D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados_Apresentacao\Dados_Apresentacao.gdb\Track1\track_1"

road = gpd.GeoDataFrame.spatial.from_featureclass(in_route)
road_gdf = gpd.GeoDataFrame(road, crs=29192, geometry=road['SHAPE'])
road_gdf.to_crs(4326, inplace=True)

track = gpd.GeoDataFrame.spatial.from_featureclass(in_track)
track_gdf = gpd.GeoDataFrame(track, crs=29192, geometry=track['SHAPE'])
track_gdf.to_crs(4326, inplace=True)

road_gdf = road_gdf.explode(index_parts=False)
gdf_rawGPS_points_temp = road_gdf.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
gdf_rawGPS_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy([a_tuple[0] for a_tuple in gdf_rawGPS_points_temp[0]], [a_tuple[1] for a_tuple in gdf_rawGPS_points_temp[0]]), crs=4326)
df_rawGPS_points = pd.DataFrame(list(zip([a_tuple[0] for a_tuple in gdf_rawGPS_points_temp[0]],[a_tuple[1] for a_tuple in gdf_rawGPS_points_temp[0]])) , columns=['lon', 'lat'])
gdf_rawGPS = gpd.GeoDataFrame(pd.concat([road_gdf, df_rawGPS_points], ignore_index=True))



#%% VALHALLA REQUEST
meili_coordinates = df_rawGPS_points.to_json(orient='records')
meili_head = '{"shape":'
meili_tail = ', "search_radius": 300, "shape_match":"map_snap", "costing":"auto", "format":"osrm"}'
meili_request_body = meili_head + meili_coordinates + meili_tail
url = "http://localhost:8002/trace_route"
headers = {'Content-type': 'application/json'}
data = str(meili_request_body)
r = requests.post(url, data=data, headers=headers)

#%% READ & FORMAT VALHALLA RESPONSE
if r.status_code == 200:
    response_text = json.loads(r.text)
search_1 = response_text.get('matchings')
search_2 = dict(search_1[0])
polyline6 = search_2.get('geometry')
search_3 = response_text.get('tracepoints')

lst_MapMatchingRoute = LineString(decode(polyline6))
gdf_MapMatchingRoute_linestring = gpd.GeoDataFrame(geometry=[lst_MapMatchingRoute], crs=4326)
gdf_MapMatchingRoute_points_temp = gdf_MapMatchingRoute_linestring.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
gdf_MapMatchingRoute_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy([a_tuple[0] for a_tuple in gdf_MapMatchingRoute_points_temp[0]], [a_tuple[1] for a_tuple in gdf_MapMatchingRoute_points_temp[0]]), crs=4326)
gdf_MapMatchingRoute = gpd.GeoDataFrame(pd.concat([gdf_MapMatchingRoute_linestring, gdf_MapMatchingRoute_points], ignore_index=True))
df_mapmatchedGPS_points = pd.DataFrame(list([d['location'] for d in search_3 if d and 'location' in d]) , columns=['lon', 'lat'])
gdf_mapmatchedGPS_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df_mapmatchedGPS_points['lon'], df_mapmatchedGPS_points['lat']), crs=4326)



# %%
routes = GeoAccessor.from_geodataframe(geo_df=gdf_MapMatchingRoute_linestring)
routes.spatial.to_featureclass(location=r'D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados_Apresentacao\Dados_Apresentacao.gdb\rota_3_teste',overwrite=True,has_z=False,has_m=False,sanitize_columns=True)

tracks = GeoAccessor.from_geodataframe(geo_df=gdf_mapmatchedGPS_points)
tracks.spatial.to_featureclass(location=r'D:\Trabalho\Zukk\Imagem\SANEPAR\SCRIPTS\Sanepar_Roterizacao\Dados_Apresentacao\Dados_Apresentacao.gdb\track_3_teste',overwrite=True,has_z=False,has_m=False,sanitize_columns=True)
# %%
