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
"""Utilities for keras models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Text, Tuple, Union

# Dependency imports

import numpy as np
import tensorflow as tf

# resources dependency
from mediapipe.model_maker.python.core.data import dataset
from mediapipe.model_maker.python.core.utils import quantization

DEFAULT_SCALE, DEFAULT_ZERO_POINT = 0, 0
ESTIMITED_STEPS_PER_EPOCH = 1000


def load_keras_model(model_path: str,
                     compile_on_load: bool = False) -> tf.keras.Model:
  """Loads a tensorflow Keras model from file and returns the Keras model.

  Args:
    model_path: Relative path to a directory containing model data, such as
      <parent_path>/saved_model/.
    compile_on_load: Whether the model should be compiled while loading. If
      False, the model returned has to be compiled with the appropriate loss
      function and custom metrics before running for inference on a test
      dataset.

  Returns:
    A tensorflow Keras model.
  """
  # Extract the file path before mediapipe/ as the `base_dir`. By joining it
  # with the `model_path` which defines the relative path under mediapipe/, it
  # yields to the aboslution path of the model files directory.
  cwd = os.path.dirname(__file__)
  base_dir = cwd[:cwd.rfind('mediapipe')]
  absolute_path = os.path.join(base_dir, model_path)
  return tf.keras.models.load_model(
      absolute_path, custom_objects={'tf': tf}, compile=compile_on_load)


def get_steps_per_epoch(steps_per_epoch: Optional[int] = None,
                        batch_size: Optional[int] = None,
                        train_data: Optional[dataset.Dataset] = None) -> int:
  """Gets the estimated training steps per epoch.

  1. If `steps_per_epoch` is set, returns `steps_per_epoch` directly.
  2. Else if we can get the length of training data successfully, returns
     `train_data_length // batch_size`.

  Args:
    steps_per_epoch: int, training steps per epoch.
    batch_size: int, batch size.
    train_data: training data.

  Returns:
    Estimated training steps per epoch.

  Raises:
    ValueError: if both steps_per_epoch and train_data are not set.
  """
  if steps_per_epoch is not None:
    # steps_per_epoch is set by users manually.
    return steps_per_epoch
  else:
    if train_data is None:
      raise ValueError('Input train_data cannot be None.')
    # Gets the steps by the length of the training data.
    return len(train_data) // batch_size


def export_tflite(
    model: tf.keras.Model,
    tflite_filepath: str,
    quantization_config: Optional[quantization.QuantizationConfig] = None,
    supported_ops: Tuple[tf.lite.OpsSet,
                         ...] = (tf.lite.OpsSet.TFLITE_BUILTINS,),
    preprocess: Optional[Callable[..., bool]] = None):
  """Converts the model to tflite format and saves it.

  Args:
    model: model to be converted to tflite.
    tflite_filepath: File path to save tflite model.
    quantization_config: Configuration for post-training quantization.
    supported_ops: A list of supported ops in the converted TFLite file.
    preprocess: A callable to preprocess the representative dataset for
        quantization. The callable takes three arguments in order: feature,
        label, and is_training.
  """
  if tflite_filepath is None:
    raise ValueError(
        "TFLite filepath couldn't be None when exporting to tflite.")

  with tempfile.TemporaryDirectory() as temp_dir:
    save_path = os.path.join(temp_dir, 'saved_model')
    model.save(save_path, include_optimizer=False, save_format='tf')
    converter = tf.lite.TFLiteConverter.from_saved_model(save_path)

    if quantization_config:
      converter = quantization_config.set_converter_with_quantization(
          converter, preprocess=preprocess)

    converter.target_spec.supported_ops = supported_ops
    tflite_model = converter.convert()

  with tf.io.gfile.GFile(tflite_filepath, 'wb') as f:
    f.write(tflite_model)


class WarmUp(tf.keras.optimizers.schedules.LearningRateSchedule):
  """Applies a warmup schedule on a given learning rate decay schedule."""

  def __init__(self,
               initial_learning_rate: float,
               decay_schedule_fn: Callable[[Any], Any],
               warmup_steps: int,
               name: Optional[str] = None):
    """Initializes a new instance of the `WarmUp` class.

    Args:
      initial_learning_rate: learning rate after the warmup.
      decay_schedule_fn: A function maps step to learning rate. Will be applied
        for values of step larger than 'warmup_steps'.
      warmup_steps: Number of steps to do warmup for.
      name: TF namescope under which to perform the learning rate calculation.
    """
    super(WarmUp, self).__init__()
    self.initial_learning_rate = initial_learning_rate
    self.warmup_steps = warmup_steps
    self.decay_schedule_fn = decay_schedule_fn
    self.name = name

  def __call__(self, step: Union[int, tf.Tensor]) -> tf.Tensor:
    with tf.name_scope(self.name or 'WarmUp') as name:
      # Implements linear warmup. i.e., if global_step < warmup_steps, the
      # learning rate will be `global_step/num_warmup_steps * init_lr`.
      global_step_float = tf.cast(step, tf.float32)
      warmup_steps_float = tf.cast(self.warmup_steps, tf.float32)
      warmup_percent_done = global_step_float / warmup_steps_float
      warmup_learning_rate = self.initial_learning_rate * warmup_percent_done
      return tf.cond(
          global_step_float < warmup_steps_float,
          lambda: warmup_learning_rate,
          lambda: self.decay_schedule_fn(step),
          name=name)

  def get_config(self) -> Dict[Text, Any]:
    return {
        'initial_learning_rate': self.initial_learning_rate,
        'decay_schedule_fn': self.decay_schedule_fn,
        'warmup_steps': self.warmup_steps,
        'name': self.name
    }


class LiteRunner(object):
  """A runner to do inference with the TFLite model."""

  def __init__(self, tflite_filepath: str):
    """Initializes Lite runner with tflite model file.

    Args:
      tflite_filepath: File path to the TFLite model.
    """
    with tf.io.gfile.GFile(tflite_filepath, 'rb') as f:
      tflite_model = f.read()
    self.interpreter = tf.lite.Interpreter(model_content=tflite_model)
    self.interpreter.allocate_tensors()
    self.input_details = self.interpreter.get_input_details()
    self.output_details = self.interpreter.get_output_details()

  def run(
      self, input_tensors: Union[List[tf.Tensor], Dict[str, tf.Tensor]]
  ) -> Union[List[tf.Tensor], tf.Tensor]:
    """Runs inference with the TFLite model.

    Args:
      input_tensors: List / Dict of the input tensors of the TFLite model. The
        order should be the same as the keras model if it's a list. It also
        accepts tensor directly if the model has only 1 input.

    Returns:
      List of the output tensors for multi-output models, otherwise just
        the output tensor. The order should be the same as the keras model.
    """

    if not isinstance(input_tensors, list) and not isinstance(
        input_tensors, dict):
      input_tensors = [input_tensors]

    interpreter = self.interpreter

    # Reshape inputs
    for i, input_detail in enumerate(self.input_details):
      input_tensor = _get_input_tensor(
          input_tensors=input_tensors,
          input_details=self.input_details,
          index=i)
      interpreter.resize_tensor_input(
          input_index=input_detail['index'], tensor_size=input_tensor.shape)
    interpreter.allocate_tensors()

    # Feed input to the interpreter
    for i, input_detail in enumerate(self.input_details):
      input_tensor = _get_input_tensor(
          input_tensors=input_tensors,
          input_details=self.input_details,
          index=i)
      if input_detail['quantization'] != (DEFAULT_SCALE, DEFAULT_ZERO_POINT):
        # Quantize the input
        scale, zero_point = input_detail['quantization']
        input_tensor = input_tensor / scale + zero_point
        input_tensor = np.array(input_tensor, dtype=input_detail['dtype'])
      interpreter.set_tensor(input_detail['index'], input_tensor)

    interpreter.invoke()

    output_tensors = []
    for output_detail in self.output_details:
      output_tensor = interpreter.get_tensor(output_detail['index'])
      if output_detail['quantization'] != (DEFAULT_SCALE, DEFAULT_ZERO_POINT):
        # Dequantize the output
        scale, zero_point = output_detail['quantization']
        output_tensor = output_tensor.astype(np.float32)
        output_tensor = (output_tensor - zero_point) * scale
      output_tensors.append(output_tensor)

    if len(output_tensors) == 1:
      return output_tensors[0]
    return output_tensors


def get_lite_runner(tflite_filepath: str) -> 'LiteRunner':
  """Returns a `LiteRunner` from file path to TFLite model."""
  lite_runner = LiteRunner(tflite_filepath)
  return lite_runner


def _get_input_tensor(input_tensors: Union[List[tf.Tensor], Dict[str,
                                                                 tf.Tensor]],
                      input_details: Dict[str, Any], index: int) -> tf.Tensor:
  """Returns input tensor in `input_tensors` that maps `input_detail[i]`."""
  if isinstance(input_tensors, dict):
    # Gets the mapped input tensor.
    input_detail = input_details
    for input_tensor_name, input_tensor in input_tensors.items():
      if input_tensor_name in input_detail['name']:
        return input_tensor
    raise ValueError('Input tensors don\'t contains a tensor that mapped the '
                     'input detail %s' % str(input_detail))
  else:
    return input_tensors[index]
