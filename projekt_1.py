#odpowiedzi na pytania ze skryptu:
# 1.Wysokość pojedynczej kondygnacji, obliczonej na podstawie wysokości budynku z
# ALS i parametru liczby kondygnacji z BDOT wynosi średnio 3,7m
# 2.Rozkład odchylenia standardowego dla wysokości budynków obliczonych z danych
# ALS za pomocą Zonal Statistic as Table: Std. Dev wynosi 3,14m

import numpy as np
import laspy
import arcpy
from arcpy.sa import *
import open3d as o3d
from matplotlib import pyplot as plt

lasL=r"C:\Rok3\foto\N-34-63-C-c-1-4-4 — kopia.las"

#na 3

#wczytanie chmur punktow LAS
las = laspy.file.File(lasL, header = None, mode = 'rw')

#poprawa intensywnosci odbicia wiazki lasera
def cutLoses(data):
    mean_value = np.mean(data)
    std_dev = np.std(data)
    threshold = 2 * std_dev
    trimmed_data = [value for value in data if abs(value - mean_value) <= threshold]
    return trimmed_data

intensity = las.intensity
intensity= cutLoses(intensity)
n_bins = 30
plt.hist(intensity, bins = n_bins)
plt.show()

#filtracja chmur punktow w oparciu o klase
def point_extraction_based_on_the_class(las, class_pnt):
    if class_pnt == 'buildings':
        print('Buildings extraction')
        buildings_only = np.where(las.raw_classification == 6)
        buildings_points = las.points[buildings_only]
        return buildings_points
    elif class_pnt == 'vegetation':
        print('Vegetation extraction')
        vegetation_low = np.where(las.raw_classification == 3)
        vegetation_medium = np.where(las.raw_classification == 4)
        vegetation_high = np.where(las.raw_classification == 5)
        vegetation = np.hstack((vegetation_low[0], vegetation_medium[0], vegetation_high[0]))
        vegetation = las.points[vegetation]
        return vegetation
    else:
        print('Ground extraction')
        ground_only = np.where(las.raw_classification == 2)
        ground_points = las.points[ground_only]
        return ground_points

def save_points_after_processing(file, las, new_las):
    las_pcd = laspy.file.File(file, header=las.header, mode = "w")
    las_pcd.points = new_las
    las_pcd.close()

ext_bui = point_extraction_based_on_the_class(las_pcd, 'buildings')
save_points_after_processing('las_bui.las', las_pcd, ext_bui)

ext_gro = point_extraction_based_on_the_class(las_pcd, 'ground')
save_points_after_processing('las_gro.las', las_pcd, ext_gro)

ext_veg = point_extraction_based_on_the_class(las_pcd, 'vegetation')
save_points_after_processing('las_veg.las', las_pcd, ext_veg)

#na 4

#wczytanie chmury punktow do formatu open3d
def las_to_o3d(file):
    las_pcd = laspy.file.File(file, mode='r')
    x = las_pcd.x
    y = las_pcd.y
    z = las_pcd.z
    las_intensity = las_pcd.intensity / max(las_pcd.intensity)

    las_points = np.vstack((x, y, z)).transpose()
    point_cloud = o3d.geometry.PointCloud()
    point_cloud.points = o3d.utility.Vector3dVector(las_points)
    return point_cloud

# def show_pcd(point_cloud, window_name='Window name'):
#     o3d.visualization.draw_geometries_with_editing([point_cloud], window_name, width=1920, height=1080, left=50, top=50)
points=las_to_o3d(lasL)

#zapis do formatu .pcd
def save_point_cloud_o3d(file, pointcloud):
    o3d.io.write_point_cloud(file, pointcloud, write_ascii=False, compressed=False, print_progress=False)

save_point_cloud_o3d("C:/Rok3/foto/chmura.pcd",points)

#wyswietlanie chmur punktow z osiami XYZ
def draw_coordinate_axes(point_cloud):
    bound = point_cloud.get_min_bound()
    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=100)
    frame.translate(bound-20)
    o3d.visualization.draw_geometries([point_cloud, frame], window_name='Point Cloud with Coordinate Axes')

draw_coordinate_axes(points)

#NMT
j=[1,3,5]
for cellSize in j:
    arcpy.conversion.LasDatasetToRaster(
        in_las_dataset="ground.las",
        out_raster=f"C:\\Rok3\\foto\\nmt{cellSize}",
        value_field="ELEVATION",
        interpolation_type="TRIANGULATION NATURAL_NEIGHBOR NO_THINNING",
        data_type="FLOAT",
        sampling_type="CELLSIZE",
        sampling_value=cellSize,
        z_factor=1
    )
#NMTP
i=[1,3,5]
for cellSize in i:
    arcpy.conversion.LasDatasetToRaster(
        in_las_dataset=lasL,
        out_raster=f"C:\\Rok3\\foto\\nmpt{cellSize}",
        value_field="ELEVATION",
        interpolation_type="BINNING AVERAGE LINEAR",
        data_type="FLOAT",
        sampling_type="CELLSIZE",
        sampling_value=cellSize,
        z_factor=1
    )

#na 5

#raster intensywnosci
arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="bud.las",
    out_raster=r"C:\Rok3\foto\intensywnosc_budynkow.tif",
    value_field="INTENSITY",
    interpolation_type="BINNING AVERAGE NONE",
    data_type="INT",
    sampling_type="CELLSIZE",
    sampling_value=1,
    z_factor=1
)

#wyekstrachowanie budynkow do formatu .shp
arcpy.conversion.RasterToPolygon(
    in_raster="intensywnosc_budynkow.tif",
    out_polygon_features=r"C:\Rok3\foto\budynkishp.shp",
    simplify="SIMPLIFY",
    raster_field="Value",
    create_multipart_features="SINGLE_OUTER_PART",
    max_vertices_per_feature=None
)

arcpy.cartography.AggregatePolygons(
    in_features="budynkishp.shp",
    out_feature_class=r"C:\Rok3\foto\budynkishp_AggregatePolygons.shp",
    aggregation_distance="2 Unknown",
    minimum_area="0 Unknown",
    minimum_hole_size="0 Unknown",
    orthogonality_option="ORTHOGONAL",
    barrier_features=None,
    out_table=r"C:\Rok3\foto\budynkishp_AggregatePolygons_Tbl.dbf",
    aggregate_field=None
)

arcpy.cartography.SimplifyPolygon(
    in_features="budynkishp_AggregatePolygons.shp",
    out_feature_class=r"C:\Rok3\foto\budynkishp_Agg_Simplify.shp",
    algorithm="POINT_REMOVE",
    tolerance="2 Unknown",
    minimum_area="0 Unknown",
    error_option="NO_CHECK",
    collapsed_point_option="KEEP_COLLAPSED_POINTS",
    in_barriers=None
)

# wyznaczanie pol powierzchni, wysokosci i objectosci(area, range, V)
znmpt = arcpy.ia.RasterCalculator(['nmpt1','nmt1'],['nmpt','nmt'], "nmpt-nmt")
znmpt.save(r"C:\Rok3\foto\znmpt")

arcpy.sa.ZonalStatisticsAsTable(
    in_zone_data="budynkishp_Agg_Simplify.shp",
    zone_field="FID",
    in_value_raster="znmpt",
    out_table=r"C:\Rok3\foto\ZonalSt_budynki.dbf",
    ignore_nodata="DATA",
    statistics_type="ALL",
    process_as_multidimensional="CURRENT_SLICE",
    percentile_values=[100],
    percentile_interpolation_type="AUTO_DETECT",
    circular_calculation="ARITHMETIC",
    circular_wrap_value=360
)

arcpy.management.JoinField(
    in_data="budynkishp_Agg_Simplify.shp",
    in_field="FID",
    join_table="ZonalSt_budynki.dbf",
    join_field="FID_",
    fields=None,
    fm_option="NOT_USE_FM",
    field_mapping=None
)

arcpy.management.CalculateField(
    in_table="budynkishp_Agg_Simplify.shp",
    field="V",
    expression="!AREA! * !RANGE!",
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

pola = ["FID", "area", "V", "RANGE"]
warstwa="budynkishp_Agg_Simplify.shp"

with arcpy.da.SearchCursor(warstwa, pola) as cursor:
    for row in cursor:
        fid, area, objetosc, wysokosc = row
        print(f"FID: {fid}, Pole: {area}, Wysokość: {wysokosc}, Objętość: {objetosc}")