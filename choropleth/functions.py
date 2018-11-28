import fiona
from mpl_toolkits.basemap import Basemap   
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPoint, MultiPolygon
from shapely.prepared import prep
from shapely.geometry import shape, mapping
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
#from matplotlib.colors import Normalize
from descartes import PolygonPatch
from os.path import dirname
from os import getcwd
import Levenshtein
from bokeh.io import show, output_file, export_png
from bokeh.models import ColumnDataSource, HoverTool, LogColorMapper, LinearColorMapper
from bokeh.models import ColorBar, BasicTicker#, AdaptiveTicker
from bokeh.palettes import RdYlBu
from bokeh.plotting import figure, save
from bokeh.resources import CDN
from numpy import nan

def createStateShp(india_shp, state) :
    '''
    Creates district level shape file of given state from india_shp (with district boundaries)
    '''
    with fiona.open(india_shp) as input:
        # The output has the same schema
        output_schema = input.schema.copy()
        # write a new shapefile
        with fiona.open('maps/' + state , 'w', 'ESRI Shapefile', output_schema, crs=input.crs) as output:
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
    d = dirname(getcwd())

    if name == 'india' :
        shp_file = d + '/maps/india/india.shp'
    elif name == 'maharashtra' :
        shp_file = d + '/maps/maharashtra/maharashtra.shp'
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
        ratio_dict = {obj : Levenshtein.ratio(str.lower(obj_name), str.lower(obj)) for obj in states}
        if obj_name == 'Telangana' :
            ratio_dict['Andhra Pradesh'] = 1

        match = max(ratio_dict.keys(), key = (lambda key:ratio_dict[key]))
    elif kind == 'maharashtra' :
        ratio_dict = {obj : Levenshtein.ratio(str.lower(obj_name), str.lower(obj)) for obj in districts}
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
    fig.colorbar(pc, label=df.columns[2], shrink = 0.9)  # Draw Colorbar and display the measure
    ax.add_collection(pc)                   # add patchcollection to axis


def computeSkipRate(length, keep_ratio) :
    #Keep polygons with few points intact
    if length < 20 :
        skip_rate = 1
    else :
        skip_rate = int(length / (length * keep_ratio))
    return(skip_rate)

def getShpXY(shp, keep_ratio) :
    '''
    Gives the x, y lists required by Bokeh to plot.
    Shape file may have 2 types : Polygon and MultiPolygon
    Multipolygons contain lists of polygon objects. They need to be separated by nan values to render.
    Check : https://automating-gis-processes.github.io/Lesson5-interactive-map-Bokeh-advanced-plotting.html
    
    skip_rate : Skips over points in the polygon (Helps reduce the html size if level of detail is not required)
                eg. keep_ratio = 0.5   ==>   Keep only half of the points in the polygon [Skip alternate points]

    '''
    obj_x, obj_y, obj_xy = [], [], []
    for (ind, obj) in enumerate(shp) :
        #Entered individual state/district
        parts = obj['geometry']['coordinates']
        l = len(parts)
        if obj['geometry']['type'] == 'Polygon' :
            skip_rate = computeSkipRate(len(parts[0]), keep_ratio)
            x_list = [parts[0][i][0] for i in range(0, len(parts[0]), skip_rate)]
            y_list = [parts[0][i][1] for i in range(0, len(parts[0]), skip_rate)]
            #x_list = [item[0] for item in parts[0]]
            #y_list = [item[1] for item in parts[0]]
            obj_x.append(x_list)
            obj_y.append(y_list)
        else :
            x_list = []
            y_list = []
            for (i, subparts) in enumerate(parts) :
                #x_list = [subparts[0][l][0] for l in range(0, len(subparts[0]), 2)]
                #y_list = [subparts[0][l][1] for l in range(0, len(subparts[0]), 2)]
                skip_rate = computeSkipRate(len(subparts[0]), keep_ratio)
                for l in range(0, len(subparts[0]), skip_rate) :
                    x_list.append(subparts[0][l][0])
                    y_list.append(subparts[0][l][1])

                #for (j, item) in enumerate(subparts[0]) :
                #    x_list.append(item[0])
                #    y_list.append(item[1])
                x_list.append(nan)
                y_list.append(nan)
            obj_x.append(x_list)
            obj_y.append(y_list)
    return(obj_x, obj_y)

def interactivePlot(kind, df_data) :
    '''
    Interactive plot in Bokeh
    '''
    d = dirname(getcwd())

    if kind == 'india' :
        shp_file = d + '/maps/india/india.shp'
    elif kind == 'maharashtra' :
        shp_file = d + '/maps/maharashtra/maharashtra.shp'
    else :
        raise NameError("Please enter one of 'india' or 'maharashtra' as input for kind.")

    if kind == 'india' :
        key = 'ST_NM'
        plotkey = 'State'
    elif kind == 'maharashtra' :
        key = 'DISTRICT'
        plotkey = 'District'
    else :
        raise NameError("Please enter one of 'india' or 'maharashtra' as input for kind.")

    shp = fiona.open(shp_file)
    # Extract features from shapefile
    obj_name = [ feat["properties"][key] for feat in shp]
    obj_name = [closestMatch(name, kind) for name in obj_name]

    #Get the x, y lists needed by Bokeh to plot
    obj_x, obj_y = getShpXY(shp, 0.15)

    #obj_xy = [ [ xy for xy in obj["geometry"]["coordinates"][0]] for obj in shp]
    #obj_poly = [ Polygon(xy) for xy in obj_xy] # coords to Polygon

    #Map state/district in data to standard names
    f = lambda x : closestMatch(x, kind)
    dfd = df_data.copy()
    dfd.iloc[:, 0] = dfd.iloc[:, 0].apply(f)

    #Get the required data values to plot in Bokeh
    data = [dfd[dfd.iloc[:, 0] == name].iloc[:, 1].get_values()[0] for name in obj_name]

    #custom_colors = ['#f2f2f2', '#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
    
    color_mapper = LinearColorMapper(palette="Viridis256", low = min(data), high = max(data))    
    source = ColumnDataSource(data=dict(
        x=obj_x, y=obj_y,
        name=obj_name, rate=data,
    ))

    TOOLS = "pan,reset,hover" #wheel_zoom,save
    p = figure(
        title=dfd.columns[1], tools=TOOLS,
        x_axis_location=None, y_axis_location=None
    )
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, border_line_color=None, ticker = BasicTicker(), location=(0,0))
    p.grid.grid_line_color = None
    p.patches('x', 'y', source=source,
            fill_color={'field': 'rate', 'transform': color_mapper},
            fill_alpha=0.8, line_color="black", line_width=0.3)

    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [(plotkey, "@name"),(dfd.columns[1], "@rate")]
    
    p.add_layout(color_bar, 'right')
    #output_file("test.html")
    export_png(p, "map.png")#, height = 1960, width = 1960)
    show(p)