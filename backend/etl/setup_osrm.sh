#!/usr/bin/env bash
# setup_osrm.sh — One-time OSRM data preparation for US road network
#
# Downloads US OSM data, filters to roads only, and prepares OSRM files
# using the MLD algorithm. All data goes to the SSD.
#
# Prerequisites:
#   brew install osmium-tool
#   docker pull osrm/osrm-backend:latest
#
# Usage:
#   bash backend/etl/setup_osrm.sh

set -euo pipefail

DATA_DIR="/Volumes/Anand-SSD/healthcare-data"
OSRM_DIR="${DATA_DIR}/osrm"
PBF_URL="https://download.geofabrik.de/north-america/us-latest.osm.pbf"
PBF_FILE="${DATA_DIR}/raw/us-latest.osm.pbf"
ROADS_PBF="${OSRM_DIR}/us-roads.osm.pbf"
OSRM_IMAGE="osrm/osrm-backend:latest"

mkdir -p "${OSRM_DIR}"

# ─── Step 1: Download US PBF ─────────────────────────────────────────
if [ -f "${PBF_FILE}" ]; then
    echo "PBF already exists: ${PBF_FILE}"
    echo "  Size: $(du -h "${PBF_FILE}" | cut -f1)"
else
    echo "Downloading US PBF from Geofabrik (~9GB)..."
    curl -L -o "${PBF_FILE}" "${PBF_URL}"
    echo "  Downloaded: $(du -h "${PBF_FILE}" | cut -f1)"
fi

# ─── Step 2: Filter to roads only ────────────────────────────────────
# This is critical for 16GB RAM Macs — full US extract needs ~16-20GB
if [ -f "${ROADS_PBF}" ]; then
    echo "Filtered roads PBF already exists: ${ROADS_PBF}"
    echo "  Size: $(du -h "${ROADS_PBF}" | cut -f1)"
else
    echo "Filtering PBF to roads only (osmium tags-filter)..."
    osmium tags-filter "${PBF_FILE}" \
        w/highway \
        -o "${ROADS_PBF}" \
        --overwrite
    echo "  Filtered: $(du -h "${ROADS_PBF}" | cut -f1)"
fi

# ─── Step 3: OSRM Extract ────────────────────────────────────────────
if [ -f "${OSRM_DIR}/us-roads.osrm" ]; then
    echo "OSRM extract already exists, skipping..."
else
    echo "Running OSRM extract (this takes 10-20 minutes)..."
    docker run --rm -t \
        -v "${OSRM_DIR}:/data" \
        "${OSRM_IMAGE}" \
        osrm-extract -p /opt/car.lua /data/us-roads.osm.pbf
fi

# ─── Step 4: OSRM Partition ──────────────────────────────────────────
if [ -f "${OSRM_DIR}/us-roads.osrm.partition" ]; then
    echo "OSRM partition already exists, skipping..."
else
    echo "Running OSRM partition..."
    docker run --rm -t \
        -v "${OSRM_DIR}:/data" \
        "${OSRM_IMAGE}" \
        osrm-partition /data/us-roads.osrm
fi

# ─── Step 5: OSRM Customize ──────────────────────────────────────────
if [ -f "${OSRM_DIR}/us-roads.osrm.cell_metrics" ]; then
    echo "OSRM customize already exists, skipping..."
else
    echo "Running OSRM customize..."
    docker run --rm -t \
        -v "${OSRM_DIR}:/data" \
        "${OSRM_IMAGE}" \
        osrm-customize /data/us-roads.osrm
fi

echo ""
echo "=== OSRM Setup Complete ==="
echo "Data directory: ${OSRM_DIR}"
echo ""
echo "To start the routing server:"
echo "  docker compose up osrm"
echo ""
echo "To test:"
echo "  curl 'http://localhost:5000/route/v1/driving/-73.98,40.74;-118.24,34.05'"
