#include "app/CloudFilesModel.h"
#include "app/MqttTailModel.h"
#include "app/PrintersModel.h"
#include "app/PrinterFilesModel.h"
#include "app/RecentJobsModel.h"

#include <QCoreApplication>

#include <iostream>
#include <string>

namespace {

bool expect(bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "FAILED: " << message << '\n';
    return false;
  }
  return true;
}

QVariantMap file(QString id, QString name) {
  QVariantMap out;
  out.insert(QStringLiteral("fileId"), id);
  out.insert(QStringLiteral("fileName"), name);
  out.insert(QStringLiteral("sizeText"), QStringLiteral("1 MB"));
  out.insert(QStringLiteral("status"), QStringLiteral("READY"));
  return out;
}

bool test_cloud_files_append_keeps_paging_contract() {
  accloud::CloudFilesModel model;
  model.setPageSize(2);

  QVariantList files;
  files.append(file(QStringLiteral("f1"), QStringLiteral("one.pwmb")));
  files.append(file(QStringLiteral("f2"), QStringLiteral("two.pws")));
  model.replaceFiles(files);

  bool ok = expect(model.count() == 2, "initial visible count should be 2")
      && expect(model.visibleCount() == 2, "initial total visible count should be 2");

  model.append(file(QStringLiteral("f3"), QStringLiteral("three.photon")));
  ok = ok
      && expect(model.count() == 2, "append on full first page should not add visible row")
      && expect(model.visibleCount() == 3, "append should update visibleCount")
      && expect(model.totalPages() == 2, "append should update total pages");

  model.setCurrentPage(1);
  ok = ok
      && expect(model.count() == 1, "second page should show appended row")
      && expect(model.get(0).value(QStringLiteral("fileId")).toString() == QStringLiteral("f3"),
                "second page should contain appended file");

  model.setTypeFilter(QStringLiteral("pwmb"));
  model.append(file(QStringLiteral("f4"), QStringLiteral("four.pwmb")));
  ok = ok
      && expect(model.visibleCount() == 2, "filtered append should rebuild visible rows")
      && expect(model.count() == 2, "filtered append should expose matching row");
  return ok;
}

bool test_mqtt_tail_append_preserves_tail_contract() {
  accloud::MqttTailModel model;
  model.appendMessage(QStringLiteral("t1"),
                      QStringLiteral("topic/a"),
                      QStringLiteral("{}"),
                      2,
                      QStringLiteral("line-a"));
  bool ok = expect(model.count() == 1, "mqtt tail append should add visible row")
      && expect(model.data(model.index(0, 0), accloud::MqttTailModel::TopicRole).toString()
                    == QStringLiteral("topic/a"),
                "mqtt tail topic should be readable");

  model.setTopicFilter(QStringLiteral("missing"));
  model.appendMessage(QStringLiteral("t2"),
                      QStringLiteral("topic/b"),
                      QStringLiteral("{}"),
                      2,
                      QStringLiteral("line-b"));
  ok = ok && expect(model.count() == 0, "filtered-out append should not become visible");
  return ok;
}

bool test_mqtt_tail_batches_hidden_updates() {
  accloud::MqttTailModel model;
  model.setUpdatesEnabled(false);
  model.appendMessage(QStringLiteral("t1"),
                      QStringLiteral("topic/a"),
                      QStringLiteral("{}"),
                      2,
                      QStringLiteral("line-a"));
  model.appendMessage(QStringLiteral("t2"),
                      QStringLiteral("topic/b"),
                      QStringLiteral("{}"),
                      2,
                      QStringLiteral("line-b"));

  bool ok = expect(model.count() == 0,
                   "hidden MQTT tail updates should not rebuild the visible model")
      && expect(model.messagesForTopic(QStringLiteral("topic/a")) == QStringLiteral("line-a"),
                "hidden MQTT messages should remain available to explicit diagnostics");

  model.setUpdatesEnabled(true);
  ok = ok
      && expect(model.count() == 2,
                "reactivating MQTT diagnostics should publish one synchronized model")
      && expect(model.data(model.index(1, 0), accloud::MqttTailModel::TopicRole).toString()
                    == QStringLiteral("topic/b"),
                "reactivated MQTT tail should expose messages received while hidden");
  return ok;
}

bool test_printer_files_model_applies_incremental_deltas() {
  accloud::PrinterFilesModel model;
  int resets = 0;
  int insertions = 0;
  int removals = 0;
  int changes = 0;
  QObject::connect(&model, &QAbstractItemModel::modelReset, [&resets]() { ++resets; });
  QObject::connect(&model,
                   &QAbstractItemModel::rowsInserted,
                   [&insertions](const QModelIndex&, int, int) { ++insertions; });
  QObject::connect(&model,
                   &QAbstractItemModel::rowsRemoved,
                   [&removals](const QModelIndex&, int, int) { ++removals; });
  QObject::connect(&model,
                   &QAbstractItemModel::dataChanged,
                   [&changes](const QModelIndex&, const QModelIndex&, const QList<int>&) {
                     ++changes;
                   });

  QVariantMap first = file(QStringLiteral("f1"), QStringLiteral("one.pwmb"));
  first.insert(QStringLiteral("printTime"), QStringLiteral("00h 10m"));
  QVariantMap second = file(QStringLiteral("f2"), QStringLiteral("two.pws"));
  QVariantList initial{first, second};
  bool ok = expect(model.replaceOrPatchFiles(initial), "initial printer files load should change")
      && expect(model.count() == 2, "initial printer files load should insert two rows")
      && expect(insertions == 1, "initial printer files load should use one insert range")
      && expect(resets == 0, "initial printer files load should avoid model reset")
      && expect(model.get(0).value(QStringLiteral("printTime")).toString()
                    == QStringLiteral("00h 10m"),
                "printer file model should preserve raw metadata");

  second.insert(QStringLiteral("status"), QStringLiteral("PROCESSING"));
  QVariantList patched{first, second};
  ok = expect(model.replaceOrPatchFiles(patched), "same identity update should change") && ok;
  ok = expect(changes == 1, "same identity update should emit dataChanged") && ok;
  ok = expect(resets == 0, "same identity update should avoid model reset") && ok;

  QVariantMap third = file(QStringLiteral("f3"), QStringLiteral("three.photon"));
  QVariantList extended{first, second, third};
  ok = expect(model.replaceOrPatchFiles(extended), "tail append should change") && ok;
  ok = expect(model.count() == 3, "tail append should expose the third row") && ok;
  ok = expect(insertions == 2, "tail append should emit an incremental insertion") && ok;
  ok = expect(model.remove(1), "explicit row removal should succeed") && ok;
  ok = expect(model.count() == 2, "explicit row removal should update count") && ok;
  ok = expect(removals == 1, "explicit row removal should emit rowsRemoved") && ok;

  QVariantList reordered{third, first};
  ok = expect(model.replaceOrPatchFiles(reordered), "identity reorder should change") && ok;
  ok = expect(resets == 1, "identity reorder should fall back to one model reset") && ok;
  return ok;
}

bool test_patch_models_preserve_identity_updates() {
  accloud::PrintersModel printers;
  int printerResets = 0;
  int printerInsertions = 0;
  QObject::connect(&printers,
                   &QAbstractItemModel::modelReset,
                   [&printerResets]() { ++printerResets; });
  QObject::connect(&printers,
                   &QAbstractItemModel::rowsInserted,
                   [&printerInsertions](const QModelIndex&, int, int) { ++printerInsertions; });
  QVariantMap p1;
  p1.insert(QStringLiteral("id"), QStringLiteral("p1"));
  p1.insert(QStringLiteral("name"), QStringLiteral("Printer"));
  QVariantList printerList;
  printerList.append(p1);
  bool ok = expect(printers.replaceOrPatchPrinters(printerList), "initial printers replace should change");
  p1.insert(QStringLiteral("state"), QStringLiteral("PRINTING"));
  QVariantList patchedPrinters;
  patchedPrinters.append(p1);
  ok = ok
      && expect(printers.replaceOrPatchPrinters(patchedPrinters), "printer patch should change")
      && expect(printers.count() == 1, "printer patch should preserve row count")
      && expect(printers.get(0).value(QStringLiteral("state")).toString() == QStringLiteral("PRINTING"),
                "printer patch should update state")
      && expect(printerResets == 0, "stable printer identities should avoid model reset");

  QVariantMap p2;
  p2.insert(QStringLiteral("id"), QStringLiteral("p2"));
  p2.insert(QStringLiteral("name"), QStringLiteral("Printer Two"));
  QVariantList extendedPrinters{p1, p2};
  ok = expect(printers.replaceOrPatchPrinters(extendedPrinters),
              "printer tail append should change") && ok;
  ok = expect(printerInsertions == 2,
              "initial printer load and tail append should use insertion ranges") && ok;
  ok = expect(printerResets == 0,
              "printer tail append should avoid model reset") && ok;

  accloud::RecentJobsModel jobs;
  QVariantMap job;
  job.insert(QStringLiteral("taskId"), QStringLiteral("j1"));
  job.insert(QStringLiteral("gcodeName"), QStringLiteral("old.pwmb"));
  QVariantList jobList;
  jobList.append(job);
  ok = ok && expect(jobs.replaceOrPatchJobs(jobList), "initial jobs replace should change");
  job.insert(QStringLiteral("gcodeName"), QStringLiteral("new.pwmb"));
  QVariantList patchedJobs;
  patchedJobs.append(job);
  ok = ok
      && expect(jobs.replaceOrPatchJobs(patchedJobs), "job patch should change")
      && expect(jobs.count() == 1, "job patch should preserve row count")
      && expect(jobs.get(0).value(QStringLiteral("gcodeName")).toString() == QStringLiteral("new.pwmb"),
                "job patch should update gcode name");
  return ok;
}

bool test_recent_jobs_last_completed_file_tracks_patches() {
  accloud::RecentJobsModel jobs;
  int updates = 0;
  QObject::connect(&jobs, &accloud::RecentJobsModel::lastCompletedFileChanged,
                   [&updates]() { ++updates; });
  auto makeJob = [](const char* task, const char* name, int status,
                    qlonglong created, qlonglong ended, const char* printer) {
    QVariantMap job;
    job.insert(QStringLiteral("taskId"), QString::fromLatin1(task));
    job.insert(QStringLiteral("gcodeName"), QString::fromLatin1(name));
    job.insert(QStringLiteral("printStatus"), status);
    job.insert(QStringLiteral("createTime"), created);
    job.insert(QStringLiteral("endTime"), ended);
    job.insert(QStringLiteral("printerId"), QString::fromLatin1(printer));
    return job;
  };

  auto oldFinished = makeJob("done-old", "old.pwsz", 2, 100, 150, "p1");
  auto latestFinished = makeJob("done-new", "latest.pwsz", 2, 110, 230, "p1");
  auto newFailure = makeJob("failed", "failed.pwsz", 3, 300, 320, "p1");
  auto running = makeJob("active", "active.pwsz", 1, 400, 0, "p1");
  bool ok = expect(jobs.replaceOrPatchJobs({newFailure, oldFinished, running, latestFinished}),
                   "recent jobs initial load should change")
      && expect(jobs.lastCompletedFile() == QStringLiteral("latest.pwsz"),
                "last printed must use the most recent successful endTime, not row order")
      && expect(updates == 1, "initial successful file should signal one change");

  // Same identities, same row count: only dataChanged is emitted by the list model.
  latestFinished.insert(QStringLiteral("gcodeName"), QStringLiteral("renamed.pwsz"));
  ok = expect(jobs.replaceOrPatchJobs({newFailure, oldFinished, running, latestFinished}),
              "same-count job metadata update should change") && ok;
  ok = expect(jobs.lastCompletedFile() == QStringLiteral("renamed.pwsz"),
              "same-count metadata change must refresh the derived name") && ok;
  ok = expect(updates == 2, "same-count metadata update should notify lastCompletedFile") && ok;
  ok = expect(!jobs.replaceOrPatchJobs({newFailure, oldFinished, running, latestFinished}),
              "identical history must not be considered a change") && ok;
  ok = expect(updates == 2, "identical history must not notify the derived property") && ok;

  // A second completed job may finish after a job created later.
  oldFinished.insert(QStringLiteral("endTime"), 360LL);
  ok = expect(jobs.replaceOrPatchJobs({newFailure, oldFinished, running, latestFinished}),
              "endTime update should change the model") && ok;
  ok = expect(jobs.lastCompletedFile() == QStringLiteral("old.pwsz"),
              "last completion must win over recent creation") && ok;

  // Missing endTime falls back to createTime, but failures never qualify.
  auto fallbackFinished = makeJob("done-fallback", "fallback.pwsz", 2, 500, 0, "p1");
  ok = expect(jobs.mergeOrPatchJobs({fallbackFinished}), "merge completed fallback") && ok;
  ok = expect(jobs.lastCompletedFile() == QStringLiteral("fallback.pwsz"),
              "missing endTime must fall back to valid createTime") && ok;
  fallbackFinished.insert(QStringLiteral("printStatus"), 4);
  ok = expect(jobs.mergeOrPatchJobs({fallbackFinished}), "status update should merge") && ok;
  ok = expect(jobs.lastCompletedFile() == QStringLiteral("old.pwsz"),
              "cancelled tasks must be excluded after a same-count update") && ok;

  // The page clears/replaces this model when changing selected printers.
  jobs.clear();
  ok = expect(jobs.lastCompletedFile().isEmpty(), "printer switch must clear old filename") && ok;
  auto otherPrinter = makeJob("p2-done", "other.pwsz", 2, 600, 700, "p2");
  ok = expect(jobs.replaceOrPatchJobs({otherPrinter}), "other printer history should load") && ok;
  ok = expect(jobs.lastCompletedFile() == QStringLiteral("other.pwsz"),
              "other printer should show its own last successful file") && ok;
  otherPrinter.insert(QStringLiteral("printStatus"), 3);
  ok = expect(jobs.replaceOrPatchJobs({otherPrinter}), "failed terminal update should apply") && ok;
  ok = expect(jobs.lastCompletedFile().isEmpty(),
              "no completed jobs must display an empty property, never a failed filename") && ok;
  return ok;
}

}  // namespace

int main(int argc, char** argv) {
  QCoreApplication app(argc, argv);
  bool ok = true;
  ok = test_cloud_files_append_keeps_paging_contract() && ok;
  ok = test_mqtt_tail_append_preserves_tail_contract() && ok;
  ok = test_mqtt_tail_batches_hidden_updates() && ok;
  ok = test_printer_files_model_applies_incremental_deltas() && ok;
  ok = test_patch_models_preserve_identity_updates() && ok;
  ok = test_recent_jobs_last_completed_file_tracks_patches() && ok;
  return ok ? 0 : 1;
}
