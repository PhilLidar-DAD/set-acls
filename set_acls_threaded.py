#!/usr/bin/env python2

import argparse
import itertools
import logging
import multiprocessing
import os
import os.path
import subprocess
import sys

_version = '0.54.12'
print "_version:", _version
_logger = logging.getLogger()
_LOG_LEVEL = logging.DEBUG
_CONS_LOG_LEVEL = logging.INFO
WORKERS = 2
DEVNULL = open(os.devnull, 'w')
OWN_USR = 'datamanager'
OWN_GRP = 'data-managrs'
# ACLS[<dir acl>] = [<list of paths>]
ACLS = {
    '''
 group:admin-group:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/ADMIN'],

    '''
     group:dac-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC',
     '/mnt/geostorage/DAC/RAWDATA',
     '/mnt/geostorage/DAC/RAWDATA/*',
     '/mnt/geostorage/DAC/RAWDATA/*/*'],

    '''
     group:dac-all:r-x---a-R-c---:------:allow
 group:dpc-leaders:r-x---a-R-c---:fd----:allow
     group:dpc-lms:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC/RAWDATA/*/*/ALTM',
     '/mnt/geostorage/DAC/RAWDATA/*/*/NAV_FILES'],

    '''
     group:dac-all:rwxpD-aARWc---:fd----:allow
 group:dpc-leaders:r-x---a-R-c---:fd----:allow
     group:dpc-lms:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC/RAWDATA/*/*/ALTM/*',
     '/mnt/geostorage/DAC/RAWDATA/*/*/BASE_DATA',
     '/mnt/geostorage/DAC/RAWDATA/*/*/NAV_FILES/*'],

    '''
     group:dac-all:rwxpD-aARWc---:fd----:allow
 group:dpc-leaders:r-x---a-R-c---:fd----:allow
     group:dpc-lms:r-x---a-R-c---:fd----:allow
     group:dpc-arc:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC/RAWDATA/*/*/ARCHIVE'],

    '''
     group:dac-all:rwxpD-aARWc---:fd----:allow
 group:dpc-leaders:r-x---a-R-c---:fd----:allow
     group:dpc-lms:r-x---a-R-c---:fd----:allow
   group:dpc-terra:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC/RAWDATA/*/*/IMAGES'],

    '''
     group:dac-all:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAC/REPORTS',
     '/mnt/geostorage/DAC/WORKING'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAD'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DAD/Working'],

    '''
     group:dpc-all:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC'],

    '''
     group:dpc-all:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS',
     '/mnt/geostorage/DPC/LMS/Extra',
     '/mnt/geostorage/DPC/OTHER_PROJECTS'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
     group:dpc-arc:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/ARC',
     '/mnt/geostorage/DPC/ARC/LIDAR_DATA',
     '/mnt/geostorage/DPC/ARC/LIDAR_DATA/1m',
     '/mnt/geostorage/DPC/ARC/LIDAR_DATA/1m/*',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Status_Maps',
     '/mnt/geostorage/DPC/ARC/MOSAICKED_DEMs',
     '/mnt/geostorage/DPC/ARC/MOSAICKED_DEMs/*'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-arc:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/ARC/LIDAR_DATA/1m/*/*',
     '/mnt/geostorage/DPC/ARC/MOSAICKED_DEMs/*/*'
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Actual_Area',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Gap_Assessment',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/MKP_Area',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/QC_1m',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Reports',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Status_Maps/*',
     '/mnt/geostorage/DPC/ARC/MISCELLANEOUS/Swath_Coverage',
     '/mnt/geostorage/DPC/ARC/PHIL-LIDAR1_QC_SUCs',
     '/mnt/geostorage/DPC/ARC/PHIL-LIDAR1_1m'],

    '''
     group:dpc-all:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/DPC_BACKUP',
     '/mnt/geostorage/DPC/OTHER_PROJECTS/*',
     '/mnt/geostorage/DPC/WORKING'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-lms:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/AQUADX',
     '/mnt/geostorage/DPC/LMS/Areas/*/*/*/LASTools',
     '/mnt/geostorage/DPC/LMS/Areas/*/*/*/LMS',
     '/mnt/geostorage/DPC/LMS/CASI',
     '/mnt/geostorage/DPC/LMS/Calibration/*/*',
     '/mnt/geostorage/DPC/LMS/Extra/Base_station_coordinates',
     '/mnt/geostorage/DPC/LMS/Extra/DAC_status_report/*',
     '/mnt/geostorage/DPC/LMS/Extra/DAC_swath_lidar_coverage/*',
     '/mnt/geostorage/DPC/LMS/Extra/Installers',
     '/mnt/geostorage/DPC/LMS/Extra/Instrument_files/*',
     '/mnt/geostorage/DPC/LMS/Extra/LMS_processed_areas/*',
     '/mnt/geostorage/DPC/LMS/Extra/Problematic_flights',
     '/mnt/geostorage/DPC/LMS/Extra/Reports',
     '/mnt/geostorage/DPC/LMS/LISFlood'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
     group:dpc-lms:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Areas',
     '/mnt/geostorage/DPC/LMS/Areas/*',
     '/mnt/geostorage/DPC/LMS/Areas/*/*',
     '/mnt/geostorage/DPC/LMS/Areas/*/*/*'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-lms:rwxpD-aARWc---:fd----:allow
   group:dpc-terra:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Areas/*/*/*/POSPac',
     '/mnt/geostorage/DPC/LMS/Extra/DAC_flight_block_plan/*',
     '/mnt/geostorage/DPC/LMS/For_Terra/*'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
     group:dpc-lms:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Calibration',
     '/mnt/geostorage/DPC/LMS/Calibration/*',
     '/mnt/geostorage/DPC/LMS/Extra/DAC_status_report',
     '/mnt/geostorage/DPC/LMS/Extra/DAC_swath_lidar_coverage',
     '/mnt/geostorage/DPC/LMS/Extra/Instrument_files',
     '/mnt/geostorage/DPC/LMS/Extra/LMS_processed_areas'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
     group:dpc-lms:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Extra/DAC_flight_block_plan',
     '/mnt/geostorage/DPC/LMS/For_Terra'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
     group:dpc-lms:r-x---a-R-c---:------:allow
     group:dpc-arc:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Extra/For_qc_arc',
     '/mnt/geostorage/DPC/LMS/Extra/For_qc_arc/*'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-lms:rwxpD-aARWc---:fd----:allow
     group:dpc-arc:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/LMS/Extra/For_qc_arc/*/*'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:------:allow
     group:dpc-arc:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:------:allow
     group:dpc-arc:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/LAS_Tiles',
     '/mnt/geostorage/DPC/TERRA/LAS_Tiles/*',
     '/mnt/geostorage/DPC/TERRA/LAS_Tiles/*/*',
     '/mnt/geostorage/DPC/TERRA/Adjusted_LAZ_Tiles',
     '/mnt/geostorage/DPC/TERRA/Adjusted_LAZ_Tiles/*'],

    '''
 group:dpc-leaders:r-x---a-R-c---:fd----:allow
   group:dpc-terra:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/Airborne_Processing'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
   group:dpc-terra:rwxpD-aARWc---:fd----:allow
     group:dpc-arc:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/LAS_Tiles/*/*/ASCII',
     '/mnt/geostorage/DPC/TERRA/LAS_Tiles/*/*/DXF',
     '/mnt/geostorage/DPC/TERRA/LAS_Tiles/*/*/MKP'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
   group:dpc-terra:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/LAS_Tiles/*/*/LAS_FILES',
     '/mnt/geostorage/DPC/TERRA/Adjusted_LAZ_Tiles/*/*'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
   group:dpc-terra:rwxpD-aARWc---:fd----:allow
 group:fmc-leaders:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/Photos/*/*/*'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:------:allow
 group:fmc-leaders:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/Photos',
     '/mnt/geostorage/DPC/TERRA/Photos/*',
     '/mnt/geostorage/DPC/TERRA/Photos/*/*'],

    '''
 group:dpc-leaders:r-x---a-R-c---:------:allow
   group:dpc-terra:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DPC/TERRA/Adjusted_LAZ_Tiles',
     '/mnt/geostorage/DPC/TERRA/Adjusted_LAZ_Tiles/*'],

    '''
     group:dvc-all:r-x-Dda-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DVC/DVC.old',
     '/mnt/geostorage/DVC/Ground_Validation_Data'],

    '''
     group:dvc-all:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DVC',
     '/mnt/geostorage/DVC/RIVER_BASINS',
     '/mnt/geostorage/DVC/RIVER_BASINS/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/MMS',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM/AWLS',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM/Validation',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/Liquidations',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/DREAM',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/DREAM',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/DREAM',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Control_Points',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Raw_Data'],

    '''
     group:dvc-all:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/Established_Controls',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/MBES',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/MMS/Processed',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/MMS/Raw',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/Pictures',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/Processed_Data',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/Raw_Data',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/Shapefiles',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM/AWLS/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM/Controls_Use',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/DVC/DREAM/Validation/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Coordination_Letters',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Proposed_Survey_Area',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/Liquidations/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/Lodging',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/Van_Rental',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Quotations/DREAM/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Signed_Borrows_Form',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/Signed_Field_Plan',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Field_plans/DREAM/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/AutoCAD',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/AWLS',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Bathymetry_Profile',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Bridge_Cross-Section',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Cross-Section_With_Bathymetry',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/DREAM/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Graphs',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Maps',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Namria_Control_Points',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Static',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Final_data/Validation',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Control_Points/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Cross-Section',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Graphs',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Maps',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Profile',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Baseline_Processing',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Certification',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Narrative_Report',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Raw_Data/*',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Report',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Summary',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Outsource/*/Traverse_And_Level_Lines',
     '/mnt/geostorage/DVC/RIVER_BASINS/*/Reports',
     '/mnt/geostorage/DVC/WORKING'],

    '''
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE',
     '/mnt/geostorage/EXCHANGE/DPC'],

    '''
 group:admin-group:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/ADMIN'],

    '''
     group:dac-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DAC'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DAD'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-arc:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DPC/ARC'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
     group:dpc-lms:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DPC/LMS'],

    '''
     group:dpc-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DPC/MISCELLANEOUS'],

    '''
 group:dpc-leaders:rwxpD-aARWc---:fd----:allow
   group:dpc-terra:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DPC/TERRA'],

    '''
     group:dvc-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/DVC'],

    '''
 group:fmc-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/FMC'],

    '''
group:training-grp:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/EXCHANGE/TRAINING'],

    '''
     group:fmc-all:r-x-Dda-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FMC/Flood_Modelling.old'],

    '''
     group:fmc-all:r-x---a-R-c---:------:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FMC',
     '/mnt/geostorage/FMC/Automation',
     '/mnt/geostorage/FMC/Automation/*'
     '/mnt/geostorage/FMC/Automation/*/*',
     '/mnt/geostorage/FMC/FLO-2D',
     '/mnt/geostorage/FMC/FLO-2D/*',
     '/mnt/geostorage/FMC/FLO-2D/*/*',
     '/mnt/geostorage/FMC/FLO-2D/*/*/Output_data',
     '/mnt/geostorage/FMC/Flood_hazard_maps',
     '/mnt/geostorage/FMC/Flood_hazard_maps/*',
     '/mnt/geostorage/FMC/Flood_hazard_maps/*/*',
     '/mnt/geostorage/FMC/HEC-HMS',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/Output_data',
     '/mnt/geostorage/FMC/HEC-RAS',
     '/mnt/geostorage/FMC/HEC-RAS/Models',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*'
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/Output_data',
     '/mnt/geostorage/FMC/Reports'],

    '''
     group:fmc-all:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FMC/Automation/*/*/*',
     '/mnt/geostorage/FMC/FLO-2D/*/*/Archiving',
     '/mnt/geostorage/FMC/FLO-2D/*/*/FLO-2D_model',
     '/mnt/geostorage/FMC/FLO-2D/*/*/Input_data',
     '/mnt/geostorage/FMC/FLO-2D/*/*/Output_data/*',
     '/mnt/geostorage/FMC/FLO-2D/*/*/Report',
     '/mnt/geostorage/FMC/Flood_forecasting',
     '/mnt/geostorage/FMC/Flood_hazard_maps/*/*/*',
     '/mnt/geostorage/FMC/HEC-HMS/Documents',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/Archiving',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/HEC-HMS_model',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/Input_data',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/Output_data/*',
     '/mnt/geostorage/FMC/HEC-HMS/Models/*/*/Report',
     '/mnt/geostorage/FMC/HEC-RAS/Documents',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/Archiving',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/HEC-RAS_model',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/Input_data',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/Output_data/*',
     '/mnt/geostorage/FMC/HEC-RAS/Models/*/*/Report',
     '/mnt/geostorage/FMC/Other_Projects',
     '/mnt/geostorage/FMC/Reports/*',
     '/mnt/geostorage/FMC/Working'],

    '''
     group:fmc-all:rwxpD-aARWc---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/FMC'],

    '''
     group:dpc-all:r-x---a-R-c---:------:allow
group:gisdta-users:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/GISDATA',
     '/mnt/geostorage/GISDATA/DELINEATIONS',
     '/mnt/geostorage/GISDATA/DENR',
     '/mnt/geostorage/GISDATA/DENR/*',
     '/mnt/geostorage/GISDATA/FROM_WEB',
     '/mnt/geostorage/GISDATA/FROM_WEB/Elevation_Datasets',
     '/mnt/geostorage/GISDATA/GIZ_DATA',
     '/mnt/geostorage/GISDATA/SAR_DEMs'],

    '''
     group:dpc-all:rwxpD-aARWc---:fd----:allow
group:gisdta-users:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/GISDATA/DELINEATIONS/*',
     '/mnt/geostorage/GISDATA/DENR/*/*',
     '/mnt/geostorage/GISDATA/DOST',
     '/mnt/geostorage/GISDATA/FROM_WEB/Elevation_Datasets/*',
     '/mnt/geostorage/GISDATA/FROM_WEB/GADM_Admin_Boundaries',
     '/mnt/geostorage/GISDATA/FROM_WEB/Kompsat3',
     '/mnt/geostorage/GISDATA/FROM_WEB/OpenStreetMap',
     '/mnt/geostorage/GISDATA/GIZ_DATA/*',
     '/mnt/geostorage/GISDATA/GMMA',
     '/mnt/geostorage/GISDATA/RE_BUILD',
     '/mnt/geostorage/GISDATA/SAR_DEMs/*',
     '/mnt/geostorage/GISDATA/YOR_INFO_CENTER'],

    '''
group:houdas-group:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/HOUDAS'],

    '''
group:mancom-group:r-x---a-R-c---:------:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/MANCOM'],

    '''
group:mancom-group:rwxpD-aARWc---:fd----:allow
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/MANCOM/*'],

    '''
group:dream-groups:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/MISC'],

    '''
group:training-grp:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/TRAINING'],

    '''
group:training-grp:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/TRAINING/*'],

    '''
 group:urbnfld-grp:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/UrbanFlooding'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
   group:ftp-users:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
    group:pl1-sucs:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1',
     '/mnt/geostorage/FTP/PL1/*/*'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/.BASE_FOLDER'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
    user:adnu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/adnu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
    user:adzu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/adzu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
    user:clsu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/clsu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:cmu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/cmu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:csu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/csu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:isu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/isu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:mit-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/mit-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
 user:msu-iit-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/msu-iit-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:upb-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/upb-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:upc-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/upc-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
    user:uplb-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/uplb-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:upm-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/upm-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:usc-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/usc-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
     user:vsu-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/vsu-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
     group:dpc-all:r-x---a-R-c---:------:allow
     group:fmc-all:r-x---a-R-c---:------:allow
user:test-ftp-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/testfolder'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:r-x---a-R-c---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/DL/DAD'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
     group:dpc-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:r-x---a-R-c---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/DL/DPPC'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
     group:fmc-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:r-x---a-R-c---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/DL/FMC'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:rwxpD-aARWc---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/UL/DAD'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
     group:dpc-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:rwxpD-aARWc---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/UL/DPPC'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
     group:fmc-all:rwxpD-aARWc---:fd----:allow
    group:pl1-sucs:rwxpD-aARWc---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL1/*/UL/FMC'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2',
     '/mnt/geostorage/FTP/PL2/*/UL'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
    group:pl2-sucs:rwxpD-aARWc---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/*/UL/MISC'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/.BASE_FOLDER'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
   user:adnu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/adnu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
   user:adzu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/adzu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
   user:clsu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/clsu2-user'],


    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:cmu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/cmu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:csu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/csu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:isu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/isu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:mit2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/mit2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
   user:mmsu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/mmsu2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
user:msu-iit2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/msu-iit2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:upc2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/upc2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
   user:uplb2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/UPLB2'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:upm2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/upm2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:usc2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/usc2-user'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    user:vsu2-user:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/vsu2-user'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
    group:pl2-sucs:r-x---a-R-c---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/PL2/*/DL'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
  group:ftp-others:r-x---a-R-c---:------:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/Others'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
  group:ftp-others:r-x---a-R-c---:fd----:allow
         user:1001:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/FTP/Others/*'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
 group:phil-lidar2:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2',
     '/mnt/geostorage/Phil-LiDAR2/*/UL'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:r-x---a-R-c---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/DL'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
    group:coastmap:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/CoastMap'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
      group:frexls:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/FREXLS'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
      group:parmap:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/PARMap'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
         group:phd:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/PHD'],

    '''
     group:dad-all:r-x---a-R-c---:------:allow
       group:remap:r-x---a-R-c---:------:allow
    group:pl2-sucs:r-x---a-R-c---:------:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/REMap'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
   user:adnu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/ADNU2',
     '/mnt/geostorage/FTP/PL2/ADNU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
   user:adzu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/ADZU2',
     '/mnt/geostorage/FTP/PL2/ADZU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
   user:clsu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/CLSU2',
     '/mnt/geostorage/FTP/PL2/CLSU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:cmu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/CMU2',
     '/mnt/geostorage/FTP/PL2/CMU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:csu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/CSU2',
     '/mnt/geostorage/FTP/PL2/CSU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:isu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/ISU2',
     '/mnt/geostorage/FTP/PL2/ISU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:mit2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/MIT2',
     '/mnt/geostorage/FTP/PL2/MIT2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
   user:mmsu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/MMSU2',
     '/mnt/geostorage/FTP/PL2/MMSU2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
user:msu-iit2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/MSU-IIT2',
     '/mnt/geostorage/FTP/PL2/MSU-IIT2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:upc2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/UPC2',
     '/mnt/geostorage/FTP/PL2/UPC2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
   user:uplb2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/UPLB2',
     '/mnt/geostorage/FTP/PL2/UPLB2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:upm2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/UPM2',
     '/mnt/geostorage/FTP/PL2/UPM2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:usc2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/USC2',
     '/mnt/geostorage/FTP/PL2/USC2/UL/*'],

    '''
     group:dad-all:rwxpD-aARWc---:fd----:allow
 group:phil-lidar2:rwxpD-aARWc---:fd----:allow
    user:vsu2-user:rwxpD-aARWc---:fd----:allow
            owner@:rwxpDdaARWcCos:fd----:allow
            group@:rwxpDdaARWcCos:fd----:allow
         everyone@:rwxpDdaARWcCos:fd----:deny
''':
    ['/mnt/geostorage/Phil-LiDAR2/*/UL/VSU2',
     '/mnt/geostorage/FTP/PL2/VSU2/UL/*']
}


def _compare_tokens(fp_tokens, sp_tokens):
    match = 0
    for fp_token, sp_token in itertools.izip(fp_tokens, sp_tokens):
        if (sp_token == '*') or (fp_token == sp_token):
            match += 1
        else:
            break
    if match == len(sp_tokens) == len(fp_tokens):
        return 255
    else:
        return match


def _find_acl(full_path):
    full_path_tokens = full_path.split(os.sep)[1:]
    _logger.debug('full_path_tokens: %s', full_path_tokens)
    max_acl = ''
    max_sp = ''
    max_match = 0
    for acl, paths in sorted(ACLS.viewitems()):
        _logger.debug("#" * 80)
        _logger.debug("acl: {0}".format(acl))
        _logger.debug("paths: {0}".format(paths))
        for search_path in sorted(paths):
            search_path_tokens = search_path.split(os.sep)[1:]
            _logger.debug('search_path_tokens: %s', search_path_tokens)
            match = _compare_tokens(full_path_tokens, search_path_tokens)
            _logger.debug('match: %s', match)
            if match > max_match:
                max_match = match
                _logger.debug('max_match: %s', max_match)
                max_sp = search_path
                _logger.debug('max_sp: %s', max_sp)
                max_acl = acl
    return max_sp, max_acl


def _apply_acl(root, fd):
    # Ignore NewFolder.py, RenameFolder.py and DeleteFolder.py
    if fd in ['NewFolder.py', 'RenameFolder.py', 'DeleteFolder.py']:
        return None
    # Get full path
    full_path = os.path.abspath(os.path.join(root, fd))
    # Get matching acl
    search_path, dir_acl = _find_acl(full_path)
    _logger.info('%s : %s', full_path, search_path)
    # return None
    # chown file/dir
    subprocess.call(['chown', OWN_USR + ':' + OWN_GRP, full_path])
    # chmod file/dir
    if os.path.isdir(full_path):
        subprocess.call(['chmod', '770', full_path])
    else:
        subprocess.call(['chmod', '660', full_path])
    # Reset acls
    subprocess.call(['setfacl', '-b', full_path])
    # Delete existing acls
    while True:
        # subprocess.call(['getfacl', full_path])
        # Delete acl at position 0
        delete = subprocess.Popen(['setfacl', '-x', '0', full_path],
                                  stderr=subprocess.STDOUT,
                                  stdout=DEVNULL)
        if delete.wait() != 0:
            # Break if it can't delete anymore
            break
    # Set proper acl
    setfacl = subprocess.Popen(['setfacl', '-M', '-', full_path],
                               stdin=subprocess.PIPE)
    if os.path.isdir(full_path):
        setfacl.communicate(input=dir_acl)
    else:
        file_acl = dir_acl.replace(':fd', ':--')
        setfacl.communicate(input=file_acl)
    setfacl.wait()
    # Delete last acl
    last_acl_id = str(len(dir_acl.split('\n')) - 2)
    _logger.debug('%s %s', full_path, last_acl_id)
    subprocess.call(['setfacl', '-x', last_acl_id, full_path])


def _apply_acl_wrapper(args):
    return _apply_acl(*args)


def _setup_logging(args):
    # Setup logging
    _logger.setLevel(_LOG_LEVEL)
    formatter = logging.Formatter('[%(asctime)s] %(filename)s \
(%(levelname)s,%(lineno)d) : %(message)s')
    # Check verbosity for console
    if args.verbose >= 1:
        global _CONS_LOG_LEVEL
        _CONS_LOG_LEVEL = logging.DEBUG
    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_CONS_LOG_LEVEL)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)


def _parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version=_version)
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument('-fo', '--folder-only', action='store_true')
    parser.add_argument('start_path')
    args = parser.parse_args()
    return args

# Parse arguments
_logger.info('Parsing arguments...')
args = _parse_arguments()
#print args
# Setup logging
_setup_logging(args)
# Get start path
start_path = os.path.abspath(args.start_path)
if not os.path.isdir(start_path):
    _logger.error("%s doesn't exist! Exiting.", start_path)
    exit(1)
_logger.info('start_path: %s', start_path)
#print args.folder_only
#exit(1)
# List all dirs and files from start path
for root, dirs, files in os.walk(start_path):
    if args.folder_only:
        fds = ['.'] + dirs
    else:
        # For each file or dir
        fds = ['.'] + files + dirs
    # fds = ['.']
    # Initialize pool
    pool = multiprocessing.Pool(processes=WORKERS)
    params = zip(itertools.repeat(root, len(fds)), fds)
    # Apply acl
    pool.map(_apply_acl_wrapper, params)
    # Wait for worker threads to finish
    pool.close()
    pool.join()
    # break
