## COPY ME and suffix with your username

# CHANGEME
TUTORIAL_STEP=END
# TUTORIAL_STEP=NONE
# TUTORIAL_STEP=PERSIST_TO_CSV
# TUTORIAL_STEP=LOAD_FEATURE_POLYGONS

# CHANGEME
POLYGONS_INPUT_PATH='resources/solution/polygons.geojson'

# CHANGEME
RASTER_INPUT_PATH='D:/PROFILS/ESCHALK/DOWNLOADS/S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958/S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE'

CSV_OUTPUT_PATH='generated\classified_points.csv'

RASTER_OUTPUT_PATH='generated/sklearn_raster.tiff'
poetry run python ./src/training_raster_clipper/main.py \
    --raster_input_path $RASTER_INPUT_PATH \
    --polygons_input_path $POLYGONS_INPUT_PATH \
    --csv_output_path $CSV_OUTPUT_PATH \
    --raster_output_path $RASTER_OUTPUT_PATH \
    --tutorial_step $TUTORIAL_STEP \
    --verbose \
    --figures \
    --cheat # cheat mode, to use the solutions
