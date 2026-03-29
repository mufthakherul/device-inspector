export interface InspectaReport {
  report_version: string;
  generated_at: string;
  mode?: string;
  profile?: string;
  agent?: { name?: string; version?: string };
  device?: {
    vendor?: string;
    model?: string;
    serial?: string;
    bios_version?: string;
  };
  summary?: {
    overall_score?: number;
    grade?: string;
    recommendation?: string;
  };
  scores?: Record<string, number>;
  tests?: Array<{
    name?: string;
    status?: string;
    status_detail?: string;
    error?: string;
  }>;
  artifacts?: string[];
}
