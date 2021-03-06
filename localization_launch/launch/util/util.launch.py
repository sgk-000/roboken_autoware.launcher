# Copyright 2020 Tier IV, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import launch
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LoadComposableNodes
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    crop_box_component = ComposableNode(
        package='pointcloud_preprocessor',
        plugin='pointcloud_preprocessor::CropBoxFilterComponent',
        name='crop_box_filter_measurement_range',
        remappings=[
            ('input', LaunchConfiguration('input_sensor_points_topic')),
            ('output',
             LaunchConfiguration('output_measurement_range_sensor_points_topic')),
        ],
        parameters=[{
            'input_frame': LaunchConfiguration('base_frame'),
            'output_frame': LaunchConfiguration('base_frame'),
            'min_x': -40.0,
            'max_x': 40.0,
            'min_y': -40.0,
            'max_y': 40.0,
            'min_z': -30.0,
            'max_z': 30.0,
            'negative': False,
        }],
        extra_arguments=[{
            'use_intra_process_comms': LaunchConfiguration('use_intra_process')
        }],
    )
    voxel_grid_downsample_component = ComposableNode(
        package='pointcloud_preprocessor',
        plugin='pointcloud_preprocessor::VoxelGridDownsampleFilterComponent',
        name='voxel_grid_downsample_filter',
        remappings=[
            ('input',
             LaunchConfiguration('input_sensor_points_topic')),
            ('output',
             LaunchConfiguration('output_voxel_grid_downsample_sensor_points_topic')),
        ],
        parameters=[{
            'voxel_size_x': 0.1,
            'voxel_size_y': 0.1,
            'voxel_size_z': 0.1,
        }],
        extra_arguments=[{
            'use_intra_process_comms': LaunchConfiguration('use_intra_process')
        }],
    )
    random_downsample_component = ComposableNode(
        package='pointcloud_preprocessor',
        plugin='pointcloud_preprocessor::VoxelGridDownsampleFilterComponent',
        name='random_downsample_filter',
        remappings=[
            ('input',
             LaunchConfiguration('output_voxel_grid_downsample_sensor_points_topic')),
            ('output',
             LaunchConfiguration('output_downsample_sensor_points_topic')),
        ],
        parameters=[{
            'sample_num': 1500,
        }],
        extra_arguments=[{
            'use_intra_process_comms': LaunchConfiguration('use_intra_process')
        }],
    )
    ransac_ground_filter_component = ComposableNode(
        package='pointcloud_preprocessor',
        plugin='pointcloud_preprocessor::RANSACGroundFilterComponent',
        name='ransac_ground_filter',
        remappings=[
            ('input', '/sensing/velodyne_lower/rectified/pointcloud'),
            ('output', '/sensing/velodyne_lower/no_ground/pointcloud'),
        ],
        parameters=[{
            'outlier_threshold': 0.1,
            'min_points': 400,
            'min_inliers': 200,
            'max_iterations': 50,
            'height_threshold': 0.3,
            'plane_slope_threshold': 10.0,
            'voxel_size_x': 0.1,
            'voxel_size_y': 0.1,
            'voxel_size_z': 0.1,
            'debug': False,
        }],
        extra_arguments=[{
            'use_intra_process_comms': LaunchConfiguration('use_intra_process')
        }],
    )

    composable_nodes = [crop_box_component,
                        voxel_grid_downsample_component,
                        random_downsample_component,
                        ransac_ground_filter_component]

    load_composable_nodes = LoadComposableNodes(
        condition=LaunchConfigurationNotEquals('container', ''),
        composable_node_descriptions=composable_nodes,
        target_container=LaunchConfiguration('container'),
    )

    util_container = ComposableNodeContainer(
            name='localization_util_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[crop_box_component,
                        voxel_grid_downsample_component,
                        random_downsample_component,
                        ransac_ground_filter_component],
            output='both',
    )

    if(LaunchConfiguration('logging')):
        return launch.LaunchDescription([util_container])
    else:
        return launch.LaunchDescription([load_composable_nodes])