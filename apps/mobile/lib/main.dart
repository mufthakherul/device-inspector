import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:qr_flutter/qr_flutter.dart';

void main() {
  runApp(const InspectaMobileApp());
}

class InspectaMobileApp extends StatelessWidget {
  const InspectaMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Inspecta Mobile',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      home: const MobileHomePage(),
    );
  }
}

class MobileHomePage extends StatefulWidget {
  const MobileHomePage({super.key});

  @override
  State<MobileHomePage> createState() => _MobileHomePageState();
}

class _MobileHomePageState extends State<MobileHomePage> {
  Map<String, dynamic>? _report;
  Map<String, dynamic>? _verifyResult;
  Map<String, dynamic>? _capabilityInfo;
  String? _status;
  String _pairingToken = 'inspecta:pairing:offline';

  @override
  void initState() {
    super.initState();
    _loadCapabilityMatrix();
  }

  Future<void> _loadCapabilityMatrix() async {
    try {
      final text = await rootBundle.loadString('assets/capability-matrix.json');
      final parsed = jsonDecode(text) as Map<String, dynamic>;
      final surfaces = parsed['surfaces'] as Map<String, dynamic>?;
      setState(() {
        _capabilityInfo = {
          'matrix_version': parsed['matrix_version'],
          'mobile': surfaces?['mobile'],
        };
      });
    } catch (_) {
      // Keep app functional even if asset is absent.
    }
  }

  Future<void> _pickReportJson() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
    );

    if (result == null || result.files.single.path == null) {
      return;
    }

    final file = File(result.files.single.path!);
    final parsed = jsonDecode(await file.readAsString()) as Map<String, dynamic>;

    setState(() {
      _report = parsed;
      _status = 'Loaded report: ${file.path}';
    });
  }

  Future<void> _verifyManifest() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
      dialogTitle: 'Select artifacts/manifest.json',
    );

    if (result == null || result.files.single.path == null) {
      return;
    }

    final manifestFile = File(result.files.single.path!);
    final manifestDir = manifestFile.parent.parent;

    final manifest = jsonDecode(await manifestFile.readAsString()) as Map<String, dynamic>;
    final entries = (manifest['entries'] as List<dynamic>? ?? const []);

    final mismatches = <Map<String, dynamic>>[];
    final missing = <String>[];

    for (final entry in entries) {
      final item = entry as Map<String, dynamic>;
      final rel = item['path'] as String?;
      final expected = item['sha256'] as String?;
      if (rel == null || expected == null) {
        mismatches.add({'path': rel ?? 'unknown', 'reason': 'missing metadata'});
        continue;
      }

      final file = File('${manifestDir.path}${Platform.pathSeparator}$rel');
      if (!await file.exists()) {
        missing.add(rel);
        mismatches.add({'path': rel, 'reason': 'missing file'});
        continue;
      }

      final bytes = await file.readAsBytes();
      final actual = sha256.convert(bytes).toString();
      if (actual != expected) {
        mismatches.add({
          'path': rel,
          'reason': 'hash mismatch',
          'expected': expected,
          'actual': actual,
        });
      }
    }

    setState(() {
      _verifyResult = {
        'ok': mismatches.isEmpty,
        'checked': entries.length,
        'mismatches': mismatches,
        'missing': missing,
        'exit_code': mismatches.isEmpty ? 0 : 1,
        'exit_reason': mismatches.isEmpty ? 'verified' : 'integrity_mismatch',
      };
      _status = 'Manifest verification complete.';
    });
  }

  Future<void> _scanPairingQr() async {
    final token = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const QrScanPage()),
    );

    if (token == null || token.isEmpty) {
      return;
    }

    setState(() {
      _pairingToken = token;
      _status = 'Pairing token updated from QR.';
    });
  }

  @override
  Widget build(BuildContext context) {
    final summary = _report?['summary'] as Map<String, dynamic>?;
    final device = _report?['device'] as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(title: const Text('Inspecta Mobile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Report Viewer', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ElevatedButton(
                        onPressed: _pickReportJson,
                        child: const Text('Open report.json'),
                      ),
                      ElevatedButton(
                        onPressed: _verifyManifest,
                        child: const Text('Verify bundle manifest'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('Vendor: ${device?['vendor'] ?? 'N/A'}'),
                  Text('Model: ${device?['model'] ?? 'N/A'}'),
                  Text('Serial: ${device?['serial'] ?? 'N/A'}'),
                  Text('Score: ${summary?['overall_score'] ?? 'N/A'}'),
                  Text('Grade: ${summary?['grade'] ?? 'N/A'}'),
                ],
              ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Pairing (offline)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text('Current token: $_pairingToken'),
                  const SizedBox(height: 10),
                  QrImageView(data: _pairingToken, version: QrVersions.auto, size: 150),
                  const SizedBox(height: 10),
                  ElevatedButton(
                    onPressed: _scanPairingQr,
                    child: const Text('Scan pairing QR'),
                  ),
                ],
              ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Verification output', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  SelectableText(const JsonEncoder.withIndent('  ').convert(_verifyResult ?? {'ok': false, 'status': 'not-run'})),
                ],
              ),
            ),
          ),
          if (_capabilityInfo != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Capability Matrix', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text('Version: ${_capabilityInfo?['matrix_version'] ?? 'N/A'}'),
                    const SizedBox(height: 4),
                    Text('Mobile capabilities:'),
                    ...( ((_capabilityInfo?['mobile'] as Map<String, dynamic>?)?['capabilities'] as List<dynamic>? ?? const [])
                        .map((cap) => Text('- $cap'))),
                  ],
                ),
              ),
            ),
          if (_status != null)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(_status!, style: const TextStyle(color: Colors.teal)),
            ),
        ],
      ),
    );
  }
}

class QrScanPage extends StatefulWidget {
  const QrScanPage({super.key});

  @override
  State<QrScanPage> createState() => _QrScanPageState();
}

class _QrScanPageState extends State<QrScanPage> {
  bool _done = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan pairing QR')),
      body: MobileScanner(
        onDetect: (capture) {
          if (_done) return;
          final value = capture.barcodes.isNotEmpty
              ? capture.barcodes.first.rawValue
              : null;
          if (value == null || value.isEmpty) return;
          _done = true;
          Navigator.of(context).pop(value);
        },
      ),
    );
  }
}
