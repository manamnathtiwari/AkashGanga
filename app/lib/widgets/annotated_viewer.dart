import 'dart:ui' as ui;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../api/config.dart';
import '../models/submission.dart';
import '../screens/result_screen.dart' show _ImageView;
import '../theme.dart';

/// Pan/zoom image with catalog objects overlaid at their pixel positions.
///
/// Annotation pixel coordinates are in the ORIGINAL image's pixel space, so we
/// load the image, read its intrinsic size, and map pixels -> displayed size.
class AnnotatedViewer extends StatefulWidget {
  const AnnotatedViewer({
    super.key,
    required this.submission,
    required this.showStars,
    required this.showDeepSky,
    this.imageView = _ImageView.original,
    this.onTapAnnotation,
  });

  final Submission submission;
  final bool showStars;
  final bool showDeepSky;
  final _ImageView imageView;
  final ValueChanged<Annotation>? onTapAnnotation;

  @override
  State<AnnotatedViewer> createState() => _AnnotatedViewerState();
}

class _AnnotatedViewerState extends State<AnnotatedViewer> {
  Size? _imageSize; // intrinsic pixel size of the original image

  String get _resolvedUrl {
    final sub = widget.submission;
    // Pick URL based on selected image view
    final raw = switch (widget.imageView) {
      _ImageView.original   => sub.imageUrl ?? '',
      _ImageView.annotated  => sub.annotatedImageUrl ?? sub.imageUrl ?? '',
      _ImageView.redGreen   => sub.redgreenImageUrl ?? sub.imageUrl ?? '',
      _ImageView.extraction => sub.extractionImageUrl ?? sub.imageUrl ?? '',
    };
    if (raw.startsWith('http')) return raw;
    return '${AppConfig.mediaBase}$raw';
  }

  void _resolveImageSize(ImageProvider provider) {
    final stream = provider.resolve(const ImageConfiguration());
    stream.addListener(ImageStreamListener((info, _) {
      if (!mounted) return;
      final size = Size(
        info.image.width.toDouble(),
        info.image.height.toDouble(),
      );
      if (_imageSize != size) setState(() => _imageSize = size);
    }));
  }

  @override
  Widget build(BuildContext context) {
    final provider = CachedNetworkImageProvider(_resolvedUrl);
    _resolveImageSize(provider);

    final visible = widget.submission.annotations.where((a) {
      // Only show our overlay on the original view;
      // the other 3 views already have overlays baked in by nova.
      if (widget.imageView != _ImageView.original) return false;
      if (a.isStar) return widget.showStars;
      return widget.showDeepSky;
    }).toList();

    return InteractiveViewer(
      minScale: 0.5,
      maxScale: 6,
      child: Center(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return AspectRatio(
              aspectRatio: _imageSize == null
                  ? 1
                  : _imageSize!.width / _imageSize!.height,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image(image: provider, fit: BoxFit.contain),
                  if (_imageSize != null)
                    LayoutBuilder(
                      builder: (context, box) {
                        final scaleX = box.maxWidth / _imageSize!.width;
                        final scaleY = box.maxHeight / _imageSize!.height;
                        return Stack(
                          children: [
                            CustomPaint(
                              size: Size(box.maxWidth, box.maxHeight),
                              painter: _MarkerPainter(visible, scaleX, scaleY),
                            ),
                            ...visible.map((a) => _label(a, scaleX, scaleY)),
                          ],
                        );
                      },
                    ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _label(Annotation a, double scaleX, double scaleY) {
    final left = a.pixelX * scaleX;
    final top = a.pixelY * scaleY;
    final color = a.isStar ? AppTheme.star : AppTheme.accent;
    return Positioned(
      left: left + 8,
      top: top - 8,
      child: GestureDetector(
        onTap: () => widget.onTapAnnotation?.call(a),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.55),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: color, width: 1),
          ),
          child: Text(
            a.displayName ?? (a.names.isNotEmpty ? a.names.first : '?'),
            style: TextStyle(color: color, fontSize: 11),
          ),
        ),
      ),
    );
  }
}

class _MarkerPainter extends CustomPainter {
  _MarkerPainter(this.annotations, this.scaleX, this.scaleY);
  final List<Annotation> annotations;
  final double scaleX;
  final double scaleY;

  @override
  void paint(Canvas canvas, Size size) {
    for (final a in annotations) {
      final center = Offset(a.pixelX * scaleX, a.pixelY * scaleY);
      final color = a.isStar ? AppTheme.star : AppTheme.accent;
      final paint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      if (a.isStar) {
        _drawCross(canvas, center, 6, paint);
      } else {
        final r = (a.radius * scaleX).clamp(10.0, 60.0);
        canvas.drawCircle(center, r, paint);
      }
    }
  }

  void _drawCross(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawLine(Offset(c.dx - s, c.dy), Offset(c.dx + s, c.dy), p);
    canvas.drawLine(Offset(c.dx, c.dy - s), Offset(c.dx, c.dy + s), p);
  }

  @override
  bool shouldRepaint(covariant _MarkerPainter old) =>
      old.annotations != annotations ||
      old.scaleX != scaleX ||
      old.scaleY != scaleY;
}

/// Kept for potential FITS decoding hooks later.
typedef ImageDecoder = Future<ui.Image> Function(List<int> bytes);
