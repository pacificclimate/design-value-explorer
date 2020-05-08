from climpyrical.mask import rotate_shapefile

import geopandas as gpd
from shapely.geometry import MultiPolygon


def load_north_america_polygons_plotly(path_to_shapefile: str) -> str:
    """Loads a polygon from Natural Earth to plot in plotly
    Args: 
        path_to_shapefile (str): Path to desired shapefile. This function uses geopandas,
        and can use any filetype supporrted by geopandas.read_file
    Returns:
        X, Y (list): List of points on the exterior of all of the polygons. Each polygon
        instance is separated by a pair None, None. This is for plotly plotting purposes
        so that it doesn't connect islands to another land point
    """
    cc = gpd.read_file(path_to_shapefile)
    # include Canada, US, Greenland, Mexico, Cuba
    cc = cc[
        (cc.iso_a2 == "CA")
        | (cc.iso_a2 == "US")
        | (cc.iso_a2 == "GL")
        | (cc.iso_a2 == "MX")
        | (cc.iso_a2 == "CU")
    ]
    # exclude Hawaii
    cc = cc[cc.name != "Hawaii"]
    cc = cc.to_crs({"init": "epsg:4326"})
    # extract geometric info of these areas
    cc = cc.geometry
    # rotate to rotated pole coordinates
    canadar = rotate_shapefile(cc.geometry)

    pts = []
    for poly in canadar:
        if isinstance(poly, MultiPolygon):
            for p in poly:
                pts.extend(p.exterior.coords)
                pts.append([None, None])
        else:
            pts.extend(poly.exterior.coords)
            pts.append([None, None])

    X, Y = zip(*pts)
    return X, Y
