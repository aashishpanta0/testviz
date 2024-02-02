from bokeh.layouts import column, row
from bokeh.plotting import figure, curdoc
import bokeh
from bokeh.models import Span, Slider, Button, Select
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import gridplot, layout
from functools import lru_cache
from bokeh.models.widgets import Slider, Button
from bokeh.models import ColumnDataSource, CustomJS, Span, LinearColorMapper, ColorBar
from bokeh.models import LinearColorMapper, ColorBar
from bokeh.palettes import mpl
import matplotlib.cm as cm
from functools import cache
from bokeh.models import Range1d, LinearAxis, FixedTicker, FuncTickFormatter


from OpenVisus import *
import numpy as np
import xarray as xr
import pandas as pd
from OpenVisus import *
from bokeh.palettes import mpl
from concurrent.futures import ThreadPoolExecutor

coolwarm = mpl['Plasma'][256]

coolwarm_hex = ["#%02x%02x%02x" % (int(r), int(g), int(b)) for r, g, b, _ in 255*cm.coolwarm(np.linspace(0, 1, 256))]
# Load datasets
db_g0 = LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/v_llc2160/v_mapped_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
db_g1 = LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/theta_mitgcm_gulf.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
db_g2 = LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/t_mapped_llc2160/t_mapped_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
#db_mapped_t = LoadDataset('/nobackupp27/apanta/idx_data/gulf_region_highres/GEOS_T/t_gulf_llc2160.idx')

# db_mapped_t = LoadDataset('/nobackupp27/apanta/idx_data/gulf_region/GEOS_T/v3_t_mapped_gulf_llc2160.idx')
db_mapped_t =LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/qi_llc2160/qi_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
db_mapped_ql =LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/ql_llc2160/ql_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
# replace line above to get right ql idx
colormap_t = LinearColorMapper(palette=coolwarm_hex, low=240, high=302)
colormap_qi = LinearColorMapper(palette=coolwarm_hex, low=0, high=0.00007)
colormap_ql = LinearColorMapper(palette=coolwarm_hex, low=0, high=0.0005)

datasets = {
    'QI (ice-cloud water)': {'path':'https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/qi_llc2160/qi_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco','title': 'GEOS: QI (ice-cloud water)','cmapper':colormap_qi},
    'T (Temperature)': {'path':'https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/t_mapped_llc2160/t_mapped_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco','title':'GEOS: T (Air Temperature) in K (1000hpa)','cmapper':colormap_t}
}




# Create a color mapper for each plot
color_mapper1 = LinearColorMapper(palette=coolwarm_hex, low=-30, high=30)
color_mapper2 = LinearColorMapper(palette=coolwarm_hex, low=0.00, high=28.5)
# color_mapper3 = LinearColorMapper(palette=coolwarm_hex, low=240, high=302)
color_mapper3 = LinearColorMapper(palette=coolwarm_hex, low=0, high=0.00007)


map_depth=[0.5,1.6,2.8,4.2,5.8,7.6,9.7,12,14.7,17.7,21.1,25,29.3,34.2,39.7,45.8,52.7,60.3,68.7,78,88.2,99.4,112,125,139,155,172,190,209,230,252,275,300,325,352,381,410,441,473,507,541,576,613,651,690,730,771,813,856,900,946,992,1040,1089,1140,1192,1246,1302,1359,1418,1480,1544,1611,1681,1754,1830,1911,1996,2086,2181,2281,2389,2503,2626,2757,2898,3050,3215,3392,3584,3792,4019,4266,4535,4828,5148,5499,5882,6301,6760]
def getWidth(db):
    p2=db.getLogicBox()[1]
    return p2[0]

    # getHeight
def getHeight(db):
    p2=db.getLogicBox()[1]
    return p2[1]

    # getDepth
def getDepth(db):
    p2=db.getLogicBox()[1]
    return p2[2]
# Define functions to read data
@cache
def db_read(time, dataset):
    data_3d = dataset.read(time=time,quality=-6)
    return data_3d[data_3d.shape[0]-1, :, :]  # 2D slice at index 51
@cache
def db_read1(time, dataset):
    data_3d = dataset.read(time=time,quality=-6)
    return data_3d[0, :, :]  # 2D slice at index 51
@cache
def readSlice(db,dir=0, slice=0,quality=-6, time=0):
    W,H,D = getWidth(db), getHeight(db), getDepth(db)
    x = [0,W] if dir!=0 else [slice,slice+1]
    y = [0,H] if dir!=1 else [slice,slice+1]
    z = [0,D] if dir!=2 else [slice,slice+1]
    ret = db.read(x=x, y=y,z=z, quality=quality,time=time)
    width,height = [value for value in ret.shape if value>1]
    return ret.reshape([width,height])

def getLongImage(depth,time,db):
    return readSlice(db,dir=0, slice=(depth//2)*2,time=time, quality=-2)
# Get dataset dimensions


width0, height0, depth0 = getWidth(db_g0), getHeight(db_g0), getDepth(db_g0)
width1, height1, depth1 = getWidth(db_g1), getHeight(db_g1), getDepth(db_g1)
width2, height2, depth2 = getWidth(db_g2), getHeight(db_g2), getDepth(db_g2)

# Create ColumnDataSources for the plots
source1 = ColumnDataSource(data=dict(image=[np.zeros((height0, width0))], x=[0], y=[0], dw=[width0], dh=[height0]))
source2 = ColumnDataSource(data=dict(image=[np.zeros((height0, width0))], x=[0], y=[0], dw=[width0], dh=[height0]))
source3 = ColumnDataSource(data=dict(image=[np.zeros((height1, width1))], x=[0], y=[0], dw=[width1], dh=[height1]))
source4 = ColumnDataSource(data=dict(image=[np.zeros((height1, width1))], x=[0], y=[0], dw=[width1], dh=[height1]))
source5 = ColumnDataSource(data=dict(image=[np.zeros((height2, width2))], x=[0], y=[0], dw=[width2], dh=[height2]))
source6 = ColumnDataSource(data=dict(image=[np.zeros((height2, width2))], x=[0], y=[0], dw=[width2], dh=[height2]))
source7 = ColumnDataSource(data=dict(image=[np.zeros((height2, width2))], x=[0], y=[0], dw=[width2], dh=[height2]))

# Create plots
p1 = figure(x_range=(0, width0), y_range=(0, height0), width=400, height=400, title="GEOS: V (Northward Wind Velocity) in m_s-1 (1000hpa)")
p2 = figure(x_range=(0, width0), y_range=(0, depth0), width=1200, height=300)
p3 = figure(x_range=(0, width1), y_range=(0, height1), width=400, height=400, title="MITgcm: T (Ocean temperature in C)")
p4 = figure(x_range=(0, width1), y_range=(0, depth1), width=1200, height=300)
p5 = figure(x_range=(0, width2), y_range=(0, height2), width=400, height=400, title='GEOS: QI (Ice-Cloud Water Mass)')
p6 = figure(x_range=(0, width2), y_range=(0, depth2), width=1200, height=300)
p7 = figure(x_range=(0, width2), y_range=(0, height2), width=400, height=400, title='GEOS: QL (Liquid-Cloud Water Mass)')
p8 = figure(x_range=(0, width2), y_range=(0, depth2), width=1200, height=300)

color_bars = {}

for plot, color_mapper in zip([p1, p2, p3, p4, p5, p6,p8],
                              [color_mapper1, color_mapper1, color_mapper2, color_mapper2, color_mapper3, color_mapper3,colormap_ql]):
    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    color_bars[plot] = color_bar

    plot.add_layout(color_bar, 'right')

# Add the images to the plots
p1.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper1, source=source1)
p2.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper1, source=source2)
p3.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper2, source=source3)
p4.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper2, source=source4)
p5.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper3, source=source5)
p6.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=color_mapper3, source=source6)
p8.image(image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=colormap_ql, source=source7)

# Slider to control time
time_slider= Slider(start=0, end=1023, value=0, step=1, title="Time Slider",width=1200)


title_dataset3='GEOS: QI (Ice-Cloud Water Mass)'
color_mapper3=colormap_qi

# Function to update data and plots
def update_color_mapper(plot, new_color_mapper):
    for renderer in plot.renderers:
        if isinstance(renderer, bokeh.models.renderers.GlyphRenderer):
            if 'image' in renderer.glyph.properties():
                renderer.glyph.color_mapper = new_color_mapper
    for cb in plot.right:
        if isinstance(cb, bokeh.models.ColorBar):
            cb.color_mapper = new_color_mapper

trim_slice=False
def load_dataset(attr, old, new):
    t = time_slider.value
    d = vertical_line_slider.value
    selected_dataset = datasets[dropdown.value]
    global db_mapped_t, title_dataset3, color_mapper3, trim_slice
    db_mapped_t = LoadDataset(selected_dataset['path'])
    title_dataset3=selected_dataset["title"]
    color_mapper3=selected_dataset["cmapper"]
    p5.title.text = selected_dataset['title']
    color_bars[p5].color_mapper = color_mapper3
    color_bars[p6].color_mapper = color_mapper3
    update_color_mapper(p5, color_mapper3)
    update_color_mapper(p6, color_mapper3)
    if dropdown.value=="T (Temperature)":
        trim_slice=True
        p6.title.text = f'Time = {t}, Longitude = {d},    Field = GEOS: T  '
    else:
        trim_slice=False
        p6.title.text = f'Time = {t}, Longitude = {d},    Field = GEOS: QI   '
        


def update_data(attrname, old, new):

    t = time_slider.value
    d = vertical_line_slider.value

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(db_read, t, db) for db in [db_g0,  db_mapped_t]]
        data1, data3 = [f.result() for f in futures]

    data2=db_read1(t,db_g1)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(getLongImage, d, t, db) for db in [ db_g1, db_mapped_t,db_mapped_ql]]
        vdata2, vdata3, vdata4 = [f.result() for f in futures]
        vdata2=np.flipud(np.fliplr(vdata2))
        vdata3=np.flipud(np.fliplr(vdata3))
        vdata4=np.flipud(np.fliplr(vdata4))
        source1.data = dict(image=[data1], x=[0], y=[0], dw=[width0], dh=[height0])
        source3.data = dict(image=[data2], x=[0], y=[0], dw=[width1], dh=[height1])
        source4.data = dict(image=[vdata2], x=[0], y=[0], dw=[width1], dh=[depth1])
        source5.data = dict(image=[data3], x=[0], y=[0], dw=[width2], dh=[height2])
        source7.data = dict(image=[vdata4], x=[0], y=[0], dw=[width2], dh=[depth2])

        if trim_slice==True:
            vdata3=vdata3[:11,:]
            p6.title.text = f'Time = {t}, Longitude = {d},    Field = GEOS: T  '
        else:
            p6.title.text = f'Time = {t}, Longitude = {d},    Field = GEOS: QI   '
        source6.data = dict(image=[vdata3], x=[0], y=[0], dw=[width2], dh=[depth2])



    p2.title.text = f'Time = {t}, Longitude = {d}'
    p8.title.text = f'Time = {t}, Longitude = {d}    Field = GEOS: QL (liquid-cloud water)'



dropdown = Select(title="Select Dataset", value='QI (ice-cloud water)', options=list(datasets.keys()))
dropdown.on_change('value', load_dataset)
dropdown.on_change('value', update_data)
dropdown_data= layout([[dropdown]])
# Attach the update_data function to the time slider
time_slider.on_change('value', update_data)

# Vertical line slider
vertical_line_slider = Slider(start=0, end=719, value=0, step=1, width=1200,title="Vertical Line Position")

# Add a Span to each plot
vline1 = Span(location=vertical_line_slider.value, dimension='height', line_color='green', line_dash='dashed', line_width=3)
vline2 = Span(location=vertical_line_slider.value, dimension='height', line_color='green', line_dash='dashed', line_width=3)
vline3 = Span(location=vertical_line_slider.value, dimension='height', line_color='green', line_dash='dashed', line_width=3)
p1.add_layout(vline1)
p3.add_layout(vline2)
p5.add_layout(vline3)

callback_id = None


# Function to update vertical line position
def update_line(attrname, old, new):
    vline1.location = vertical_line_slider.value
    vline2.location = vertical_line_slider.value
    vline3.location = vertical_line_slider.value

# Attach the update_line function to the vertical line slider
vertical_line_slider.on_change('value', update_line)
vertical_line_slider.on_change('value', update_data)

# Function to update time during animation
animating = False  # Flag to keep track of animation state
callbacks = {}  # Dictionary to store callback IDs

def animate_update():
    global animating  # Use nonlocal to modify the outer animating variable
    if not animating:  # Check if the animation is paused
        return

    year = int(time_slider.value) + 1
    if year > 1023:  # Set the maximum year to 1000
        year = 0
        animating = False  # Stop the animation at the last year
        play_button.label = '► Play'  # Change button label to "► Play"

    time_slider.value = year
    update_data(None, None, None)

def animate():
    global animating  # Use nonlocal to modify the outer animating variable
    animating = not animating  # Toggle animation state

    if animating:
        play_button.label = '❚❚ Pause'
        # Add the animation callback only if it's not already added
        if 'animation' not in callbacks:
            callbacks['animation'] = curdoc().add_periodic_callback(animate_update, 100)
    else:
        play_button.label = '► Play'
        # Remove the animation callback only if it's already added
        if 'animation' in callbacks:
            curdoc().remove_periodic_callback(callbacks['animation'])
            del callbacks['animation']

# Add the animate function to the play_button
play_button = Button(label="► Play", width=120, height=60)
play_button.on_click(animate)

# Arrange plots and widgets in a layout
combined_p4_p6 = column(p8,p6, p4, sizing_mode="stretch_both",spacing=0)

# Arrange plots and widgets in the overall layout
layout = column(
    row(column(time_slider, vertical_line_slider), play_button),
    row(p1, p3,p5),
    row(combined_p4_p6),
    row(p2)

)
p6.xaxis.visible = False
p6.xgrid.visible = False
p6.toolbar_location = None
p6.xaxis.axis_label_standoff = 0

p8.xaxis.visible = False
p8.xgrid.visible = False
p8.toolbar_location = None
p8.xaxis.axis_label_standoff = 0

p4.border_fill_color = None
p4.outline_line_color = None
p6.border_fill_color = None
p6.outline_line_color = None
# Call update_data once to initialize the plots

# p6.yaxis.visible = False
# p6.ygrid.visible = False
p4.yaxis.visible = False
p4.ygrid.visible = False
p4.xaxis.visible = False
p4.xgrid.visible = False

p1.yaxis.visible = False
p3.yaxis.visible = False
p5.yaxis.visible = False
p1.ygrid.visible = False
p3.ygrid.visible = False
p5.ygrid.visible = False
p1.xaxis.visible = False
p3.xaxis.visible = False
p5.xaxis.visible = False
p1.xgrid.visible = False
p3.xgrid.visible = False
p5.xgrid.visible = False

p1.extra_y_ranges = {"lat": Range1d(start=30, end=45)}
p1.add_layout(LinearAxis(y_range_name="lat"), 'left')

p3.extra_y_ranges = {"lat": Range1d(start=30, end=45)}
p3.add_layout(LinearAxis(y_range_name="lat"), 'left')

p5.extra_y_ranges = {"lat": Range1d(start=30, end=45)}
p5.add_layout(LinearAxis(y_range_name="lat"), 'left')


p1.extra_x_ranges = {"lon": Range1d(start=-75, end=-60)}
p1.add_layout(LinearAxis(x_range_name="lon"), 'below')

p3.extra_x_ranges = {"lon": Range1d(start=-75, end=-60)}
p3.add_layout(LinearAxis(x_range_name="lon"), 'below')

p5.extra_x_ranges = {"lon": Range1d(start=-75, end=-60)}
p5.add_layout(LinearAxis(x_range_name="lon"), 'below')

map_depth=map_depth[0::8]
map_values = list(reversed(map_depth))
p4.extra_y_ranges = {"Depth (m)": Range1d(start=0, end=len(map_values) - 1)}
lat_axis = LinearAxis(y_range_name="Depth (m)", axis_label="Depth (m)")
lat_axis.ticker =  FixedTicker(ticks=list(range(len(map_values)))) # Set ticks at every 10th value from map_depth
lat_axis.formatter = FuncTickFormatter(code="""
    var labels = %s;
    return labels[tick];
""" % map_values)

p4.add_layout(lat_axis, 'left')

p4.extra_x_ranges = {"lat": Range1d(start=45, end=30)}
lat_axis=LinearAxis(x_range_name="lat")
lat_axis.axis_label = "Latitude"
p4.add_layout(lat_axis, 'below')

# p6.extra_y_ranges = {"Pressure(hpa)": Range1d(start=1000, end=700)}
# lat_axis=LinearAxis(y_range_name="Pressure(hpa)")
# lat_axis.axis_label = "Pressure(hpa)"  
# p6.add_layout(lat_axis, 'left')
update_data(None, None, None)

# Add the layout to the document


coolwarm = mpl['Plasma'][256] # This line generates a colormap with 256 colors

# Convert the colormap to hexadecimal format
coolwarm_hex = ["#%02x%02x%02x" % (int(r), int(g), int(b)) for r, g, b, _ in 255*cm.coolwarm(np.linspace(0, 1, 256))]


db = LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/eflux_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')
db1 = LoadDataset('https://maritime.sealstorage.io/api/v0/s3/utah/nasa/dyamond/GULF/hflux_gulf_llc2160.idx?access_key=any&secret_key=any&endpoint_url=https://maritime.sealstorage.io/api/v0/s3&cached=arco')

@lru_cache(maxsize=None)
def db_read2(time,quality, dataset):
    return dataset.read(time=time, quality=quality)

def modify_doc(doc):
    init_time = 0
    init_quality=0
    data = db_read2(time=init_time,quality=init_quality, dataset=db)
    data1 = db_read2(time=init_time,quality=init_quality, dataset=db1)

    data_df = pd.DataFrame(data)
    data_df1 = pd.DataFrame(data1)
    data_json = data_df.to_json(orient='records')
    data_json1 = data_df1.to_json(orient='records')

    color_mapper = LinearColorMapper(palette=coolwarm_hex, low=-200, high=800)
    color_mapper1 = LinearColorMapper(palette=coolwarm_hex, low=-200, high=800)

    p1 = figure(title="EFLUX,     Time = 0 ,      Longitude = 0", x_axis_label='lon', y_axis_label='lat',
                x_range=(0, data.shape[1]), y_range=(0, data.shape[0]),
                tools="pan,wheel_zoom,xbox_select,reset")
    image_renderer1 = p1.image(image=[data], x=0, y=0, dw=data.shape[1], dh=data.shape[0], color_mapper=color_mapper)

    color_bar1 = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p1.add_layout(color_bar1, 'right')

    vline1 = Span(location=0, dimension='height', line_color='green',  line_dash='dashed',line_width=3)
    p1.add_layout(vline1)

    p2 = figure(title="HFLUX,     Time = 0 ,      Longitude = 0", x_axis_label='lon', y_axis_label='lat',
                x_range=(0, data1.shape[1]), y_range=(0, data1.shape[0]),
                tools="pan,wheel_zoom,xbox_select,reset")
    image_renderer2 = p2.image(image=[data1], x=0, y=0, dw=data1.shape[1], dh=data1.shape[0], color_mapper=color_mapper1)

    color_bar2 = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p2.add_layout(color_bar2, 'right')

    vline2 = Span(location=0, dimension='height', line_color='green', line_dash='dashed', line_width=3)
    p2.add_layout(vline2)

    # vertical_line_slider = Slider(start=0, end=data.shape[1]-1, value=0, step=1, title="Interactive Line Longitude")
    # time_slider = Slider(start=0, end=1023, value=init_time, step=1, title="Time")

    source1 = ColumnDataSource(data=dict(x=np.arange(data.shape[0]), y=data[:, 0]))
    p3 = figure(width=600, height=300, title="Values on the Interactive Line (EFLUX)",
                x_axis_label='Latitude', y_axis_label='Values',
                x_range=(0, data.shape[0]), y_range=(-200, 800))  # Set initial y-axis range
    line_renderer1 = p3.line('x', 'y', source=source1, line_color="blue", line_width=2)

    source2 = ColumnDataSource(data=dict(x=np.arange(data1.shape[0]), y=data1[:, 0]))
    p4 = figure(width=600, height=300, title="Values on the Interactive Line (HFLUX)",
                x_axis_label='Latitude', y_axis_label='Values',
                x_range=(0, data1.shape[0]), y_range=(-200, 800))  # Set initial y-axis range
    line_renderer2 = p4.line('x', 'y', source=source2, line_color="red", line_width=2)
    quality_slider = Slider(start=-6, end=0, value=init_quality, step=1, title="Quality")


    def slider_update(attr, old, new):
        slider_val = int(vertical_line_slider.value)
        time_val = int(time_slider.value)
        quality_val = int(quality_slider.value)
        if quality_val==0 or quality_val==-1:
            slider_val = slider_val
        if quality_val==-2 or quality_val==-3:
            slider_val= slider_val//2
        if quality_val==-4 or quality_val==-5:
            slider_val = slider_val//4
        if quality_val==-6:
            slider_val = slider_val//8
        new_data = db_read2(time=time_val, quality=quality_val,dataset=db)
        new_data1 = db_read2(time=time_val, quality=quality_val, dataset=db1)
        source1.data = dict(x=np.arange(new_data.shape[0]), y=new_data[:, slider_val])
        source2.data = dict(x=np.arange(new_data1.shape[0]), y=new_data1[:, slider_val])
        # vertical_line_slider.end = new_data.shape[1] - 1
        image_renderer1.data_source.data['image'] = [new_data]
        image_renderer1.data_source.data['dw'] = [new_data.shape[1]]
        image_renderer1.data_source.data['dh'] = [new_data.shape[0]]
        line_renderer1.data_source.data = dict(x=np.arange(new_data.shape[0]), y=new_data[:, slider_val])
        image_renderer2.data_source.data['image'] = [new_data1]
        image_renderer2.data_source.data['dw'] = [new_data1.shape[1]]
        image_renderer2.data_source.data['dh'] = [new_data1.shape[0]]
        line_renderer2.data_source.data = dict(x=np.arange(new_data1.shape[0]), y=new_data1[:, slider_val])
        vline1.location = slider_val
        vline2.location = slider_val
        p1.x_range.start = 0
        p1.x_range.end = new_data.shape[1]
        p1.y_range.start = 0
        p1.y_range.end = new_data.shape[0]
        p2.x_range.start = 0
        p2.x_range.end = new_data1.shape[1]
        p2.y_range.start = 0
        p2.y_range.end = new_data1.shape[0]
        p1.title.text = f'EFLUX,     Time = {time_val},     Longitude = {slider_val},     Quality = {quality_val}'
        p2.title.text = f'HFLUX,     Time = {time_val},     Longitude = {slider_val},     Quality = {quality_val}'

    vertical_line_slider.on_change('value', slider_update)
    def update_sliders(attr, old, new):
        time_val = int(time_slider.value)
        slider_val = int(vertical_line_slider.value)
        quality_val = int(quality_slider.value)
        if quality_val==0 or quality_val==-1:
            slider_val = slider_val
        if quality_val==-2 or quality_val==-3:
            slider_val= slider_val//2
        if quality_val==-4 or quality_val==-5:
            slider_val = slider_val//4
        if quality_val==-6:
            slider_val = slider_val//8
        new_data = db_read2(time=time_val, quality=quality_val, dataset=db)
        new_data1 = db_read2(time=time_val, quality=quality_val, dataset=db1)

        # Update the range of the longitudinal slider based on the data shape
        # vertical_line_slider.end = new_data.shape[1] - 1

        # Update the plot data in place
        source1.data.update(x=np.arange(new_data.shape[0]), y=new_data[:, slider_val])
        source2.data.update(x=np.arange(new_data1.shape[0]), y=new_data1[:, slider_val])

        # Update the image width and height attributes in place
        image_renderer1.glyph.update(dw=new_data.shape[1], dh=new_data.shape[0])
        image_renderer2.glyph.update(dw=new_data1.shape[1], dh=new_data1.shape[0])

        # Update the image data source in place
        image_renderer1.data_source.data.update(image=[new_data], dw=[new_data.shape[1]], dh=[new_data.shape[0]])
        image_renderer2.data_source.data.update(image=[new_data1], dw=[new_data1.shape[1]], dh=[new_data1.shape[0]])

        # Update the vertical lines
        vline1.location = slider_val
        vline2.location = slider_val

        # Update the plot range in one line
        p1.x_range.update(start=0, end=new_data.shape[1])
        p1.y_range.update(start=0, end=new_data.shape[0])

        p2.x_range.update(start=0, end=new_data1.shape[1])
        p2.y_range.update(start=0, end=new_data1.shape[0])

        # Update the line plot range in one line
        p3.x_range.update(start=0, end=new_data.shape[0])
        p4.x_range.update(start=0, end=new_data1.shape[0])

        # Update the plot titles
        p1.title.text = f'EFLUX, Time = {time_val}, Longitude = {slider_val}, Quality = {quality_val}'
        p2.title.text = f'HFLUX, Time = {time_val}, Longitude = {slider_val}, Quality = {quality_val}'

        # Trigger a change in the data sources
        source1.trigger('data', source1.data, source1.data)
        source2.trigger('data', source2.data, source2.data)

    # Attach the callback function to the quality slider
    quality_slider.on_change('value', update_sliders)

    # animating = False  # Flag to keep track of animation state
    # callbacks = {}  # Dictionary to store callback IDs


    def update(attr, old, new):
        new_time = int(time_slider.value)
        quality_val = int(quality_slider.value)
        slider_val = int(vertical_line_slider.value)
        if quality_val==0 or quality_val==-1:
            slider_val = slider_val
        if quality_val==-2 or quality_val==-3:
            slider_val= slider_val//2
        if quality_val==-4 or quality_val==-5:
            slider_val = slider_val//4
        if quality_val==-6:
            slider_val = slider_val//8
        new_data = db_read2(time=new_time,quality=quality_val, dataset=db)
        new_data1 = db_read2(time=new_time,quality=quality_val, dataset=db1)
        # vertical_line_slider.end = new_data.shape[1] - 1


          # Get the current value of the longitude slider
        source1.data = dict(x=np.arange(new_data.shape[0]), y=new_data[:, slider_val])  # Use slider_val instead of 0
        image_renderer1.data_source.data['image'] = [new_data]
        image_renderer1.data_source.data['dw'] = [new_data.shape[1]]
        image_renderer1.data_source.data['dh'] = [new_data.shape[0]]
        line_renderer1.data_source.data = dict(x=np.arange(new_data.shape[0]), y=new_data[:, slider_val])  # Use slider_val instead of 0

        source2.data = dict(x=np.arange(new_data1.shape[0]), y=new_data1[:, slider_val])  # Use slider_val instead of 0
        image_renderer2.data_source.data['image'] = [new_data1]
        image_renderer2.data_source.data['dw'] = [new_data1.shape[1]]
        image_renderer2.data_source.data['dh'] = [new_data1.shape[0]]
        line_renderer2.data_source.data = dict(x=np.arange(new_data1.shape[0]), y=new_data1[:, slider_val])  # Use slider_val instead of 0
        p1.title.text = f'EFLUX,     Time = {new_time},     Longitude = {slider_val},     Quality = {quality_val}'
        p2.title.text = f'HFLUX,     Time = {new_time},     Longitude = {slider_val},     Quality = {quality_val}'

    time_slider.on_change('value', update)

    p1.yaxis.visible = False
    p2.yaxis.visible = False

    p1.ygrid.visible = False
    p2.ygrid.visible = False

    p1.xaxis.visible = False
    p2.xaxis.visible = False

    p1.xgrid.visible = False
    p2.xgrid.visible = False

    p3.xaxis.visible = False
    p4.xaxis.visible = False
    p3.xgrid.visible = False
    p4.xgrid.visible = False

    p3.extra_x_ranges = {"latline": Range1d(start=30, end=45)}
    lat_axis=LinearAxis(x_range_name="latline")
    lat_axis.axis_label = "Latitude"
    p3.add_layout(lat_axis, 'below')

    p4.extra_x_ranges = {"latline": Range1d(start=30, end=45)}
    lat_axis=LinearAxis(x_range_name="latline")
    lat_axis.axis_label = "Latitude"
    p4.add_layout(lat_axis, 'below')


    p1.extra_y_ranges = {"lat": Range1d(start=30, end=45)}
    lat_axis=LinearAxis(y_range_name="lat")
    lat_axis.axis_label = "Latitude"
    p1.add_layout(lat_axis, 'left')

    p2.extra_y_ranges = {"lat": Range1d(start=30, end=45)}
    lat_axis=LinearAxis(y_range_name="lat")
    lat_axis.axis_label = "Latitude"
    p2.add_layout(lat_axis, 'left')


    p1.extra_x_ranges = {"lon": Range1d(start=-75, end=-60)}
    lat_axis=LinearAxis(x_range_name="lon")
    lat_axis.axis_label = "Longitude"
    p1.add_layout(lat_axis, 'below')

    p2.extra_x_ranges = {"lon": Range1d(start=-75, end=-60)}
    lat_axis=LinearAxis(x_range_name="lon")
    lat_axis.axis_label = "Longitude"
    p2.add_layout(lat_axis, 'below')

    # Create two separate columns, each containing the data plot and its corresponding line plot
    column1 = column(p1, p3)
    column2 = column(p2, p4)

    # Modify your layout to include the animate button and both columns
    layout = column(column(quality_slider), row(column1, column2))
    # doc.add_root(layout)
    return column(column(quality_slider), row(column1, column2))
lay=modify_doc(curdoc())

final_layout=column(dropdown_data,column(time_slider,vertical_line_slider, play_button,row(column(

    row(p1, p3,p5),
    row(combined_p4_p6)

),lay)))
# modify_doc(curdoc())
curdoc().add_root(final_layout)