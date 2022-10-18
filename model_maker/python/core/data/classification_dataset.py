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
"""Common classification dataset library."""

from typing import Any, Tuple

import tensorflow as tf

from mediapipe.model_maker.python.core.data import dataset as ds


class ClassificationDataset(ds.Dataset):
  """DataLoader for classification models."""

  def __init__(self, dataset: tf.data.Dataset, size: int, index_to_label: Any):
    super().__init__(dataset, size)
    self.index_to_label = index_to_label

  @property
  def num_classes(self: ds._DatasetT) -> int:
    return len(self.index_to_label)

  def split(self: ds._DatasetT,
            fraction: float) -> Tuple[ds._DatasetT, ds._DatasetT]:
    """Splits dataset into two sub-datasets with the given fraction.

    Primarily used for splitting the data set into training and testing sets.

    Args:
      fraction: float, demonstrates the fraction of the first returned
        subdataset in the original data.

    Returns:
      The splitted two sub datasets.
    """
    return self._split(fraction, self.index_to_label)
