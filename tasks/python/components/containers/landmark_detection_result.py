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
"""Landmark Detection Result data class."""

import dataclasses
from typing import Any, Optional

from mediapipe.tasks.cc.components.containers.proto import landmarks_detection_result_pb2
from mediapipe.tasks.python.components.containers import rect as rect_module
from mediapipe.tasks.python.components.containers import classification as classification_module
from mediapipe.tasks.python.components.containers import landmark as landmark_module
from mediapipe.tasks.python.core.optional_dependencies import doc_controls

_LandmarksDetectionResultProto = landmarks_detection_result_pb2.LandmarksDetectionResult
_NormalizedRect = rect_module.NormalizedRect
_ClassificationList = classification_module.ClassificationList
_NormalizedLandmarkList = landmark_module.NormalizedLandmarkList
_LandmarkList = landmark_module.LandmarkList


@dataclasses.dataclass
class LandmarksDetectionResult:
  """Represents the landmarks detection result.

  Attributes:
    landmarks : A `NormalizedLandmarkList` object.
    classifications : A `ClassificationList` object.
    world_landmarks : A `LandmarkList` object.
    rect : A `NormalizedRect` object.
  """

  landmarks: Optional[_NormalizedLandmarkList]
  classifications: Optional[_ClassificationList]
  world_landmarks: Optional[_LandmarkList]
  rect: _NormalizedRect

  @doc_controls.do_not_generate_docs
  def to_pb2(self) -> _LandmarksDetectionResultProto:
    """Generates a LandmarksDetectionResult protobuf object."""
    return _LandmarksDetectionResultProto(
      landmarks=self.landmarks.to_pb2(),
      classifications=self.classifications.to_pb2(),
      world_landmarks=self.world_landmarks.to_pb2(),
      rect=self.rect.to_pb2())

  @classmethod
  @doc_controls.do_not_generate_docs
  def create_from_pb2(
      cls,
      pb2_obj: _LandmarksDetectionResultProto
  ) -> 'LandmarksDetectionResult':
    """Creates a `LandmarksDetectionResult` object from the given protobuf
    object."""
    return LandmarksDetectionResult(
      landmarks=_NormalizedLandmarkList.create_from_pb2(pb2_obj.landmarks),
      classifications=_ClassificationList.create_from_pb2(
        pb2_obj.classifications),
      world_landmarks=_LandmarkList.create_from_pb2(pb2_obj.world_landmarks),
      rect=_NormalizedRect.create_from_pb2(pb2_obj.rect))

  def __eq__(self, other: Any) -> bool:
    """Checks if this object is equal to the given object.
    Args:
      other: The object to be compared with.
    Returns:
      True if the objects are equal.
    """
    if not isinstance(other, LandmarksDetectionResult):
      return False

    return self.to_pb2().__eq__(other.to_pb2())
