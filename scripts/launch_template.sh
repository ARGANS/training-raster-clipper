

# CHANGEME
TUTORIAL_STEP=NONE
# TUTORIAL_STEP=LOAD_FEATURE_POLYGONS
# TUTORIAL_STEP=LOAD_SENTINEL_DATA
# TUTORIAL_STEP=RASTERIZE_GEOJSON
# TUTORIAL_STEP=PRODUCE_CLIPS
# TUTORIAL_STEP=PERSIST_TO_CSV
# TUTORIAL_STEP=CLASSIFY_SENTINEL_DATA
# TUTORIAL_STEP=PERSIST_CLASSIFICATION_TO_RASTER
# TUTORIAL_STEP=ALL
# TUTORIAL_STEP=END

# CHANGEME
# POLYGONS_INPUT_PATH='resources/solution/polygons.geojson'
POLYGONS_INPUT_PATH='resources/your_work/polygons.geojson'

# CHANGEME
RASTER_INPUT_PATH='XXXXX.SAFE'

CSV_OUTPUT_PATH='generated/classified_points.csv'

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
    