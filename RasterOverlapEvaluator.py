# -*- coding: utf-8 -*-
"""RasterOverlapEvaluator.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/gist/jorgelizarazo94/1766497d446e33a6162e1c72145aa333/rasteroverlapevaluator.ipynb
"""

import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling
from rasterio.enums import Resampling
from shapely.geometry import box
from rasterio.mask import mask
from rasterio.io import MemoryFile

class RasterOverlapEvaluator:
    
    @staticmethod
    def read_raster(file_path):
        with rasterio.open(file_path) as src:
            data = src.read(1)
            transform = src.transform
            crs = src.crs
            return data, transform, crs

    @staticmethod
    def reproject_and_clip_raster(src_raster, src_transform, src_crs, ref_transform, ref_crs, ref_shape):
        # Create the destination transform and shape based on the reference raster
        dst_transform = ref_transform
        dst_shape = ref_shape
        
        # Create an empty array for the destination data
        dst_data = np.zeros(dst_shape, dtype=src_raster.dtype)
        
        # Reproject the source raster to match the reference raster
        reproject(
            source=src_raster,
            destination=dst_data,
            src_transform=src_transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=ref_crs,
            resampling=Resampling.nearest
        )
        
        # Calculate the bounds of the reference raster
        left, bottom = ref_transform * (0, ref_shape[0])
        right, top = ref_transform * (ref_shape[1], 0)
        ref_bounds = box(left, bottom, right, top)
        
        # Mask areas outside the reference raster's extent
        with MemoryFile() as memfile:
            with memfile.open(
                driver='GTiff', 
                height=dst_shape[0],
                width=dst_shape[1],
                count=1,
                dtype=dst_data.dtype,
                crs=ref_crs,
                transform=ref_transform
            ) as dst:
                dst.write(dst_data, 1)
                out_image, out_transform = mask(dst, [ref_bounds], crop=True, nodata=0)
        
        return out_image[0], out_transform

    @staticmethod
    def calculate_overlap(raster1, raster2):
        overlap_area = np.sum((raster1 > 0) & (raster2 > 0))
        total_area = np.sum(raster1 > 0) + np.sum(raster2 > 0) - overlap_area
        if total_area == 0:
            return 0
        return overlap_area / total_area

    @staticmethod
    def evaluate_model(student_raster_path, correct_raster_path):
        student_raster, student_transform, student_crs = RasterOverlapEvaluator.read_raster(student_raster_path)
        correct_raster, correct_transform, correct_crs = RasterOverlapEvaluator.read_raster(correct_raster_path)
        
        # Reproject and clip the student's raster to match the correct raster
        student_raster_aligned, _ = RasterOverlapEvaluator.reproject_and_clip_raster(
            student_raster, student_transform, student_crs, correct_transform, correct_crs, correct_raster.shape)
        
        overlap_percentage = RasterOverlapEvaluator.calculate_overlap(student_raster_aligned, correct_raster)
        return overlap_percentage * 100
    
    @staticmethod
    def evaluate_model_with_multiple_correct_rasters(student_raster_path, correct_raster_paths):
        student_raster, student_transform, student_crs = RasterOverlapEvaluator.read_raster(student_raster_path)
        
        max_overlap_percentage = 0
        best_match_index = -1
        
        for i, correct_raster_path in enumerate(correct_raster_paths):
            correct_raster, correct_transform, correct_crs = RasterOverlapEvaluator.read_raster(correct_raster_path)
            
            # Reproject and clip the student's raster to match the correct raster
            student_raster_aligned, _ = RasterOverlapEvaluator.reproject_and_clip_raster(
                student_raster, student_transform, student_crs, correct_transform, correct_crs, correct_raster.shape)
            
            overlap_percentage = RasterOverlapEvaluator.calculate_overlap(student_raster_aligned, correct_raster) * 100
            
            if overlap_percentage > max_overlap_percentage:
                max_overlap_percentage = overlap_percentage
                best_match_index = i
        
        return max_overlap_percentage, best_match_index


