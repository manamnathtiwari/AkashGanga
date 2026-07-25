import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

import '../models/submission.dart';

/// Offline cache of solved submissions so history + last results work offline.
class LocalCache {
  static const _boxName = 'submissions';
  late final Box<String> _box;

  Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox<String>(_boxName);
  }

  List<Submission> all() {
    final items = _box.values
        .map((s) => Submission.fromJson(jsonDecode(s) as Map<String, dynamic>))
        .toList();
    items.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return items;
  }

  Submission? get(int id) {
    final raw = _box.get(id.toString());
    if (raw == null) return null;
    return Submission.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  Future<void> put(Submission submission) =>
      _box.put(submission.id.toString(), jsonEncode(submission.toJson()));

  Future<void> putAll(List<Submission> submissions) async {
    for (final s in submissions) {
      await put(s);
    }
  }

  Future<void> clear() => _box.clear();
}
