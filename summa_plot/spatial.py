'''Spatial plotting for SUMMA output'''

import shapely
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from cartopy.feature import NaturalEarthFeature
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon


def add_map_features(ax, states_provinces=True, country_borders=True,
                     land=True, ocean=True, lake=False):
    '''Add background features to an axis'''
    if states_provinces:
        states_provinces = NaturalEarthFeature(
                category='cultural', name='admin_1_states_provinces_lines',
                scale='50m', facecolor='none')
        ax.add_feature(states_provinces, edgecolor='black', alpha=.8, zorder=2)
    if country_borders:
        ctry_borders = NaturalEarthFeature(
            category='cultural', name='admin_0_boundary_lines_land',
            scale='50m', facecolor='none')
        ax.add_feature(ctry_borders, edgecolor='black', zorder=2, linewidth=1)
    if land:
        land = NaturalEarthFeature(
            category='physical', name='land', scale='50m', facecolor='gray')
        ax.add_feature(land, facecolor='lightgray', zorder=0)
    if ocean:
        ocean = NaturalEarthFeature(
            category='physical', name='ocean', scale='50m', facecolor='blue')
        ax.add_feature(ocean, facecolor='lightblue', zorder=1)
    if lake:
        rivers_lakes = NaturalEarthFeature(
            category='physical', name='rivers_lake_centerlines',
            scale='50m', facecolor='none')
        ax.add_feature(rivers_lakes, facecolor='lightblue', zorder=2)


def gen_patches(data_array, geodf, simplify_level=500):
    '''Simplify polygons and generate a PatchCollection for faster plotting'''
    vals = []
    patches = []

    for val, shp in zip(data_array.values, geodf.geometry):
        if isinstance(shp, shapely.geometry.MultiPolygon):
            for sub in shp:
                patches.append(Polygon(np.asarray(
                    sub.simplify(simplify_level).exterior)))
                vals.append(val)
        else:
            patches.append(
                    Polygon(np.asarray(shp.simplify(simplify_level).exterior)))
            vals.append(val)
    patches = PatchCollection(patches, linewidth=0., edgecolor=None, alpha=1.0)
    patches.set_array(np.array(vals))
    return patches


def spatial(data_array, geodf, simplify_level=500, proj=ccrs.Mercator()):
    '''Make a spatial plot'''
    geodf_crs = geodf.to_crs(crs=proj.proj4_params)
    patches = gen_patches(data_array, geodf_crs, simplify_level)
    fig, ax = plt.subplots(nrows=1, ncols=1, subplot_kw=dict(projection=proj))
    ax.add_collection(patches)
    add_map_features(ax)
    ax.autoscale_view()
    return fig, ax


def hovmuller(data_array, xdim, ydim, how='mean', cmap='viridis'):
    '''Make a Hovmuller plot'''
    # Check if dimensions are valid
    time_groups = ['year', 'month', 'day', 'hour',
                   'minute', 'second', 'dayofyear',
                   'week', 'dayofweek', 'weekday', 'quarter']
    x_da_dim = xdim in list(data_array.dims)
    x_tg_dim = xdim in time_groups.keys()
    if x_tg_dim:
        xdim = 'time.{}'.format(xdim)
        if not how:
            raise Exception("Must specify aggregation "
                            "method for x dimension")
    elif not x_da_dim:
        raise Exception("x dimension not valid")

    y_da_dim = ydim in list(data_array.dims)
    y_tg_dim = ydim in time_groups.keys()
    if y_tg_dim:
        ydim = 'time.{}'.format(ydim)
        if not how:
            raise Exception("Must specify aggregation "
                            "method for y dimension")
    elif not y_da_dim:
        raise Exception("y dimension not valid")

    # Make sure the aggregation method is valid
    aggregation_methods = {'mean': lambda x: x.mean(),
                           'max': lambda x: x.max(),
                           'min': lambda x: x.min(),
                           'median': lambda x: x.median(),
                           'std': lambda x: x.std()}
    if how not in aggregation_methods.keys():
        raise Exception("Invalid time aggregation method given")

    # Do the group statements
    aggregate = aggregation_methods[how]
    grouped1 = data_array.groupby(ydim)
    grouped2 = grouped1.apply(lambda x: aggregate(x.groupby(xdim)))
    x = grouped2[(list(grouped2.dims)[1])]
    y = grouped2[(list(grouped2.dims)[0])]
    z = np.ma.masked_invalid(grouped2.values)
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.axes.pcolormesh(x, y, z, cmap=cmap)
    ax.axes.axis([x.min(), x.max(), y.min(), y.max()])

    # TODO: Format axes and labels
    daysofweek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                  'Thursday', 'Friday', 'Saturday']
    seasons = ['DJF', 'MAM', 'JJA', 'SON']
    return fig, ax
