/* Copyright 2022 The MediaPipe Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "mediapipe/tasks/cc/core/model_asset_bundle_resources.h"

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/str_join.h"
#include "mediapipe/framework/port/status_macros.h"
#include "mediapipe/tasks/cc/common.h"
#include "mediapipe/tasks/cc/metadata/utils/zip_utils.h"
#include "mediapipe/util/resource_util.h"

namespace mediapipe {
namespace tasks {
namespace core {

namespace {
using ::absl::StatusCode;
}  // namespace

ModelAssetBundleResources::ModelAssetBundleResources(
    const std::string& tag,
    std::unique_ptr<proto::ExternalFile> model_asset_bundle_file)
    : tag_(tag), model_asset_bundle_file_(std::move(model_asset_bundle_file)) {}

/* static */
absl::StatusOr<std::unique_ptr<ModelAssetBundleResources>>
ModelAssetBundleResources::Create(
    const std::string& tag,
    std::unique_ptr<proto::ExternalFile> model_asset_bundle_file) {
  if (model_asset_bundle_file == nullptr) {
    return CreateStatusWithPayload(
        StatusCode::kInvalidArgument,
        "The model asset bundle file proto cannot be nullptr.",
        MediaPipeTasksStatus::kInvalidArgumentError);
  }
  auto model_bundle_resources = absl::WrapUnique(
      new ModelAssetBundleResources(tag, std::move(model_asset_bundle_file)));
  MP_RETURN_IF_ERROR(
      model_bundle_resources->ExtractModelFilesFromExternalFileProto());
  return model_bundle_resources;
}

absl::Status
ModelAssetBundleResources::ExtractModelFilesFromExternalFileProto() {
  if (model_asset_bundle_file_->has_file_name()) {
    // If the model asset bundle file name is a relative path, searches the file
    // in a platform-specific location and returns the absolute path on success.
    ASSIGN_OR_RETURN(
        std::string path_to_resource,
        mediapipe::PathToResourceAsFile(model_asset_bundle_file_->file_name()));
    model_asset_bundle_file_->set_file_name(path_to_resource);
  }
  ASSIGN_OR_RETURN(model_asset_bundle_file_handler_,
                   ExternalFileHandler::CreateFromExternalFile(
                       model_asset_bundle_file_.get()));
  const char* buffer_data =
      model_asset_bundle_file_handler_->GetFileContent().data();
  size_t buffer_size =
      model_asset_bundle_file_handler_->GetFileContent().size();
  return metadata::ExtractFilesfromZipFile(buffer_data, buffer_size,
                                           &model_files_);
}

absl::StatusOr<absl::string_view> ModelAssetBundleResources::GetModelFile(
    const std::string& filename) const {
  auto it = model_files_.find(filename);
  if (it == model_files_.end()) {
    auto model_files = ListModelFiles();
    std::string all_model_files =
        absl::StrJoin(model_files.begin(), model_files.end(), ", ");

    return CreateStatusWithPayload(
        StatusCode::kNotFound,
        absl::StrFormat("No model file with name: %s. All model files in the "
                        "model asset bundle are: %s.",
                        filename, all_model_files),
        MediaPipeTasksStatus::kFileNotFoundError);
  }
  return it->second;
}

std::vector<std::string> ModelAssetBundleResources::ListModelFiles() const {
  std::vector<std::string> model_names;
  for (const auto& [model_name, _] : model_files_) {
    model_names.push_back(model_name);
  }
  return model_names;
}

}  // namespace core
}  // namespace tasks
}  // namespace mediapipe
