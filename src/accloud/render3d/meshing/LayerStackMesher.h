#pragma once

#include "domain/photons/LayerMaskSource.h"
#include "domain/photons/LayerRange.h"
#include "domain/photons/MeshChunk.h"

#include <cstddef>
#include <functional>
#include <cstdint>
#include <string>
#include <thread>
#include <vector>

namespace accloud::render3d {

enum class CutSurfaceMode {
  Open,
  Closed,
};

enum class CutSurfaceBoundary {
  Lower,
  Upper,
};

inline constexpr std::size_t kMinimumMeshWorkerCount = 1;
// Keep two logical CPU slots outside the mesh pool when the platform reports
// them; on very small machines at least one mesh worker remains available.
[[nodiscard]] inline constexpr std::size_t maximumMeshWorkerCountForCores(
    std::size_t logicalCores) noexcept {
  return logicalCores > 2 ? logicalCores - 2 : 1;
}

[[nodiscard]] inline std::size_t maximumMeshWorkerCount() noexcept {
  const auto detected = static_cast<std::size_t>(std::thread::hardware_concurrency());
  // Unknown topology: avoid assuming free cores.
  return maximumMeshWorkerCountForCores(detected == 0 ? 3 : detected);
}

struct MeshBuildOptions {
  double pitchXMm = 1.0;
  double pitchYMm = 1.0;
  double pitchZMm = 1.0;
  std::size_t chunkLayerCount = 8;
  CutSurfaceMode cutSurfaceMode = CutSurfaceMode::Open;
  // Preview sampling along Z. A value of 2 decodes one source layer out of
  // two while preserving the first and last selected layers. The sampled mask
  // is extruded until the next sampled layer, so the model keeps its original
  // Z extent at reduced geometric fidelity.
  std::size_t layerStride = 1;
  // Number of chunk workers. Four is the pure-core default; desktop preferences
  // use six on >=8-core machines. Callers
  // are bounded at runtime to reserve two logical CPU slots.
  std::size_t workerCount = 4;
};

struct MeshWorkerStats {
  std::size_t workerIndex = 0;
  std::size_t taskCount = 0;
  std::size_t decodedLayerCount = 0;
  std::size_t chunkCount = 0;
  std::uint64_t durationMs = 0;
};

struct CutSurfaceBuildResult {
  bool ok = false;
  photons::MeshChunk chunk;
  std::size_t decodedLayerCount = 0;
  std::string error;
};

struct MeshBuildResult {
  bool ok = false;
  bool cancelled = false;
  std::vector<photons::MeshChunk> chunks;
  std::size_t decodedLayerCount = 0;
  std::size_t effectiveWorkerCount = 1;
  std::vector<MeshWorkerStats> workerStats;
  std::string error;
};

struct MeshBuildCallbacks {
  std::function<bool(photons::MeshChunk&&)> consumeChunk;
  std::function<bool()> isCancelled;
  std::function<void(std::size_t completedLayers, std::size_t totalLayers)> progress;
};

class LayerStackMesher {
public:
  [[nodiscard]] CutSurfaceBuildResult buildCutSurface(
      photons::LayerMaskSource& source,
      std::size_t maskLayer,
      std::size_t planeLayer,
      CutSurfaceBoundary boundary,
      const MeshBuildOptions& options) const;

  [[nodiscard]] MeshBuildResult build(
      photons::LayerMaskSource& source,
      photons::LayerRange range,
      const MeshBuildOptions& options,
      const MeshBuildCallbacks& callbacks = {}) const;
};

} // namespace accloud::render3d
