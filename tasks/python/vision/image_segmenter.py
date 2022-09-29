# Copyright 2022 The MediaPipe Authors. All Rights Reserved.
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
"""MediaPipe image segmenter task."""

import dataclasses
from typing import Callable, List, Mapping, Optional

from mediapipe.python import packet_creator
from mediapipe.python import packet_getter
from mediapipe.python._framework_bindings import image as image_module
from mediapipe.python._framework_bindings import packet as packet_module
from mediapipe.python._framework_bindings import task_runner as task_runner_module
from mediapipe.tasks.cc.vision.image_segmenter.proto import image_segmenter_options_pb2
from mediapipe.tasks.python.components.proto import segmenter_options
from mediapipe.tasks.python.core import base_options as base_options_module
from mediapipe.tasks.python.core import task_info as task_info_module
from mediapipe.tasks.python.core.optional_dependencies import doc_controls
from mediapipe.tasks.python.vision.core import base_vision_task_api
from mediapipe.tasks.python.vision.core import vision_task_running_mode as running_mode_module

_BaseOptions = base_options_module.BaseOptions
_ImageSegmenterOptionsProto = image_segmenter_options_pb2.ImageSegmenterOptions
_SegmenterOptions = segmenter_options.SegmenterOptions
_RunningMode = running_mode_module.VisionTaskRunningMode
_TaskInfo = task_info_module.TaskInfo
_TaskRunner = task_runner_module.TaskRunner

_SEGMENTATION_OUT_STREAM_NAME = 'segmented_mask_out'
_SEGMENTATION_TAG = 'GROUPED_SEGMENTATION'
_IMAGE_IN_STREAM_NAME = 'image_in'
_IMAGE_OUT_STREAM_NAME = 'image_out'
_IMAGE_TAG = 'IMAGE'
_TASK_GRAPH_NAME = 'mediapipe.tasks.vision.ImageSegmenterGraph'


@dataclasses.dataclass
class ImageSegmenterOptions:
  """Options for the image segmenter task.

  Attributes:
    base_options: Base options for the image segmenter task.
    running_mode: The running mode of the task. Default to the image mode.
      Image segmenter task has three running modes:
      1) The image mode for detecting objects on single image inputs.
      2) The video mode for detecting objects on the decoded frames of a video.
      3) The live stream mode for detecting objects on a live stream of input
         data, such as from camera.
    segmenter_options: Options for the image segmenter task.
    result_callback: The user-defined result callback for processing live stream
      data. The result callback should only be specified when the running mode
      is set to the live stream mode.
  """
  base_options: _BaseOptions
  running_mode: _RunningMode = _RunningMode.IMAGE
  segmenter_options: _SegmenterOptions = _SegmenterOptions()
  result_callback: Optional[
      Callable[[List[image_module.Image], image_module.Image, int],
               None]] = None

  @doc_controls.do_not_generate_docs
  def to_pb2(self) -> _ImageSegmenterOptionsProto:
    """Generates an ImageSegmenterOptions protobuf object."""
    base_options_proto = self.base_options.to_pb2()
    base_options_proto.use_stream_mode = False if self.running_mode == _RunningMode.IMAGE else True
    segmenter_options_proto = self.segmenter_options.to_pb2()

    return _ImageSegmenterOptionsProto(
        base_options=base_options_proto,
        segmenter_options=segmenter_options_proto
    )


class ImageSegmenter(base_vision_task_api.BaseVisionTaskApi):
  """Class that performs image segmentation on images."""

  @classmethod
  def create_from_model_path(cls, model_path: str) -> 'ImageSegmenter':
    """Creates an `ImageSegmenter` object from a TensorFlow Lite model and the default `ImageSegmenterOptions`.

    Note that the created `ImageSegmenter` instance is in image mode, for
    performing image segmentation on single image inputs.

    Args:
      model_path: Path to the model.

    Returns:
      `ImageSegmenter` object that's created from the model file and the default
      `ImageSegmenterOptions`.

    Raises:
      ValueError: If failed to create `ImageSegmenter` object from the provided
        file such as invalid file path.
      RuntimeError: If other types of error occurred.
    """
    base_options = _BaseOptions(model_asset_path=model_path)
    options = ImageSegmenterOptions(
        base_options=base_options, running_mode=_RunningMode.IMAGE)
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(cls,
                          options: ImageSegmenterOptions) -> 'ImageSegmenter':
    """Creates the `ImageSegmenter` object from image segmenter options.

    Args:
      options: Options for the image segmenter task.

    Returns:
      `ImageSegmenter` object that's created from `options`.

    Raises:
      ValueError: If failed to create `ImageSegmenter` object from
        `ImageSegmenterOptions` such as missing the model.
      RuntimeError: If other types of error occurred.
    """

    def packets_callback(output_packets: Mapping[str, packet_module.Packet]):
      if output_packets[_IMAGE_OUT_STREAM_NAME].is_empty():
        return
      segmentation_result = packet_getter.get_image_list(
          output_packets[_SEGMENTATION_OUT_STREAM_NAME])
      image = packet_getter.get_image(output_packets[_IMAGE_OUT_STREAM_NAME])
      timestamp = output_packets[_IMAGE_OUT_STREAM_NAME].timestamp
      options.result_callback(segmentation_result, image, timestamp)

    task_info = _TaskInfo(
        task_graph=_TASK_GRAPH_NAME,
        input_streams=[':'.join([_IMAGE_TAG, _IMAGE_IN_STREAM_NAME])],
        output_streams=[
            ':'.join([_SEGMENTATION_TAG, _SEGMENTATION_OUT_STREAM_NAME]),
            ':'.join([_IMAGE_TAG, _IMAGE_OUT_STREAM_NAME])
        ],
        task_options=options)
    return cls(
        task_info.generate_graph_config(
            enable_flow_limiting=options.running_mode ==
            _RunningMode.LIVE_STREAM), options.running_mode,
        packets_callback if options.result_callback else None)

  # TODO: Create an Image class for MediaPipe Tasks.
  def segment(self,
              image: image_module.Image) -> List[image_module.Image]:
    """Performs the actual segmentation task on the provided MediaPipe Image.

    Args:
      image: MediaPipe Image.

    Returns:
      A segmentation result object that contains a list of segmentation masks
      as images.

    Raises:
      ValueError: If any of the input arguments is invalid.
      RuntimeError: If object detection failed to run.
    """
    output_packets = self._process_image_data(
        {_IMAGE_IN_STREAM_NAME: packet_creator.create_image(image)})
    segmentation_result = packet_getter.get_image_list(
        output_packets[_SEGMENTATION_OUT_STREAM_NAME])
    return segmentation_result
