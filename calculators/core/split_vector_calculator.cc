// Copyright 2019 The MediaPipe Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "mediapipe/calculators/core/split_vector_calculator.h"

#include <vector>

#include "mediapipe/framework/formats/landmark.pb.h"
#include "mediapipe/framework/formats/rect.pb.h"
#include "tensorflow/lite/interpreter.h"

#if !defined(MEDIAPIPE_DISABLE_GL_COMPUTE)
#include "tensorflow/lite/delegates/gpu/gl/gl_buffer.h"
#endif  //  !MEDIAPIPE_DISABLE_GPU

namespace mediapipe {

// Example config:
// node {
//   calculator: "SplitTfLiteTensorVectorCalculator"
//   input_stream: "tflitetensor_vector"
//   output_stream: "tflitetensor_vector_range_0"
//   output_stream: "tflitetensor_vector_range_1"
//   options {
//     [mediapipe.SplitVectorCalculatorOptions.ext] {
//       ranges: { begin: 0 end: 1 }
//       ranges: { begin: 1 end: 2 }
//       element_only: false
//     }
//   }
// }
typedef SplitVectorCalculator<TfLiteTensor, false>
    SplitTfLiteTensorVectorCalculator;
REGISTER_CALCULATOR(SplitTfLiteTensorVectorCalculator);

typedef SplitVectorCalculator<::mediapipe::NormalizedLandmark, false>
    SplitLandmarkVectorCalculator;
REGISTER_CALCULATOR(SplitLandmarkVectorCalculator);

typedef SplitVectorCalculator<::mediapipe::NormalizedRect, false>
    SplitNormalizedRectVectorCalculator;
REGISTER_CALCULATOR(SplitNormalizedRectVectorCalculator);

#if !defined(MEDIAPIPE_DISABLE_GL_COMPUTE)
typedef SplitVectorCalculator<::tflite::gpu::gl::GlBuffer, true>
    MovableSplitGlBufferVectorCalculator;
REGISTER_CALCULATOR(MovableSplitGlBufferVectorCalculator);
#endif
}  // namespace mediapipe
