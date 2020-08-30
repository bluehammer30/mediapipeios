# Copyright 2020 The MediaPipe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for mediapipe.python._framework_bindings.image_frame."""

import random
from absl.testing import absltest
import cv2
import mediapipe as mp
import numpy as np
import PIL.Image


# TODO: Add unit tests specifically for memory management.
class ImageFrameTest(absltest.TestCase):

  def testCreateImageFrameFromGrayCvMat(self):
    w, h = random.randrange(3, 100), random.randrange(3, 100)
    mat = cv2.cvtColor(
        np.random.randint(2**8 - 1, size=(h, w, 3), dtype=np.uint8),
        cv2.COLOR_RGB2GRAY)
    mat[2, 2] = 42
    image_frame = mp.ImageFrame(image_format=mp.ImageFormat.GRAY8, data=mat)
    self.assertTrue(np.array_equal(mat, image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'index dimension mismatch'):
      print(image_frame[w, h, 1])
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[w, h])
    self.assertEqual(42, image_frame[2, 2])

  def testCreateImageFrameFromRgbCvMat(self):
    w, h, channels = random.randrange(3, 100), random.randrange(3, 100), 3
    mat = cv2.cvtColor(
        np.random.randint(2**8 - 1, size=(h, w, channels), dtype=np.uint8),
        cv2.COLOR_RGB2BGR)
    mat[2, 2, 1] = 42
    image_frame = mp.ImageFrame(image_format=mp.ImageFormat.SRGB, data=mat)
    self.assertTrue(np.array_equal(mat, image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[w, h, channels])
    self.assertEqual(42, image_frame[2, 2, 1])

  def testCreateImageFrameFromRgb48CvMat(self):
    w, h, channels = random.randrange(3, 100), random.randrange(3, 100), 3
    mat = cv2.cvtColor(
        np.random.randint(2**16 - 1, size=(h, w, channels), dtype=np.uint16),
        cv2.COLOR_RGB2BGR)
    mat[2, 2, 1] = 42
    image_frame = mp.ImageFrame(image_format=mp.ImageFormat.SRGB48, data=mat)
    self.assertTrue(np.array_equal(mat, image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[w, h, channels])
    self.assertEqual(42, image_frame[2, 2, 1])

  def testCreateImageFrameFromGrayPilImage(self):
    w, h = random.randrange(3, 100), random.randrange(3, 100)
    img = PIL.Image.fromarray(
        np.random.randint(2**8 - 1, size=(h, w), dtype=np.uint8), 'L')
    image_frame = mp.ImageFrame(
        image_format=mp.ImageFormat.GRAY8, data=np.asarray(img))
    self.assertTrue(np.array_equal(np.asarray(img), image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'index dimension mismatch'):
      print(image_frame[w, h, 1])
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[w, h])

  def testCreateImageFrameFromRgbPilImage(self):
    w, h, channels = random.randrange(3, 100), random.randrange(3, 100), 3
    img = PIL.Image.fromarray(
        np.random.randint(2**8 - 1, size=(h, w, channels), dtype=np.uint8),
        'RGB')
    image_frame = mp.ImageFrame(
        image_format=mp.ImageFormat.SRGB, data=np.asarray(img))
    self.assertTrue(np.array_equal(np.asarray(img), image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[w, h, channels])

  def testCreateImageFrameFromRgba64PilImage(self):
    w, h, channels = random.randrange(3, 100), random.randrange(3, 100), 4
    img = PIL.Image.fromarray(
        np.random.randint(2**16 - 1, size=(h, w, channels), dtype=np.uint16),
        'RGBA')
    image_frame = mp.ImageFrame(
        image_format=mp.ImageFormat.SRGBA64,
        data=np.asarray(img, dtype=np.uint16))
    self.assertTrue(np.array_equal(np.asarray(img), image_frame.numpy_view()))
    with self.assertRaisesRegex(IndexError, 'out of bounds'):
      print(image_frame[1000, 1000, 1000])

  def testImageFrameNumbyView(self):
    w, h, channels = random.randrange(3, 100), random.randrange(3, 100), 3
    mat = cv2.cvtColor(
        np.random.randint(2**8 - 1, size=(h, w, channels), dtype=np.uint8),
        cv2.COLOR_RGB2BGR)
    image_frame = mp.ImageFrame(image_format=mp.ImageFormat.SRGB, data=mat)
    output_ndarray = image_frame.numpy_view()
    self.assertTrue(np.array_equal(mat, image_frame.numpy_view()))
    # The output of numpy_view() is a reference to the internal data and it's
    # unwritable after creation.
    with self.assertRaisesRegex(ValueError,
                                'assignment destination is read-only'):
      output_ndarray[0, 0, 0] = 0
    copied_ndarray = np.copy(output_ndarray)
    copied_ndarray[0, 0, 0] = 0

  def testCroppedGray8Image(self):
    w, h = random.randrange(20, 100), random.randrange(20, 100)
    channels, offset = 3, 10
    mat = cv2.cvtColor(
        np.random.randint(2**8 - 1, size=(h, w, channels), dtype=np.uint8),
        cv2.COLOR_RGB2GRAY)
    image_frame = mp.ImageFrame(
        image_format=mp.ImageFormat.GRAY8,
        data=mat[offset:-offset, offset:-offset])
    self.assertTrue(
        np.array_equal(mat[offset:-offset, offset:-offset],
                       image_frame.numpy_view()))

  def testCroppedRGBImage(self):
    w, h = random.randrange(20, 100), random.randrange(20, 100)
    channels, offset = 3, 10
    mat = cv2.cvtColor(
        np.random.randint(2**8 - 1, size=(h, w, channels), dtype=np.uint8),
        cv2.COLOR_RGB2BGR)
    image_frame = mp.ImageFrame(
        image_format=mp.ImageFormat.SRGB,
        data=mat[offset:-offset, offset:-offset, :])
    self.assertTrue(
        np.array_equal(mat[offset:-offset, offset:-offset, :],
                       image_frame.numpy_view()))


if __name__ == '__main__':
  absltest.main()
