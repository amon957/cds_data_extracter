# Extract data from Copernicus Climate Data Store into a csv file
This program provides an interactive web application for extracting daily data from climate data store using cdsapi. It enables user to enter the following filtering parameters.
- Area extent
- Variable of interest
- Date range
- Aggregation type

## Methodology
- Specification of filtering parameters
- Hourly data for the entire day are extracted (24 hrs)
- 24 hour data downloaded is saved as netcdf format
- Perform aggregation as specified by the user (sum, maximum, minimum & average)
- Reading netcdf data into pandas dataframe
- Latitude & Longitude coordinates are then added into the dataframe

## Application Interface
![Application Interface](Application_Interface.PNG)


[Visit Application](https://amon957-cds-data-extracter-climate-data-extracter-xsmm00.streamlit.app/)

## Python Libraries Used
- streamlit : For web interface creation
- streamlit_folium : For rendering folium map in streamlit application
- folium : Creating and rendering map for easy identification of your area of interest
- datetime : For reading date range
- shapely : For Creating polygon for the extent
- geopandas : Assigning projection to the extent polygon created with shapely
- cdsapi : Application interface for communication with Climate Data Store, requesting data
- urllib : For reguesting and opening netcdf file link
- xarray : Reading and manipulating (Aggregation of data) netcdf file (Reading Multi-dimensional data from Climate Data Store)
- numpy : Holding multi-dimensional data from xarray as individual variables i.e latitude, longitude & variable of interest for easy extraction into a table form
- pandas : Organizing converted data into table form (Using dataframe) before exporting it into a csv file
