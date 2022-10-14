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
"""Image classifier dataset library."""

import os
import random

from typing import List, Optional, Tuple
import tensorflow as tf
import tensorflow_datasets as tfds

from mediapipe.model_maker.python.core.data import classification_dataset


def _load_image(path: str) -> tf.Tensor:
  """Loads image."""
  image_raw = tf.io.read_file(path)
  image_tensor = tf.cond(
      tf.image.is_jpeg(image_raw),
      lambda: tf.image.decode_jpeg(image_raw, channels=3),
      lambda: tf.image.decode_png(image_raw, channels=3))
  return image_tensor


def _create_data(
    name: str, data: tf.data.Dataset, info: tfds.core.DatasetInfo,
    label_names: List[str]
) -> Optional[classification_dataset.ClassificationDataset]:
  """Creates a Dataset object from tfds data."""
  if name not in data:
    return None
  data = data[name]
  data = data.map(lambda a: (a['image'], a['label']))
  size = info.splits[name].num_examples
  return Dataset(data, size, label_names)


class Dataset(classification_dataset.ClassificationDataset):
  """Dataset library for image classifier."""

  @classmethod
  def from_folder(
      cls,
      dirname: str,
      shuffle: bool = True) -> classification_dataset.ClassificationDataset:
    """Loads images and labels from the given directory.

    Assume the image data of the same label are in the same subdirectory.

    Args:
      dirname: Name of the directory containing the data files.
      shuffle: boolean, if shuffle, random shuffle data.

    Returns:
      Dataset containing images and labels and other related info.

    Raises:
      ValueError: if the input data directory is empty.
    """
    data_root = os.path.abspath(dirname)

    # Assumes the image data of the same label are in the same subdirectory,
    # gets image path and label names.
    all_image_paths = list(tf.io.gfile.glob(data_root + r'/*/*'))
    all_image_size = len(all_image_paths)
    if all_image_size == 0:
      raise ValueError('Image size is zero')

    if shuffle:
      # Random shuffle data.
      random.shuffle(all_image_paths)

    label_names = sorted(
        name for name in os.listdir(data_root)
        if os.path.isdir(os.path.join(data_root, name)))
    all_label_size = len(label_names)
    label_to_index = dict(
        (name, index) for index, name in enumerate(label_names))
    all_image_labels = [
        label_to_index[os.path.basename(os.path.dirname(path))]
        for path in all_image_paths
    ]

    path_ds = tf.data.Dataset.from_tensor_slices(all_image_paths)

    autotune = tf.data.AUTOTUNE
    image_ds = path_ds.map(_load_image, num_parallel_calls=autotune)

    # Loads label.
    label_ds = tf.data.Dataset.from_tensor_slices(
        tf.cast(all_image_labels, tf.int64))

    # Creates  a dataset if (image, label) pairs.
    image_label_ds = tf.data.Dataset.zip((image_ds, label_ds))

    tf.compat.v1.logging.info(
        'Load image with size: %d, num_label: %d, labels: %s.', all_image_size,
        all_label_size, ', '.join(label_names))
    return Dataset(image_label_ds, all_image_size, label_names)

  @classmethod
  def load_tf_dataset(
      cls, name: str
  ) -> Tuple[Optional[classification_dataset.ClassificationDataset],
             Optional[classification_dataset.ClassificationDataset],
             Optional[classification_dataset.ClassificationDataset]]:
    """Loads data from tensorflow_datasets.

    Args:
      name: the registered name of the tfds.core.DatasetBuilder. Refer to the
        documentation of tfds.load for more details.

    Returns:
      A tuple of Datasets for the train/validation/test.

    Raises:
      ValueError: if the input tf dataset does not have train/validation/test
      labels.
    """
    data, info = tfds.load(name, with_info=True)
    if 'label' not in info.features:
      raise ValueError('info.features need to contain \'label\' key.')
    label_names = info.features['label'].names

    train_data = _create_data('train', data, info, label_names)
    validation_data = _create_data('validation', data, info, label_names)
    test_data = _create_data('test', data, info, label_names)
    return train_data, validation_data, test_data
