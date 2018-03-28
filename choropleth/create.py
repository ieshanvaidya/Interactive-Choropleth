import fiona
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import os

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