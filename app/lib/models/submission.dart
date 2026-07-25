/// Data models mirroring the AkashGanga backend responses.

class Annotation {
  final String kind;
  final List<String> names;
  final String? displayName;
  final double pixelX;
  final double pixelY;
  final double radius;

  Annotation({
    required this.kind,
    required this.names,
    required this.displayName,
    required this.pixelX,
    required this.pixelY,
    required this.radius,
  });

  bool get isStar => kind == 'star';

  factory Annotation.fromJson(Map<String, dynamic> json) => Annotation(
        kind: json['kind'] as String? ?? 'unknown',
        names: (json['names'] as List?)?.map((e) => e.toString()).toList() ?? [],
        displayName: json['display_name'] as String?,
        pixelX: (json['pixel_x'] as num?)?.toDouble() ?? 0,
        pixelY: (json['pixel_y'] as num?)?.toDouble() ?? 0,
        radius: (json['radius'] as num?)?.toDouble() ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'kind': kind,
        'names': names,
        'display_name': displayName,
        'pixel_x': pixelX,
        'pixel_y': pixelY,
        'radius': radius,
      };
}

class Submission {
  final int id;
  final String status; // pending | submitted | solving | success | failed
  final String? error;
  final String? originalFilename;
  final String? sourceUrl;
  final String? imageUrl;
  final String? annotatedImageUrl;
  final String? redgreenImageUrl;
  final String? extractionImageUrl;
  final String? solverJobId;
  final double? ra;
  final double? dec;
  final double? pixscale;
  final double? orientation;
  final double? radius;
  final double? parity;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<Annotation> annotations;
  final List<String> objectsInField;

  Submission({
    required this.id,
    required this.status,
    this.error,
    this.originalFilename,
    this.sourceUrl,
    this.imageUrl,
    this.annotatedImageUrl,
    this.redgreenImageUrl,
    this.extractionImageUrl,
    this.solverJobId,
    this.ra,
    this.dec,
    this.pixscale,
    this.orientation,
    this.radius,
    this.parity,
    required this.createdAt,
    required this.updatedAt,
    this.annotations = const [],
    this.objectsInField = const [],
  });

  bool get isDone => status == 'success' || status == 'failed';
  bool get isSolved => status == 'success';

  factory Submission.fromJson(Map<String, dynamic> json) => Submission(
        id: json['id'] as int,
        status: json['status'] as String,
        error: json['error'] as String?,
        originalFilename: json['original_filename'] as String?,
        sourceUrl: json['source_url'] as String?,
        imageUrl: json['image_url'] as String?,
        annotatedImageUrl: json['annotated_image_url'] as String?,
        redgreenImageUrl: json['redgreen_image_url'] as String?,
        extractionImageUrl: json['extraction_image_url'] as String?,
        solverJobId: json['solver_job_id'] as String?,
        ra: (json['ra'] as num?)?.toDouble(),
        dec: (json['dec'] as num?)?.toDouble(),
        pixscale: (json['pixscale'] as num?)?.toDouble(),
        orientation: (json['orientation'] as num?)?.toDouble(),
        radius: (json['radius'] as num?)?.toDouble(),
        parity: (json['parity'] as num?)?.toDouble(),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
        annotations: (json['annotations'] as List?)
                ?.map((e) => Annotation.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        objectsInField:
            (json['objects_in_field'] as List?)?.map((e) => e.toString()).toList() ??
                const [],
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'status': status,
        'error': error,
        'original_filename': originalFilename,
        'source_url': sourceUrl,
        'image_url': imageUrl,
        'annotated_image_url': annotatedImageUrl,
        'redgreen_image_url': redgreenImageUrl,
        'extraction_image_url': extractionImageUrl,
        'solver_job_id': solverJobId,
        'ra': ra,
        'dec': dec,
        'pixscale': pixscale,
        'orientation': orientation,
        'radius': radius,
        'parity': parity,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
        'annotations': annotations.map((a) => a.toJson()).toList(),
        'objects_in_field': objectsInField,
      };
}
