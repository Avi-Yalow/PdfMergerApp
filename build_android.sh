#!/usr/bin/env bash
# Build the Android APK using Buildozer.
#
# Prerequisites (Ubuntu/Debian – tested on 22.04):
#   sudo apt-get update && sudo apt-get install -y \
#       git zip unzip openjdk-17-jdk python3-pip \
#       autoconf libtool pkg-config zlib1g-dev \
#       libncurses5-dev libncursesw5-dev libtinfo5 \
#       cmake libffi-dev libssl-dev
#
#   pip install buildozer
#
# Usage:
#   bash build_android.sh          # builds a debug APK
#   bash build_android.sh release  # builds a release APK (requires keystore)

set -e

BUILD_TYPE="${1:-debug}"

if ! command -v buildozer &> /dev/null; then
    echo "Error: buildozer is not installed."
    echo "Install it with:  pip install buildozer"
    exit 1
fi

echo "=========================================="
echo "  PDF Merger & Splitter – Android build"
echo "  Build type: ${BUILD_TYPE}"
echo "=========================================="

buildozer android "${BUILD_TYPE}"

echo ""
echo "Build complete!  APK is in the bin/ directory."
