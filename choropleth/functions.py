import fiona
from mpl_toolkits.basemap import Basemap   
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPoint, MultiPolygon
from shapely.prepared import prep
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from descartes import PolygonPatch
import os
import Levenshtein

def createStateShp(india_shp, state) :
    '''
    Creates district level shape file of given state from india_shp (with district boundaries)
    '''
    with fiona.open(india_shp) as input:
        # The output has the same schema
        output_schema = input.schema.copy()
        # write a new shapefile
        with fiona.open('maps\\' + state , 'w', 'ESRI Shapefile', output_schema, crs=input.crs) as output:
            #Select the required state using a filter
            selection = filter(lambda f: f['properties']['ST_NM']==state, input)
            for elem in selection: 
                 output.write(elem)
                 # or output.write({'properties': elem['properties'],'geometry': elem['geometry']})

def createMap(name) :
    '''
    Creates the basemap object for given input.
    Works only for india, maharashtra

    name : india/state name as string
           eg. 'india', 'maharashtra'
    '''
    d = os.path.dirname(os.getcwd())

    if name == 'india' :
        shp_file = d + '\\maps\\india\\india.shp'
    elif name == 'maharashtra' :
        shp_file = d + '\\maps\\maharashtra\\maharashtra.shp'
    else :
        print('Name not supported as of yet')
        return(None)
    shp = fiona.open(shp_file) # Shapefile
    coords = shp.bounds         # Extract the bound coordinates from the shapefile
    shp.close()

    fig, ax = plt.subplots(figsize=(10,10))  # figure and axis objects
    
    #Adjustments made to co-ordinates as the map is going out of bounds
    if name == 'india' :
        m = Basemap(
            projection='tmerc', ellps='WGS84', # set transverse mercator proj. and ellipsoid
            lon_0=(coords[0] + coords[2]) / 2, # longitude center
            lat_0=(coords[1] + coords[3]) / 2, # latitude center 
            llcrnrlon=coords[0],    # left lower corner 
            llcrnrlat=coords[1] - 1,
            urcrnrlon=coords[2] + 3,    # upper right corner 
            urcrnrlat=coords[3],
            resolution='c',  suppress_ticks=True
            )
    else :
        m = Basemap(
            projection='tmerc', ellps='WGS84', # set transverse mercator proj. and ellipsoid
            lon_0=(coords[0] + coords[2]) / 2, # longitude center
            lat_0=(coords[1] + coords[3]) / 2, # latitude center 
            llcrnrlon=coords[0] - 0.5,    # left lower corner 
            llcrnrlat=coords[1] - 0.5,
            urcrnrlon=coords[2] + 0.5,    # upper right corner 
            urcrnrlat=coords[3] + 0.5,
            resolution='c',  suppress_ticks=True
            )        
    m.readshapefile(shp_file[:-4], name=name, drawbounds=True, color='black')
    
    return(m)

def closestMatch(obj_name, kind) :
    '''
    Gives closest match to given obj.
    eg.: kind = 'india', obj_name = 'Mhrashtr'
         returns 'Maharashtra'
    Based on Levenshtein ratio
    '''

    #Telangana not included
    states = ['Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh',
              'Chhattisgarh', 'Dadra and Nagar Haveli', 'Daman and Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
              'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Lakshadweep', 'Madhya Pradesh', 
              'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 
              'Sikkim', 'Tamil Nadu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal']

    #Palghar not included
    districts = ['Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 'Chandrapur',
                 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur',
                 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 'Nandurbar',
                 'Nashik', 'Osmanabad', 'Parbhani', 'Pune', 'Raigad', 'Ratnagiri', 'Sangli',
                 'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha', 'Washim', 'Yavatmal']

    if kind == 'india' :
        ratio_dict = {obj : Levenshtein.ratio(obj_name, obj) for obj in states}
        if obj_name == 'Telangana' :
            ratio_dict['Andhra Pradesh'] = 1
        match = max(ratio_dict.keys(), key = (lambda key:ratio_dict[key]))

    elif kind == 'maharashtra' :
        ratio_dict = {obj : Levenshtein.ratio(obj_name, obj) for obj in districts}
        match = max(ratio_dict.keys(), key = (lambda key:ratio_dict[key]))
    else :
        raise NameError("Please enter one of 'india' or 'maharashtra' as input for kind.")

    return(match)

def matchNames(df_map, df_data, kind) :
    '''
    Match the names of shape file states/districts to the names in data
    
    Required :
    df_map - Basemap object created by createMap()
    df_data - df with 2 cols : Object and Value
    
    Return tabular data with map features and corresponding data values
    '''
    dfm = df_map.copy()
    dfd = df_data.copy()

    f = lambda x : closestMatch(x, kind)
    dfm.loc[:, 'Object'] = dfm.loc[:, 'Object'].apply(f)
    dfd.loc[:, 'Object'] = dfd.loc[:, 'Object'].apply(f)
    return(dfm, dfd)


def staticPlot(m, kind, df_data) :
    '''
    Plot static choropleth on map
    
    Given basemap object m
    Tabular data : Assumed as pandas dataframe with two columns - Object and Value (Can take any name)
    
    '''
    if kind == 'india' :
        key = 'ST_NM'
    elif kind == 'maharashtra' :
        key = 'DISTRICT'
    else :
        raise NameError("Please enter one of 'india' or 'maharashtra' as input for kind.")

    df_map = pd.DataFrame( {
                            "poly": [Polygon(xy) for xy in eval('m.' + kind)],
                            "Object": [x[key] for x in eval('m.' + kind + '_info')]
                            })

    dfm, dfd = matchNames(df_map, df_data, kind)

    df = pd.merge(dfm, dfd, on = 'Object')

    fig, ax = plt.gcf(), plt.gca()

    df.patch = df.poly.map(lambda x: PolygonPatch(x))
    pc = PatchCollection(df.patch, match_original = False, zorder = 2)

    pc.set(array = df.iloc[:, 2].get_values(), cmap='Reds') # impose color map onto patch collection
    fig.colorbar(pc, label="TEMP")  # Draw Colorbar and display the measure
    ax.add_collection(pc)                   # add patchcollection to axis