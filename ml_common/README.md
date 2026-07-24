# ml_common

Shared Python utilities used by training and inference.

## Purpose

This package contains code that must be reused by both ML services, such as S3 storage clients and model bundle storage helpers.

## Current Modules

- `ml_common.storage` - S3-compatible storage configuration and client.
- `ml_common.artifacts` - helpers for uploading and downloading model bundles.

## Usage

The package is installed locally by `training` and `inference` as an editable path dependency.