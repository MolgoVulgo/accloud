#include "app/usecases/printing/DirectPrintPreparationPolicy.h"

#include <array>
#include <cstdlib>
#include <iostream>
#include <string>

using namespace accloud::usecases::printing;

namespace {
void require(bool passed, const char* label) {
    if (!passed) {
        std::cerr << label << '\n';
        std::exit(1);
    }
}

DirectPreparation makeCreated() {
    DirectPreparation op;
    op.operationId = "direct-0001";
    op.printerId = "printer-1";
    op.state = DirectPreparationState::Created;
    return op;
}

void testPersistenceKeys() {
    constexpr std::array states{
        DirectPreparationState::Created, DirectPreparationState::Uploading,
        DirectPreparationState::CloudPending, DirectPreparationState::CloudReady,
        DirectPreparationState::DispatchReady, DirectPreparationState::DispatchReserved,
        DirectPreparationState::DispatchUnknown, DirectPreparationState::HttpAccepted,
        DirectPreparationState::MqttActive, DirectPreparationState::Terminal,
        DirectPreparationState::Cancelled, DirectPreparationState::TimedOut,
        DirectPreparationState::Rejected, DirectPreparationState::Failed,
    };
    for (const auto state : states) {
        require(directPreparationStateFromKey(directPreparationStateKey(state)) == state,
                "all durable direct-preparation states must roundtrip");
    }
    require(directPreparationStateFromKey("future-invalid") == DirectPreparationState::DispatchUnknown,
            "unrecognized persisted preparation must never replay an order");
}

DirectPreparation pendingCloud() {
    auto started = beginDirectUpload(makeCreated());
    require(started.accepted, "upload start must succeed with stable operation identity");
    auto uploaded = uploadCompleted(started.operation, "cloud-123");
    require(uploaded.accepted && uploaded.effect == DirectPreparationEffect::CheckCloud,
            "upload completion must require independent cloud check");
    return uploaded.operation;
}

DirectPreparation readyCloud() {
    auto p = cloudFileObserved(pendingCloud(), "cloud-123", 1, "gcode-123");
    require(p.accepted && p.effect == DirectPreparationEffect::CheckPrinter,
            "cloud readiness must require fresh printer check");
    return p.operation;
}

void testReadinessMustBeExactAndConfirmed() {
    auto p = pendingCloud();
    require(cloudFileObserved(p, "other-cloud", 1, "gcode-123").accepted == false,
            "stale cloud response cannot advance operation");
    require(cloudFileObserved(p, "cloud-123", 0, "gcode-123").operation.state
                == DirectPreparationState::CloudPending,
            "gcode id alone cannot establish cloud readiness");
    require(cloudFileObserved(p, "cloud-123", 1, "").operation.state
                == DirectPreparationState::CloudPending,
            "upload status alone cannot establish cloud readiness");
    require(cloudFileObserved(p, "cloud-123", 1, "0").operation.state
                == DirectPreparationState::CloudPending,
            "gcode zero must not establish readiness");
    auto p2 = readyCloud();
    require(p2.state == DirectPreparationState::CloudReady && p2.cloudGcodeId == "gcode-123",
            "confirmed cloud file must retain server gcode id");
}

void testPrinterRecheckAndDispatchReservation() {
    auto initial = readyCloud();
    for (const auto flags : std::array<std::array<bool, 3>, 3>{{{false, true, true},
                                                                 {true, false, true},
                                                                 {true, true, false}}}) {
        auto blocked = printerRechecked(initial, flags[0], flags[1], flags[2]);
        require(blocked.operation.state == DirectPreparationState::Rejected,
                "offline, occupied or incompatible printer must block dispatch");
        require(reserveDirectPrintDispatch(blocked.operation).effect == DirectPreparationEffect::None,
                "blocked printer must never reserve print order");
    }
    auto checked = printerRechecked(initial, true, true, true);
    require(checked.operation.state == DirectPreparationState::DispatchReady,
            "compatible idle printer must become dispatch ready");
    auto reserved = reserveDirectPrintDispatch(checked.operation);
    require(reserved.accepted && reserved.effect == DirectPreparationEffect::PersistReservation,
            "dispatch reservation must first demand durable persistence");
    require(reserveDirectPrintDispatch(reserved.operation).effect == DirectPreparationEffect::None,
            "duplicate reservation must be inert");
    require(directReservationPersisted(reserved.operation, false).effect == DirectPreparationEffect::None,
            "failed durable write must not emit printer order");
    auto committed = directReservationPersisted(reserved.operation, true);
    require(committed.effect == DirectPreparationEffect::SendPrintOrder,
            "one dispatch effect is permitted after successful write");
    require(directReservationPersisted(committed.operation, true).effect == DirectPreparationEffect::None,
            "duplicate persist completion must be inert for the same operation instance");
    require(cancelDirectPreparation(reserved.operation).accepted == false,
            "cancellation after reservation cannot make a replay safe");
}

void testLostResponseCannotRetry() {
    auto reserved = reserveDirectPrintDispatch(printerRechecked(readyCloud(), true, true, true).operation);
    auto failure = directPrintHttpResult(reserved.operation, false);
    require(failure.operation.state == DirectPreparationState::DispatchUnknown,
            "HTTP error is uncertain once dispatch was reserved");
    require(recoverDirectPreparation(failure.operation).effect == DirectPreparationEffect::None,
            "uncertain HTTP result must never send again after restart");
    auto recoveredReserved = recoverDirectPreparation(reserved.operation);
    require(recoveredReserved.operation.state == DirectPreparationState::DispatchUnknown,
            "crash after reservation must persist ambiguity");
    require(recoveredReserved.effect == DirectPreparationEffect::None,
            "crash after reservation must never trigger re-dispatch");
    require(directReservationPersisted(failure.operation, true).effect == DirectPreparationEffect::None,
            "late storage callback must not dispatch uncertain operation");
    require(timeoutDirectPreparation(reserved.operation).operation.state
                == DirectPreparationState::DispatchUnknown,
            "timeout after reservation must not unlock dispatch");
}

void testCancellationAndRestart() {
    auto pending = pendingCloud();
    require(recoverDirectPreparation(pending).effect == DirectPreparationEffect::CheckCloud,
            "pending cloud state can resume read-only checking");
    require(cancelDirectPreparation(pending).operation.state == DirectPreparationState::Cancelled,
            "pre-dispatch cancellation must be possible");
    require(timeoutDirectPreparation(pending).operation.state == DirectPreparationState::TimedOut,
            "cloud readiness deadline must stop without sending");
    auto created = makeCreated();
    created.printerId.clear();
    require(!beginDirectUpload(created).accepted, "missing printer cannot initiate upload");
    require(uploadCompleted(beginDirectUpload(makeCreated()).operation, "").operation.state
                == DirectPreparationState::Failed,
            "missing cloud file must stop without dispatch");
}

void testCorrelatedMqttResults() {
    auto reserved = reserveDirectPrintDispatch(printerRechecked(readyCloud(), true, true, true).operation);
    auto accepted = directPrintHttpResult(reserved.operation, true);
    require(accepted.operation.state == DirectPreparationState::HttpAccepted,
            "HTTP accepted is not MQTT printing");
    require(!directPrintMqttActive(accepted.operation, false).accepted,
            "unmatched MQTT message cannot advance print");
    auto active = directPrintMqttActive(accepted.operation, true);
    require(active.operation.state == DirectPreparationState::MqttActive,
            "matching MQTT status may establish printing");
    require(!directPrintMqttTerminal(active.operation, false).accepted,
            "unmatched MQTT terminal message cannot finalize print");
    require(directPrintMqttTerminal(active.operation, true).operation.state
                == DirectPreparationState::Terminal,
            "matching MQTT terminal message may finalize print");
}
}

int main() {
    testPersistenceKeys();
    testReadinessMustBeExactAndConfirmed();
    testPrinterRecheckAndDispatchReservation();
    testLostResponseCannotRetry();
    testCancellationAndRestart();
    testCorrelatedMqttResults();
    std::cout << "direct print preparation safety policy tests passed\n";
}
