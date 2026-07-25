import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/config.dart';
import '../models/submission.dart';
import '../providers.dart';
import '../theme.dart';
import '../widgets/annotated_viewer.dart';

class ResultScreen extends ConsumerStatefulWidget {
  const ResultScreen({super.key, required this.submissionId});
  final int submissionId;

  @override
  ConsumerState<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends ConsumerState<ResultScreen> {
  Timer? _poller;
  Submission? _sub;
  bool _showStars = true;
  bool _showDeepSky = true;
  Annotation? _selected;
  _ImageView _imageView = _ImageView.original;

  // The 4 image-view modes
  static const _views = [
    _ImageView.original,
    _ImageView.annotated,
    _ImageView.redGreen,
    _ImageView.extraction,
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _poller?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    final repo = ref.read(submissionsRepositoryProvider);
    final sub = await repo.get(widget.submissionId);
    if (!mounted) return;
    setState(() => _sub = sub);
    if (!sub.isDone) {
      _poller = Timer.periodic(
        const Duration(seconds: 4),
        (_) => _poll(),
      );
    }
  }

  Future<void> _poll() async {
    final repo = ref.read(submissionsRepositoryProvider);
    final sub = await repo.get(widget.submissionId);
    if (!mounted) return;
    setState(() => _sub = sub);
    if (sub.isDone) {
      _poller?.cancel();
      ref.invalidate(submissionsListProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sub = _sub;
    return Scaffold(
      appBar: AppBar(
        title: Text(sub?.originalFilename ??
            sub?.sourceUrl?.split('/').last ??
            'Image #${widget.submissionId}'),
        actions: [
          if (sub != null && sub.isSolved) ...[
            // Star overlay toggle (only meaningful on original view)
            if (_imageView == _ImageView.original) ...[
              IconButton(
                tooltip: 'Stars',
                icon: Icon(Icons.star,
                    color: _showStars ? AppTheme.star : Colors.white24),
                onPressed: () => setState(() => _showStars = !_showStars),
              ),
              IconButton(
                tooltip: 'Deep sky',
                icon: Icon(Icons.blur_circular,
                    color: _showDeepSky ? AppTheme.accent : Colors.white24),
                onPressed: () => setState(() => _showDeepSky = !_showDeepSky),
              ),
            ],
          ],
        ],
      ),
      body: sub == null
          ? const Center(child: CircularProgressIndicator())
          : sub.isSolved
              ? Column(children: [
                  // ── Image-type selector tabs ──────────────────────
                  _ImageTypeTabs(
                    selected: _imageView,
                    sub: sub,
                    onChanged: (v) => setState(() {
                      _imageView = v;
                      _selected = null;
                    }),
                  ),
                  // ── Viewer ───────────────────────────────────────
                  Expanded(
                    child: AnnotatedViewer(
                      submission: sub,
                      imageView: _imageView,
                      showStars: _showStars && _imageView == _ImageView.original,
                      showDeepSky:
                          _showDeepSky && _imageView == _ImageView.original,
                      onTapAnnotation: (a) =>
                          setState(() => _selected = a),
                    ),
                  ),
                  if (_selected != null)
                    _AnnotationSheet(_selected!,
                        onClose: () => setState(() => _selected = null)),
                  _CalibrationBar(sub),
                ])
              : _SolveStatus(sub),
    );
  }
}

class _SolveStatus extends StatelessWidget {
  const _SolveStatus(this.sub);
  final Submission sub;

  @override
  Widget build(BuildContext context) {
    if (sub.status == 'failed') {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error, color: AppTheme.danger, size: 56),
            const SizedBox(height: 16),
            const Text('Could not solve this image',
                style: TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            Text(sub.error ?? 'Unknown error',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white54)),
          ]),
        ),
      );
    }
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          CircularProgressIndicator(),
          SizedBox(height: 24),
          Text('Mapping the sky…', style: TextStyle(fontSize: 18)),
          SizedBox(height: 8),
          Text(
            'Our engine is searching billions of star patterns.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white54),
          ),
        ]),
      ),
    );
  }
}

class _CalibrationBar extends StatelessWidget {
  const _CalibrationBar(this.sub);
  final Submission sub;

  static String _fmt(double? v, [int dp = 3]) =>
      v == null ? '—' : v.toStringAsFixed(dp);

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppTheme.panel,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _Chip('RA', _fmt(sub.ra, 2)),
          _Chip('Dec', _fmt(sub.dec, 2)),
          _Chip('Scale', '${_fmt(sub.pixscale, 2)}″/px'),
          _Chip('PA', '${_fmt(sub.orientation, 1)}°'),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, children: [
      Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
      const SizedBox(height: 2),
      Text(value, style: const TextStyle(fontSize: 13)),
    ]);
  }
}

class _AnnotationSheet extends StatelessWidget {
  const _AnnotationSheet(this.annotation, {required this.onClose});
  final Annotation annotation;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final color = annotation.isStar ? AppTheme.star : AppTheme.accent;
    return Container(
      width: double.infinity,
      color: AppTheme.panel,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(annotation.isStar ? Icons.star : Icons.blur_circular,
              color: color, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  annotation.displayName ??
                      (annotation.names.isNotEmpty
                          ? annotation.names.first
                          : 'Unknown'),
                  style: const TextStyle(fontSize: 16),
                ),
                if (annotation.names.length > 1) ...[
                  const SizedBox(height: 2),
                  Text(annotation.names.skip(1).join(', '),
                      style: const TextStyle(
                          color: Colors.white38, fontSize: 12)),
                ],
                const SizedBox(height: 4),
                Text(
                  'Type: ${annotation.kind}  ·  '
                  'x:${annotation.pixelX.toStringAsFixed(0)}  '
                  'y:${annotation.pixelY.toStringAsFixed(0)}',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 18),
            onPressed: onClose,
          ),
        ],
      ),
    );
  }
}

// ── Image view modes ────────────────────────────────────────────────────────
enum _ImageView { original, annotated, redGreen, extraction }

class _ImageTypeTabs extends StatelessWidget {
  const _ImageTypeTabs({
    required this.selected,
    required this.sub,
    required this.onChanged,
  });
  final _ImageView selected;
  final Submission sub;
  final void Function(_ImageView) onChanged;

  @override
  Widget build(BuildContext context) {
    final tabs = [
      (
        _ImageView.original,
        Icons.photo,
        'Original',
        true, // always available
      ),
      (
        _ImageView.annotated,
        Icons.grid_on,
        'Annotated',
        sub.annotatedImageUrl != null,
      ),
      (
        _ImageView.redGreen,
        Icons.bubble_chart,
        'Red/Green',
        sub.redgreenImageUrl != null,
      ),
      (
        _ImageView.extraction,
        Icons.scatter_plot,
        'Extraction',
        sub.extractionImageUrl != null,
      ),
    ];

    return Container(
      color: AppTheme.panel,
      child: Row(
        children: tabs.map((t) {
          final (view, icon, label, available) = t;
          final isSelected = selected == view;
          return Expanded(
            child: InkWell(
              onTap: available ? () => onChanged(view) : null,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      icon,
                      size: 20,
                      color: !available
                          ? Colors.white12
                          : isSelected
                              ? AppTheme.star
                              : Colors.white38,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      label,
                      style: TextStyle(
                        fontSize: 10,
                        color: !available
                            ? Colors.white12
                            : isSelected
                                ? AppTheme.star
                                : Colors.white38,
                        fontWeight: isSelected
                            ? FontWeight.bold
                            : FontWeight.normal,
                      ),
                    ),
                    if (isSelected)
                      Container(
                        margin: const EdgeInsets.only(top: 3),
                        height: 2,
                        width: 24,
                        color: AppTheme.star,
                      ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
