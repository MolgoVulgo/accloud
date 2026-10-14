#pragma once

#include <initializer_list>
#include <string>
#include <string_view>
#include <utility>

namespace accloud::usecases::printing {

// Pure policy for a future durable direct-print coordinator. No transport and no
// persistence is performed here. A caller MUST durably commit DispatchReserved
// before executing SendPrintOrder. An unknown HTTP outcome cannot be retried.
enum class DirectPreparationState {
    Created,
    Uploading,
    CloudPending,
    CloudReady,
    DispatchReady,
    DispatchReserved,
    DispatchUnknown,
    HttpAccepted,
    MqttActive,
    Terminal,
    Cancelled,
    TimedOut,
    Rejected,
    Failed,
};

enum class DirectPreparationEffect {
    None,
    CheckCloud,
    CheckPrinter,
    PersistReservation,
    SendPrintOrder,
};

struct DirectPreparation {
    std::string operationId;
    std::string printerId;
    std::string cloudFileId;
    std::string cloudGcodeId;
    DirectPreparationState state{DirectPreparationState::Created};
    bool dispatchEffectIssued{false}; // Volatile guard; durable reservation remains mandatory.
};

struct DirectPreparationTransition {
    DirectPreparation operation;
    DirectPreparationEffect effect{DirectPreparationEffect::None};
    bool accepted{false};
};

[[nodiscard]] inline std::string_view directPreparationStateKey(DirectPreparationState state) {
    switch (state) {
    case DirectPreparationState::Created: return "created";
    case DirectPreparationState::Uploading: return "uploading";
    case DirectPreparationState::CloudPending: return "cloud_pending";
    case DirectPreparationState::CloudReady: return "cloud_ready";
    case DirectPreparationState::DispatchReady: return "dispatch_ready";
    case DirectPreparationState::DispatchReserved: return "dispatch_reserved";
    case DirectPreparationState::DispatchUnknown: return "dispatch_unknown";
    case DirectPreparationState::HttpAccepted: return "http_accepted";
    case DirectPreparationState::MqttActive: return "mqtt_active";
    case DirectPreparationState::Terminal: return "terminal";
    case DirectPreparationState::Cancelled: return "cancelled";
    case DirectPreparationState::TimedOut: return "timed_out";
    case DirectPreparationState::Rejected: return "rejected";
    case DirectPreparationState::Failed: return "failed";
    }
    return "dispatch_unknown";
}

// Unknown persisted states are deliberately non-replayable.
[[nodiscard]] inline DirectPreparationState directPreparationStateFromKey(std::string_view key) {
    for (auto state : {DirectPreparationState::Created, DirectPreparationState::Uploading,
                       DirectPreparationState::CloudPending, DirectPreparationState::CloudReady,
                       DirectPreparationState::DispatchReady, DirectPreparationState::DispatchReserved,
                       DirectPreparationState::DispatchUnknown, DirectPreparationState::HttpAccepted,
                       DirectPreparationState::MqttActive, DirectPreparationState::Terminal,
                       DirectPreparationState::Cancelled, DirectPreparationState::TimedOut,
                       DirectPreparationState::Rejected, DirectPreparationState::Failed}) {
        if (directPreparationStateKey(state) == key) return state;
    }
    return DirectPreparationState::DispatchUnknown;
}

[[nodiscard]] inline DirectPreparationTransition beginDirectUpload(DirectPreparation input) {
    if (input.state != DirectPreparationState::Created || input.operationId.empty()
        || input.printerId.empty()) return {input};
    input.state = DirectPreparationState::Uploading;
    return {input, DirectPreparationEffect::None, true};
}

[[nodiscard]] inline DirectPreparationTransition uploadCompleted(DirectPreparation input,
                                                                  std::string fileId) {
    if (input.state != DirectPreparationState::Uploading) return {input};
    if (fileId.empty()) {
        input.state = DirectPreparationState::Failed;
        return {input, DirectPreparationEffect::None, true};
    }
    input.cloudFileId = std::move(fileId);
    input.state = DirectPreparationState::CloudPending;
    // Do not trust an initial upload HTTP result as proof of cloud readiness.
    return {input, DirectPreparationEffect::CheckCloud, true};
}

[[nodiscard]] inline DirectPreparationTransition cloudFileObserved(DirectPreparation input,
                                                                    std::string_view observedFileId,
                                                                    int uploadStatus,
                                                                    std::string gcodeId) {
    if (input.state != DirectPreparationState::CloudPending || input.cloudFileId.empty()
        || observedFileId != input.cloudFileId) return {input};
    if (uploadStatus != 1 || gcodeId.empty() || gcodeId == "0") {
        return {input, DirectPreparationEffect::CheckCloud, true};
    }
    input.cloudGcodeId = std::move(gcodeId);
    input.state = DirectPreparationState::CloudReady;
    return {input, DirectPreparationEffect::CheckPrinter, true};
}

[[nodiscard]] inline DirectPreparationTransition printerRechecked(DirectPreparation input,
                                                                   bool online, bool idle,
                                                                   bool compatible) {
    if (input.state != DirectPreparationState::CloudReady) return {input};
    input.state = (online && idle && compatible)
        ? DirectPreparationState::DispatchReady : DirectPreparationState::Rejected;
    return {input, DirectPreparationEffect::None, true};
}

// First write the DispatchReserved state to durable storage. This transition
// must NOT emit any print order yet.
[[nodiscard]] inline DirectPreparationTransition reserveDirectPrintDispatch(DirectPreparation input) {
    if (input.state != DirectPreparationState::DispatchReady || input.cloudFileId.empty()
        || input.cloudGcodeId.empty()) return {input};
    input.state = DirectPreparationState::DispatchReserved;
    return {input, DirectPreparationEffect::PersistReservation, true};
}

// Only a CONFIRMED durable write permits the single transport attempt.
[[nodiscard]] inline DirectPreparationTransition directReservationPersisted(DirectPreparation input,
                                                                             bool durableWriteSucceeded) {
    if (input.state != DirectPreparationState::DispatchReserved || input.dispatchEffectIssued) return {input};
    if (!durableWriteSucceeded) {
        input.state = DirectPreparationState::Failed;
        return {input, DirectPreparationEffect::None, true};
    }
    input.dispatchEffectIssued = true;
    return {input, DirectPreparationEffect::SendPrintOrder, true};
}

[[nodiscard]] inline DirectPreparationTransition directPrintHttpResult(DirectPreparation input,
                                                                        bool accepted) {
    if (input.state != DirectPreparationState::DispatchReserved) return {input};
    // Even an HTTP error/timeout might mean the server received the command.
    input.state = accepted ? DirectPreparationState::HttpAccepted
                           : DirectPreparationState::DispatchUnknown;
    return {input, DirectPreparationEffect::None, true};
}

[[nodiscard]] inline DirectPreparationTransition cancelDirectPreparation(DirectPreparation input) {
    switch (input.state) {
    case DirectPreparationState::Created:
    case DirectPreparationState::Uploading:
    case DirectPreparationState::CloudPending:
    case DirectPreparationState::CloudReady:
    case DirectPreparationState::DispatchReady:
        input.state = DirectPreparationState::Cancelled;
        return {input, DirectPreparationEffect::None, true};
    default:
        return {input};
    }
}

[[nodiscard]] inline DirectPreparationTransition timeoutDirectPreparation(DirectPreparation input) {
    switch (input.state) {
    case DirectPreparationState::Created:
    case DirectPreparationState::Uploading:
    case DirectPreparationState::CloudPending:
    case DirectPreparationState::CloudReady:
    case DirectPreparationState::DispatchReady:
        input.state = DirectPreparationState::TimedOut;
        return {input, DirectPreparationEffect::None, true};
    case DirectPreparationState::DispatchReserved:
        input.state = DirectPreparationState::DispatchUnknown;
        return {input, DirectPreparationEffect::None, true};
    default:
        return {input};
    }
}

[[nodiscard]] inline DirectPreparationTransition recoverDirectPreparation(DirectPreparation input) {
    switch (input.state) {
    case DirectPreparationState::CloudPending:
        return {input, DirectPreparationEffect::CheckCloud, true};
    case DirectPreparationState::CloudReady:
        return {input, DirectPreparationEffect::CheckPrinter, true};
    case DirectPreparationState::DispatchReserved:
        input.state = DirectPreparationState::DispatchUnknown;
        return {input, DirectPreparationEffect::None, true};
    case DirectPreparationState::Uploading:
    case DirectPreparationState::Created:
    case DirectPreparationState::DispatchReady:
        // Never implicitly restart an upload or skip pre-dispatch checks.
        return {input, DirectPreparationEffect::None, true};
    default:
        return {input};
    }
}

[[nodiscard]] inline DirectPreparationTransition directPrintMqttActive(DirectPreparation input,
                                                                        bool correlated) {
    if (!correlated) return {input};
    if (input.state != DirectPreparationState::HttpAccepted
        && input.state != DirectPreparationState::DispatchUnknown) return {input};
    input.state = DirectPreparationState::MqttActive;
    return {input, DirectPreparationEffect::None, true};
}

[[nodiscard]] inline DirectPreparationTransition directPrintMqttTerminal(DirectPreparation input,
                                                                          bool correlated) {
    if (!correlated) return {input};
    if (input.state != DirectPreparationState::MqttActive
        && input.state != DirectPreparationState::HttpAccepted
        && input.state != DirectPreparationState::DispatchUnknown) return {input};
    input.state = DirectPreparationState::Terminal;
    return {input, DirectPreparationEffect::None, true};
}

} // namespace accloud::usecases::printing
