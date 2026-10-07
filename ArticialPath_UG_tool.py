
#####################-------Create Artificial Path inside the Polygon-------####################
#####################-------Created by: Unisha Ghimire-------####################


###----If you have any question regarding the toolbox, contact Unisha, email: unisha.ghimire@merrick.com----###

###This toolbox create an Artificial Path that connect the inflow streamline/s to outflow streamline inside a Polygon.
###Please recheck the output feature layer to make sure the Artificial path created is following all EDH criteria and topological rule.


import arcpy

from arcpy import env


##overwrite the output
env.overwriteOutput=True



## todo: main syntax starts
#
# ##replace the values with parameters
inputfc1 = arcpy.GetParameterAsText(0)
inputfc2 = arcpy.GetParameterAsText(1)
outputfc1 = arcpy.GetParameterAsText(2)


#todo 1: Eliminate Polygon Part

elim_poly = "Polygons_T12_EliminatePolygo_python"

arcpy.management.EliminatePolygonPart(
    in_features=inputfc1,
    out_feature_class=elim_poly,
    condition="PERCENT",
    part_area="0 SquareMeters",
    part_area_percent=50,
    part_option="ANY"
)


#todo 2: Collapse Hydro Polygon

out_line_feature_class = "EliminatePolygo_python_chpHydroLine"

arcpy.cartography.CollapseHydroPolygon(
    in_features=elim_poly,
    out_line_feature_class=out_line_feature_class,
    merge_adjacent_input_polygons="NO_MERGE",
    connecting_features=inputfc2,
    collapse_width="0 Meters",
    collapse_width_tolerance=20,
    minimum_length="0 Meters",
    taper_length_percentage=50,
    out_poly_feature_class=None
)

# ============================================================
# todo 2.1: Delete unnecessary lines
# ============================================================

# Select features where:
# InLine_ID = -1
# AND InLine_FID = -1
# AND MIN_Width = 0

where_clause = "InLine_ID = -1 AND InLine_FID = -1 AND MIN_Width = 0"


# ----------------------------
# Make temporary feature layer
# ----------------------------

arcpy.management.MakeFeatureLayer(
    out_line_feature_class,
    "out_line_layer"
)


# ----------------------------
# Select by attribute
# ----------------------------

arcpy.management.SelectLayerByAttribute(
    "out_line_layer",
    "NEW_SELECTION",
    where_clause
)


# ----------------------------
# Get selected ObjectIDs
# ----------------------------

selected_oids = []

fields = ["OID@"]

cursor = arcpy.da.SearchCursor(
    "out_line_layer",
    fields
)

for row in cursor:
    selected_oids.append(row[0])

del cursor


# ----------------------------
# Delete selected features
# ----------------------------

cursor = arcpy.da.UpdateCursor(
    out_line_feature_class,
    ["OID@"]
)

for row in cursor:

    if row[0] in selected_oids:
        cursor.deleteRow()

del cursor


# ----------------------------
# Delete temporary layer
# ----------------------------

arcpy.management.Delete("out_line_layer")


# ----------------------------
# Print result
# ----------------------------

print("Selected features deleted.")
print("Number of features deleted: " + str(len(selected_oids)))

# ============================================================
# Merge all lines into one multipart feature
# ============================================================

merged_line = "EliminatePolygo_python_chpHydroLine_Merged"

arcpy.management.Dissolve(
    in_features=out_line_feature_class,
    out_feature_class=merged_line
)

# ============================================================
# Explode multipart into singlepart features
# ============================================================

singlepart_line = "EliminatePolygo_python_chpHydroLine_SinglePart"

arcpy.management.MultipartToSinglepart(
    in_features=merged_line,
    out_feature_class=singlepart_line
)

# ============================================================
# Simplify final hydro line
# ============================================================

arcpy.cartography.SimplifyLine(
    in_features=singlepart_line,
    out_feature_class=outputfc1,
    algorithm="POINT_REMOVE",
    tolerance="5 Meters",
    error_resolving_option="FLAG_ERRORS",
    collapsed_point_option="KEEP_COLLAPSED_POINTS",
    error_checking_option="NO_CHECK",
    in_barriers=inputfc1,
    error_option="RESOLVE_ERRORS"
)

print("Lines simplified successfully.")


# ============================================================
# Clean up temporary feature classes
# ============================================================

arcpy.management.Delete(out_line_feature_class)
arcpy.management.Delete(merged_line)
arcpy.management.Delete(singlepart_line)

print("Temporary feature classes deleted.")


# ============================================================
# Set output parameter
# ============================================================

arcpy.SetParameterAsText(2, outputfc1)

