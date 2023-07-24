# -*- coding: utf-8 -*-
"""
Created on Sat Nov 26 21:44:14 2022

@author: Amon Melly
"""
#
from streamlit_folium import folium_static
from shapely.geometry import Polygon
from urllib.request import urlopen
from datetime import date
import geopandas as gpd
import streamlit as st
import pandas as pd
import xarray as xr
import numpy as np
import folium
import cdsapi

#-----------------------PAGE LAYOUT SETUP--------------------------------------

st.set_page_config(page_title='Data Extracter', page_icon=None, layout="wide")
st.subheader('Daily Data Extraction From Copernicus Climate Data Store')
col1,col2=st.columns((1,2))

#-------------------MAP CREATOR FUNCTION---------------------------------------

def create_map_intance(center=[0,0],extent=None):
    Map=folium.Map(location=center, zoom_start=2)
    if extent==None:
        pass
    else:
        folium.GeoJson(data=extent,
                       style_function=lambda x: {'fillColor': 'orange'}).add_to(Map)
        Map.fit_bounds(Map.get_bounds())
    return Map

#--------------------------START OF BACKEND/DATA PROCESSING--------------------

def gen_dates(d_from,d_to):
    dates=pd.date_range(start=d_from,end=d_to)
    return(list(dates.strftime("%Y-%m-%d")))


def get_data(parameters):
    key=st.secrets["key"]
    c = cdsapi.Client("https://cds.climate.copernicus.eu/api/v2",key)
    params={
        "variable": parameters['variable'],
        "product_type": "reanalysis",
        "date": parameters['date'],
        "time": ["00:00","01:00","02:00","03:00","04:00","05:00",
                 "06:00","07:00","08:00","09:00","10:00","11:00",
                 "12:00","13:00","14:00","15:00","16:00","17:00",
                 "18:00","19:00","20:00","21:00","22:00","23:00"],
        "area":parameters['area'],
        "format": "netcdf"
        }
    data_request = c.retrieve("reanalysis-era5-single-levels",params)
    with urlopen(data_request.location) as f:
        ds = xr.open_dataset(f.read())
    return ds


def aggregation(data,aggr):
    if aggr=='Sum':
        aggregated_data=data.resample(time='1D').sum()
    elif aggr=='Maximum':
        aggregated_data=data.resample(time='1D').max()
    elif aggr=='Minimum':
        aggregated_data=data.resample(time='1D').min()
    elif aggr=='Average':
        aggregated_data=data.resample(time='1D').mean()
    return (aggregated_data)


def extract_to_dataframe(aggregated_data,variable_initial,days):
    
    longitudes=np.array(aggregated_data['longitude'])
    latitudes=np.array(aggregated_data['latitude'])
    
    v_data=np.array(aggregated_data[variable_initial])
    
    dict_data_values={}
    
    for i in range(len(v_data)):
        data_values=[]
        all_days=v_data[i]
        for j in range(len(all_days)):
            day=all_days[j,:]
            for k in day:
                data_values.append(round(k,2))
        dict_data_values[days[i]]=data_values
    lats=[]
    lons=[]

    for i in range(len(latitudes)):
        for j in range(len(longitudes)):
            lons.append(round(longitudes[j],4))
            lats.append(round(latitudes[i],4))
            
    dict_data_values['latitude']=lats
    dict_data_values['longitude']=lons
    
    return(pd.DataFrame(dict_data_values))


def create_extent_geo(n,s,e,w):
    if n==0 and s==0 and e==0 and w==0:
        return None
    else:
        coords=((w,n),(e,n),(e,s),(w,s),(w,n))
        geo=Polygon(coords)
        return(gpd.GeoSeries(geo,crs='epsg:4326'))


def data_processing_module(params):
    d_from=params['date_from']
    d_to=params['date_to']
    dates=gen_dates(d_from,d_to)
    params['date']=dates
    
    data=get_data(params)
    aggregated_data=aggregation(data,params['aggregation'])
    df=extract_to_dataframe(aggregated_data,params['short_name'],dates)
    return(df)


def convert_df(df):
    return df.to_csv().encode('utf-8')


def generate_variable_properties():
    data_table=pd.read_csv('data_table.csv')
    variables=list(data_table['Name'])
    description=list(data_table['Description'])
    cds_variable=list(data_table['CDS_Variable'])
    short_name=list(data_table['ShortName'])
    
    properties={}
    for i in range(len(variables)):
        properties[variables[i]]={'cds_name':cds_variable[i],'short_name':short_name[i],
                                  'description':description[i]}
    return (properties,variables)
        
#----------------------------END OF BACKEND------------------------------------


#-------------------------START OF FRONT END-----------------------------------



with col1:
    tab1,tab2,tab3=st.tabs(['Set Extent','Filter Parameters','Metadata'])
    with tab1:
        n=st.number_input('North')
        s=st.number_input('South')
        e=st.number_input('East')
        w=st.number_input('West')
        df_geo=create_extent_geo(n,s,e,w)
    with tab2:
        properties,variables=generate_variable_properties()
        
        variables.insert(0,'---Select---')
        variable=st.selectbox('Variable',variables)
        date_from=st.date_input('From',min_value=date(1959,1,1),max_value=date.today())
        date_to=st.date_input('To',min_value=date(1959,1,1),max_value=date.today())
        aggr=st.selectbox('Daily Aggregation Type',['---Select---','Sum','Minimum','Maximum',
                                              'Average'])
        df_geo=create_extent_geo(n,s,e,w)
        if st.button("Extract"):
            if date_from>date_to:
                st.error('Check Date Range')
            else:
                if aggr=='---Select---':
                    st.error('Error: Select Aggregation Type')
                else:
                    ns=n-s
                    ew=w-e
                    if ns<0:
                        ns=ns*-1
                    if ew<0:
                        ew=ew*-1
                    if ns<0.25:
                        st.error('Error: Extend < Spatial Resolution (0.25) in North South Direction')
                    elif ew<0.25:
                        st.error('Error: Extend < Spatial Resolution (0.25) in East West Direction')
                    else:
                        if variable=='---Select---':
                            st.error('Error: Select Variable')
                        else:
                            with st.spinner('Data Extraction in Progress...'):
                                df=data_processing_module({
                                    'area':str(n)+'/'+str(w)+'/'+str(s)+'/'+str(e),
                                    'date_from':date_from,
                                    'date_to':date_to,
                                    'aggregation':aggr,
                                    'variable':properties[variable]['cds_name'],
                                    'short_name':properties[variable]['short_name']
                                    })
                            st.success('Extraction Successful')
                            st.dataframe(df)
                            
                            csv = convert_df(df)

                            st.download_button(
                                label="Download data as CSV",
                                data=csv,
                                file_name=variable+'.csv',
                                mime='text/csv',
                            )
    with tab3:
        metadata={
            'Variable': variable,
            'Spatial Resolution': '0.25 * 0.25 Degrees',
            'Projection': 'Latitude-Longitude',
            'Horizontal Coverage':'{} North, {} South, {} East, {} West'
            .format(n,s,e,w),
            'Temporal Resolution': 'Dailly',
            'Temporal Coverage':'From {} to {}'.format(date_from,date_to),
            'Aggregation':aggr,
            'Data Type':'Gridded',
            'File Format':'csv'
            }
        st.json(metadata)
        attr={'Attribute':list(metadata.keys()),'Value':list(metadata.values())}
        md=pd.DataFrame(attr,index=[1,2,3,4,5,6,7,8,9])
        st.download_button(label='Save to file',
                           data=md.to_csv(),
                           file_name='metadata.csv',
                           mime='text/csv',
                           )

with col2:
    try:
        geo_j = df_geo.to_json()
        Map=create_map_intance([df_geo.centroid.y,df_geo.centroid.x],geo_j)
    except AttributeError:
        Map=create_map_intance()
    folium_static(Map)
    try:
        if variable=='---Select---':
            pass
        else:
            st.subheader('DESCRIPTION')
            st.markdown(properties[variable]['description'])
    except AttributeError:
        pass
    
#----------------------------END OF FRONT END----------------------------------
